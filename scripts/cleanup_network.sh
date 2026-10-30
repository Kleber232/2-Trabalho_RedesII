#!/usr/bin/env bash
set -euo pipefail

services=(server-http1 server-http2 server-http3 benchmark-client)
for service in "${services[@]}"; do
    if docker compose ps --status running --services | grep -Fxq "$service"; then
        qdisc="$(docker compose exec -T "$service" tc qdisc show dev eth0)"
        if grep -q '^qdisc netem ' <<<"$qdisc"; then
            docker compose exec -T "$service" tc qdisc del dev eth0 root
        fi
    fi
done
