# Parte 4 — Implementação: emulação de rede com tc netem (1:15)

Arquivos mostrados: `scripts/set_network_lan.sh`, `scripts/set_network_wan.sh` e `scripts/cleanup_network.sh`.

## Cena 4.1 — O que é tc, qdisc e netem (0:20)

**Fundo / tela:**
Slide com um esquema simples:

```
aplicação → pilha TCP/IP → [ qdisc root: netem (atraso, perda) ] → eth0 → rede
```

Ao lado: "tc = traffic control" e "qdisc = disciplina de enfileiramento".

**Narração:**

Para emular a rede, usamos o tc, o controle de tráfego do Linux. Todo pacote que sai de uma interface passa por uma fila, a qdisc. O netem é uma qdisc que atrasa os pacotes e pode descartar uma porcentagem deles. Como atua na saída, o atraso vale para um sentido só.

## Cena 4.2 — Cenário LAN (0:25)

**Fundo / tela:**
`scripts/set_network_lan.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

services=(server-http1 server-http2 server-http3 benchmark-client)
for service in "${services[@]}"; do
    docker compose exec -T "$service" tc qdisc replace dev eth0 root netem delay 0.5ms
done
```

**Narração:**

Na rede local, o script aplica meio milissegundo de atraso na eth zero dos quatro contêineres. Ida e volta somam um milissegundo de RTT, sem perda. O docker compose exec roda o tc dentro do contêiner, e o menos T desliga o terminal interativo. O replace cria a regra ou substitui a existente, permitindo trocar de cenário sem erro.

## Cena 4.3 — Cenário WAN (0:15)

**Fundo / tela:**
`scripts/set_network_wan.sh`:

```bash
for service in server-http1 server-http2 server-http3; do
    docker compose exec -T "$service" tc qdisc replace dev eth0 root netem delay 25ms loss 2%
done
docker compose exec -T benchmark-client tc qdisc replace dev eth0 root netem delay 25ms
```

**Narração:**

Na rede longa, cada sentido recebe vinte e cinco milissegundos, somando cinquenta de RTT. A perda de dois por cento fica só na saída dos servidores, sentido dos dados; nos dois lados, a perda real chegaria perto de quatro por cento.

## Cena 4.4 — Limpeza das regras (0:15)

**Fundo / tela:**
`scripts/cleanup_network.sh`:

```bash
qdisc="$(docker compose exec -T "$service" tc qdisc show dev eth0)"
if grep -q '^qdisc netem ' <<<"$qdisc"; then
    docker compose exec -T "$service" tc qdisc del dev eth0 root
fi
```

**Narração:**

O script de limpeza verifica se há regra netem e a remove com tc qdisc del, restaurando a interface. O set menos e u o pipefail faz os scripts pararem no primeiro erro.
