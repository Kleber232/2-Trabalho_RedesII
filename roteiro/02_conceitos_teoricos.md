# Parte 2 — Conceitos teóricos básicos (2:45)

Base: seção 1 do enunciado e seção "Fundamentação teórica" do relatório (Tanenbaum e Wetherall, 5ª edição, p. 363–368; RFCs 9000, 9001 e 9114).

## Cena 2.0 — Transição da abertura (0:20)

**Fundo / tela:**
Transição suave do slide de integrantes para um slide com a pergunta em destaque:
"O que acontece entre clicar num link e a página aparecer?"

Opcional: animação simples de um navegador enviando uma requisição a um servidor.

**Narração:**

Antes de iniciar a demonstração do código, é importante entender um pouco melhor como funcionam os protocolos de comunicação na Web, qual é o papel de cada um e quais são suas principais diferenças. Assim, fica mais fácil compreender como acontece a troca de informações entre clientes e servidores durante o funcionamento de uma aplicação web.

## Cena 2.1 — Os três protocolos (0:35)

**Fundo / tela:**
Slide com a tabela comparativa do enunciado (seção 1):

| Protocolo | Transporte | Segurança | Multiplexação | HoL blocking |
|---|---|---|---|---|
| HTTP/1.1 | TCP | Opcional | Não tem (conexões paralelas) | Alto, na aplicação |
| HTTPS (HTTP/2) | TCP | TLS 1.3 obrigatório | Quadros numa conexão | Médio/alto, no TCP |
| HTTP/3 | UDP (QUIC) | TLS 1.3 integrado | Streams independentes | Nulo entre streams |

**Narração:**

Para quem está utilizando o navegador, os três protocolos funcionam de maneira bastante semelhante: eles utilizam os mesmos tipos de requisições, cabeçalhos e respostas. A principal diferença está na forma como essas informações são transportadas. O HTTP um ponto um utiliza o TCP, sem criptografia por padrão. Já o HTTP dois também utiliza o TCP, mas com uma camada de segurança TLS, permitindo ainda o envio de múltiplas requisições e respostas simultaneamente pela mesma conexão. Por outro lado, o HTTP tres utiliza o QUIC, um protocolo baseado em UDP que já incorpora mecanismos de criptografia e permite uma comunicação mais eficiente.

## Cena 2.2 — Handshake e RTT (0:35)

**Fundo / tela:**
Slide com três linhas do tempo lado a lado, cliente à esquerda e servidor à direita:
- TCP: SYN, SYN-ACK, ACK → 1 RTT antes do primeiro byte da requisição
- TCP + TLS 1.3: 1 RTT do TCP + 1 RTT do TLS → 2 RTT
- QUIC: transporte e TLS juntos → 1 RTT (0-RTT na retomada de sessão)

**Narração:**

E por que isso é importante? Por causa do RTT, que representa o tempo que um pacote leva para chegar até o servidor e retornar ao cliente. Antes de começar a troca de dados, cliente e servidor precisam estabelecer uma conexão. No TCP, esse processo exige uma ida e volta. Quando utilizamos TLS, temos etapas adicionais para negociar a segurança da comunicação. Já o QUIC consegue combinar o estabelecimento da conexão com a negociação de segurança, reduzindo esse tempo inicial. Quando cada ida e volta leva cerca de cinquenta milissegundos, essa diferença pode impactar diretamente o desempenho. E é justamente isso que o TTFB, ou tempo até o primeiro byte, nos ajuda a observar.

## Cena 2.3 — Bloqueio de início de linha (0:35)

**Fundo / tela:**
Slide com três faixas representando fluxos A, B e C:
- TCP: um pacote perdido do fluxo A trava também os fluxos B e C até a retransmissão
- QUIC: a perda no fluxo A atrasa só o fluxo A

Sugestão visual: uma fila de caixa de supermercado, em que um cliente parado segura todos os que estão atrás.

**Narração:**

.. O segundo ponto é o bloqueio de início de linha, também conhecido como Head-of-Line Blocking. Imagine uma fila de supermercado: se o primeiro cliente tiver algum problema no caixa, todos os que estão atrás precisam esperar. No HTTP um ponto um, as respostas são processadas de forma sequencial, o que pode causar esse tipo de bloqueio. O HTTP dois melhora isso permitindo vários fluxos de comunicação simultâneos pela mesma conexão. Porém, como ainda utiliza o TCP, os dados precisam ser entregues em ordem. Se um pacote se perde, os demais fluxos podem ficar esperando até que ele seja retransmitido. Já no HTTP tres, com o QUIC, cada fluxo possui seu próprio controle de entrega. Dessa forma, a perda de um pacote afeta apenas o fluxo correspondente, sem bloquear os demais.

## Cena 2.4 — Controle de congestionamento e perdas (0:40)

**Fundo / tela:**
Slide com o gráfico "dente de serra" do TCP Reno (pode ser a Figura 6.41 do Tanenbaum, p. 364, com a fonte citada) e a frase: "perda = sinal de congestionamento".
+-
**Narração:**

O terceiro ponto é a forma como o TCP reage à perda de pacotes. Como explica Tanenbaum, o TCP aumenta gradualmente a velocidade de transmissão e, quando identifica uma perda, reduz sua taxa de envio, geralmente pela metade. Esse comportamento cria um padrão conhecido como dente de serra. O CUBIC, utilizado no Linux, segue esse princípio de controle de congestionamento: ele interpreta a perda de pacotes como um possível sinal de congestionamento na rede. Porém, nem toda perda significa congestionamento. Em situações como uma conexão móvel, por exemplo, a perda pode acontecer devido a interferências no sinal. Mesmo assim, o TCP pode reduzir sua velocidade desnecessariamente. É justamente para observar esse comportamento que criamos um cenário com dois por cento de perda de pacotes. Agora que entendemos esses três conceitos, vamos ver como preparamos o ambiente para testar tudo isso na prática.