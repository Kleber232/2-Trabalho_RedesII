#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

REPETITIONS="${REPETITIONS:-5}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
OUTPUT_DIR="/workspace/results/${RUN_ID}"
HOST_OUTPUT_DIR="${ROOT_DIR}/results/${RUN_ID}"
CERT_DIR="${ROOT_DIR}/certs"
WWW_DIR="${ROOT_DIR}/www"
ENV_STARTED=0

cleanup() {
    local exit_code=$?
    trap - EXIT
    if [[ "$ENV_STARTED" -eq 1 ]]; then
        if ! ./scripts/cleanup_network.sh; then
            echo "Falha ao remover as regras tc netem." >&2
            exit_code=1
        fi
        if ! docker compose down --remove-orphans; then
            echo "Falha ao encerrar os contêineres Docker." >&2
            exit_code=1
        fi
    fi
    exit "$exit_code"
}
trap cleanup EXIT INT TERM
trap 'exit 130' INT
trap 'exit 143' TERM

for command in docker openssl; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Comando obrigatório não encontrado: $command" >&2
        exit 1
    fi
done
docker compose version >/dev/null

mkdir -p "$CERT_DIR" "$WWW_DIR" "$HOST_OUTPUT_DIR"
if [[ ! -s "$CERT_DIR/server.crt" || ! -s "$CERT_DIR/server.key" ]]; then
    MSYS2_ARG_CONV_EXCL='/CN=' openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 365 \
        -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt" \
        -subj "/CN=server-http2" \
        -addext "subjectAltName=DNS:localhost,DNS:server-http2,DNS:server-http3,IP:127.0.0.1,IP:172.20.0.20,IP:172.20.0.30" \
        -addext "basicConstraints=critical,CA:TRUE"
    chmod 644 "$CERT_DIR/server.crt"
    chmod 600 "$CERT_DIR/server.key"
fi

if [[ ! -f "$WWW_DIR/file_50mb.bin" || "$(wc -c < "$WWW_DIR/file_50mb.bin")" -ne 50000000 ]]; then
    dd if=/dev/urandom of="$WWW_DIR/file_50mb.bin" bs=1000000 count=50 status=none
fi
for index in $(seq 1 100); do
    file="$WWW_DIR/file_${index}.bin"
    if [[ ! -f "$file" || "$(wc -c < "$file")" -ne 10000 ]]; then
        dd if=/dev/urandom of="$file" bs=10000 count=1 status=none
    fi
done

# Keep Linux container paths intact when Docker CLI is invoked from Git Bash.
export MSYS_NO_PATHCONV=1
ENV_STARTED=1
docker compose up -d --build

ready=0
for attempt in $(seq 1 60); do
    if docker compose exec -T benchmark-client python -c \
        'import socket; [socket.create_connection((host, 443 if host != "server-http1" else 80), timeout=1).close() for host in ("server-http1", "server-http2", "server-http3")]' \
        >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 2
done
if [[ "$ready" -ne 1 ]]; then
    echo "O contêiner de benchmark não ficou pronto no tempo esperado." >&2
    exit 1
fi
docker compose exec -T benchmark-client test -r /workspace/certs/server.crt

run_test() {
    local test_id="$1" load="$2" protocol="$3" scenario="$4"
    docker compose exec -T benchmark-client python benchmark_client.py \
        --test-id "$test_id" \
        --load "$load" \
        --protocol "$protocol" \
        --scenario "$scenario" \
        --repetitions "$REPETITIONS" \
        --ca-file /workspace/certs/server.crt \
        --output-dir "$OUTPUT_DIR"
}

./scripts/set_network_lan.sh
run_test T01 A http1 LAN
run_test T02 A http2 LAN
run_test T03 A http3 LAN
run_test T07 B http1 LAN
run_test T08 B http2 LAN
run_test T09 B http3 LAN

./scripts/set_network_wan.sh
run_test T04 A http1 WAN
run_test T05 A http2 WAN
run_test T06 A http3 WAN
run_test T10 B http1 WAN
run_test T11 B http2 WAN
run_test T12 B http3 WAN

docker compose exec -T benchmark-client python plot_results.py \
    --input "$OUTPUT_DIR/results.json" \
    --output-dir "$OUTPUT_DIR/plots"

echo "Experimentos concluídos. Resultados: $HOST_OUTPUT_DIR"
