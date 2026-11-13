# Proposta 1 — resultados das cinco imagens e oito classificadores

**Data de consolidação:** 13/11/2026. **Fonte:** [`Tabelas_Figuras_e_Reproducao.zip` no Drive](https://drive.google.com/file/d/1dqCY48klV2nHZnW7EghkM_bo8-g7kLUU/view), especialmente `relatorio/areas_previstas_cinco_imagens.csv` e `relatorio/validacao_area1_comparacao.csv`. [Dados numéricos consolidados](./RESULTADOS_CONSOLIDADOS_CINCO_AREAS_8_MODELOS_2026-11-13.csv).

**Natureza:** tabelas transcritas de artefatos de uma execução prévia com imagens reais; a consolidação não constitui reexecução do Colab. Classes denominadas **árvores e gramíneas previstas**, não comprovação de cobertura real. Hectares = pixels previstos × 0,25 m² / 10.000, sobre máscara válida. A classificação é binária inclusive para áreas construídas e outros alvos, logo NÃO é inventário de arborização. Predições das cinco imagens têm áreas geográficas parcialmente sobrepostas entre Area1/Sagrada, de modo que **não se deve somar áreas como extensão territorial única**.

## Area1 — Caxias do Sul

- Quadrantes processados: **812**; segmentos com predição: **131.776**; área da máscara classificada: **1.174,02 ha**.
- [Pacote dos oito mapas GeoTIFF](https://drive.google.com/file/d/1DETrhSCnIIcUG92LHz1sFUkVNstD6fte/view).

| Classificador | Seg. árvores | Seg. gramíneas | Árvores previstas (ha) | Gramíneas previstas (ha) | Pixels árvores (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 124.562 | 7.214 | 1.106,66 | 67,36 | 94,3% |
| SVM RBF | 123.368 | 8.408 | 1.096,57 | 77,45 | 93,4% |
| Regressão logística | 54.520 | 77.256 | 457,39 | 716,63 | 39,0% |
| Extra Trees | 102.833 | 28.943 | 937,56 | 236,47 | 79,9% |
| KNN | 110.545 | 21.231 | 997,85 | 176,18 | 85,0% |
| HistGradientBoosting | 92.109 | 39.667 | 808,18 | 365,84 | 68,8% |
| Gaussian Naive Bayes | 118.794 | 12.982 | 1.067,71 | 106,31 | 90,9% |
| Dummy | 131.776 | 0 | 1.174,02 | 0,00 | 100,0% |

## Sagrada Família — Caxias do Sul

- Quadrantes processados: **1.681**; segmentos com predição: **318.830**; área da máscara classificada: **2.678,75 ha**.
- [Pacote dos oito mapas GeoTIFF](https://drive.google.com/file/d/18GwhiVAC_LT1rxZgmICTvz2VLjABFKQQ/view).

| Classificador | Seg. árvores | Seg. gramíneas | Árvores previstas (ha) | Gramíneas previstas (ha) | Pixels árvores (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 295.051 | 23.779 | 2.464,00 | 214,75 | 92,0% |
| SVM RBF | 289.994 | 28.836 | 2.423,81 | 254,94 | 90,5% |
| Regressão logística | 161.057 | 157.773 | 1.228,28 | 1.450,47 | 45,9% |
| Extra Trees | 248.324 | 70.506 | 2.116,94 | 561,80 | 79,0% |
| KNN | 263.188 | 55.642 | 2.214,17 | 464,58 | 82,7% |
| HistGradientBoosting | 235.942 | 82.888 | 1.923,17 | 755,57 | 71,8% |
| Gaussian Naive Bayes | 260.716 | 58.114 | 2.228,25 | 450,50 | 83,2% |
| Dummy | 318.830 | 0 | 2.678,75 | 0,00 | 100,0% |

## Centro — Novo Hamburgo

- Quadrantes processados: **1.764**; segmentos com predição: **317.756**; área da máscara classificada: **2.667,18 ha**.
- [Pacote dos oito mapas GeoTIFF](https://drive.google.com/file/d/1co5EApBv9zHWsCjdF7W0s-nC5jZ1QcqW/view).

| Classificador | Seg. árvores | Seg. gramíneas | Árvores previstas (ha) | Gramíneas previstas (ha) | Pixels árvores (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 307.368 | 10.388 | 2.606,92 | 60,27 | 97,7% |
| SVM RBF | 317.756 | 0 | 2.667,18 | 0,00 | 100,0% |
| Regressão logística | 0 | 317.756 | 0,00 | 2.667,18 | 0,0% |
| Extra Trees | 302.228 | 15.528 | 2.593,44 | 73,74 | 97,2% |
| KNN | 0 | 317.756 | 0,00 | 2.667,18 | 0,0% |
| HistGradientBoosting | 298.987 | 18.769 | 2.568,76 | 98,42 | 96,3% |
| Gaussian Naive Bayes | 317.756 | 0 | 2.667,18 | 0,00 | 100,0% |
| Dummy | 317.756 | 0 | 2.667,18 | 0,00 | 100,0% |

## Lomba Grande — Novo Hamburgo

- Quadrantes processados: **4.485**; segmentos com predição: **614.030**; área da máscara classificada: **4.612,19 ha**.
- [Pacote dos oito mapas GeoTIFF](https://drive.google.com/file/d/1ePRzJQColP1dvqJJv9P3LaSVo1LxE30w/view).

| Classificador | Seg. árvores | Seg. gramíneas | Árvores previstas (ha) | Gramíneas previstas (ha) | Pixels árvores (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 472.881 | 141.149 | 3.497,19 | 1.115,00 | 75,8% |
| SVM RBF | 425.151 | 188.879 | 3.151,13 | 1.461,07 | 68,3% |
| Regressão logística | 317.655 | 296.375 | 2.365,70 | 2.246,49 | 51,3% |
| Extra Trees | 304.657 | 309.373 | 2.403,19 | 2.209,00 | 52,1% |
| KNN | 373.875 | 240.155 | 2.776,92 | 1.835,27 | 60,2% |
| HistGradientBoosting | 445.729 | 168.301 | 3.308,96 | 1.303,23 | 71,7% |
| Gaussian Naive Bayes | 213.879 | 400.151 | 1.587,53 | 3.024,66 | 34,4% |
| Dummy | 614.030 | 0 | 4.612,19 | 0,00 | 100,0% |

## Cristo Rei — São Leopoldo

- Quadrantes processados: **1.722**; segmentos com predição: **335.628**; área da máscara classificada: **2.664,41 ha**.
- [Pacote dos oito mapas GeoTIFF](https://drive.google.com/file/d/1ih1_ti5svuc-ZIq-zOiuEa1ymYFjf239/view).

| Classificador | Seg. árvores | Seg. gramíneas | Árvores previstas (ha) | Gramíneas previstas (ha) | Pixels árvores (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 313.056 | 22.572 | 2.458,37 | 206,04 | 92,3% |
| SVM RBF | 307.263 | 28.365 | 2.414,78 | 249,63 | 90,6% |
| Regressão logística | 202.965 | 132.663 | 1.480,80 | 1.183,61 | 55,6% |
| Extra Trees | 266.191 | 69.437 | 2.135,16 | 529,25 | 80,1% |
| KNN | 279.068 | 56.560 | 2.197,07 | 467,34 | 82,5% |
| HistGradientBoosting | 270.225 | 65.403 | 2.077,61 | 586,80 | 78,0% |
| Gaussian Naive Bayes | 242.730 | 92.898 | 1.974,53 | 689,88 | 74,1% |
| Dummy | 335.628 | 0 | 2.664,41 | 0,00 | 100,0% |

## F1-macro — somente validação espacial interna da Area1

Estas são médias de cinco divisões espaciais por escala, com protocolo de validação aninhada e embargo de 25 m registrado nos artefatos. **Não são métricas de validação externa das outras quatro áreas.**

| Classificador | 250 m | 500 m |
|---|---:|---:|
| Random Forest | 0,7801 | 0,8057 |
| SVM RBF | 0,8586 | 0,8689 |
| Regressão logística | 0,8376 | 0,8567 |
| Extra Trees | 0,7804 | 0,7899 |
| KNN | 0,8473 | 0,8558 |
| HistGradientBoosting | 0,7687 | 0,7932 |
| Gaussian Naive Bayes | 0,7250 | 0,7287 |
| Dummy | 0,3051 | 0,2853 |

## Interpretação e pendências

- **Centro de Novo Hamburgo:** SVM RBF, Gaussian Naive Bayes e Dummy marcaram 100% dos pixels válidos como árvores; Regressão Logística e KNN marcaram 100% como gramíneas. A divergência é compatível com mudança acentuada de domínio e recomenda não usar estas saídas como área real de vegetação.
- **Sagrada Família:** contém a Area1 e seus 510 pontos originais. Os 200 pontos externos cegos foram selecionados fora da Area1 + buffer 25 m, conforme pacote de execução, mas precisam receber rótulos independentes para validação.
- **800 amostras cegas:** quatro conjuntos de 200; a rotulação humana independente continua pendente. **F1-macro externo indisponível**. Não inferir acurácia de comparação entre mapas ou distribuição das previsões.
- **NIR:** registro do produto Jilin-1 apoia ordem B/G/R/NIR, vermelho banda 3 e NIR banda 4. O índice utilizou valores digitais e não reflectância calibrada; não confundir identificação de canal com harmonização radiométrica.
- **Rastreabilidade:** a auditoria complementar de 13/11/2026 apontou tamanho diferente do arquivo multiespectral original no Drive em relação ao manifesto de treinamento; recomenda checagem por SHA256 antes de fechar a dissertação.

**Não foi modificado** código científico, dados brutos, resultados históricos ou branch `main` nesta consolidação.
