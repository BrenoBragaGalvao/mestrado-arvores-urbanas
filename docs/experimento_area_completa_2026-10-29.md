# Registro do experimento — área completa (29/10/2026)

## Origem e versão de referência

O autor forneceu o notebook `Segmentação_breno_imagem_completa.ipynb` e os dados geoespaciais `Area1`.

O arquivo [`Segmentacao_area_completa.ipynb`](../Segmentacao_area_completa.ipynb) publicado atualmente no GitHub **restaura as 116 células originais** (85 de código, 31 de Markdown), com o conteúdo das células preservado. A versão simplificada de 9 células que esteve no repositório anteriormente **não é o notebook principal atual**.

A cópia publicada no GitHub conserva as saídas textuais anteriores, mas não os arquivos incorporados de imagem/HTML; o [notebook completo no Drive](https://drive.google.com/file/d/1TIgMWSOGHENy9nkiaG5b1BcFKA5f5d_i/view) conserva também essas saídas ricas.

**Situação de verificação:** os resultados apresentados a seguir são **históricos**, extraídos do notebook fornecido. Não comprovam uma nova execução integral, e a execução atual no Colab não é acompanhada automaticamente por este repositório.

## Objetivos da pesquisa

1. Segmentar imagens de alta resolução e classificar segmentos de árvores e gramíneas com NDVI, brilho HSV, bordas Canny, K-Means e Random Forest.
2. Avaliar a proximidade planimétrica de objetos selecionados com postes. Os dados `Area1` **não incluem cabos/linhas de energia**, portanto não suportam validação de interferência com fios.

## Parâmetros observados no notebook original

| Etapa | Código efetivamente publicado |
|---|---|
| RGB e segmentação | `quickshift(im, kernel_size=3, max_dist=5, ratio=0.04)` |
| Extração inicial | Médias e desvios-padrão RGB/NIR por objeto |
| Agrupamento | `KMeans(n_clusters=6, random_state=42, n_init=10)` |
| Seleção de candidatos | Segmentos do `kmeans_cluster == 3` |
| Rótulos | Interseção espacial (`sjoin`) com `Arvores.gpkg` e `Grama.gpkg` |
| Atributos para Random Forest | Médias de brilho HSV, bordas Canny e NDVI |
| Treino/teste | `train_test_split(..., test_size=0.2, random_state=42)`, **sem `stratify`** |
| Classificador | `RandomForestClassifier(n_estimators=500, random_state=42)` |
| Tratamento de rótulos | **Sem etapa explícita de deduplicação** de segmentos |
| Estimativas de altura | C1–C6, versões potencial e linear; seleção final com C3 potencial |
| Seleção da etapa espacial | `Power_tree_size_C3 > 7`, **sem condição de classe prevista árvore** |
| Proximidade de postes | `gpd.sjoin_nearest` em 1 m, 3 m e 5 m |
| Memória e exportação | Matrizes/imagens processadas integralmente; saídas em caminhos relativos no Colab |

A escolha do cluster 3 é uma decisão exploratória do código e o identificador do cluster não tem significado universal.

## Resultados históricos do notebook recebido

| Indicador | Valor histórico |
|---|---:|
| Linhas rotuladas (pares objeto–rótulo) | **458** |
| Treino | **366** |
| Teste | **92** |
| Acurácia arredondada | **0,87** |
| Precisão / recall / F1 para árvore | 0,80 / 0,92 / 0,85 |
| Precisão / recall / F1 para gramínea | 0,94 / 0,83 / 0,88 |

Esses valores foram lidos de saídas salvas no notebook original, **não reprocessados de forma independente nesta revisão documental**. Um registro objeto–rótulo não é necessariamente um objeto arbóreo distinto: a associação espacial pode criar mais de um registro para o mesmo segmento.

Uma rodada anterior do projeto apresentava 133 registros rotulados, 106 de treino, 27 de teste e acurácia de 0,81. Como os conjuntos são diferentes, a diferença de acurácia **não demonstra ganho estatisticamente comprovado**.

## Dados e sistema de coordenadas

| Dados | Finalidade |
|---|---|
| `AOI_RGB_NEW.tif` | Imagem RGB para segmentação |
| `AOI_NEW_MULTI.tif` | RGB + NIR para características |
| `AOI_new.shp/.shx/.dbf/.prj/.cpg` | Área de interesse |
| `Arvores.gpkg` e `Grama.gpkg` | Rótulos de referência |
| `postes.gpkg` | Localização de postes |

Os rasters têm **6.942 × 7.294 pixels**, pixel de aproximadamente **0,5 metro** e CRS **EPSG:31982**. Os vetores de árvores, gramíneas e postes têm como CRS de origem **EPSG:4674**; operações espaciais métricas devem usar CRS projetado. As grades das imagens RGB e multiespectral têm leve diferença de origem, relevante à interpretação por objeto.

[Localização atual dos dados no Google Drive](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6)

## Saídas e execução

Os arquivos `polygons.json`, `polygons_arvores.json`, `features_stack.tif` e `arvores_segmentadas.json` são gravados no **diretório corrente do Colab**, normalmente `/content`. O notebook original não aponta automaticamente para a pasta `outputs/` do Drive nem gera os arquivos `metricas_classificacao.json` ou `resumo_proximidade_postes.csv` mencionados na antiga documentação.

A imagem integral pode exigir RAM alta. **Não há validação registrada de que a execução atual terminou com sucesso.** Os antigos testes sintéticos e o workflow de GitHub Actions foram removidos da árvore atual; resultados históricos de testes anteriores não equivalem à validação da execução real.

## Limitações e próximos passos científicos

- Verificar resultados e erros da execução integral, inclusive consumo de memória.
- Revisar potenciais duplicações e vazamento de informação na separação de treino/teste.
- Analisar a influência da escolha do cluster e testar generalização em outras áreas.
- Avaliar o filtro de classe na seleção espacial; no código original ele não é aplicado.
- Validar a estimativa C3 com alturas reais: **estimativa de porte não é medição de altura**.
- Distinguir proximidade bidimensional a **postes** de distância a **cabos** e de diagnóstico de risco operacional.
- Explorar, em experimentos futuros explicitamente separados, ablação de atributos, modelos comparativos, validação espacial e incerteza das métricas.

Este documento descreve e contextualiza a versão **original**; nenhuma alteração metodológica é proposta como se já estivesse implementada.
