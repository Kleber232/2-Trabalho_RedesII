# Roteiro do vídeo — Guia geral

Vídeo de apresentação do Trabalho Prático 2 de Redes II (UFPI/CSHNB):
**Estudo Experimental de Desempenho de Protocolos Web — HTTP/1.1, HTTPS/HTTP/2 e HTTP/3-QUIC em Ambiente Emulado.**

O enunciado pede um vídeo de **15 minutos** explicando a execução, os pontos importantes da implementação, os resultados e a conclusão dos experimentos. O link do vídeo (YouTube) precisa estar no relatório: sem vídeo, a nota é zero.

## Ordem e tempo das partes

| Arquivo | Parte | Tempo alvo | Acumulado |
|---|---|---:|---:|
| `01_abertura_integrantes.md` | Abertura e integrantes | 0:40 | 0:40 |
| `02_conceitos_teoricos.md` | Conceitos teóricos básicos | 2:45 | 3:25 |
| `03_implementacao_infraestrutura.md` | Docker Compose, Dockerfiles, Nginx, Caddy, certificados | 3:20 | 6:45 |
| `04_implementacao_emulacao_rede.md` | Emulação de rede com `tc netem` | 1:15 | 8:00 |
| `05_implementacao_cliente_python.md` | Cliente de benchmark em Python | 2:25 | 10:25 |
| `06_implementacao_graficos.md` | Estatística e gráficos | 0:30 | 10:55 |
| `07_execucao.md` | Execução com um único comando | 1:20 | 12:15 |
| `08_resultados.md` | Resultados (relatório e gráficos) | 2:40 | 14:55 |
| `09_conclusao.md` | Conclusão e encerramento | 0:40 | 15:35 |

Os tempos foram estimados para uma voz com cerca de 150 palavras por minuto. Se o VoiceStudio falar mais rápido ou mais devagar, ajuste a velocidade da voz, não o texto.

## Como cada arquivo está organizado

Cada parte é dividida em **cenas**. Cada cena tem:

- **Fundo / tela:** o que mostrar no vídeo enquanto a voz fala (arquivo aberto, trecho de código destacado, gráfico, página do relatório, terminal).
- **Narração:** o texto que vai para o VoiceStudio. Basta copiar e colar.

O texto da narração foi escrito **para ser falado por voz sintética**:

- siglas e versões estão escritas como se falam ("HTTP um ponto um", "TLS um ponto três", "RTT de cinquenta milissegundos");
- não há símbolos como `%`, `ms`, `/` ou `µs`, que vozes sintéticas costumam ler errado;
- nomes de arquivos e comandos aparecem por extenso quando são lidos ("docker compose ponto yml").

Se a voz pronunciar algum termo de forma estranha (por exemplo "QUIC", "netem", "Caddy"), use o dicionário de pronúncia do VoiceStudio:

| Termo | Sugestão de pronúncia |
|---|---|
| QUIC | "quic" (como a palavra inglesa *quick*) |
| netem | "nê-tem" |
| Caddy | "quédi" |
| Nginx | "en-jin-ics" |
| httpx | "agá tê tê pê" |
| aioquic | "ai-ô-quic" |
| CUBIC | "cúbic" |
| qdisc | "quiú-disc" |

## Material de fundo que precisa estar pronto

- **Editor de código** (VS Code) com o repositório aberto, fonte grande (pelo menos 18) e tema escuro ou claro bem contrastado.
- **Terminal** (Git Bash ou terminal do Linux) com fonte grande.
- **Relatório em PDF** (`relatorio/report.pdf`) aberto num leitor que permita zoom.
- **Gráficos** da segunda rodada em `results/20261020T205948Z-881/plots/`: `ttfb.png`, `total_load.png` e `rps.png`.
- **Tabela-resumo** `results/20261020T205948Z-881/plots/summary.md`, aberta em visualização Markdown.
- **Diagrama da arquitetura** (opcional, mas recomendado): pode ser o desenho ASCII da seção 2 do enunciado ou um slide simples com os quatro contêineres na rede `net_bench`.
- **Slides simples** para as partes teóricas (sugestões de conteúdo estão em cada cena).

## Dica de gravação da execução

A execução completa demora bastante. Só a Carga A na WAN leva cerca de 160 segundos por repetição para HTTP/1.1 e HTTP/2, vezes cinco repetições. Grave a execução inteira uma vez e, na edição:

- mostre em velocidade normal o início (subida dos contêineres e aplicação do `netem`);
- acelere ou corte o meio, deixando visíveis as linhas de progresso de cada teste;
- mostre em velocidade normal o final (gráficos gerados e limpeza do ambiente).

Para mostrar o comando rodando dentro do tempo do vídeo, também dá para gravar uma execução curta com `REPETITIONS=2`. Nesse caso, avise na tela que os resultados apresentados vêm da execução completa, com cinco repetições.

## Checklist antes de publicar

- [ ] O vídeo tem cerca de 15 minutos.
- [ ] Os dois integrantes aparecem ou são citados na abertura.
- [ ] O link não listado do YouTube foi colocado no relatório, no lugar de "a inserir após a gravação".
- [ ] O PDF do relatório foi recompilado depois de inserir o link.
