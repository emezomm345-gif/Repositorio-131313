# Skin CPM – tufos de pelo

## Versão atual: v16.17

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
