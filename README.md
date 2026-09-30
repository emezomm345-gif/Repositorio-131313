# Skin CPM – tufos de pelo

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
  branco continua branco: focinho, peito, dentro das orelhas, ponta da cauda). Na cabeça **só os óculos** em 3D
  (armação de bronze, lentes laranja, ponte e a alça cinza com fivela em volta da cabeça) — sem gorro e sem
  bandana. Colete de couro com o **peito do próprio Emezomm** no decote (onde a skin pintava a bandana verde:
  `--pelo`), mangas cinza, luvas pretas, cinto verde com fivela, calça marrom e botas, com a segunda camada.
  Tufos do peito escondidos pelo colete. Prévia: `previews/variante_CACADORES.png`.
  Comando: `python3 tools/variante.py modelo/skin_v16.28.bbmodel modelo/variantes/CACADORES/skin_CACADORES_64x64_original.png modelo/variantes/CACADORES/skin_v16.28_CACADORES.bbmodel --fur verde --acessorios cacadores --hide fur_chest --pelo body.north:0-4,body.south:0-1,body.up`

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
