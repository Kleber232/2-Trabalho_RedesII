# Parte 8 — Resultados (2:40)

Base: seções "Resultados" e "Discussão" do relatório (`relatorio/report.pdf`). Os números são da **segunda rodada** (`results/20261020T205948Z-881`), a mesma das figuras do relatório.

## Cena 8.1 — Como ler os gráficos (0:15)

**Fundo / tela:**
Relatório em PDF na seção "Resultados", com a Tabela "Comparação selecionada entre as duas rodadas" visível. Depois, zoom no gráfico `total_load.png`, mostrando a legenda e uma barra de erro.

**Narração:**

Os resultados estão no relatório: duas rodadas dos doze testes, com cinco repetições, e os gráficos da segunda rodada. Cada barra é a média, e o traço preto é a barra de erro de um desvio-padrão.

## Cena 8.2 — Carga A: objeto grande de 50 MB (0:30)

**Fundo / tela:**
Gráfico `total_load.png` (Figura "Tempo total da carga" do relatório). Destacar primeiro o grupo "Carga A / LAN" e depois "Carga A / WAN". Na tela, um quadro com os números:

| Teste | Protocolo | Cenário | Tempo médio | Vazão |
|---|---|---|---:|---:|
| T01 | HTTP/1.1 | LAN | 0,48 s | ~105 MB/s |
| T02 | HTTP/2 | LAN | 0,77 s | ~65 MB/s |
| T03 | HTTP/3 | LAN | 3,82 s | ~13 MB/s |
| T04 | HTTP/1.1 | WAN | 164,7 s | ~0,30 MB/s |
| T05 | HTTP/2 | WAN | 159,6 s | ~0,31 MB/s |
| T06 | HTTP/3 | WAN | 110,2 s | ~0,45 MB/s |

**Narração:**

No arquivo de cinquenta megabytes, a rede local favoreceu o TCP: HTTP um ponto um em meio segundo, HTTP dois em oito décimos e HTTP três em quase quatro segundos. Isso não torna o QUIC lento: o cliente aioquic roda em Python, e o Tanenbaum lembra que um host sem recursos vira gargalo. Na rede longa, HTTP um ponto um e HTTP dois levaram cerca de cento e sessenta segundos, e o HTTP três, cento e dez, o melhor tempo.

## Cena 8.3 — O colapso do TCP explicado pela teoria (0:25)

**Fundo / tela:**
Relatório na subseção "Objeto grande e transporte", destacando o parágrafo da estimativa AIMD. Na tela, a conta:

```
p = 2%  →  janela W ≈ √(8 / 3p) ≈ 12 segmentos
vazão ≈ 0,75 × W × MSS / RTT ≈ 0,75 × 12 × 1448 B / 50 ms ≈ 0,25 MB/s
medido: 0,30 MB/s (T04) e 0,31 MB/s (T05)
```

**Narração:**

Por que o TCP desabou? Pelo dente de serra do livro, com dois por cento de perda há uma perda a cada cinquenta pacotes, e a janela fica em torno de doze segmentos. A vazão estimada é de zero vírgula vinte e cinco megabyte por segundo, e medimos zero vírgula trinta: mesma ordem de grandeza. O TLS não muda isso, porque os dois dependem do TCP.

## Cena 8.4 — TTFB e handshakes (0:20)

**Fundo / tela:**
Gráfico `ttfb.png` (Figura "TTFB" do relatório), destacando o grupo "Carga A / WAN".

**Narração:**

No TTFB da Carga A na rede longa, que inclui o handshake, foram trezentos e dezenove milissegundos no HTTP um ponto um, duzentos e vinte e oito no HTTP dois e cento e trinta e um no HTTP três, compatível com o handshake de um RTT do QUIC. Na rede local, não houve vantagem clara.

## Cena 8.5 — Carga B: cem objetos pequenos e HoL blocking (0:40)

**Fundo / tela:**
Gráfico `rps.png` (Figura "RPS" do relatório), destacando "Carga B / LAN" e depois "Carga B / WAN". Na tela:

| Teste | Protocolo | Cenário | RPS médio | TTFB p50 |
|---|---|---|---:|---:|
| T07 | HTTP/1.1 | LAN | ~57 | 1,07 s |
| T08 | HTTP/2 | LAN | ~248 | 0,28 s |
| T09 | HTTP/3 | LAN | ~225 | 0,07 s |
| T10 | HTTP/1.1 | WAN | ~11,8 | 4,15 s |
| T11 | HTTP/2 | WAN | ~69,2 | 0,76 s |
| T12 | HTTP/3 | WAN | ~94,0 | 0,15 s |

**Narração:**

Nos cem arquivos pequenos em rede local, o HTTP um ponto um ficou em cinquenta e sete requisições por segundo, por servir uma resposta de cada vez, contra duzentas e quarenta e oito do HTTP dois e duzentas e vinte e cinco do HTTP três. Na rede longa, aparece o bloqueio de início de linha: doze no HTTP um ponto um, sessenta e nove no HTTP dois e noventa e quatro no HTTP três, que também teve o menor TTFB mediano, cento e cinquenta milissegundos. Uma perda no TCP trava todos os fluxos do HTTP dois; no QUIC, só o seu stream.

## Cena 8.6 — Variação e limitações (0:25)

**Fundo / tela:**
Relatório nas subseções "Variação entre rodadas e limites de inferência" e "Limitações e reprodutibilidade". Destacar na Tabela de comparação a linha do T08 (162 → 248 RPS) e as barras de erro grandes de T11 e T12 no gráfico `rps.png`.

**Narração:**

Há limites. As barras de erro na rede longa são grandes, e o HTTP dois em rede local variou de cento e sessenta e duas para duzentas e quarenta e oito requisições por segundo entre rodadas. Cinco repetições ficam abaixo do que o livro recomenda, e não medimos o algoritmo de congestionamento ativo, nem confirmamos o uso do BBR.
