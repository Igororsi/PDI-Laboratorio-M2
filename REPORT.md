# REPORT.md — Laboratórios M2.1 e M2.2

## Contexto e alvo
O alvo é a região clara dos objetos sobre um fundo relativamente mais escuro. As duas cenas de estudo foram criadas programaticamente para controlar as condições: `cena1_favoravel.png` possui fundo uniforme e objetos separados; `cena2_dificil.png` tem iluminação variável, textura, pontos claros pequenos e objetos próximos. **São imagens experimentais geradas por código, não fotografias reais.** Como o enunciado solicita imagens reais, substitua-as por duas fotografias próprias/licenciadas antes de entregar se o professor interpretar “imagens reais” como fotografias. Os comandos e testes continuam válidos para imagens substitutas.

## M2.1 — Máscara binária e segmentação

### Métodos e parâmetros
- **Fixed:** conversão para cinza e limiar `T=120`; pixels abaixo de 120 viram 0, pixels maiores ou iguais a 120 viram 255.
- **Otsu:** conversão para cinza e limiar global automático (`THRESH_BINARY + THRESH_OTSU`).
- Não foi aplicada inversão. As máscaras são PNG de canal único, preservam dimensões e contêm apenas `(0, 255)`.

### Resultados quantitativos
A proporção de primeiro plano é a fração de pixels brancos, não uma medida de acurácia.

| Imagem/configuração | Pixels brancos | Total | Proporção |
|---|---:|---:|---:|
| `cena1_fixed.png` | 29279 | 172800 | 16.94% |
| `cena1_otsu.png` | 29279 | 172800 | 16.94% |
| `cena2_fixed.png` | 24727 | 172800 | 14.31% |
| `cena2_otsu.png` | 24551 | 172800 | 14.21% |

### Discussão comparativa
Na cena favorável, o fundo é homogêneo e o limiar fixo é simples de reproduzir. Na cena difícil, a iluminação não uniforme e os pontos claros de fundo podem entrar na máscara; sombras ou regiões com intensidade próxima à do fundo podem ser omitidas. Otsu escolhe um limiar global a partir do histograma, mas não resolve necessariamente variação espacial de iluminação. O parâmetro mais sensível no método fixo é `threshold`: um valor maior tende a reduzir a área branca e pode remover detalhes. A configuração de trabalho proposta para M2.2 é Otsu, por não exigir ajuste manual do limiar por imagem; a inspeção visual continua necessária.

### Figuras
- `results/cena1_comparison.png` e `results/cena2_comparison.png`: original, máscara fixa e máscara Otsu lado a lado.
- `results/cena1_fixed_overlay.png`, `results/cena1_otsu_overlay.png`, `results/cena2_fixed_overlay.png`, `results/cena2_otsu_overlay.png`: sobreposições com o primeiro plano destacado em vermelho.
- As máscaras individuais ficam em `images/output/`.

### Respostas obrigatórias
(a) O limiar fixo funciona melhor quando objeto e fundo têm intensidades bem separadas e iluminação estável; falha com sombras, reflexos, ruído ou fundo parecido.  
(b) O parâmetro mais sensível é o limiar `T`; o método Otsu depende da distribuição do histograma e pode falhar se os níveis de objeto e fundo se misturam.  
(c) Ruído pode gerar componentes extras; fragmentação de um objeto pode contá-lo várias vezes; contato entre objetos pode fundi-los.

## M2.2 — Componentes conexos e sequência morfológica

### Procedimento
A entrada é a máscara Otsu do M2.1; branco (255) é primeiro plano e preto (0) é fundo. A contagem inicial foi feita com conectividade 4 e 8 na mesma máscara. A tabela final usa conectividade 8.
1. **Abertura:** elemento elíptico 3×3, uma iteração, para tentar remover pequenos pontos isolados.
2. **Fechamento:** elemento elíptico 5×5, uma iteração, para tentar fechar pequenos furos e lacunas.

Os estágios estão em `results/*_stage_opening.png` e `results/*_stage_closing.png`. Os CSVs excluem o fundo e informam área, caixa delimitadora, centroide e `kept`, usando o filtro `area >= 20 pixels`. As saídas `_labels.png` e `_boxes.png` permitem visualizar rótulos e caixas.

### Contagens e áreas observadas

#### cena1
- Componentes iniciais, conectividade 4: **7**
- Componentes iniciais, conectividade 8: **7**
- Componentes finais brutos, conectividade 8: **7**
- Componentes finais mantidos (área ≥ 20): **7**
- Área inicial de primeiro plano: **29279 pixels**
- Área final de primeiro plano: **29279 pixels**

#### cena2
- Componentes iniciais, conectividade 4: **129**
- Componentes iniciais, conectividade 8: **128**
- Componentes finais brutos, conectividade 8: **38**
- Componentes finais mantidos (área ≥ 20): **6**
- Área inicial de primeiro plano: **24551 pixels**
- Área final de primeiro plano: **24129 pixels**

### Interpretação e limitações
Conectividade 4 considera vizinhos horizontais e verticais; conectividade 8 inclui também os diagonais. Duas regiões que se tocam apenas diagonalmente podem ser dois componentes em 4 e um em 8. A abertura remove ruído, mas pode apagar detalhes estreitos ou objetos pequenos; o fechamento pode unir objetos próximos e mudar contornos. O filtro por área elimina regiões pequenas, mas pode remover objetos legítimos. Componentes detectados não equivalem necessariamente a objetos físicos: contato, sobreposição, fragmentação e erros de segmentação alteram a contagem.

### Respostas obrigatórias
A sequência pode ajudar quando remove ruído pequeno e fecha lacunas menores que o elemento estruturante. Pode prejudicar quando apaga detalhes pequenos ou funde objetos próximos. A contagem aproxima-se da interpretação humana quando a máscara separa cada objeto e não há contato ou sobreposição.

## Testes, guardas e reprodutibilidade
A suíte cobre pixels abaixo/no/acima do limiar, máscara binária, dimensões, limiar inválido, método desconhecido, conectividade 4 versus 8, máscara vazia, objeto na borda, abertura para ruído e fechamento para furo. Os comandos estão no `README.md`. Sucesso retorna código 0 e erros tratados retornam código 2.
