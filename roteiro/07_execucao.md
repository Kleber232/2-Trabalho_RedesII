# Parte 7 — Execução com um único comando (1:20)

Arquivo mostrado: `run_experiments.sh`, depois o terminal.

## Cena 7.1 — O comando único (0:10)

**Fundo / tela:**
Terminal na raiz do projeto, digitando:

```bash
chmod +x run_experiments.sh scripts/*.sh
REPETITIONS=5 ./run_experiments.sh
```

**Narração:**

Tudo roda com um único comando. O chmod mais x dá permissão de execução, só na primeira vez. A variável REPETITIONS define as repetições; o padrão é cinco.

## Cena 7.2 — Preparação e limpeza garantida (0:20)

**Fundo / tela:**
Início de `run_experiments.sh`:

```bash
set -euo pipefail
REPETITIONS="${REPETITIONS:-5}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"

cleanup() {
    ...
    ./scripts/cleanup_network.sh
    docker compose down --remove-orphans
}
trap cleanup EXIT INT TERM
```

**Narração:**

O script cria uma pasta de resultados com a data e o número do processo, sem sobrescrever execuções anteriores. O trap garante a limpeza: a função cleanup roda ao final, com sucesso, erro ou control C, removendo o netem e executando docker compose down, que para e apaga os contêineres.

## Cena 7.3 — Subida dos contêineres e espera ativa (0:15)

**Fundo / tela:**
Terminal mostrando a saída do `docker compose up`, e o trecho do script:

```bash
docker compose up -d --build

for attempt in $(seq 1 60); do
    if docker compose exec -T benchmark-client python -c \
        'import socket; [socket.create_connection((host, 443 if host != "server-http1" else 80), timeout=1).close() for host in ...]'; then
        ready=1; break
    fi
    sleep 2
done
```

Opcional: rodar em outro terminal `docker compose ps` para mostrar os quatro contêineres em execução.

**Narração:**

Depois de gerar certificado e arquivos, o docker compose up sobe o ambiente: menos d roda em segundo plano, e menos menos build reconstrói as imagens. O script tenta conectar nos servidores a cada dois segundos e só começa quando os três respondem.

## Cena 7.4 — Os doze testes da matriz (0:20)

**Fundo / tela:**
Trecho final do script e, em seguida, o terminal com as linhas de progresso (pode ser acelerado na edição):

```bash
./scripts/set_network_lan.sh
run_test T01 A http1 LAN
run_test T02 A http2 LAN
run_test T03 A http3 LAN
run_test T07 B http1 LAN
run_test T08 B http2 LAN
run_test T09 B http3 LAN

./scripts/set_network_wan.sh
run_test T04 A http1 WAN
...
run_test T12 B http3 WAN
```

Formato da linha de progresso (valores ilustrativos): `T08 amostra 3/5: 245.00 RPS, p50=296000 us, p99=343000 us`

Opcional: mostrar a regra aplicada com `docker compose exec server-http1 tc qdisc show dev eth0`.

**Narração:**

Primeiro aplicamos a rede local e rodamos seus seis testes, depois a rede longa e os outros seis, trocando a regra do netem uma única vez. Cada run test executa o cliente no contêiner com o teste, a carga, o protocolo e o cenário, e cada amostra imprime o progresso.

## Cena 7.5 — Geração dos gráficos e encerramento (0:10)

**Fundo / tela:**
Final da saída do terminal: `Gráficos salvos em ...` e `Experimentos concluídos. Resultados: ...`. Depois, o explorador de arquivos aberto na pasta `results/<RUN_ID>/` mostrando `results.json`, `results.csv` e `plots/`.

**Narração:**

No fim, o script gera gráficos e tabela, limpa o ambiente, e a pasta de resultados guarda os dados brutos e os gráficos.
