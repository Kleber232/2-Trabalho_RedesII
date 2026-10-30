#!/usr/bin/env python3
"""Asynchronous HTTP/1.1, HTTP/2, and HTTP/3 download benchmark."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import statistics
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator
from urllib.parse import urlsplit

import httpx
from aioquic.asyncio import QuicConnectionProtocol, connect
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import DataReceived, HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent
from aioquic.h3.connection import H3_ALPN

CSV_FIELDS = [
    "timestamp",
    "test_id",
    "protocol",
    "scenario",
    "load",
    "sample_index",
    "request_index",
    "url",
    "status_code",
    "http_version",
    "ttfb_us",
    "total_us",
    "bytes_received",
]

ENDPOINTS = {
    "http1": ("http://server-http1", "HTTP/1.1"),
    "http2": ("https://server-http2", "HTTP/2"),
    "http3": ("https://server-http3", "HTTP/3"),
}


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Não é possível calcular percentil sem amostras.")
    position = (len(ordered) - 1) * percent / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def file_paths(load: str) -> list[str]:
    if load == "A":
        return ["/file_50mb.bin"]
    return [f"/file_{index}.bin" for index in range(1, 101)]


def summarize(
    args: argparse.Namespace,
    sample_index: int,
    requests: list[dict[str, Any]],
    batch_started_ns: int,
) -> dict[str, Any]:
    elapsed_us = (time.perf_counter_ns() - batch_started_ns) / 1_000
    latencies = [float(row["total_us"]) for row in requests]
    ttfbs = [float(row["ttfb_us"]) for row in requests]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_id": args.test_id,
        "protocol": args.protocol,
        "scenario": args.scenario,
        "load": args.load,
        "sample_index": sample_index,
        "connection_mode": "cold" if args.load == "A" else "warm",
        "request_count": len(requests),
        "bytes_received": sum(int(row["bytes_received"]) for row in requests),
        "batch_duration_us": elapsed_us,
        "rps": len(requests) / (elapsed_us / 1_000_000),
        "mean_ttfb_us": statistics.fmean(ttfbs),
        "p50_ttfb_us": percentile(ttfbs, 50),
        "p99_ttfb_us": percentile(ttfbs, 99),
        "mean_request_total_us": statistics.fmean(latencies),
        "p50_total_us": percentile(latencies, 50),
        "p99_total_us": percentile(latencies, 99),
        "total_load_us": elapsed_us,
    }


def make_record(
    args: argparse.Namespace,
    sample_index: int,
    request_index: int,
    url: str,
    status_code: int,
    http_version: str,
    ttfb_us: float,
    total_us: float,
    bytes_received: int,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_id": args.test_id,
        "protocol": args.protocol,
        "scenario": args.scenario,
        "load": args.load,
        "sample_index": sample_index,
        "request_index": request_index,
        "url": url,
        "status_code": status_code,
        "http_version": http_version,
        "ttfb_us": ttfb_us,
        "total_us": total_us,
        "bytes_received": bytes_received,
    }


async def httpx_request(
    client: httpx.AsyncClient,
    url: str,
    protocol: str,
    args: argparse.Namespace,
    sample_index: int,
    request_index: int,
) -> dict[str, Any]:
    started_ns = time.perf_counter_ns()
    request = client.build_request(
        "GET",
        url,
        headers={
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
        },
    )
    response = await client.send(request, stream=True)
    try:
        response.raise_for_status()
        if protocol == "http2" and response.http_version != "HTTP/2":
            raise RuntimeError(f"HTTP/2 solicitado, servidor respondeu {response.http_version}.")
        if protocol == "http1" and response.http_version != "HTTP/1.1":
            raise RuntimeError(f"HTTP/1.1 solicitado, servidor respondeu {response.http_version}.")
        first_body_ns: int | None = None
        byte_count = 0
        async for chunk in response.aiter_bytes():
            if first_body_ns is None:
                first_body_ns = time.perf_counter_ns()
            byte_count += len(chunk)
        finished_ns = time.perf_counter_ns()
        if first_body_ns is None:
            first_body_ns = finished_ns
        return make_record(
            args,
            sample_index,
            request_index,
            url,
            response.status_code,
            response.http_version,
            (first_body_ns - started_ns) / 1_000,
            (finished_ns - started_ns) / 1_000,
            byte_count,
        )
    finally:
        await response.aclose()


class Http3BenchmarkProtocol(QuicConnectionProtocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.http = H3Connection(self._quic)
        self.pending: dict[int, dict[str, Any]] = {}

    async def fetch(
        self,
        url: str,
        args: argparse.Namespace,
        sample_index: int,
        request_index: int,
        started_ns: int,
    ) -> dict[str, Any]:
        parsed = urlsplit(url)
        authority = parsed.netloc
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"
        stream_id = self._quic.get_next_available_stream_id()
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self.pending[stream_id] = {
            "future": future,
            "started_ns": started_ns,
            "first_body_ns": None,
            "byte_count": 0,
            "status_code": 0,
        }
        self.http.send_headers(
            stream_id,
            [
                (b":method", b"GET"),
                (b":scheme", b"https"),
                (b":authority", authority.encode()),
                (b":path", path.encode()),
                (b"cache-control", b"no-cache, no-store"),
                (b"pragma", b"no-cache"),
            ],
        )
        self.http.send_data(stream_id, b"", end_stream=True)
        self.transmit()
        return await future

    def quic_event_received(self, event: QuicEvent) -> None:
        for http_event in self.http.handle_event(event):
            state = self.pending.get(http_event.stream_id)
            if state is None:
                continue
            if isinstance(http_event, HeadersReceived):
                for name, value in http_event.headers:
                    if name == b":status":
                        state["status_code"] = int(value.decode())
                if http_event.stream_ended:
                    self._finish(http_event.stream_id, state)
            elif isinstance(http_event, DataReceived):
                if http_event.data and state["first_body_ns"] is None:
                    state["first_body_ns"] = time.perf_counter_ns()
                state["byte_count"] += len(http_event.data)
                if http_event.stream_ended:
                    self._finish(http_event.stream_id, state)

    def _finish(self, stream_id: int, state: dict[str, Any]) -> None:
        future = state["future"]
        if future.done():
            return
        finished_ns = time.perf_counter_ns()
        first_body_ns = state["first_body_ns"] or finished_ns
        future.set_result(
            {
                "started_ns": state["started_ns"],
                "first_body_ns": first_body_ns,
                "finished_ns": finished_ns,
                "status_code": state["status_code"],
                "byte_count": state["byte_count"],
            }
        )
        self.pending.pop(stream_id, None)


@asynccontextmanager
async def http3_connection(
    host: str, port: int, ca_file: Path
) -> AsyncIterator[Http3BenchmarkProtocol]:
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        server_name=host,
        cafile=str(ca_file),
    )
    async with connect(
        host,
        port,
        configuration=configuration,
        create_protocol=Http3BenchmarkProtocol,
        wait_connected=True,
    ) as protocol:
        try:
            yield protocol
        finally:
            protocol.close()


async def http3_request(
    protocol: Http3BenchmarkProtocol,
    url: str,
    args: argparse.Namespace,
    sample_index: int,
    request_index: int,
    started_ns: int,
) -> dict[str, Any]:
    result = await protocol.fetch(url, args, sample_index, request_index, started_ns)
    if not 200 <= result["status_code"] < 300:
        raise RuntimeError(f"HTTP/3 retornou status {result['status_code']} para {url}.")
    return make_record(
        args,
        sample_index,
        request_index,
        url,
        result["status_code"],
        "HTTP/3",
        (result["first_body_ns"] - started_ns) / 1_000,
        (result["finished_ns"] - started_ns) / 1_000,
        result["byte_count"],
    )


def make_httpx_client(protocol: str, verify: Path) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        http1=protocol == "http1",
        http2=protocol == "http2",
        verify=False if protocol == "http1" else str(verify),
        follow_redirects=False,
        trust_env=False,
        timeout=httpx.Timeout(120),
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
    )


async def run_sample(
    args: argparse.Namespace, sample_index: int, ca_file: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    base_url, _ = ENDPOINTS[args.protocol]
    urls = [f"{base_url}{path}" for path in file_paths(args.load)]
    records: list[dict[str, Any]] = []
    batch_started_ns = time.perf_counter_ns()
    is_cold = args.load == "A"

    if args.protocol == "http3":
        host, port = "server-http3", 443
        if is_cold:
            for index, url in enumerate(urls, start=1):
                started_ns = time.perf_counter_ns()
                async with http3_connection(host, port, ca_file) as protocol:
                    records.append(
                        await http3_request(
                            protocol, url, args, sample_index, index, started_ns
                        )
                    )
        else:
            async with http3_connection(host, port, ca_file) as protocol:
                tasks = [
                    asyncio.create_task(
                        http3_request(
                            protocol,
                            url,
                            args,
                            sample_index,
                            index,
                            time.perf_counter_ns(),
                        )
                    )
                    for index, url in enumerate(urls, start=1)
                ]
                records.extend(await asyncio.gather(*tasks))
    elif is_cold:
        for index, url in enumerate(urls, start=1):
            async with make_httpx_client(args.protocol, ca_file) as client:
                records.append(
                    await httpx_request(
                        client, url, args.protocol, args, sample_index, index
                    )
                )
    else:
        async with make_httpx_client(args.protocol, ca_file) as client:
            tasks = [
                asyncio.create_task(
                    httpx_request(
                        client, url, args.protocol, args, sample_index, index
                    )
                )
                for index, url in enumerate(urls, start=1)
            ]
            records.extend(await asyncio.gather(*tasks))

    summary = summarize(args, sample_index, records, batch_started_ns)
    return summary, records


def append_results(
    output_dir: Path,
    summaries: list[dict[str, Any]],
    requests: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "results.json"
    if json_path.exists():
        with json_path.open(encoding="utf-8") as source:
            data = json.load(source)
    else:
        data = {"schema_version": 1, "runs": [], "requests": []}
    data["runs"].extend(summaries)
    data["requests"].extend(requests)
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    csv_path = output_dir / "results.csv"
    write_header = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(requests)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--protocol", required=True, choices=ENDPOINTS)
    parser.add_argument("--load", required=True, choices=("A", "B"))
    parser.add_argument("--scenario", required=True, choices=("LAN", "WAN"))
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--ca-file", type=Path, default=Path("certs/server.crt"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.repetitions < 2:
        parser.error("--repetitions deve ser pelo menos 2 para estimar variabilidade.")
    return args


async def main() -> None:
    args = parse_args()
    summaries: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    for sample_index in range(1, args.repetitions + 1):
        summary, records = await run_sample(args, sample_index, args.ca_file)
        summaries.append(summary)
        requests.extend(records)
        print(
            f"{args.test_id} amostra {sample_index}/{args.repetitions}: "
            f"{summary['rps']:.2f} RPS, "
            f"p50={summary['p50_total_us']:.0f} us, "
            f"p99={summary['p99_total_us']:.0f} us"
        )
    append_results(args.output_dir, summaries, requests)


if __name__ == "__main__":
    asyncio.run(main())
