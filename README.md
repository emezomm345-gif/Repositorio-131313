# Skin CPM – tufos de pelo

- `modelo/skin_v16.11_original.bbmodel`: modelo original (sem alterações).
- `modelo/skin_v16.11_tufos.bbmodel`: modelo com tufos de pelo 2D em camadas (abra no Blockbench, formato CPM).
- `modelo/skin_v16.11_tufos_texture.png`: textura 128×128 com os sprites dos tufos.
- `previews/`: renders de frente, lado, costas e 3/4.
- `tools/build.py`: gera o modelo com tufos a partir do original (`python3 tools/build.py <original> <saida>`).
- `tools/render.py`, `tools/zoom.py`: renderizador simples para prévias.

Grupos novos: `fur_head_top`, `fur_head_back`, `fur_head_sides` (dentro de `head`) e `fur_chest` (dentro de `body`).
Os sprites usam só a paleta da skin e ficam em áreas da textura que nenhuma face usava (y 108–121 e x 0–63 / y 16–29).
