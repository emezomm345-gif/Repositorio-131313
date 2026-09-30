# Skin CPM – tufos de pelo

- `modelo/skin_v16.11_original.bbmodel`: modelo original (sem alterações).
- `modelo/skin_v16.11_tufos.bbmodel`: modelo com tufos de pelo 2D em camadas (abra no Blockbench, formato CPM).
- `modelo/Emezomm-CPM_v16_11_128_tufos.png`: textura 128×128 com os sprites dos tufos (já embutida no .bbmodel).
- `previews/`: renders de frente, lado, costas e 3/4.
- `tools/build.py`: gera o modelo com tufos a partir do original (`python3 tools/build.py <original> <saida>`).
- `tools/render.py`, `tools/zoom.py`: renderizador simples para prévias.

Grupos novos: `fur_head_top`, `fur_head_back`, `fur_head_sides` (dentro de `head`) e `fur_chest` (dentro de `body`).
Os sprites são pixel art simples desenhados à mão (`ART` em `tools/build.py`): 2 px por unidade (mesma densidade da skin), 3 tons chapados da paleta da skin (preto 16/24/36, branco 196/224/240), pontas em degrau e algumas falhas para simular pelo. Ficam em áreas da textura que nenhuma face usava (y 108–114).
