#!/usr/bin/env bash
set -euo pipefail

# Delay both directions by 25 ms; inject loss on the server egress only so the
# end-to-end path has 2% loss rather than compounding loss on both endpoints.
for service in server-http1 server-http2 server-http3; do
    docker compose exec -T "$service" tc qdisc replace dev eth0 root netem delay 25ms loss 2%
done
docker compose exec -T benchmark-client tc qdisc replace dev eth0 root netem delay 25ms
