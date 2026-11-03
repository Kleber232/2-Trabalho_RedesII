# Parte 6 — Implementação: estatística e gráficos (0:30)

Arquivo mostrado: `plot_results.py`.

## Cena 6.1 — Agrupamento, média e desvio-padrão (0:20)

**Fundo / tela:**
Função `plot_metric` de `plot_results.py`:

```python
for run in runs:
    key = (str(run["load"]), str(run["scenario"]), str(run["protocol"]))
    grouped[key].append(float(run[metric]))
...
means.append(statistics.fmean(values))
errors.append(statistics.stdev(values) if len(values) > 1 else 0.0)
...
axis.bar(positions, means, width, yerr=errors, capsize=4,
         label=PROTOCOL_LABELS[protocol])
```

**Narração:**

O plot results agrupa as amostras por carga, cenário e protocolo e calcula média e desvio-padrão das cinco repetições. No matplotlib, o y err desenha o desvio como barra de erro, exigida pelo enunciado para mostrar se a diferença entre protocolos é real ou ruído.

## Cena 6.2 — Validação e tabela-resumo (0:15)

**Fundo / tela:**
Função `load_runs` e o arquivo gerado `results/20261020T205948Z-881/plots/summary.md`:

```python
expected_tests = {f"T{index:02d}" for index in range(1, 13)}
found_tests = {str(run["test_id"]) for run in runs}
if found_tests != expected_tests:
    raise ValueError(f"Resultados incompletos; testes ausentes: ...")
```

**Narração:**

Antes de desenhar, o script confere se os doze testes estão presentes. Ele gera os gráficos de TTFB, tempo total e requisições por segundo, e uma tabela com média, mediana, desvio e percentis de cada teste.
