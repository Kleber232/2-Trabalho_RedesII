#!/usr/bin/env python3
"""Generate error-bar plots from benchmark_client.py results.json."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = {
    "mean_ttfb_us": ("TTFB médio (µs)", "ttfb"),
    "total_load_us": ("Tempo total da carga (µs)", "total_load"),
    "rps": ("Requisições por segundo (RPS)", "rps"),
}
PROTOCOL_LABELS = {"http1": "HTTP/1.1", "http2": "HTTP/2", "http3": "HTTP/3"}


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Não é possível calcular percentil sem amostras.")
    position = (len(ordered) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def load_runs(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    runs = data.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError(f"Nenhuma amostra de execução encontrada em {path}.")
    expected_tests = {f"T{index:02d}" for index in range(1, 13)}
    found_tests = {str(run["test_id"]) for run in runs}
    if found_tests != expected_tests:
        missing = ", ".join(sorted(expected_tests - found_tests))
        raise ValueError(f"Resultados incompletos; testes ausentes: {missing or 'nenhum'}.")
    return runs


def plot_metric(runs: list[dict[str, Any]], output_dir: Path, metric: str) -> None:
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for run in runs:
        key = (str(run["load"]), str(run["scenario"]), str(run["protocol"]))
        grouped[key].append(float(run[metric]))

    combinations = sorted(
        {(load, scenario) for load, scenario, _ in grouped},
        key=lambda item: (item[0], item[1]),
    )
    protocols = ["http1", "http2", "http3"]
    width = 0.24
    figure, axis = plt.subplots(figsize=(10, 6))
    for protocol_index, protocol in enumerate(protocols):
        means: list[float] = []
        errors: list[float] = []
        positions: list[float] = []
        for group_index, (load, scenario) in enumerate(combinations):
            values = grouped.get((load, scenario, protocol))
            if not values:
                continue
            means.append(statistics.fmean(values))
            errors.append(statistics.stdev(values) if len(values) > 1 else 0.0)
            positions.append(group_index + (protocol_index - 1) * width)
        axis.bar(
            positions,
            means,
            width,
            yerr=errors,
            capsize=4,
            label=PROTOCOL_LABELS[protocol],
        )

    axis.set_xticks(
        range(len(combinations)),
        [f"Carga {load}\n{scenario}" for load, scenario in combinations],
    )
    axis.set_ylabel(METRICS[metric][0])
    axis.set_xlabel("Perfil de carga e cenário")
    axis.set_title(f"{METRICS[metric][0]} por protocolo (média ± desvio-padrão)")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(title="Protocolo")
    figure.tight_layout()
    figure.savefig(output_dir / f"{METRICS[metric][1]}.png", dpi=160)
    plt.close(figure)


def write_summary(
    runs: list[dict[str, Any]],
    requests: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[str(run["test_id"])].append(run)
    requests_by_test: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        requests_by_test[str(request["test_id"])].append(request)

    rows: list[dict[str, Any]] = []
    for test_id, samples in sorted(grouped.items()):
        test_requests = requests_by_test[test_id]
        row: dict[str, Any] = {
            "test_id": test_id,
            "protocol": samples[0]["protocol"],
            "load": samples[0]["load"],
            "scenario": samples[0]["scenario"],
        }
        for metric in ("mean_ttfb_us", "rps", "total_load_us"):
            sample_values = [float(sample[metric]) for sample in samples]
            slug = {"mean_ttfb_us": "ttfb", "rps": "rps", "total_load_us": "total"}[metric]
            row[f"{slug}_mean"] = statistics.fmean(sample_values)
            row[f"{slug}_median"] = statistics.median(sample_values)
            row[f"{slug}_std"] = (
                statistics.stdev(sample_values) if len(sample_values) > 1 else 0.0
            )
            row[f"{slug}_sample_p50"] = percentile(sample_values, 50)
            row[f"{slug}_sample_p99"] = percentile(sample_values, 99)
        for metric, slug in (("ttfb_us", "ttfb"), ("total_us", "request_total")):
            values = [float(request[metric]) for request in test_requests]
            row[f"{slug}_request_p50"] = percentile(values, 50)
            row[f"{slug}_request_p99"] = percentile(values, 99)
        rows.append(row)

    output_csv = output_dir / "summary.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    markdown = [
        "# Resumo estatístico dos 12 testes",
        "",
        "Médias, medianas e desvios-padrão são calculados sobre as cinco repetições; "
        "p50/p99 de TTFB e duração da requisição são calculados sobre requisições "
        "individuais. p50/p99 de RPS e tempo total da carga são calculados sobre as "
        "cinco repetições. Tempos em microssegundos.",
        "",
        "| ID | Protocolo | Carga | Rede | TTFB média (µs) | TTFB mediana (µs) | TTFB DP (µs) | TTFB req. p50 (µs) | TTFB req. p99 (µs) | RPS média | RPS mediana | RPS DP | RPS p50 amostras | RPS p99 amostras | Carga média (µs) | Carga mediana (µs) | Carga DP (µs) | Carga p50 amostras (µs) | Carga p99 amostras (µs) | Duração req. p50 (µs) | Duração req. p99 (µs) |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        markdown.append(
            "| {test_id} | {protocol} | {load} | {scenario} | "
            "{ttfb_mean:.2f} | {ttfb_median:.2f} | {ttfb_std:.2f} | "
            "{ttfb_request_p50:.2f} | {ttfb_request_p99:.2f} | "
            "{rps_mean:.4f} | {rps_median:.4f} | {rps_std:.4f} | "
            "{rps_sample_p50:.4f} | {rps_sample_p99:.4f} | "
            "{total_mean:.2f} | {total_median:.2f} | {total_std:.2f} | "
            "{total_sample_p50:.2f} | {total_sample_p99:.2f} | "
            "{request_total_request_p50:.2f} | {request_total_request_p99:.2f} |".format(
                **row
            )
        )
    (output_dir / "summary.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/results.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/plots"))
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as source:
        data = json.load(source)
    runs = load_runs(args.input)
    requests = data.get("requests")
    if not isinstance(requests, list) or not requests:
        raise ValueError(f"Nenhum registro individual de requisição encontrado em {args.input}.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for metric in METRICS:
        plot_metric(runs, args.output_dir, metric)
    write_summary(runs, requests, args.output_dir)
    print(f"Gráficos salvos em {args.output_dir}")


if __name__ == "__main__":
    main()
