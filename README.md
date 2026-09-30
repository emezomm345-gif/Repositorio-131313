# Skin CPM – tufos de pelo

## Versão atual: v16.23 (olhos consertados, cauda deitada, botão das orelhas)

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
