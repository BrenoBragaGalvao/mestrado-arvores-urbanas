# V3 — Alturas logarítmicas e estimativas Meta/WRI, nos 257 pontos

## Objetivo e advertência

Comparar a **altura calculada pela fórmula logarítmica** com a **altura
modelada pelo mapa Meta/WRI CHMv2** em todos os 257 pontos originais
de árvores da Area1, Caxias do Sul. O mapa não representa medição de
campo e a área usada é de um **superpixel**, não de uma copa individual
delimitada. Portanto não se reivindica estimativa validada de altura real.

## Fórmulas ajustadas aos 257 pontos

- Pixel Meta: H = 1.02061062 + 0.43611553 × ln(1+A)
- Meta raio 5 m: H = 4.83406389 + 0.26716928 × ln(1+A)

A é a área do superpixel em m². **As fórmulas acima foram ajustadas com
todos os 257 pontos, apenas para ilustrar uma previsão final por ponto.**
Para estimar desempenho sem reutilizar os mesmos alvos, apresentar as
**previsões fora do treinamento (OOF)** dos 5 folds espaciais (250/500 m
e embargo de 25 m), conforme abaixo.

## Validação espacial externa (predições OOF)

| Referência Meta | Blocos | MAE log vs. Meta | RMSE log vs. Meta | MAE constante | Até 2 m | Até 5 m |
|---|---:|---:|---:|---:|---:|---:|
| Pixel exato | 250 m | 4,58 m | 6,02 m | 4,58 m | 16,34% | 75,10% |
| Pixel exato | 500 m | 4,50 m | 5,93 m | 4,45 m | 16,34% | 76,26% |
| Máximo raio 5 m | 250 m | 4,81 m | 6,12 m | 4,78 m | 24,12% | 57,20% |
| Máximo raio 5 m | 500 m | 4,73 m | 6,06 m | 4,67 m | 24,90% | 57,98% |

**Interpretação:** em ambos os alvos e ambas as escalas, a logarítmica
não superou o controle constante em MAE. O objetivo aqui é mostrar
explicitamente a altura prevista de cada ponto e sua divergência em
relação ao mapa Meta, sem declarar validade como altura real.

## Primeiros 12 pontos (IDs fixos, sem escolha pelos resultados)

| ID | Área (m²) | Meta pixel (m) | Log pixel ajuste total (m) | Log pixel OOF 250 m (m) | Meta raio 5 m (m) | Log raio 5 m ajuste total (m) | Log raio OOF 250 m (m) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 251,50 | 16,00 | 3,43 | 3,02 | 17,00 | 6,31 | 5,97 |
| 1 | 261,50 | 0,00 | 3,45 | 3,02 | 6,00 | 6,32 | 5,97 |
| 2 | 68,75 | 10,00 | 2,87 | 3,40 | 13,00 | 5,97 | 6,50 |
| 3 | 369,25 | 19,00 | 3,60 | 3,04 | 20,00 | 6,41 | 5,97 |
| 4 | 130,50 | 0,00 | 3,15 | 3,86 | 2,00 | 6,14 | 6,87 |
| 5 | 35,00 | 0,00 | 2,58 | 2,92 | 2,00 | 5,79 | 6,11 |
| 6 | 156,00 | 0,00 | 3,23 | 3,98 | 0,00 | 6,18 | 6,98 |
| 7 | 155,25 | 0,00 | 3,22 | 3,98 | 0,00 | 6,18 | 6,97 |
| 8 | 203,50 | 3,00 | 3,34 | 4,17 | 6,00 | 6,26 | 7,13 |
| 9 | 109,50 | 6,00 | 3,07 | 3,73 | 9,00 | 6,09 | 6,77 |
| 10 | 194,25 | 0,00 | 3,32 | 4,14 | 3,00 | 6,24 | 7,11 |
| 11 | 63,50 | 5,00 | 2,84 | 3,34 | 6,00 | 5,95 | 6,45 |

## Arquivos e rastreabilidade

- CSV com **257 linhas, uma por árvore**, incluindo localização, área,
  altura da Meta, altura logarítmica calculada com todos os pontos,
  previsão fora da amostra (250 e 500 m) e diferenças: 
  [v3_logaritmica_257_alturas_vs_meta.csv](v3_logaritmica_257_alturas_vs_meta.csv).
- [Métricas OOF](v3_logaritmica_resumo_validacao.csv) e
  [resumo JSON](v3_logaritmica_resumo.json).
- [Gráfico de comparação no pixel](v3_logaritmica_meta_pixel.png) e
  [gráfico de comparação em 5 m](v3_logaritmica_meta_raio5.png).
- Script: [v3_comparar_logaritmica_meta.py](../../experimentos/v3_comparar_logaritmica_meta.py).

**Limitações:** o modelo é calibrado contra outro modelo, não
contra alturas reais. Valor zero no pixel não prova ausência de
árvore; máximo em 5 m pode corresponder a outro indivíduo.
Os coeficientes originais do notebook inicial não foram alterados.
