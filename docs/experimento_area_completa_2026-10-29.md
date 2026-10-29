# Experimento com a área completa — 29/10/2026

## Origem e escopo

Registro do notebook **`Segmentação_breno_imagem_completa(1).ipynb`** fornecido pelo autor em 29/10/2026, com dados geoespaciais da pasta `Area1` (também disponibilizados por [Google Drive](https://drive.google.com/drive/folders/1hvCcpETqIPc37aNp3oJLVFTss3nejCdf)).

O projeto tem **duas propostas**:

1. Classificação orientada a objetos de **árvores versus gramíneas**, pela combinação de NDVI, brilho HSV e bordas de Canny, com agrupamento K-Means e classificador Random Forest.
2. Identificação de objetos arbóreos próximos à infraestrutura elétrica. **O arquivo de dados recebido nesta rodada contém geometrias de postes, mas não de cabos/linhas de energia**; logo, o experimento espacial implementa proximidade a *postes*, e não a cabos energizados.

## Parâmetros do notebook recebido

| Etapa | Configuração observada |
|---|---|
| Segmentação RGB | Quickshift: `kernel_size=3`, `max_dist=5`, `ratio=0.04` |
| Características espectrais | Médias e desvios-padrão RGB + NIR por polígono |
| Agrupamento | K-Means, 6 clusters, `random_state=42`, `n_init=10` |
| Pré-seleção da vegetação | Cluster de índice **3**, dependente do ajuste do K-Means |
| Características do classificador | Média de brilho HSV, média de bordas Canny, média do NDVI |
| Classificador | Random Forest, 500 árvores, `random_state=42` |
| Divisão treino/teste | `test_size=0.2`, `random_state=42` |
| Altura estimada (exploratória) | `2.5 * area ** 0.4` (configuração C3) |
| Filtro de altura | Estimativa **maior que 7 metros** |
| Análise espacial | Vizinhança de postes a **1 m, 3 m, 5 m** |

## Resultados reportados na execução anexada

| Indicador | Resultado |
|---|---:|
| Linhas na tabela de treinamento (pares objeto–rótulo) | **458** |
| Registros de treinamento | **366** |
| Registros de teste | **92** |
| Acurácia global arredondada | **0,87** |
| Precisão / recall / F1 da classe árvore | 0,80 / 0,92 / 0,85 |
| Precisão / recall / F1 da classe gramínea | 0,94 / 0,83 / 0,88 |

Os números foram **extraídos das saídas salvas no notebook fornecido**. Não representam uma reexecução independente no ambiente deste repositório. É importante distinguir **458 registros rotulados** de 458 árvores distintas; a união espacial (`sjoin`) pode produzir múltiplos pares para o mesmo objeto.

O experimento anterior do repositório apresentava **133 registros rotulados, 27 de teste e acurácia 0,81**; mantemos esses números para comparação histórica. Não é adequado interpretar a diferença de acurácia como ganho comprovado: os conjuntos de teste são diferentes.

## Dados do lote Area1

| Arquivo | Finalidade |
|---|---|
| `AOI_RGB_NEW.tif` | Raster RGB de referência para Quickshift |
| `AOI_NEW_MULTI.tif` | Raster com quatro bandas RGB + NIR |
| `AOI_new.shp/.shx/.dbf/.prj/.cpg` | Área de interesse |
| `Arvores.gpkg` | Rótulos de árvores |
| `Grama.gpkg` | Rótulos de gramíneas |
| `postes.gpkg` | Pontos de postes |

Os rasters têm **6.942 × 7.294 pixels**, resolução de **0,5 m/pixel** e CRS **EPSG:31982**; os vetores de rótulo e postes são originariamente **EPSG:4674** e precisam ser reprojetados antes de operações métricas. Os arquivos raster estão ligeiramente deslocados entre si, o que requer cuidado ao utilizar bandas de diferentes produtos.

**O ZIP não possui geometria de linhas de energia.** Não se deve afirmar validação da distância às linhas com esses arquivos.

## Correção de interpretação da etapa espacial

No código anexado, os segmentos do cluster 3 seguem para o cálculo de área e altura mesmo quando `predicted_classe == 'grama'`. A versão limpa disponível no repositório aplica o filtro `predicted_classe == 'arvore'` antes da análise de altura e proximidade. A alteração é metodologicamente necessária, mas **os quantitativos espaciais devem ser recalculados**.

## Pendências científicas

- Ampliar a validação por área geográfica e por objetos independentes para evitar vazamento espacial/duplicações no treino e teste.
- Comparar com baselines simples e técnicas alternativas (SVM, outros classificadores e técnicas de detecção/segmentação quando comparáveis).
- Executar estudo de ablação de NDVI, brilho e bordas; avaliar métricas por classe e intervalos de confiança.
- Identificar na revisão bibliográfica os gaps que a abordagem se propõe a preencher.
- Validar a estimativa de altura com medições reais; a configuração C3 é **empírica**, não uma equação publicada literalmente pela referência alométrica.
- Validar a análise de proximidade com geometrias reais das linhas, se disponíveis, e não confundir proximidade bidimensional com risco operacional comprovado.

**Situação:** registro documental concluído; resultados de execução do notebook recebido, não experimento independente repetido.
