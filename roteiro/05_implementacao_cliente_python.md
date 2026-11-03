# Parte 5 — Implementação: cliente de benchmark em Python (2:25)

Arquivo mostrado: `benchmark_client.py`.

## Cena 5.1 — Por que um cliente próprio e por que assíncrono (0:25)

**Fundo / tela:**
Topo de `benchmark_client.py`:

```python
import asyncio
import httpx
from aioquic.asyncio import QuicConnectionProtocol, connect
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import DataReceived, HeadersReceived

ENDPOINTS = {
    "http1": ("http://server-http1", "HTTP/1.1"),
    "http2": ("https://server-http2", "HTTP/2"),
    "http3": ("https://server-http3", "HTTP/3"),
}
```

**Narração:**

Usamos um cliente próprio porque navegadores têm cache e otimizações que não controlamos. Ele é assíncrono, com asyncio: enquanto uma requisição espera a rede, o programa atende outras, e assim disparamos cem downloads ao mesmo tempo. O httpx cuida do HTTP um ponto um e do HTTP dois, e o aioquic do HTTP três. O ENDPOINTS liga cada protocolo ao seu servidor.

## Cena 5.2 — Requisição com httpx e medição de TTFB (0:30)

**Fundo / tela:**
Função `httpx_request`, destacando as linhas de tempo:

```python
started_ns = time.perf_counter_ns()
request = client.build_request("GET", url,
    headers={"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
response = await client.send(request, stream=True)
...
if protocol == "http2" and response.http_version != "HTTP/2":
    raise RuntimeError(...)
first_body_ns = None
async for chunk in response.aiter_bytes():
    if first_body_ns is None:
        first_body_ns = time.perf_counter_ns()
    byte_count += len(chunk)
finished_ns = time.perf_counter_ns()
```

**Narração:**

Esta função mede uma requisição. O relógio é o perf counter em nanossegundos, monotônico e de alta resolução. Marcamos o início, enviamos o GET pedindo para não usar cache, com stream igual a true. Sem o streaming, o httpx baixaria tudo antes de devolver o controle, e não saberíamos quando chegou o primeiro byte. Conferimos se a versão do protocolo é a pedida e lemos o corpo em pedaços: o primeiro pedaço marca o TTFB, o último, o tempo total.

## Cena 5.3 — Configuração do cliente httpx (0:20)

**Fundo / tela:**
Função `make_httpx_client`:

```python
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
```

**Narração:**

O cliente httpx habilita só o protocolo do teste, verifica o nosso certificado e, com trust env falso, ignora proxies do sistema. O limite de uma conexão faz o HTTP dois multiplexar tudo num canal, enquanto no HTTP um ponto um as cem requisições ficam em fila, mostrando a serialização.

## Cena 5.4 — HTTP/3 com aioquic: streams e eventos (0:25)

**Fundo / tela:**
Classe `Http3BenchmarkProtocol`, métodos `fetch` e `quic_event_received`:

```python
stream_id = self._quic.get_next_available_stream_id()
self.http.send_headers(stream_id, [
    (b":method", b"GET"), (b":scheme", b"https"),
    (b":authority", authority.encode()), (b":path", path.encode()),
    (b"cache-control", b"no-cache, no-store"),
])
self.http.send_data(stream_id, b"", end_stream=True)
self.transmit()
return await future

def quic_event_received(self, event):
    for http_event in self.http.handle_event(event):
        if isinstance(http_event, HeadersReceived): ...   # status
        elif isinstance(http_event, DataReceived):
            if http_event.data and state["first_body_ns"] is None:
                state["first_body_ns"] = time.perf_counter_ns()
            if http_event.stream_ended:
                self._finish(http_event.stream_id, state)
```

**Narração:**

No aioquic, montamos o HTTP três manualmente. Cada requisição recebe um novo stream do QUIC: é a ideia de fluxos independentes no código. Enviamos os pseudocabeçalhos method, scheme, authority e path, e o transmit despacha os pacotes. A resposta chega como eventos: cabeçalhos com o status e dados com o corpo, cujo primeiro pedaço marca o TTFB. Quando o stream termina, uma future do asyncio entrega os tempos.

## Cena 5.5 — Controle de vício de sessão: conexão fria e conexão quente (0:30)

**Fundo / tela:**
Função `run_sample`:

```python
is_cold = args.load == "A"
...
elif is_cold:
    for index, url in enumerate(urls, start=1):
        async with make_httpx_client(args.protocol, ca_file) as client:
            records.append(await httpx_request(client, url, ...))
else:
    async with make_httpx_client(args.protocol, ca_file) as client:
        tasks = [asyncio.create_task(httpx_request(client, url, ...))
                 for index, url in enumerate(urls, start=1)]
        records.extend(await asyncio.gather(*tasks))
```

**Narração:**

Esta é a parte central: o controle de vício de sessão. Na Carga A, a conexão é fria: o cliente nasce dentro do async with e é fechado antes da próxima medição, então nada é reaproveitado e o handshake entra no tempo. Na Carga B, a conexão é quente: um único cliente, cem tarefas com create task e um gather que espera todas, avaliando a multiplexação sem repetir handshakes. O HTTP três segue a mesma lógica.

## Cena 5.6 — Métricas e exportação dos dados brutos (0:10)

**Fundo / tela:**
Funções `summarize` e `append_results`:

```python
"rps": len(requests) / (elapsed_us / 1_000_000),
"p50_total_us": percentile(latencies, 50),
"p99_total_us": percentile(latencies, 99),
...
json_path = output_dir / "results.json"
csv_path = output_dir / "results.csv"
```

E um trecho do `results.csv` com a coluna `timestamp`.

**Narração:**

Ao final de cada amostra, calculamos as requisições por segundo e os percentis cinquenta e noventa e nove, e exportamos tudo, com timestamp, para results ponto json e results ponto csv.
