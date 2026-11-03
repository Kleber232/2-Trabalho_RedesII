# Parte 3 — Implementação: infraestrutura Docker (3:20)

Arquivos mostrados: `docker-compose.yml`, `Dockerfile.nginx`, `Dockerfile.caddy`, `Dockerfile.client`, `nginx/http1.conf`, `nginx/http2.conf`, `caddy/Caddyfile` e o trecho de certificados e arquivos em `run_experiments.sh`.

## Cena 3.1 — Visão geral da arquitetura (0:15)

**Fundo / tela:**
Diagrama da arquitetura (seção 2 do enunciado), adaptado com o cliente:

```
                    rede bridge net_bench (172.20.0.0/16)
   ┌──────────────────┬────────────────────┬────────────────────┬──────────────────┐
   server_http11      server_http2_tls     server_http3_quic    benchmark_client
   Nginx HTTP/1.1     Nginx HTTP/2+TLS1.3  Caddy HTTP/3 QUIC    Python httpx/aioquic
   172.20.0.10:80     172.20.0.20:443/tcp  172.20.0.30:443/udp  172.20.0.40
   └───────────── tc netem na eth0 de cada contêiner (atraso e perda) ─────────────┘
```

**Narração:**

Todo o ambiente roda em contêineres Docker, para isolar os testes da rede real. São quatro: um servidor por protocolo e um cliente, que executa o benchmark. Todos ficam na mesma rede virtual, onde injetamos atraso e perda.

## Cena 3.2 — O que é o Docker Compose e o que é um serviço (0:30)

**Fundo / tela:**
`docker-compose.yml`, destacando o primeiro serviço:

```yaml
services:
  server-http1:
    image: tp2-nginx-netem:local
    build:
      context: .
      dockerfile: Dockerfile.nginx
    container_name: server_http11
```

**Narração:**

O Docker Compose descreve vários contêineres num único arquivo. Cada item de services é um serviço, a receita de um contêiner: imagem, portas, arquivos e rede. O build diz que a imagem vem de um Dockerfile nosso, e o image dá nome a ela. O container name fixa o nome do contêiner, como server http onze; sem ele, o Docker inventa um nome e os comandos não o encontrariam.

## Cena 3.3 — cap_add, ports, volumes e networks (0:55)

**Fundo / tela:**
Continuação do mesmo serviço, destacando cada bloco enquanto é falado:

```yaml
    cap_add:
      - NET_ADMIN
    ports:
      - "8080:80"
    volumes:
      - ./www:/usr/share/nginx/html:ro
      - ./nginx/http1.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      net_bench:
        ipv4_address: 172.20.0.10
```

E, no final do arquivo:

```yaml
networks:
  net_bench:
    name: net_bench
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Narração:**

O cap add NET ADMIN concede ao contêiner a capacidade de administrar a rede. Sem ela, o tc falha com operação não permitida. É mais seguro que um contêiner privilegiado, porque libera só o necessário.

O ports mapeia uma porta do computador para uma do contêiner: oito mil e oitenta dois pontos oitenta leva a porta oito mil e oitenta da máquina até a porta oitenta do Nginx, permitindo testar por fora com o navegador. O cliente não precisa disso, porque está na mesma rede.

Os volumes ligam pastas do projeto ao contêiner, como os arquivos de teste e a configuração do Nginx, em modo somente leitura, o sufixo ro. E o networks coloca o serviço na rede net bench, do tipo bridge, um switch virtual. Cada contêiner tem IP fixo, e o DNS interno do Docker permite acessar o servidor pelo nome.

## Cena 3.4 — Diferenças dos outros serviços (0:25)

**Fundo / tela:**
`docker-compose.yml`, trechos de `server-http2`, `server-http3` e `benchmark-client`:

```yaml
  server-http2:
    ports:
      - "8443:443"
    volumes:
      - ./certs:/etc/nginx/certs:ro
  server-http3:
    image: tp2-caddy-netem:local
    ports:
      - "9443:443/tcp"
      - "9443:443/udp"
  benchmark-client:
    volumes:
      - ./:/workspace
    command: ["sleep", "infinity"]
```

**Narração:**

Os outros serviços seguem a mesma ideia. O HTTP dois usa a porta quatrocentos e quarenta e três, do HTTPS, e monta os certificados. O HTTP três publica a porta em TCP e em UDP, porque o QUIC usa UDP. O cliente monta o projeto na pasta workspace, para salvar os resultados no computador, e roda sleep infinity só para ficar ligado.

## Cena 3.5 — Dockerfiles (0:20)

**Fundo / tela:**
Os três Dockerfiles lado a lado:

```dockerfile
# Dockerfile.nginx
FROM nginx:alpine
RUN apk add --no-cache iproute2
```

```dockerfile
# Dockerfile.client
FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /workspace
CMD ["sleep", "infinity"]
```

**Narração:**

O Dockerfile é a receita de uma imagem. O FROM escolhe a base, as mesmas do enunciado: nginx alpine e caddy dois ponto sete alpine. O RUN executa comandos na construção: instalamos o iproute dois, que fornece o comando tc. No cliente, a base é o Python, e o pip instala httpx, aioquic e matplotlib.

## Cena 3.6 — Configuração dos servidores web (0:30)

**Fundo / tela:**
`nginx/http2.conf` e `caddy/Caddyfile`:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate     /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    ssl_protocols TLSv1.3;
    ssl_session_cache off;
    ssl_session_tickets off;
    location / {
        add_header Cache-Control "no-store, no-cache, must-revalidate" always;
    }
}
```

```
:443 {
    tls /etc/caddy/certs/server.crt /etc/caddy/certs/server.key
    root * /srv
    file_server
}
```

**Narração:**

No Nginx, listen quatrocentos e quarenta e três ssl http dois ativa TLS e HTTP dois na mesma porta, e ssl protocols aceita só o TLS um ponto três. Desligamos o cache e os tickets de sessão para impedir a retomada de sessão: toda conexão nova faz o handshake completo, que é o que queremos medir. O cabeçalho Cache-Control no-store proíbe cache. O Caddy foi escolhido porque já ativa o HTTP três em UDP automaticamente.

## Cena 3.7 — Certificado e arquivos de teste (0:20)

**Fundo / tela:**
Trecho de `run_experiments.sh`:

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 365 \
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt" \
    -subj "/CN=server-http2" \
    -addext "subjectAltName=DNS:localhost,DNS:server-http2,DNS:server-http3,..."

dd if=/dev/urandom of="$WWW_DIR/file_50mb.bin" bs=1000000 count=50
dd if=/dev/urandom of="$file" bs=10000 count=1   # 100 arquivos de 10 KB
```

**Narração:**

O TLS exige um certificado. Geramos um autoassinado com o openssl, listando os nomes dos servidores no subject alternative name, e o cliente confia nele em vez de desligar a verificação. Os arquivos de teste, um de cinquenta megabytes e cem de dez quilobytes, são gerados com bytes aleatórios, para que nenhuma compressão distorça as medições.
