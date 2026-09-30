# Skin CPM – tufos de pelo

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
