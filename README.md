# Processamento de Imagens — Laboratórios M2.1 e M2.2

Projeto único em Python/OpenCV com as operações `segment` e `analyze`.

## Requisitos
- Python 3.10 ou superior
- OpenCV e NumPy (`pip install -r requirements.txt`)

## Executar localmente
Na pasta do projeto:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

O módulo é chamado por `python pdi_lab.py`. Esta forma é portátil e equivale à interface `pdi_lab` descrita no enunciado.

## M2.1 — Segmentação

Limiar fixo em cinza (T=120):
```bash
python pdi_lab.py --input images/input/cena1_favoravel.png --output images/output/cena1_fixed.png --operation segment --method fixed --threshold 120
```

Otsu na mesma imagem:
```bash
python pdi_lab.py --input images/input/cena1_favoravel.png --output images/output/cena1_otsu.png --operation segment --method otsu
```

Repetir as duas configurações na segunda imagem:
```bash
python pdi_lab.py --input images/input/cena2_dificil.png --output images/output/cena2_fixed.png --operation segment --method fixed --threshold 120
python pdi_lab.py --input images/input/cena2_dificil.png --output images/output/cena2_otsu.png --operation segment --method otsu
```

Métodos aceitos: `fixed`, `otsu`, `adaptive`, `hsv`. Parâmetros adicionais: `--block-size` (ímpar >=3), `--constant`, `--hsv-low H S V`, `--hsv-high H S V` e `--invert`. OpenCV usa HSV com H de 0 a 179 e S/V de 0 a 255. A faixa HSV padrão seleciona pixels com valor alto e baixa saturação; ajuste conforme a classe escolhida.

## M2.2 — Componentes conexos e morfologia

A entrada de `analyze` é uma máscara binária gerada pelo próprio projeto; a saída é um prefixo:
```bash
python pdi_lab.py --input images/output/cena1_otsu.png --output results/cena1 --operation analyze --connectivity 8 --min-area 20
python pdi_lab.py --input images/output/cena2_otsu.png --output results/cena2 --operation analyze --connectivity 8 --min-area 20
```

Arquivos gerados por prefixo:
- `_initial.csv`, `_final.csv`: componentes com área, caixa, centroide e `kept`.
- `_stage_opening.png`: após abertura.
- `_stage_closing.png`: após fechamento (máscara final).
- `_labels.png`: visualização colorida dos rótulos.
- `_boxes.png`: caixas delimitadoras dos componentes mantidos.
- `_summary.json`: conectividade, contagens, áreas, filtro e parâmetros.

Morfologia padrão: abertura com elemento elíptico 3×3, seguida de fechamento 5×5, uma iteração cada. A abertura busca remover pontos pequenos; o fechamento tenta preencher pequenos furos e conectar pequenas interrupções. Alterar por `--kernel-shape rect|ellipse`, `--open-kernel`, `--close-kernel` e `--iterations`.

## Testes
```bash
python -m unittest discover -s tests -v
```
Os testes incluem pixels abaixo/no/acima do limiar, diagonal para conectividade 4/8, ruído, furo, máscara vazia, borda, falha de leitura, método desconhecido, parâmetro inválido, código de saída e validação das saídas.

## Limitações
Os componentes conexos são regiões conectadas, não necessariamente objetos físicos. Contato, sobreposição e fragmentação alteram a contagem. As duas imagens incluídas são cenas de estudo geradas para controle experimental, não fotografias de campo; para a versão final da análise, podem ser substituídas por fotos próprias/licenciadas mantendo os mesmos comandos.

## Arquivos
- `REPORT.md`: mini relatório M2.1 e M2.2.
- `AI_USAGE.md`: declaração de uso de IA.
- `lab.json`: metadados do projeto.
