# Divisão das falas entre os integrantes

Um áudio por cena, no mesmo padrão de nome já usado em `roteiro/audios/`:
`<parte>_audio_<cena>_<nome>.wav`, por exemplo `04_audio_01_vinicius.wav`.

## Critério da divisão

- **Kleber** abre o vídeo, apresenta a teoria e a infraestrutura Docker (partes 1 a 3, já gravadas) e faz o encerramento final (cena 9.2).
- **Vinicius** assume a partir da emulação de rede e segue pelo cliente Python, gráficos, execução, resultados e conclusões (partes 4 a 9.1).
- A troca de voz acontece numa mudança natural de assunto: a parte 3 termina no Docker, e a parte 4 começa na rede. A cena 4.1 já abre com o Vinicius se apresentando ("Agora quem continua sou eu, Vinicius…").
- O tempo fica quase meio a meio: cerca de **7:40 do Kleber** e **8:40 do Vinicius**.

Os tempos das partes 1 a 3 são os dos áudios gravados. Os das partes 4 a 9 são estimados pela velocidade real desses áudios, cerca de 153 palavras por minuto com as pausas.

## Kleber — já gravado

| Áudio | Cena | Duração |
|---|---|---:|
| `01_audio_1_kleber.wav` | 1.1 Título do trabalho | 0:18 |
| `01_audio_02_kleber.wav` | 1.2 Integrantes e roteiro | 0:19 |
| `02_audio_01_kleber.wav` | 2.0 Transição da abertura | 0:23 |
| `02_audio_02_kleber.wav` | 2.1 Os três protocolos | 0:43 |
| `02_audio_03_kleber.wav` | 2.2 Handshake e RTT | 0:46 |
| `02_audio_04_kleber.wav` | 2.3 Bloqueio de início de linha | 0:52 |
| `02_audio_05_kleber.wav` | 2.4 Controle de congestionamento | 0:54 |
| `03_audio_01_kleber.wav` | 3.1 Visão geral da arquitetura | 0:21 |
| `03_audio_02_kleber.wav` | 3.2 Docker Compose e serviço | 0:25 |
| `03_audio_03_kleber.wav` | 3.3 cap_add, ports, volumes, networks | 0:55 |
| `03_audio_04_kleber.wav` | 3.4 Outros serviços | 0:23 |
| `03_audio_05_kleber.wav` | 3.5 Dockerfiles | 0:19 |
| `03_audio_06_kleber.wav` | 3.6 Nginx e Caddy | 0:30 |
| `03_audio_07_kleber.wav` | 3.7 Certificado e arquivos de teste | 0:24 |
| **Subtotal gravado** | | **7:32** |

## Vinicius — a gravar

| Áudio | Cena | Duração estimada |
|---|---|---:|
| `04_audio_01_vinicius.wav` | 4.1 tc, qdisc e netem (com a apresentação do Vinicius) | 0:30 |
| `04_audio_02_vinicius.wav` | 4.2 Cenário LAN | 0:23 |
| `04_audio_03_vinicius.wav` | 4.3 Cenário WAN | 0:16 |
| `04_audio_04_vinicius.wav` | 4.4 Limpeza das regras | 0:13 |
| `05_audio_01_vinicius.wav` | 5.1 Cliente próprio e assíncrono | 0:24 |
| `05_audio_02_vinicius.wav` | 5.2 Requisição httpx e TTFB | 0:31 |
| `05_audio_03_vinicius.wav` | 5.3 Configuração do cliente httpx | 0:20 |
| `05_audio_04_vinicius.wav` | 5.4 HTTP/3 com aioquic | 0:27 |
| `05_audio_05_vinicius.wav` | 5.5 Conexão fria e conexão quente | 0:30 |
| `05_audio_06_vinicius.wav` | 5.6 Métricas e exportação | 0:12 |
| `06_audio_01_vinicius.wav` | 6.1 Média, desvio e barras de erro | 0:18 |
| `06_audio_02_vinicius.wav` | 6.2 Validação e tabela-resumo | 0:14 |
| `07_audio_01_vinicius.wav` | 7.1 O comando único | 0:11 |
| `07_audio_02_vinicius.wav` | 7.2 Preparação e limpeza garantida | 0:20 |
| `07_audio_03_vinicius.wav` | 7.3 Subida dos contêineres | 0:17 |
| `07_audio_04_vinicius.wav` | 7.4 Os doze testes | 0:20 |
| `07_audio_05_vinicius.wav` | 7.5 Gráficos e encerramento | 0:09 |
| `08_audio_01_vinicius.wav` | 8.1 Como ler os gráficos | 0:14 |
| `08_audio_02_vinicius.wav` | 8.2 Carga A, objeto grande | 0:31 |
| `08_audio_03_vinicius.wav` | 8.3 Colapso do TCP pela teoria | 0:26 |
| `08_audio_04_vinicius.wav` | 8.4 TTFB e handshakes | 0:22 |
| `08_audio_05_vinicius.wav` | 8.5 Carga B e HoL blocking | 0:40 |
| `08_audio_06_vinicius.wav` | 8.6 Variação e limitações | 0:23 |
| `09_audio_01_vinicius.wav` | 9.1 Conclusões principais | 0:27 |
| **Subtotal estimado** | | **8:38** |

## Kleber — encerramento, a gravar

| Áudio | Cena | Duração estimada |
|---|---|---:|
| `09_audio_02_kleber.wav` | 9.2 Encerramento e agradecimento | 0:10 |

## Total

| Integrante | Tempo |
|---|---:|
| Kleber | ~7:42 |
| Vinicius | ~8:38 |
| **Vídeo** | **~16:20** |

O vídeo deve passar cerca de 1 minuto e 20 segundos dos 15 pedidos no enunciado. Como as partes 4 a 9 ainda não foram gravadas, dá para recuperar esse minuto enxugando a narração delas antes de gravar.
