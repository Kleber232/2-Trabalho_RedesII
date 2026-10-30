#!/usr/bin/env bash
set -euo pipefail

services=(server-http1 server-http2 server-http3 benchmark-client)
for service in "${services[@]}"; do
    docker compose exec -T "$service" tc qdisc replace dev eth0 root netem delay 0.5ms
done
