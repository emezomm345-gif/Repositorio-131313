# Skin CPM – tufos de pelo

## Caçadores v16.34 — andar mais inclinado

Arquivo atual: `modelo/variantes/CACADORES/skin_v16.34_CACADORES.bbmodel`
(`LEAN=-12 tools/andar_animado.py`). Ao andar, o tronco inclina 12° para a frente (antes eram 8°); a cabeça
compensa para continuar olhando à frente.

## Caçadores v16.33 — cabeça animada ao andar

Arquivo atual: `modelo/variantes/CACADORES/skin_v16.33_CACADORES.bbmodel`.

Foi criado um grupo novo, `cabeca_mov`, dentro da cabeça, com tudo o que a cabeça carrega. O balanço global do
andar agora também mexe nele:
- **Movimento:** a cabeça vai junto com o sobe e desce e com a inclinação dos ombros, acena um instante depois de
  cada passo, inclina contra a rolagem e gira um pouco contra o giro dos ombros, segurando o olhar.
- **Olhar:** a cabeça do Minecraft continua livre, então o olhar segue a câmera e os mods.
- **Outros estados:** os "Repouso do corpo" também seguram esse grupo parado.

## Caçadores v16.32 — corrida A + andar mais animado e inclinado

Arquivo atual: `modelo/variantes/CACADORES/skin_v16.32_CACADORES.bbmodel`. É a base A (escolhida) passada por
`tools/andar_animado.py`. Prévia: `previews/variante_CACADORES_andar.gif` (braços e pernas simulados).

- **Postura do andar:**
  - o tronco inclina 8° para a frente, em volta do quadril (antes eram 2,5°);
  - cabeça, ombros e braços acompanham o tronco, e a cabeça levanta o olhar de volta para a frente;
  - braços um pouco à frente e soltos.
- **Balanço do corpo:** quique, rolagem de peso e giro de ombros quase o dobro de antes, no ritmo do passo do
  Minecraft.
- **Compatibilidade:** tudo continua somando ao Minecraft, então Better Combat e TACZ seguem funcionando.

## Caçadores v16.31 A / B / C — corrida compatível com Better Combat e TACZ (teste)

O nosso ciclo de corrida e o golpe recriado substituíam por completo os braços (e as pernas) do Minecraft. Com
isso, correndo, sumiam as animações do Better Combat e do TACZ. Para testar, geramos três bases a partir de
`skin_v16.30_CACADORES.bbmodel` com `tools/compat_corrida.py`. Em todas, o golpe recriado saiu: atacar volta a ser o
golpe do Minecraft ou do Better Combat.

- **A** (`skin_v16.31_CACADORES_A.bbmodel`): braços e pernas são os do Minecraft e dos mods. Fica o nosso corpo
  da corrida (inclinação, giro, quique, cabeça, cauda), e os braços acompanham o tronco: inclinam e vão um pouco à
  frente e para fora, somados ao braço do mod.
- **B** (`..._B.bbmodel`): pernas com a nossa passada; braços do Minecraft e dos mods. O corpo é igual ao da A.
- **C** (`..._C.bbmodel`): como a A, mas a corrida nunca gira os braços, só move os ombros junto com o tronco. O
  ângulo dos braços é exatamente o do mod, então a mira do TACZ fica exata.

## Templário v16.38 — movimentos do L.A.S.T, gatilhos, limpeza

Arquivo atual: `modelo/variantes/BRANCA/skin_v16.38_BRANCA.bbmodel`. A base é o seu
`ajuste_usuario_v16.37_BRANCA.bbmodel`, com os mesmos passos do Caçadores
(`LOOPING="Rezar,Meditacao extrema"`).

- **Movimentos:** são 100% os do L.A.S.T. Tem as mesmas animações de movimento; só os nomes das saídas foram
  corrigidos, como explicado abaixo.
- **Emotes:** nenhum foi adicionado nem removido.
  - Rezar e Meditação extrema viraram liga/desliga, com os olhos fechados no mesmo botão.
  - As expressões (incluindo Subestimar) já eram liga/desliga.
  - Os gestos com começo e fim continuam iguais.
  - Ordem do menu: expressões → Rezar, Meditação extrema → Investigar, Pouso de herói, Estalar o pescoço, Explosão
    de luz → configurações.
- **Saídas renomeadas:** as saídas que o Blockbench tinha renomeado (`p:running2`, `g:Raiva2`…) voltaram aos
  nomes certos, para o CPM ligar cada uma à sua pose.
- **Limpeza:**
  - removidos 14 elementos invisíveis no seu arquivo: tufos do peito, bochechas e dois tufos das costas que você
    tinha apagado. Saíram também os 17 grupos e as 229 trilhas deles, e a animação "Respirar", que só mexia
    nessas peças invisíveis;
  - 1621 pixels sem uso apagados da textura;
  - parado, o modelo ficou idêntico (24 ângulos comparados).

## Caçadores v16.30 — movimentos do L.A.S.T, gatilhos, limpeza

Arquivo atual: `modelo/variantes/CACADORES/skin_v16.30_CACADORES.bbmodel`. A base é o seu
`ajuste_usuario_v16.29_CACADORES.bbmodel`, com os mesmos passos do L.A.S.T:

1. `tools/movimento.py` → `tools/movimento_last.py` →
   `LOOPING="Jogar moeda" MENU="..." tools/movimento_last2.py` → `tools/limpar.py`.
2. **Movimentos:** são 100% os do L.A.S.T: andar (postura e balanço do corpo), parado, correr, pular e comer
   padrão, agachar, rastejar, nadar, escada, dormir, cara de dor, voo, queda, virar e transições. As animações dos
   acessórios (bandana e óculos) continuam.
3. **Emotes:** nenhum foi adicionado nem removido.
   - Jogar moeda virou liga/desliga.
   - As expressões e Óculos nos olhos já eram liga/desliga.
   - Os gestos com começo e fim continuam iguais.
   - Ordem do menu: expressões → Óculos nos olhos → Jogar moeda → Saudação do velho oeste, Reconhecer o alvo,
     Finalizando contrato, Alongamento, Estalar o pescoço → Esconder orelhas, Esconder cauda, Ignorar capacete.
4. **Limpeza:**
   - 10 tufos do peito invisíveis e `tail_2_bevel` oculto removidos, junto com os 14 grupos e as 134 trilhas
     deles;
   - 1193 pixels sem uso apagados da textura;
   - as caixas da segunda camada da skin (hat, jacket, sleeves, pants) foram mantidas, para poder pintar depois;
   - parado, o modelo ficou idêntico (24 ângulos comparados).

## L.A.S.T v16.51 — Cinema: braços firmes

Arquivo atual: `modelo/variantes/LAST/skin_v16.51_LAST.bbmodel`.

Na v16.50 os braços do Cinema eram calculados quadro a quadro pela direção até a placa, e isso fazia os ângulos
virarem e girarem. Agora são ângulos simples, sempre os mesmos, interpolados direto da pose do peito para a pose
sobre a cabeça. Os braços sobem firmes, sem girar, e ficam parados segurando a placa no alto, sem o balanço.

## L.A.S.T v16.50 — emote "Cinema"

Arquivo atual: `modelo/variantes/LAST/skin_v16.50_LAST.bbmodel`, gerado por `tools/last_cinema.py` sobre a v16.49.
Prévia: `previews/variante_LAST_cinema.gif`.

**Cinema** (gesto de duração, no menu depois de "Finalizando missão"):
- As mãos vêm à frente do peito e uma placa holográfica aparece entre elas, piscando como holograma.
- As duas mãos pegam a placa pelas laterais. Ele abaixa um pouco (preparação) e a levanta sobre a cabeça, passando
  um pouco do ponto e assentando.
- Segura a placa no alto balançando de leve, com cara orgulhosa, orelhas em pé e cauda abanando. Depois abaixa e o
  holograma some.
- **A placa:** brilha, no mesmo ciano dos outros hologramas do L.A.S.T, tem bordas de rolo de filme e o texto
  **CINEMA**, legível de frente e de trás.
- **Parado:** a placa fica escondida dentro do tronco, como os outros hologramas, e o modelo fica idêntico.

## L.A.S.T v16.49 — limpeza

Arquivo atual: `modelo/variantes/LAST/skin_v16.49_LAST.bbmodel`. Ele é a v16.48 passada por `tools/limpar.py`, e
nada visível mudou: comparei os renders, parado e em várias animações, e são idênticos.

- **Elementos removidos:**
  - os 10 tufos do peito, que estavam escondidos pela roupa e eram invisíveis;
  - `tail_2_bevel`, que estava oculto.
- **Grupos e trilhas:** saíram os 14 grupos que ficaram vazios (os tufos do peito e os grupos que os moviam) e as
  144 trilhas de animação que mexiam neles.
- **Textura:** 1017 pixels que nenhuma face usava foram apagados.
- **Tamanho do arquivo:** caiu de 5,1 MB para 4,4 MB.
- **Animações:** nenhuma estava vazia, sem efeito ou com transição órfã.

## L.A.S.T v16.48 — emotes em loop viram liga/desliga, menu organizado

Arquivo atual: `modelo/variantes/LAST/skin_v16.48_LAST.bbmodel`.

- **Pensativo e Tristeza:** viraram botões de ligar/desligar, como as expressões. Ficam ligados até você apertar de
  novo, mesmo andando, e entram e saem suaves (`g:`).
- **Emotes com começo e fim:** não mudaram.
- **Ordem do menu de gestos:**
  1. Expressões: Raiva, Super sério, WTF, Tranquilidade.
  2. Poses em loop: Pensativo, Tristeza.
  3. Emotes: Saudação, Alongamento, Estalar o pescoço, Investigar, Pouso de herói, Alerta de emergência, Mapa 3D,
     Holograma de missão, Finalizando missão.
  4. Configurações: Esconder orelhas, Esconder cauda, Ignorar capacete.

## L.A.S.T v16.47 — começar / parar de andar mais suave

Arquivo atual: `modelo/variantes/LAST/skin_v16.47_LAST.bbmodel`.

O CPM não deixa a pose de andar ter transição: ela é reiniciada o tempo todo no jogo, então qualquer transição
recomeça sem parar e trava. A troca parado ↔ andando é sempre instantânea. O que dá para fazer é diminuir o tamanho
do salto: a postura fixa do andar caiu pela metade (inclinação, braços, pés, cabeça). O balanço do peito continua.

## L.A.S.T v16.46 — peito parado na escada / trepadeira

Arquivo atual: `modelo/variantes/LAST/skin_v16.46_LAST.bbmodel`.

O balanço do andar agora move um grupo novo, `corpo_mov`, que fica dentro do `body` e contém tudo o que o tronco
carrega: tronco, pelos do peito e cauda. O "Repouso do corpo" que desliga o balanço também age só nesse grupo e
nunca no corpo do Minecraft.

- **Escada / trepadeira:** o repouso voltou para essas poses. O peito não se mexe mais sozinho, e agachar ali
  continua sendo o agachar do Minecraft.
- **Modelo:** visualmente é igual, porque o grupo novo não muda nada parado.

## L.A.S.T v16.45 — agachar na escada / trepadeira

Arquivo atual: `modelo/variantes/LAST/skin_v16.45_LAST.bbmodel`.

Na escada e na trepadeira, o CPM usa a pose de escada mesmo quando você está agachado. O "Repouso do corpo" fixava
o tronco em pé e na posição normal, enquanto o Minecraft agachava as pernas e os braços; ficava quebrado (tronco de
um jeito, pernas para trás). Esse repouso saiu das poses de escada, e agachar ali volta a ser o agachar do Minecraft.

## L.A.S.T v16.44 — pulo e comer padrão, dois emotes removidos, cauda da corrida

Arquivo atual: `modelo/variantes/LAST/skin_v16.44_LAST.bbmodel`.

- **Pular:** sem animação do corpo; braços, pernas, corpo e cabeça são os do Minecraft. Cauda, tufos e orelhas
  continuam.
- **Comer, beber e tomar poção:** removidos, voltam ao padrão do Minecraft.
- **Emotes removidos:** "Deitar e olhar o céu" e "Sentado no bloco".
- **Cauda ao correr:** mais baixa. A curva para cima ao longo da cauda saiu e a base desceu 8°. Ela fica reta para
  trás, flutuando, e continua ondulando.

## L.A.S.T v16.43 — transições mais suaves

Arquivo atual: `modelo/variantes/LAST/skin_v16.43_LAST.bbmodel`.

- **Entradas:** voltaram a ser suaves (0,25 s) em cair, voar, voo criativo, dormir, montado, escada, pegando fogo,
  congelando, comer, escudo e luneta. Correr entra em 0,15 s e pular em 0,05 s, porque com mais tempo a corrida
  com pulos volta a travar.
- **Saídas:** continuam com 0,3–0,6 s.
- **Parado, andar e agachar:** continuam sem transição, porque o CPM reinicia essas poses no jogo.
- **Aviso — Blockbench:** ao abrir o arquivo, o Blockbench renomeia as saídas repetidas (`p:running` →
  `p:running2`). Ao exportar, o CPM avisa "animação de estágio desconhecida". Clique em corrigir e escolha a mesma
  pose; sem isso as saídas não são exportadas e a pose termina de uma vez.

## L.A.S.T v16.42 — dormir com pernas retas, postura do andar

Arquivo atual: `modelo/variantes/LAST/skin_v16.42_LAST.bbmodel`.

- **Dormindo:** pernas quase retas, porque antes subiam demais.
- **Andando:** postura nova, com braços levemente à frente e soltos, mãos viradas para dentro e pés um pouco
  abertos. O balanço de braços e pernas ao andar continua sendo o do Minecraft: no jogo, o CPM reinicia a pose
  de andar o tempo todo e só aceita uma postura fixa ali.

## L.A.S.T v16.41 — andar mais contido, corrida agressiva, cara de dor

Arquivo atual: `modelo/variantes/LAST/skin_v16.41_LAST.bbmodel`.

- **Andar:** o corpo (peito) balança bem menos, com metade do giro, da rolagem e do sobe e desce.
- **Correr:** mais agressivo. Inclinação de −18°, passada e braçada maiores, giro de ombros e quique mais fortes,
  cabeça firme olhando à frente.
- **Machucado, pegando fogo e congelando:** cara de dor no lugar da cara triste. Sobrancelhas puxadas para baixo e
  juntas (como raiva), olhos apertados, focinho franzido, orelhas para trás.

## L.A.S.T v16.40 — sem entradas nas poses que o CPM reinicia

Arquivo atual: `modelo/variantes/LAST/skin_v16.40_LAST.bbmodel`.

O CPM entra de novo nas poses com frequência, e cada entrada (`p:<pose>`) recomeça e segura as animações da pose.
Por isso o "Repouso do corpo" não chegava a tocar, e o peito continuava balançando parado ou agachado.

- Parado, agachado, agachado andando, rastejar e nadar não têm mais entrada nem saída: as animações valem na hora.
- As outras entradas duram no máximo 0,1 s.
- O balanço do corpo voltou um pouco mais forte.

## L.A.S.T v16.39 — parado sem balanço do peito

Arquivo atual: `modelo/variantes/LAST/skin_v16.39_LAST.bbmodel`. Igual à v16.38, mas parado o corpo não balança mais.
Era uma leve troca de peso parado, que depois de andar parecia o peito ainda se mexendo.

## L.A.S.T v16.38 — correções do andar (cabeça travada, parada brusca)

Arquivo atual: `modelo/variantes/LAST/skin_v16.38_LAST.bbmodel`.

- **Cabeça travada depois de andar:** o "Repouso do corpo" também mexia (de forma não aditiva) na cabeça e nos
  braços. Agora mexe só no corpo; a cabeça e os braços ficam 100% com o Minecraft.
- **Balanço:** só o corpo balança agora (sobe e desce, rola, gira os ombros), e com amplitude um pouco menor.
- **Parada brusca:** o CPM não consegue misturar a parada com o balanço. O salto ao parar continua, mas ficou menor.

## L.A.S.T v16.37 — andar com balanço que funciona no jogo

Arquivo atual: `modelo/variantes/LAST/skin_v16.37_LAST.bbmodel`.

O teste da v16.36 mostrou que, no jogo, o CPM mostra a pose de andar mas fica reiniciando as animações dela: só uma
postura fixa sobrevive. Por isso o movimento do andar mudou de lugar:

- **Balanço:** foi para uma animação global, "Andando - balanco do corpo". O relógio dela nunca reinicia. O corpo
  sobe e desce duas vezes por passada, o peso rola para o lado da perna de apoio, os ombros giram (os braços
  acompanham) e a cabeça vem junto com um leve atraso.
- **Outros estados:** em todos os outros estados (parado, correr, agachar, pular, nadar, emotes…) uma animação
  "Repouso do corpo" desliga esse balanço. Ela devolve os valores normais só da rotação do corpo e das posições de
  corpo, cabeça e braços. O balanço dos braços e pernas, os itens e o olhar continuam os do Minecraft. Agachado, ela
  usa os valores do agachar do próprio Minecraft.
- **Postura fixa:** na pose de andar ficou a postura fixa (inclinação, braços abertos).

## L.A.S.T v16.36 — andar: postura fixa visível + teste

Arquivo atual: `modelo/variantes/LAST/skin_v16.36_LAST.bbmodel`.

O andar agora tem uma postura fixa bem visível: inclinação de −6°, braços abertos 10° e cabeça erguida. Ela aparece
desde o primeiro quadro e não depende do tempo da animação. Por cima continua a camada de movimento (sobe e desce,
rolagem, giro de ombros).

Serve também de teste no jogo:
- Se ao andar ele não inclinar nem abrir os braços, o CPM não está ativando a pose "andando" nessa instalação.
- Se inclinar mas não balançar, a pose está sendo reiniciada o tempo todo.

## L.A.S.T v16.35 — andar: correção para aparecer no jogo

Arquivo atual: `modelo/variantes/LAST/skin_v16.35_LAST.bbmodel`.

Na v16.34 a camada "corpo solto" do andar não aparecia no jogo. No CPM as animações principais de uma pose só
começam depois da transição de entrada (`p:walking`), e o CPM entra de novo na pose de andar com frequência. Com isso a
entrada recomeçava e a camada nunca chegava a tocar.

O que mudou:
- O andar não tem mais transição de entrada nem de saída. A própria camada começa do zero e aparece em 0,15 s.
- O movimento ficou mais forte:
  - o corpo desce 0,8 px a cada passo;
  - rolagem de 3,5° e giro de ombros de 8°;
  - os braços abrem 5° ± 6°.

## L.A.S.T v16.34 — andar mais solto

Arquivo atual: `modelo/variantes/LAST/skin_v16.34_LAST.bbmodel`, gerado por `tools/movimento_last2.py`. É igual à
v16.33, só muda o andar.

Braços e pernas continuam no balanço do Minecraft, que é o único que não recomeça no jogo. Por cima entra uma camada
"corpo solto", no ritmo do passo do Minecraft (0,55 s):
- o corpo sobe e desce a cada pisada;
- o peso rola para o lado da perna de apoio;
- os ombros giram;
- os braços se abrem e fecham de lado, com atraso;
- a cabeça estabiliza o olhar um instante depois;
- o quadril abre as pernas na passagem.

Essa camada começa do zero e entra em 0,3 s. Se o CPM entrar de novo na pose de andar, ela só aparece de novo,
sem tranco.

Prévia: `previews/variante_LAST_andar.gif`. Os braços e pernas da prévia são simulados.

## L.A.S.T v16.33 — versão atual (estável no jogo)

Arquivo: `modelo/variantes/LAST/skin_v16.33_LAST.bbmodel`, gerado por `tools/movimento_last2.py` sobre a v16.30.

O que o CPM permite, aprendido testando no jogo:
- **Andar e agachado andando:** o CPM detecta "andando" pela mudança de posição entre quadros e entra e sai dessa pose
  o tempo todo. Por isso um ciclo próprio recomeçava sem parar ("dá uma flicada e volta para o começo"). Agora usam o
  balanço do próprio Minecraft (sincronizado, nunca recomeça) com postura por cima: leve inclinação, braços soltos e um
  pouco abertos, transição suave de 0,3 s. As poses de item (arco, escudo, besta, luneta) voltam a ser as do
  Minecraft e seguem a mira.
- **Rastejar e nadar:** essas poses continuam ativas com você parado, então nada ali pode se mexer sozinho. As
  braçadas e pernadas são as do Minecraft (só quando você se move) e por cima vai uma postura fixa: cabeça olhando à
  frente e pernas um pouco abertas.
- **Correr:** é estável (o CPM usa o próprio sprint). Continua com o nosso ciclo: passada, ombros, quique, inclinação
  e cauda baixa.
- **Pular:** também é estável. As pernas fazem o nosso ciclo de impulso, encolher e esticar; os braços continuam os
  do Minecraft (itens funcionam).
- **Agachado:** ombros mais baixos (−1 px), patas à frente.
- **Golpe:** recriado pela fórmula do Minecraft, para aparecer também correndo.

## L.A.S.T v16.32 — correção: animações contínuas no jogo

Arquivo atual: `modelo/variantes/LAST/skin_v16.32_LAST.bbmodel`. As animações são as mesmas da v16.31, com uma
correção.

**O problema no jogo:** no CPM, as animações de uma pose só começam depois da transição de entrada (`p:<pose>`
setup). Ela durava 0,3 s andando e 0,45 s correndo, e nesse tempo aparecia o balanço do Minecraft. Ao entrar de novo
na pose (por exemplo, depois de cada pulo), o ciclo voltava ao começo: parecia que fazia a animação e voltava para a
inicial.

**A correção:**
- As entradas de andar, correr, agachado andando, pular, rastejar e nadar agora são curtas (0,05–0,15 s).
- Os ciclos começam na posição de passagem (pernas juntas, braços embaixo), perto de onde o balanço do Minecraft
  também está. Entrar na pose ou voltar a ela depois de um pulo não dá mais tranco.

## L.A.S.T v16.31 — passos de verdade (andar, correr, agachar, rastejar, nadar, pular)

Arquivo `modelo/variantes/LAST/skin_v16.31_LAST.bbmodel`, gerado por `tools/movimento_last2.py` sobre a v16.30.

Nesses estados, braços e pernas agora são os nossos ciclos, e não mais o balanço do Minecraft. Por cima do balanço
não dá para sincronizar ombro, peso e passo, porque o CPM não informa a fase do passo. O ritmo é o do próprio
Minecraft: 0,55 s por passada andando e 0,47 s correndo.

- **Andar / correr:** a perna vai à frente rápida (pé no ar) e empurra devagar (pé no chão). Os braços balançam com
  atraso. Os ombros giram contra o quadril, o corpo desce a cada pisada, o peso passa para a perna de apoio e a
  cabeça estabiliza o olhar.
- **Correr:** inclinado para a frente, passada maior e mais quique. A cauda não sobe mais tanto.
- **Agachado andando:** passos lentos de quem espreita, patas baixas e à frente.
- **Agachado parado:** em posição, alerta, ombros respirando, um pé à frente.
- **Rastejar:** rastejo militar. Um braço de cada vez puxa o corpo, as pernas empurram como sapo, o corpo rola e a
  cabeça olha adiante.
- **Nadar:** pernadas longas, uma perna depois da outra; as braçadas continuam as do Minecraft.
- **Pular:** impulso, as pernas encolhem uma depois da outra e esticam para o chão; os braços sobem e abrem.
- **Virar:** as pernas giram com o corpo, e a perna do lado para onde você vira dá um passo para fora.
- **Poses de item recriadas:** como os braços do andar substituem os do Minecraft, estas foram refeitas pelas
  fórmulas do próprio jogo: escudo, arco, besta (carregando e pronta), luneta, tridente, corneta, pincel, comer e o
  golpe.

**Limites que o CPM impõe:**
- A mira do arco, da besta, da luneta e da corneta não acompanha o olhar para cima e para baixo; fica na horizontal.
- Ao começar ou parar de andar, braços e pernas podem dar um pequeno salto de posição: o CPM não consegue misturar
  o ciclo próprio com o balanço do Minecraft.

## L.A.S.T v16.30 — corrida, pulo, natação, voo e virar mais soltos

Arquivo `modelo/variantes/LAST/skin_v16.30_LAST.bbmodel`, gerado por `tools/movimento_last.py` sobre a v16.29. Só o
L.A.S.T muda; modelo e textura são os mesmos.

- **Correndo:** o corpo inclina bem para a frente (−12°), e essa inclinação "respira". O tronco balança devagar e de
  forma orgânica, e a cabeça estabiliza o olhar um pouco depois do corpo. Braços soltos e um pouco abertos. Entra e
  sai com suavidade (passa um pouco do ponto e assenta).
- **Virando:** quando você vira a câmera, o tronco e os ombros giram junto, na direção para onde você olha, com as
  pernas plantadas. Olhar para cima ou para baixo inclina o tronco um pouco. A cauda e as orelhas já acompanhavam.
- **Pulando:** impulso com os braços subindo, as pernas encolhem uma depois da outra, ele estica para o chão e olha
  para onde vai cair.
- **Aterrissagem:** o corpo afunda, os braços vão para a frente, ele quica um pouco e assenta.
- **Pulo correndo:** a inclinação da corrida passa para a do pulo e volta, sem tranco.
- **Caindo:** braços e pernas se debatem mais devagar e soltos, cada um no seu tempo.
- **Nadando:** o corpo rola com as braçadas, a cabeça fica estável e as pernas batem uma depois da outra.
- **Elytra:** braços para trás como asas, com uma vibração lenta; pernas soltas atrás, leve rolagem.
- **Voo criativo:** pairando, sobe e desce, pernas balançando e braços flutuando, cada um com seu atraso.
- **Braços e pernas:** o balanço do Minecraft continua por baixo. Ele mantém o passo sincronizado com a velocidade e
  evita tranco ao começar a correr, pular ou parar.
- Prévia: `previews/variante_LAST_movimento.gif`. Os braços e pernas da corrida na prévia são simulados.

## Movimento do corpo (v16.29 / Templário v16.34)

O CPM não usa animações de texture pack (Fresh Animations etc.). Por isso `tools/movimento.py` anima o corpo em todos
os estados de movimento, seguindo as regras de animação avançada (preparação, peso, atraso entre as partes,
overshoot, assentamento, loops contínuos):

- **Braços e pernas:** o balanço de braços/pernas do próprio Minecraft continua. É o único sincronizado com a sua
  velocidade real e mantém as poses de item funcionando (arco seguindo a mira, escudo, besta, luneta). Por cima dele
  entram postura, peso, inclinação e reações.
- **Andando:** leve inclinação, braços soltos ao lado do corpo, cabeça compensando.
- **Correndo:** tronco bem inclinado para a frente, cabeça olhando adiante, braços mais à frente.
- **Agachado:** postura de raposa espreitando, patas prontas.
- **Pulando:** impulso, encolhe as pernas, estica para a aterrissagem.
- **Caindo:** braços abertos se equilibrando, pernas prontas, olhando para baixo.
- **Atacando:** preparação, golpe com giro do tronco, o outro braço em contrapeso, peso no pé da frente,
  continuação do movimento e assentamento. É sincronizado com o próprio golpe (o CPM toca essa animação pelo
  progresso do ataque).
- **Comendo / bebendo** (novo, mão direita ou esquerda): leva a comida à frente do focinho e mastiga.
- **Escada:** mãos nos degraus; subindo, mãos e pés alternam.
- **Nadando / rastejando:** onda no corpo, cabeça olhando para a frente.
- **Elytra:** corpo aerodinâmico, braços para trás.
- **Voo criativo:** pairando com as pernas soltas.
- **Dormindo:** encolhido como raposa.
- **Montado:** mãos nas rédeas.
- **Machucado:** impacto, recuo e recuperação.
- **Morrendo:** o corpo amolece.
- **Pegando fogo:** batendo nas chamas.
- **Congelando:** se abraçando e tremendo.
- **Parado:** troca de peso bem sutil.
- Tudo entra e sai suave (`p:<pose>`), e as animações que já existiam (cauda, orelhas, pelos) continuam iguais.
  Modelo e textura não mudam.
- Prévia: `previews/variante_LAST_movimento.gif`. O balanço de braços/pernas da prévia é simulado; no jogo é o do
  Minecraft.
- Arquivos: `modelo/skin_v16.29.bbmodel`, `modelo/variantes/LAST/skin_v16.29_LAST.bbmodel`,
  `modelo/variantes/BRANCA/skin_v16.34_BRANCA.bbmodel`.
- Gerar: `python3 tools/movimento.py <modelo.bbmodel> <saida.bbmodel>`. Também funciona no arquivo dos Caçadores.

## Variantes (universo L.A.S.T)

Mesma estrutura, mesmo rosto, mesmas animações/emotes/expressões — só a textura da roupa (e, quando a variante
pedir, a cor do pelo) muda. Cada variante é um modelo separado: exporte cada `.bbmodel` com o plugin do CPM e
coloque os `.cpmmodel` em `.minecraft/player_models`; no menu de **Modelos** do CPM, dentro do jogo, você escolhe e
aplica qualquer um na hora.

- `tools/variante.py <base.bbmodel> <skin64.png> <saida.bbmodel> [--hide ...] [--lambda] [--fur paleta] [--head-top linhas]`:
  gera uma variante. Lê a skin 64×64 no layout padrão e redesenha corpo/braços/pernas em 2 px por unidade
  (Scale2x + acabamento leve de tecido; cores fortes ficam nítidas). A **segunda camada** da skin vai na casca
  própria do modelo (jaqueta, mangas e calças, 0,15 maior que o corpo) na mesma resolução. A textura da variante
  é **256×256**: o atlas antigo fica intacto no canto superior esquerdo (mesmas UVs) e o resto vai no espaço novo.
  - `--fur <paleta>`: troca a cor do **pelo escuro** (cabeça, orelhas, tufos, cauda, pálpebras) com um mapa de
    gradiente sobre o brilho do próprio pelo — as sombras e transições ficam onde estão. O **pelo branco/cinza**
    (focinho, peito, dentro das orelhas, ponta da cauda) é de todos os Emezomm e **não muda** (transição suave
    entre os dois). Nunca muda também: olhos pintados, íris, nariz, faixa das sobrancelhas, cílios, objetos.
  - `--acessorios <nome>`: acessórios **3D** da variante (`tools/acessorios.py`, pixel art pintada em código,
    2 px por unidade), como peças novas presas na cabeça/focinho — o modelo existente não é alterado.
  - `--head-top <linhas>`: acessórios de cabeça (gorro, óculos, faixas) vão na casca do chapéu (0,25 em volta da
    cabeça, que fica visível só nessas variantes): as primeiras <linhas> da cabeça da skin + a camada de chapéu
    da skin. O rosto embaixo não muda.
  - `--brow <paleta>`: cor da sobrancelha (faixa) combinando com o pelo da variante.
  - `--emotes <nomes>`: mantém só esses emotes/configurações (e suas transições); `--remove-props <prefixos>`
    tira os objetos dos emotes retirados (ex.: `holo,bracelete`).
  - `--slim`: braços slim (3 de largura) lendo o formato slim da skin; `--ear-blend`: transição pintada nas
    laterais da cabeça onde as orelhas encostam.
  - `--head-paint r0-r1`: pinta as linhas r0..r1 da cabeça da skin (capuz, gola) na cabeça do modelo — só tecido e
    dourado, nunca o pelo ou o rosto — e põe as mesmas linhas da camada de chapéu em relevo na casca da cabeça.
  - `--smooth`: pedacinhos soltos (< 4 px) da 2ª camada vão só para a 1ª, a 1ª fica igual por baixo da 2ª e as
    cores próximas ganham transição suave; `--keep-tex arquivo:peça.face,...` mantém pintura feita à mão.
  - `--hide`: grupos ou peças de tufo cobertos pela roupa/acessório (apontados para um texel transparente).
  - `--pelo parte.face[:linhas],...`: onde a skin pintou um acessório verde que a variante não usa (bandana),
    mostra o pelo do próprio Emezomm (já com a cor da variante).
  - A cabeça do modelo nunca é tocada (só a cor do pelo, com `--fur`).
- **L.A.S.T** — `modelo/variantes/LAST/skin_v16.28_LAST.bbmodel` (+ `Emezomm-CPM_v16.28_LAST_256.png`), da skin
  `skin_LAST_64x64_original.png` (pixels quase transparentes da camada externa — sobras de borracha — ignorados).
  Jaqueta cinza/preta, camisa branca com o **λ laranja** no peito (nas duas camadas), faixa na cintura, calça
  branca com faixas e botas, com a segunda camada em relevo. Tufos do peito escondidos pela camisa.
  Prévia: `previews/variante_LAST.png`.
  Comando: `python3 tools/variante.py modelo/skin_v16.28.bbmodel modelo/variantes/LAST/skin_LAST_64x64_original.png modelo/variantes/LAST/skin_v16.28_LAST.bbmodel --hide fur_chest --lambda`

- **Caçadores de recompensas** (variante verde) — `modelo/variantes/CACADORES/skin_v16.28_CACADORES.bbmodel`
  (+ `Emezomm-CPM_v16.28_CACADORES_256.png`), da skin `skin_CACADORES_64x64_original.png`. Pelo escuro verde (o
  branco continua branco), sobrancelha verde, colete de couro com o peito do Emezomm no decote, mangas cinza,
  luvas, cinto e botas, com a segunda camada. Prévias: `previews/variante_CACADORES.png` e
  `previews/variante_CACADORES_emotes.gif`.
  - **Óculos** no estilo do ajuste enviado (inclinados 25° no alto da testa, alça descendo até a nuca).
  - **Bandana no pescoço** como a referência: faixa com losangos e o **triângulo liso** com borda escura,
    contorno claro por dentro e losangos, mais o losango em relevo no centro. A ponta fica num grupo próprio.
  - **Acessórios animados**: a ponta da bandana balança parada, sacode andando, esvoaça correndo/pulando/caindo;
    os óculos quicam com os passos e levantam nos pulos e quedas.
  - **Emote Jogar moeda** (loop até se mover; a moeda fica escondida dentro do braço direito): moeda de ouro maciça
    e detalhada, preparação, peteleco, sobe bem alto girando e balançando, a cabeça e as orelhas acompanham, a mão
    sobe para pegar e dá o tranco.
  - Também ficam: expressões (Raiva, Super serio, WTF, Tranquilidade), Alongamento, Estalar o pescoco e as
    configurações de orelha, cauda e capacete. Sem nada tecnológico (hologramas e bracelete removidos do modelo,
    óculos sem brilho). Retirados nesta variante: Limpar a poeira, Afiar a lâmina, Encarar o horizonte, Reconhecer o
    alvo, Finalizando contrato, Saudacao do velho oeste e a opção de colocar os óculos (com contrato, carvão e tudo
    o que era deles).
  - Gerar: `python3 tools/variante.py modelo/skin_v16.28.bbmodel modelo/variantes/CACADORES/skin_CACADORES_64x64_original.png modelo/variantes/CACADORES/skin_v16.28_CACADORES.bbmodel --fur verde --brow verde --acessorios cacadores --hide fur_chest --pelo body.north:0-4,body.south:0-1,body.up --emotes "Raiva,Super serio,WTF,Tranquilidade,Alongamento,Estalar o pescoco,Esconder orelhas,Esconder cauda,Ignorar capacete" --remove-props holo,bracelete`
    e depois `python3 tools/cacadores_emotes.py modelo/variantes/CACADORES/skin_v16.28_CACADORES.bbmodel modelo/variantes/CACADORES/skin_v16.28_CACADORES.bbmodel`
    (`tools/animlib.py` = ferramentas de animação compartilhadas com o gerador principal).

- **Templário — versão atual: `modelo/variantes/BRANCA/skin_v16.33_BRANCA.bbmodel`** (+ `Emezomm-CPM_v16.33_BRANCA_256.png`):
  o seu v16.32 (nada dele mudou: elementos, grupos, animações e pixels pintados ficam idênticos) + os emotes finais
  (prévia: `previews/variante_BRANCA_emotes.gif`):
  - **Rezar** (contínuo, até você se mover): fecha os olhos com a **sobrancelha franzida** (rosto sério), abaixa a
    cabeça e junta as mãos segurando um **crucifixo dourado grande** (com um rubi no centro); respira devagar (o peito
    puxa, a cabeça e os braços acompanham um pouco depois), orelhas para trás, cauda calma.
  - **Meditacao extrema** (contínuo): **levita em pé**, olhos fechados e sobrancelha franzida (rosto sério), braços
    um pouco abertos ao lado do corpo e pernas soltas. Na entrada ele dá uma pequena agachada, sobe, passa um pouco do
    ponto e assenta; no ar sobe e desce devagar (corpo primeiro, cabeça, braços e pernas respondendo depois), a cauda
    e os pelos ondulam sem peso; na saída desce e faz um pequeno impacto ao tocar o chão.
  - **Subestimar** (expressão alternável, só no rosto, como Raiva/WTF): "e isso?" — uma sobrancelha erguida, o outro
    olho meio fechado de tédio, olhando para baixo, orelhas de lado e uma bufada pelo focinho.
  - **Explosao de luz** (gesto de duração): o crucifixo aparece nas mãos juntas, ele abaixa um pouco a cruz e o corpo
    (preparação), ergue com as duas mãos acima da cabeça (passa um pouco e assenta), segura parado enquanto a luz junta
    e a cruz solta uma **explosão de luz** (raios brilhantes em 3D + clarão, com brilho `glow`), que empurra o
    corpo, as orelhas, os pelos e a cauda; depois a luz some e ele abaixa a cruz.
  - O crucifixo e a luz são peças novas, escondidas dentro do braço direito fora desses emotes (invisíveis em
    qualquer ângulo) e pintadas em espaço livre do atlas. Os olhos fechados usam uma animação de pálpebras própria
    chamada `<emote>#olhos`: o CPM ignora o que vem depois do `#`, então ela faz parte do mesmo botão.
  - Animação refeita com as regras de animação avançada: entradas e saídas com preparação, overshoot e assentamento;
    o tronco começa, braços, cabeça, orelhas, cauda e pelos chegam depois (atraso de fase); recuo da explosão
    amortecido; loops contínuos (todas as ondas fecham no fim do ciclo); a escala só é usada onde é efeito (a luz e
    o crucifixo aparecendo).
  - **Pálpebras corrigidas** (vale para todas as expressões e emotes): com o olho fechado, às vezes aparecia um risco
    preto (a íris) entre a faixa da sobrancelha e a pálpebra, ou acima da faixa, quando a sobrancelha subia ou
    inclinava (Raiva, WTF, Expressão, Rezar, Meditação, Subestimar), e uma fresta escura entre a pálpebra e o rosto
    vista de lado. A pálpebra de cima agora sobe 2 texels (até cobrir toda a íris, atrás da faixa) e as duas
    pálpebras ficam mais fundas, encostando no rosto quando aparecem. Paradas continuam escondidas dentro da cabeça;
    só esses 4 elementos mudaram.
  - Gerar: `python3 tools/templario_emotes.py modelo/variantes/BRANCA/skin_v16.32_BRANCA.bbmodel modelo/variantes/BRANCA/skin_v16.33_BRANCA.bbmodel`
- **Templário v16.32** — `modelo/variantes/BRANCA/skin_v16.32_BRANCA.bbmodel` (+ `Emezomm-CPM_v16.32_BRANCA_256.png`):
  é o seu arquivo com os ajustes e melhorias de textura (`ajuste_usuario_v16.32_BRANCA.bbmodel`) + a **cruz dourada
  nas costas**, copiada da cruz da frente (mesmo dourado e sombreado, simétrica, no painel branco das costas). Só a
  textura das costas mudou (88 pixels). A partir daqui o arquivo de referência do Templário é este, com as suas
  edições à mão; o comando abaixo gera a base antiga (sem elas).
- **Templário (variante branca)** — `modelo/variantes/BRANCA/skin_v16.28_BRANCA.bbmodel`
  (+ `Emezomm-CPM_v16.28_BRANCA_256.png`), da skin `skin_BRANCA_64x64_original.png`. Pelo escuro vira
  **branco/cinza-claro** (o branco original continua), rosto igual, **sobrancelha** no branco do pelo só que mais
  escura (destaca), **transição suave** pintada nas laterais da cabeça onde as orelhas encostam. **Braços slim**
  (3 de largura, como a skin — sem bug nos ombros). Roupa de cavaleiro: tabardo creme com **cruz dourada**,
  ombreiras e braços de couro escuro com detalhes dourados, cinto, calça e botas com rebites dourados, com a
  segunda camada (pedacinhos soltos da 2ª camada vão para a 1ª e as cores próximas têm transição suave:
  `--smooth`). **Capuz pintado na cabeça** como na skin (`--head-paint 5-7`): faixa
  dourada inclinada e pano creme nas laterais, na nuca e embaixo da cabeça (na frente só os cantos dourados ao lado
  do focinho; rosto intacto), com a faixa em **relevo** contínua na casca da cabeça (camada de chapéu da skin). Regra dos tufos: onde tem
  roupa o tufo não aparece — escondidos os do peito, os 2 de baixo da nuca (caem sobre o capuz) e a peça de pelo
  das bochechas que fica dentro do capuz; os **pelos ao lado do rosto** continuam. Os ajustes que você mandou
  (`ajuste_usuario_v16.29/v16.31_BRANCA.bbmodel`) foram seguidos. A pintura que você
  fez nos ombros (`ajuste_usuario_v16.29_BRANCA.bbmodel`) é mantida (`--keep-tex`).
  **Emotes:** expressões (Raiva, Super serio, WTF, Tranquilidade), Investigar, Pouso de heroi, Estalar o pescoco e
  as configurações (orelhas, cauda, capacete). Retirados: todos os tecnológicos (com hologramas e bracelete),
  Alongamento, Deitar e olhar o ceu, Pensativo, Tristeza, Sentado no bloco e Saudacao.
  Prévia: `previews/variante_BRANCA.png`.
  Comando: `python3 tools/variante.py modelo/skin_v16.28.bbmodel modelo/variantes/BRANCA/skin_BRANCA_64x64_original.png modelo/variantes/BRANCA/skin_v16.28_BRANCA.bbmodel --fur branco --brow branco --hide fur_chest,bochechas,fur_back_3,fur_back_4 --slim --ear-blend --smooth --head-paint 5-7 --keep-tex "modelo/variantes/BRANCA/ajuste_usuario_v16.29_BRANCA.bbmodel:left_arm.west,left_arm.up,right_arm.east,right_arm.up" --emotes "Raiva,Super serio,WTF,Tranquilidade,Investigar,Pouso de heroi,Estalar o pescoco,Esconder orelhas,Esconder cauda,Ignorar capacete" --remove-props holo,bracelete`

**Aviso sobre o Blockbench:** as transições de entrada e saída do CPM têm o **mesmo nome** (ex.: `p:walking` e
`g:Raiva`, uma "setup" e outra "finish"). Ao abrir o projeto, o Blockbench renomeia a segunda para `p:walking2` /
`g:Raiva2`. Na exportação o CPM avisa as `p:...2` e oferece corrigir (escolha a pose correspondente); as `g:` e `c:`
com "2" no fim perdem a transição de saída. Os arquivos gerados aqui saem com os nomes certos.

## Versão atual: v16.28 (WTF refeito)

- `modelo/skin_v16.28.bbmodel` (+ `Emezomm-CPM_v16_28_128.png`): **modelo atual**. Visual parado idêntico
  (conferido em 5 ângulos); só a expressão **WTF** mudou. `previews/v16_28_wtf.gif`: prévia.
  `tools/v16_28_emotes.py` gera tudo.
- **WTF** agora é o choque travado de "que porra é essa": olhos **arregalados** (faixa lá em cima, reta),
  **pupilas minúsculas** tremendo de leve, olhar fixo pra frente, orelhas duras e **gotas de suor** escorrendo
  pelo rosto (3 gotas novas `suor_1..3`, escondidas dentro da cabeça fora da expressão). O rubor da v16.27 saiu.

## v16.27 (ajustes: capacete, expressões, pescoço, inventário)

- `modelo/skin_v16.27.bbmodel` (+ `Emezomm-CPM_v16_27_128.png`). Visual parado idêntico à v16.26
  (conferido em 5 ângulos); `previews/v16_27_expressoes.gif`: prévia. `tools/v16_27_emotes.py` gera tudo.

- **Ignorar capacete consertado.** Causa: o exportador do CPM só grava um canal de escala se ele muda mais de
  0,01 em relação a 1 — a opção usava escala exatamente 1, então saía **vazia**. Agora usa 1,015 (invisível).
- **Expressões só no rosto** — agora são **camadas** (liga/desliga): ficam ativas até você desligar, mesmo
  andando, e entram/saem suaves (`g:<nome>`). Mexem só em pálpebras/faixa, olhos, focinho, orelhas e pelos da
  cabeça — corpo e cauda livres.
  - **Raiva** — sobrancelhas bem franzidas, orelhas coladas pra trás, focinho franzindo, pelos da cabeça eriçados.
  - **Super serio** — olhar reto, fechado e fixo; orelhas um pouco pra trás; nada se mexe.
  - **WTF** (refeito: estranheza + vergonha + surpresa) — pálpebras levantadas (uma mais que a outra), olhar
    desviando de lado e voltando, **rubor nas bochechas** (novo, escondido dentro da cabeça fora da expressão),
    orelhas abertas pros lados com tremidinhas nervosas.
  - **Tranquilidade** (nova) — pálpebras suaves e relaxadas, olhar calmo, orelhas soltas balançando devagar.
- **Estalar o pescoco** agora é um gesto com fim (4,6 s): começa e termina na pose normal.
- **Inventário**: a cauda balança bem menos e mais devagar (era 16° a cada 0,6 s; agora 3,5° a cada 2,4 s).

## v16.26 (últimos emotes)

- `modelo/skin_v16.26.bbmodel` (+ `Emezomm-CPM_v16_26_128.png`). Tudo da v16.25 idêntico
  (geometria, textura e todas as animações — conferido); só foram adicionados 5 emotes.
- `tools/v16_26_emotes.py`: gera tudo. `previews/v16_26_emotes.gif`: prévia dos emotes novos.

### Emotes novos — todos contínuos (loop até você se mover, com entrada e saída suaves)
- **Raiva** — inclinado pra frente, braços tensos, orelhas coladas pra trás, sobrancelhas franzidas, pelos e
  cauda eriçados, cauda chicoteando, respiração pesada e focinho franzindo.
- **Sentado no bloco** — fique em pé **na beirada de um bloco**, virado pra fora: ele senta no bloco, apoiado nas
  mãos atrás, pernas balançando pra fora da beirada, cauda deitada no bloco e olhando em volta.
- **Estalar o pescoco** — inclina a cabeça pra um lado (estalo), pro outro (estalo), gira o pescoço e solta os
  ombros; a cada estalo os olhos apertam, as orelhas e os pelos dão um tranco.
- **Super serio** — braços cruzados, olhar reto e fechado, orelhas um pouco pra trás, cauda parada.
- **WTF** — cabeça puxada pra trás e inclinada, uma pálpebra levantada e a outra franzida, orelhas abertas
  pros lados, olhar travado ("que porra é essa?").

## v16.25 (emotes finais + ignorar capacete)

- `modelo/skin_v16.25.bbmodel` (+ `Emezomm-CPM_v16_25_128.png`). Geometria e textura idênticas
  à v16.24; animações antigas idênticas (conferido), exceto as mudanças abaixo.
- `tools/v16_25_emotes.py`: gera tudo. `previews/v16_25_emotes.gif`: prévia dos emotes novos.

### Removidos
Parecer serio, Flexoes, Comemoracao, Dar de ombros e Descansar (com as transições deles).

### Configurações (alternáveis do CPM)
- **Esconder orelhas**, **Esconder cauda** (como antes).
- **Ignorar capacete** (novo) — com ele ligado as orelhas aparecem mesmo de capacete/cabeça de mob.
  Como funciona: o capacete agora esconde as orelhas com uma animação **não aditiva** própria
  ("Com capacete - orelhas", prioridade 50); "Ignorar capacete" (prioridade 60) volta as orelhas ao tamanho
  normal e "Esconder orelhas" (prioridade 70) continua vencendo os dois. Os tufos do topo da cabeça continuam
  escondidos pelo capacete, pra não atravessar.

### Emotes contínuos (loop até você se mover; entrada e saída suaves `c:<nome>`)
- **Deitar e olhar o ceu** (como antes).
- **Pensativo** — agora é contínuo: mão no queixo, cabeça balança devagar, olhos vagando, orelha mexendo.
- **Tristeza** (novo) — cabisbaixo, ombros caídos, orelhas e cauda pra baixo, suspiro pesado a cada ciclo
  (sem choro).

### Emotes de duração (começam e terminam sozinhos, com entrada e saída suaves)
- Alerta de emergencia, Mapa 3D, Holograma de missao, Investigar, Saudacao (como antes).
- **Alongamento** (novo) — estica os braços pra cima na ponta dos pés, inclina pros dois lados, puxa cada braço
  sobre o peito e balança as pernas; orelhas e pelos acompanham.
- **Finalizando missao** (novo) — ergue o bracelete, abre o holograma, passa até o último item, toca e o
  **check verde** aparece "carimbando"; acena com a cabeça, fecha o holograma, soquinho de vitória e abana a cauda.
- **Pouso de heroi** (novo) — use logo ao cair de um lugar alto: impacto com joelho e mão no chão, pelos
  levantando, cabeça baixa… levanta o olhar pra frente, se ergue devagar e fica de pé imponente.

## v16.24 (configurações + emotes)

- `modelo/skin_v16.24.bbmodel`. Tudo da v16.23 continua igual (animações antigas idênticas,
  visual parado idêntico — conferido).
- `tools/v16_24_emotes.py`: gera tudo. `previews/v16_24_emotes.gif`: prévia de todos os emotes.

### Configurações (alternáveis do CPM)
- **Esconder orelhas**, **Esconder cauda** (a cauda e o anel de pelo da raiz).

### Emotes contínuos (poses personalizadas do CPM — ficam em loop e o CPM cancela sozinho quando você se move)
- **Descansar** — senta, abaixa as orelhas e deixa a cauda repousar no chão.
- **Parecer serio** — continência perfeita… mas a cauda não para de balançar.
- **Deitar e olhar o ceu** — deitado de costas, mãos atrás da cabeça, cauda de lado.
- **Flexoes** — flexões de verdade (mãos no chão, corpo em prancha subindo e descendo).
Cada um tem transição de entrada e de saída (`c:<nome>` setup/finish).

### Emotes de duração (gestos do CPM — começam e terminam sozinhos, com entrada e saída suaves)
- **Alerta de emergencia** — ergue o pulso, toca no bracelete, o sinal pisca e aparece a confirmação.
- **Mapa 3D** — projeta um mapa holográfico e gira com a outra mão.
- **Holograma de missao** — ergue o bracelete, projeta a interface e navega tocando nela.
- **Investigar** — ajoelha, fareja e examina o chão.
- **Saudacao** — acena, inclina a cabeça e abana a cauda.
- **Pensativo** — mão no queixo, olha para cima, mexe uma orelha.
- **Comemoracao** — salto exagerado, aterrissa meio torto e se recupera.
- **Dar de ombros**.

### Objetos dos emotes (invisíveis fora deles)
- `bracelete` (dentro do antebraço esquerdo; nos emotes cresce e aparece no pulso, com LEDs brilhando).
- `holo` → `holo_mapa`, `holo_painel` (+ `holo_card`), `holo_sinal`, `holo_ok`: hologramas translúcidos
  e brilhantes guardados dentro do corpo; os emotes os puxam para a frente e aumentam.

## v16.23 (olhos consertados, cauda deitada, botão das orelhas)

- `modelo/skin_v16.23.bbmodel`: **modelo atual**. Visual parado idêntico à v16.22 (conferido em 5 ângulos).
- `tools/v16_23_animacoes.py`: gera tudo. `previews/v16_23_olhos_cauda.png`: conferência.

- **Piscar tinha parado — causa**: no CPM a escala de animações aditivas é **multiplicada**. Várias animações
  (piscar, olhar p/ baixo, vida, poses) deixavam as pálpebras em 0,04 ao mesmo tempo → 0,04 × 0,04… e o piscar
  nunca conseguia fechar. **Correção**: as pálpebras agora são movidas só por animações **não aditivas**
  "<nome> - olhos", com prioridade (piscar = 0, franzir das poses = 20, arco/luneta = 30, dormir/morrer = 40):
  sempre exatamente uma delas manda nas pálpebras. Olhar para baixo e vida baixa franzem só com a faixa cinza.
- **Flicker no olho**: as pálpebras escondidas ficavam 0,01 atrás da face (disputa de profundidade);
  agora ficam 0,1 para dentro da cabeça.
- **Preto "vazado" acima da faixa** (bloquear, arco, luneta): nova capa cor de pelo `cobre_olho_R/L` sobre o
  topo do olho pintado, escondida atrás da faixa no repouso (plano de 1 face só).
- **Cauda com o corpo deitado** (nadar, rastejar, elytra): aponta para baixo, na direção dos pés.
- **Botão "Esconder orelhas"** (alternável do CPM): liga/desliga as orelhas.

## v16.22 (tufos grudados, transições suaves, rosto mais aberto)

- `modelo/skin_v16.22.bbmodel`: **modelo atual** (cubos e textura idênticos à v16.21; visual parado conferido pixel a pixel).
- `tools/v16_22_animacoes.py`: gera tudo. `previews/v16_22_transicao_agachar.gif`: transição ao agachar/levantar.

- **Tufos grudados no corpo**: cada tufo da cabeça e do peito ganhou um osso próprio `mov_<tufo>` (rotação 0,
  pivô na raiz do tufo). As animações não giram/escalam mais o grupo inteiro (o que enfiava tufos no corpo e
  deixava outros flutuando): cada tufo só **levanta** um pouco da pele em volta da própria raiz e volta,
  nunca abaixo da posição de repouso (conferido numericamente nos 24 tufos).
- **Transições suaves**: cada pose de movimento tem animação de entrada (`setup`) e de saída (`finish`) do
  CPM (nome `p:<pose>`), que levam da posição normal até a pose e de volta em 0,15–0,6 s — as orelhas
  abaixam aos poucos ao agachar e sobem aos poucos ao levantar, a cauda sobe aos poucos ao cair, etc.
- **Íris**: o olhar sozinho agora anda no máximo 0,15 e o seguir a cabeça 0,32 (somados 0,47, espaço até a
  borda do olho 0,62) — não sai mais do olho.
- **Farejar**: bem mais sutil (menos vezes, movimento de ~1/3).
- **Rosto mais aberto**: nova animação sempre ativa **"Expressao"** — a faixa cinza fica um pouco mais alta
  (aparece mais olho) e de vez em quando sobe (surpresa leve) ou levanta de um lado só (curioso); no piscar
  ela desce junto com a pálpebra.

## v16.21 (animações corrigidas)

- `modelo/skin_v16.21.bbmodel`: **modelo atual** (modelo/texture idênticos à v16.20, só animações mudaram).
- `tools/v16_21_animacoes.py`: gera as animações. `previews/v16_21_animacoes.gif`: prévia.

- **Sinal corrigido**: o exportador do CPM inverte X/Y tanto da rotação dos grupos quanto das keyframes;
  as versões anteriores inverteram mais uma vez, por isso no jogo a cauda descia ao cair, ficava baixa ao
  correr, subia ao agachar, e as orelhas/olhos iam para o lado errado. Agora a keyframe tem o valor direto.
- **Emotes removidos** (gestos e alternáveis) — serão adicionados um a um.
- **Física da cauda**: caindo → sobe (arrasto do ar); correndo → esticada para trás; agachado → baixa
  (compensando a inclinação do corpo); pulando → sobe; nadando/elytra/rastejando → reta, como leme.
- **Olhos acompanham a cabeça**: virar a cabeça leva a íris para o lado (um pouco antes da cabeça);
  olhar para cima abre os olhos e sobe a íris; olhar para baixo desce a íris e franze (pálpebras descem).

Animações (41): sempre ativas: Piscar, Respirar, Orelhas vivas, Focinho farejando, Pelos balancando, Olhar em volta.
Por estado: Parado - cauda — `standing`; Andando — `walking`; Correndo — `running`; Agachado - espreitando — `sneaking`; Agachado andando — `sneak_walk`; Pulando — `jumping`; Caindo — `falling`; Nadando — `swimming`; Voando (elytra) — `flying`; Voo criativo — `creative_flying`; Dormindo — `sleeping`; Montado — `riding`; Morrendo — `dying`; Machucado — `hurt`; Pegando fogo — `on_fire`; Congelando — `freezing`; Rastejando — `crawling`; Na escada — `on_ladder`; Subindo escada — `climbing_on_ladder`; No inventario — `in_gui`; Mirando arco (esquerda) — `bow_left`; Luneta (esquerda) — `spyglass_left`; Bloqueando (esquerda) — `blocking_left`; Atacando (esquerda) — `punch_left`; Mirando arco (direita) — `bow_right`; Luneta (direita) — `spyglass_right`; Bloqueando (direita) — `blocking_right`; Atacando (direita) — `punch_right`; Vida — `health`; Virando a cabeca — `head_rotation_yaw`; Olhando cima/baixo — `head_rotation_pitch`; Com capacete — `armor_head`; Com peitoral — `armor_body`; Com calca — `armor_legs`; Com cabeca de mob — `wearing_skull`.

## v16.20 (correções de exportação e flicker)

- `modelo/skin_v16.20.bbmodel`: **modelo atual** (v16.19 + correções abaixo; textura igual à v16.19).
- `tools/v16_20_correcoes.py`: script da correção.

1. **Erro "Camada de Skin não suporta poses e gestos personalizados"**: o `cpm_data` do projeto agora
   traz a configuração de codificação de animação com as 6 camadas livres (chapéu, jaqueta, mangas,
   pernas da calça), igual ao modelo Plantifox. Pode ser mudado no CPM em Animação → Camadas de Skin.
2. **Flicker**: 95 planos finos (tufos, tufos das orelhas, bochechas) tinham as DUAS faces opostas
   texturizadas. Agora cada um tem só a face de fora (north; nos `ear_*_tufts_behind` a south);
   a outra ficou com UV `[0,0,0,0]` e textura nula, que é como o exportador do CPM remove uma face.
   Tamanho, posição, rotação, UV e textura da face que ficou não mudaram.
3. `fur_chest_7` era uma cópia exata de `fur_chest_6` no mesmo lugar (faces coincidentes) e foi removida.

Grupos, pivôs, animações e textura: idênticos à v16.19 (conferido).

## v16.19 (correção dos olhos)

- `modelo/skin_v16.19_animado.bbmodel`: **modelo atual** (sua v16.18 + correções abaixo).
- `modelo/skin_v16.18_usuario.bbmodel`: a v16.18 exatamente como você enviou.
- `tools/v16_19_animacoes.py`: gera tudo. `previews/v16_19_piscar.gif`: o piscar novo.

Correções:
- **Olho fechando de verdade**: 2 pálpebras novas por olho no grupo `palpebras`:
  `palp_sup_R/L` → `palpebra_sup_R/L` (de cima, cor do pelo com a linha de cílios cinza curva) e
  `palp_inf_R/L` → `palpebra_inf_R/L` (de baixo). Ficam escondidas dentro da cabeça com o olho aberto
  (o visual parado é idêntico, conferido pixel a pixel) e deslizam por cima do olho para fechar.
  Pivô da de cima na borda de cima, da de baixo na borda de baixo. O olho não é mais achatado.
  Semicerrar usa só a de cima; a de baixo sobe apenas quando o olho fecha quase todo.
  A faixa cinza (`palp_R/L`) só acompanha um pouco.
- **Sem boca**: removidas "Falando", "Comendo (esquerda/direita)" e todo movimento de mandíbula
  (em Feliz, Bravo, Piscadela). "Bocejar" virou **"Sonolento"** (olhos pesando, orelhas relaxando,
  uma piscada para acordar). O osso `mandibula` foi retirado (o `snout_bottom` voltou ao `focinho`, sem mudança).
- "Feliz" agora fecha os olhos inteiros (sorriso de olhos fechados).
- As outras animações continuam iguais (54 no total).

## v16.18 (animações)

- `modelo/skin_v16.18_animado.bbmodel`: **modelo atual** = sua v16.17 + 57 animações CPM + íris brilhando.
- `modelo/Emezomm-CPM_v16_18_128.png`: textura.
- `modelo/skin_v16.17_usuario.bbmodel`: a v16.17 exatamente como você enviou.
- `tools/v16_18_animacoes.py`: gera tudo (cada animação é descrita por curvas, fácil de ajustar).
- `tools/preview_anim.py` e `previews/v16_18_animacoes.gif`: prévias.

Nada do modelo foi movido. Para animar partes isoladas foram criados ossos "embrulho" com rotação 0
(não mudam nada na posição): `olho_R/L`, `iris_R/L` (em `olhos`), `palp_R/L` (em `palpebras`),
`nariz`, `mandibula` (em `focinho`), `orelha_R_mov`, `orelha_L_mov` (em `orelhas`).
A íris (`eye_R_iris`, `eye_L_iris`) agora tem **CPM Glow** (brilha no escuro) e as laterais ficaram no mesmo branco 247 da frente.

Todas as animações são **aditivas**: a animação padrão do Minecraft (braços, pernas, corpo, cabeça) continua igual.

### Sempre ativas (global)
- Piscar (6.0s)
- Respirar (3.6s)
- Orelhas vivas (7.0s)
- Focinho farejando (5.0s)
- Pelos balancando (4.0s)
- Olhar em volta (9.0s)

### Automáticas por estado do jogador (poses do CPM)
- Parado - cauda — `standing`
- Andando — `walking`
- Correndo — `running`
- Agachado - espreitando — `sneaking`
- Agachado andando — `sneak_walk`
- Pulando — `jumping`
- Caindo — `falling`
- Nadando — `swimming`
- Voando (elytra) — `flying`
- Voo criativo — `creative_flying`
- Dormindo — `sleeping`
- Montado — `riding`
- Morrendo — `dying`
- Machucado — `hurt`
- Pegando fogo — `on_fire`
- Congelando — `freezing`
- Comendo (esquerda) — `eating_left`
- Comendo (direita) — `eating_right`
- Rastejando — `crawling`
- Na escada — `on_ladder`
- Subindo escada — `climbing_on_ladder`
- No inventario — `in_gui`
- Mirando arco (esquerda) — `bow_left`
- Luneta (esquerda) — `spyglass_left`
- Bloqueando (esquerda) — `blocking_left`
- Atacando (esquerda) — `punch_left`
- Mirando arco (direita) — `bow_right`
- Luneta (direita) — `spyglass_right`
- Bloqueando (direita) — `blocking_right`
- Atacando (direita) — `punch_right`
- Falando — `speaking`
- Vida — `health`
- Virando a cabeca — `head_rotation_yaw`
- Olhando cima/baixo — `head_rotation_pitch`
- Com capacete — `armor_head`
- Com peitoral — `armor_body`
- Com calca — `armor_legs`
- Com cabeca de mob — `wearing_skull`

### Gestos (roda de gestos do CPM)
- Abanar a cauda (repete)
- Feliz (repete)
- Bravo (repete)
- Triste (repete)
- Surpreso (uma vez)
- Farejar (uma vez)
- Bocejar (uma vez)
- Piscadela (uma vez)
- Sacudir o pelo (uma vez)

### Alternáveis (layers do CPM)
- Orelhas para tras
- Orelhas atentas
- Cauda enrolada
- Cauda erguida

## v16.17

- `modelo/skin_v16.17.bbmodel`: **modelo atual** = sua v16.16 + sobrancelha nova + pálpebras + transição cauda/corpo.
- `modelo/Emezomm-CPM_v16_17_128.png`: textura (128×128, só pixels livres foram usados).
- `modelo/skin_v16.16_cauda_usuario.bbmodel`: a v16.16 exatamente como você enviou.
- `tools/v16_17_palpebra_cauda.py`: script da mudança.

O que mudou (nada foi reposicionado):
- `sobrancelha_R/L`: só a textura — cinza da skin (108 / 94), em arco.
- `palpebras` (grupo novo em `head`, depois de `sobrancelhas`): `palpebra_R/L`, linha cinza (97 / 60) na borda
  de cima de cada olho, com um vão preto até a sobrancelha. Pivô na linha da pálpebra (bom para piscar).
- `tail_base`: textura própria — começa com a cor exata das costas onde sai do corpo e passa em degraus
  (com pontilhado) para o pelo da cauda.
- `fur_cauda_raiz` (grupo novo em `body`): 8 mechas em volta da raiz da cauda; raiz na cor das costas, pontas
  no pelo da cauda, cobrindo a emenda.

## v16.15 (cauda)

- `modelo/skin_v16.15_cauda.bbmodel`: **modelo atual** = v16.14 + cauda de raposa. Nada do que já existia foi alterado.
- `modelo/Emezomm-CPM_v16_15_128_cauda.png`: textura (continua 128×128, a cauda só usa pixels livres).
- `tools/v16_15_cauda.py`: gera a cauda (`python3 tools/v16_15_cauda.py modelo/skin_v16.14_tufos.bbmodel modelo/skin_v16.15_cauda.bbmodel`).

Cauda (ossos em cadeia, pivô de cada um na articulação):

```
body
└─ cauda          pivô (0, 13.2, 1.6)  rot X 42  (sai da lombar e desce)
   └─ cauda_1     pivô z 4.1           rot X -9  (vai curvando para cima)
      └─ cauda_2  pivô z 7.6           rot X -9  (parte mais grossa)
         └─ cauda_3     pivô z 11.6    rot X -8  (transição preto -> branco)
            └─ cauda_ponta  z 15.1     rot X -7  (ponta branca)
```

Cada osso tem o segmento (`tail_*`), um cuboide girado 45° (`tail_*_bevel`, deixa o corte octogonal)
e as camadas de pelo (`fur_tail_*`) em cima, embaixo, nos lados e nas diagonais, sempre caindo para a ponta.
A cor vem de um só "mapa" da cauda: preto da skin → cinza quente (109,104,100) → bege (188,179,172) → branco,
com borda em zigue-zague; os pelos pegam a cor do ponto da cauda de onde saem.

## v16.14

- `modelo/skin_v16.14_tufos.bbmodel`: **modelo atual** (seus ajustes da v16.14 + sobrancelha retexturizada + outliner organizado).
- `modelo/Emezomm-CPM_v16_14_128_tufos.png`: textura da v16.14 (já embutida no .bbmodel).
- `modelo/skin_v16.14_tufos_original_usuario.bbmodel`: a v16.14 exatamente como você enviou.
- `tools/v16_14_sobrancelha_organizar.py`: script que faz só isso, sem mover nada.

Organização da cabeça:

```
head
├─ head, hat
├─ olhos          eye_R, eye_R_iris, eye_L, eye_L_iris
├─ sobrancelhas   sobrancelha_R, sobrancelha_L
├─ focinho        snout_side_R/L, snout_top, snout_bottom, nose
├─ bochechas      cheek_R, cheek_L
├─ orelhas        orelha_L, orelha_R
└─ fur_head       fur_top, fur_back, fur_cheek_R/L
body
└─ fur_chest      fur_chest_rows, fur_chest_edge_R/L
```

## Histórico (v16.11)

- `modelo/skin_v16.11_original.bbmodel`: modelo original (sem alterações).
- `modelo/skin_v16.11_tufos.bbmodel`: modelo com tufos de pelo 2D em camadas (abra no Blockbench, formato CPM).
- `modelo/Emezomm-CPM_v16_11_128_tufos.png`: textura 128×128 com os sprites dos tufos (já embutida no .bbmodel).
- `previews/`: renders de frente, lado, costas e 3/4.
- `tools/build.py`: gera o modelo com tufos a partir do original (`python3 tools/build.py <original> <saida>`).
- `tools/render.py`, `tools/zoom.py`: renderizador simples para prévias.

## Grupos e pivôs

```
head
└─ fur_head            pivô (0, 24, 0)      = pivô da cabeça
   ├─ fur_top          pivô (0, 32, -0.5)   topo da cabeça, 4 fileiras caindo para trás
   ├─ fur_back         pivô (0, 29, 4)      nuca, 4 fileiras caindo para baixo
   ├─ fur_side_R / _L  pivô (±4, 29.8, 1.2) laterais, 4 mechas cada
   └─ fur_cheek_R / _L pivô (±4, 26, -2.2)  bochechas brancas, 3 mechas cada
body
└─ fur_chest           pivô (0, 24, -2.15)  = frente do peito
   ├─ fur_chest_rows   pivô (0, 24.3, -2.15) 6 fileiras brancas descendo
   └─ fur_chest_edge_R / _L                 2 mechas nas bordas
```

Cada mecha tem o pivô na **raiz** (onde encosta no corpo), então girar a mecha ou o grupo faz o pelo balançar a partir da base.

## Textura

Cada mecha tem a sua própria textura, pintada automaticamente a partir da skin:

- a **raiz** de cada mecha usa exatamente a cor da skin no ponto onde ela sai do corpo,
- cada pixel da mecha pega a cor da skin logo abaixo dele (então o branco do peito/focinho continua branco,
  o preto continua preto, e as bordas fazem a transição sozinhas),
- o desenho em pixel art (`ART` em `tools/build.py`: `M` = cor da skin, `S` = um pouco mais escuro,
  `L` = um pouco mais claro) só dá forma e sombra, com a sombra entrando aos poucos a partir da raiz,
- toda cor final é "encaixada" na paleta que a skin já usa, então nenhuma cor nova é inventada.

Os sprites ficam em áreas da textura que nenhuma face usava.
