# Proposta 1 — registro operacional e síntese científica da transferência a partir da Area1

**Consolidação auditada em 13/11/2026.** Repositório: [mestrado-arvores-urbanas](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas). Branch: `feature/validacao-geografica-externa`. [PR #6](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/pull/6).

> **Natureza da entrega.** Este arquivo sintetiza e confere **artefatos reais de uma execução prévia**; nesta rodada foram relidos o CSV consolidado, a lista de arquivos do Drive, o notebook de reprodução, a evidência espectral e o atlas visual. **Não houve uma nova sessão de treinamento/inferência no Google Colab nesta rodada.** Não há F1-macro externo válido disponível para as quatro regiões.

## 1. Objetivo e hipótese operacional

Investigar se os oito algoritmos clássicos de aprendizado de máquina treinados **exclusivamente** nos pontos originais da Area1 conseguem distinguir *árvores* de *gramíneas* em quatro outras imagens urbanas, **sem usar rótulos locais para reestimar parâmetros**. As cinco imagens incluem a própria origem Area1, para mapa descritivo, e Sagrada Família, Centro, Lomba Grande e Cristo Rei, para inferência transferida.

**Entradas de treinamento:** [`Arvores.gpkg` e `Grama.gpkg` originais no Drive](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6), 257+253=510 pontos, reduzidos a **505 segmentos Quickshift únicos** após ligação ponto→segmento (257 árvore, 248 gramínea na reconstrução corrigida). Os 510 pontos geográficos não são deslocados para as outras cidades. Transfere-se somente o classificador treinado. Não há treinamento com as bases locais de 250+250 segmentos neste experimento.

## 2. Pipeline descrito na execução de referência

- Segmentação **Quickshift** em janelas independentes de até 256×256 pixels; `kernel_size=3`, `max_dist=5`, `ratio=0,04`, semente 42.
- Atributos por segmento: média de brilho **V em HSV**, média da borda **Canny** e média do índice espectral calculado com **vermelho (banda 3)** e **NIR (banda 4)**. Produtos Jilin-1 foram auditados com XMLs e correlação de canais. Os valores do índice provêm de **números digitais**, sem harmonização radiométrica entre sensores; não apresentá-los como NDVI de reflectância calibrada.
- Ortoimagem multiespectral alinhada à grade RGB com **WarpedVRT / reamostragem bilinear**, resolução nominal de 0,5 m e CRS EPSG:31982.
- **Área de treino e hiperparâmetros:** cinco divisões espaciais de avaliação por blocos de 250 m e 500 m, embargo **geométrico** de 25 m e três divisões internas para escolha de regularização moderada/forte. Oito modelos finais congelados; `StandardScaler` integra os pipelines dos algoritmos que o requerem.
- A validação espacial da Area1 é **interna à origem**, e os mapas da própria Area1 não são teste independente. A transferência às quatro imagens não utiliza rótulos dessas imagens.
- O Dummy é o controle simples e não representa método de identificação de vegetação.

[Código do notebook de reprodução](./proposta1_cinco_areas_colab.ipynb) · [Orquestrador](./executar_proposta1_cinco_areas.py) · [Evidência de bandas vinculada aos hashes](./bandas_verificadas_jilin.json) · [Documentação anterior de execução](https://drive.google.com/file/d/17OPMv9DjUqcwYQVenxPU1Ec5qG9rRJ-I/view).

## 3. Artefatos existentes e verificações atuais

A pasta [resultados do experimento](https://drive.google.com/drive/folders/1JAcdZwUNqgFfsaJwNqOcsJsUypNqr2mY) contém o pacote [oito modelos fixos + validação interna](https://drive.google.com/file/d/1Hsn1WQxic6150_fXrqXpkLkaePkTIEl-/view), [tabelas/figuras/reprodução](https://drive.google.com/file/d/1dqCY48klV2nHZnW7EghkM_bo8-g7kLUU/view) e cinco ZIPs de mapas, com **oito classificadores por área**. O [atlas visual de cinco imagens](https://drive.google.com/file/d/1NRkUKDa2_Tx46SPJEvTbYpnTEnefYsEv/view) também documenta cinco comparações RGB × oito modelos, bandas e atributos. Foi possível confirmar as pastas e arquivos existentes via Drive e ler as descrições do atlas.

Na presente conferência, as **40 linhas** do [CSV consolidado](./RESULTADOS_CONSOLIDADOS_CINCO_AREAS_8_MODELOS_2026-11-13.csv) passaram nas checagens de: oito modelos por imagem; soma idêntica de segmentos previstos em cada classe para todos os modelos da mesma área; soma idêntica de hectares previstos; coerência entre percentual de árvore e razão de área prevista (erro residual por arredondamento inferior a 0,00001 ponto percentual). Isso é **auditoria numérica de tabelas**, não releitura pixel a pixel dos 40 GeoTIFFs nesta sessão. [Auditoria de rasters de sessão anterior](./AUDITORIA_INDEPENDENTE_2026-11-13.md).

| Área | Segmentos classificados | Área com predição (ha) | Mapas existentes | Métrica externa |
|---|---:|---:|---:|---|
| Area1 — Caxias do Sul | 131.776 | 1.174,02 | 8 | não aplicável (origem) |
| Sagrada Família — Caxias do Sul | 318.830 | 2.678,75 | 8 | não avaliada |
| Centro — Novo Hamburgo | 317.756 | 2.667,18 | 8 | não avaliada |
| Lomba Grande — Novo Hamburgo | 614.030 | 4.612,19 | 8 | não avaliada |
| Cristo Rei — São Leopoldo | 335.628 | 2.664,41 | 8 | não avaliada |

**Total de segmentos registrados nas cinco imagens: 1.718.020** (não equivale a área urbana única: Area1 se sobrepõe a Sagrada Família). As áreas em hectares são **predições sobre pixels válidos**, sem correção por erro de classificação e sem classe de fundo para telhados, asfalto, solo exposto e água.

## 4. Desempenho espacial interno da Area1

Médias de F1-macro reportadas no novo protocolo aninhado, com a ordem de bandas corrigida, sem transferência:

| Classificador | F1-macro 250 m | F1-macro 500 m |
|---|---:|---:|
| Random Forest | 0,7801 | 0,8057 |
| SVM RBF | 0,8586 | 0,8689 |
| Regressão logística | 0,8376 | 0,8567 |
| Extra Trees | 0,7804 | 0,7899 |
| KNN | 0,8473 | 0,8558 |
| HistGradientBoosting | 0,7687 | 0,7932 |
| Gaussian Naive Bayes | 0,7250 | 0,7287 |
| Dummy | 0,3051 | 0,2853 |

O **SVM RBF** teve a maior média observada nas duas escalas: **0,8586** (250 m) e **0,8689** (500 m). As médias de folds não demonstram superioridade estatística nem validam transferibilidade. [Históricos diferentes da Area1](https://drive.google.com/file/d/1KcODyNBdy7TChBhIG79fiRWe9xzDnUdK/view) empregaram outras versões de canal/alinhamento e/ou outros protocolos, não podendo ser tratados como comparação pareada.

## 5. Resultados de transferência — 40 combinações de imagem × modelo

`Seg.` = **segmentos previstos** em cada classe; `ha` = hectares previstos em cada classe. Estas tabelas **não apresentam acurácia externa**.

### Area1 — Caxias do Sul

[Oito mapas GeoTIFF](https://drive.google.com/file/d/1DETrhSCnIIcUG92LHz1sFUkVNstD6fte/view) · [Figuras do atlas e comparativos](https://drive.google.com/file/d/1MIC-KnqBUXlrdZMUYfUe8REMRWeU2_Q8/view)

| Modelo | Seg. árvore | Seg. gramínea | Árvore prevista (ha) | Gramínea prevista (ha) | Pixels árvore (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 124.562 | 7.214 | 1.106,66 | 67,36 | 94,26 |
| SVM RBF | 123.368 | 8.408 | 1.096,57 | 77,45 | 93,40 |
| Regressão logística | 54.520 | 77.256 | 457,39 | 716,63 | 38,96 |
| Extra Trees | 102.833 | 28.943 | 937,56 | 236,47 | 79,86 |
| KNN | 110.545 | 21.231 | 997,85 | 176,18 | 84,99 |
| HistGradientBoosting | 92.109 | 39.667 | 808,18 | 365,84 | 68,84 |
| Gaussian Naive Bayes | 118.794 | 12.982 | 1.067,71 | 106,31 | 90,94 |
| Dummy | 131.776 | 0 | 1.174,02 | 0,00 | 100,00 |

### Sagrada Família — Caxias do Sul

[Oito mapas GeoTIFF](https://drive.google.com/file/d/18GwhiVAC_LT1rxZgmICTvz2VLjABFKQQ/view) · [Figuras do atlas e comparativos](https://drive.google.com/file/d/15f_mBHWyIgShjyJT3Haqp9-6MQAOMYQc/view)

| Modelo | Seg. árvore | Seg. gramínea | Árvore prevista (ha) | Gramínea prevista (ha) | Pixels árvore (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 295.051 | 23.779 | 2.464,00 | 214,75 | 91,98 |
| SVM RBF | 289.994 | 28.836 | 2.423,81 | 254,94 | 90,48 |
| Regressão logística | 161.057 | 157.773 | 1.228,28 | 1.450,47 | 45,85 |
| Extra Trees | 248.324 | 70.506 | 2.116,94 | 561,80 | 79,03 |
| KNN | 263.188 | 55.642 | 2.214,17 | 464,58 | 82,66 |
| HistGradientBoosting | 235.942 | 82.888 | 1.923,17 | 755,57 | 71,79 |
| Gaussian Naive Bayes | 260.716 | 58.114 | 2.228,25 | 450,50 | 83,18 |
| Dummy | 318.830 | 0 | 2.678,75 | 0,00 | 100,00 |

### Centro — Novo Hamburgo

[Oito mapas GeoTIFF](https://drive.google.com/file/d/1co5EApBv9zHWsCjdF7W0s-nC5jZ1QcqW/view) · [Figuras do atlas e comparativos](https://drive.google.com/file/d/16zhmFcbPwGA_b2dDX3O0XaJpQENzQ7fz/view)

| Modelo | Seg. árvore | Seg. gramínea | Árvore prevista (ha) | Gramínea prevista (ha) | Pixels árvore (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 307.368 | 10.388 | 2.606,92 | 60,27 | 97,74 |
| SVM RBF | 317.756 | 0 | 2.667,18 | 0,00 | 100,00 |
| Regressão logística | 0 | 317.756 | 0,00 | 2.667,18 | 0,00 |
| Extra Trees | 302.228 | 15.528 | 2.593,44 | 73,74 | 97,24 |
| KNN | 0 | 317.756 | 0,00 | 2.667,18 | 0,00 |
| HistGradientBoosting | 298.987 | 18.769 | 2.568,76 | 98,42 | 96,31 |
| Gaussian Naive Bayes | 317.756 | 0 | 2.667,18 | 0,00 | 100,00 |
| Dummy | 317.756 | 0 | 2.667,18 | 0,00 | 100,00 |

### Lomba Grande — Novo Hamburgo

[Oito mapas GeoTIFF](https://drive.google.com/file/d/1ePRzJQColP1dvqJJv9P3LaSVo1LxE30w/view) · [Figuras do atlas e comparativos](https://drive.google.com/file/d/1M_1GrUk9KyPGmM0DZ4pkNHtmqNODR20E/view)

| Modelo | Seg. árvore | Seg. gramínea | Árvore prevista (ha) | Gramínea prevista (ha) | Pixels árvore (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 472.881 | 141.149 | 3.497,19 | 1.115,00 | 75,82 |
| SVM RBF | 425.151 | 188.879 | 3.151,13 | 1.461,07 | 68,32 |
| Regressão logística | 317.655 | 296.375 | 2.365,70 | 2.246,49 | 51,29 |
| Extra Trees | 304.657 | 309.373 | 2.403,19 | 2.209,00 | 52,11 |
| KNN | 373.875 | 240.155 | 2.776,92 | 1.835,27 | 60,21 |
| HistGradientBoosting | 445.729 | 168.301 | 3.308,96 | 1.303,23 | 71,74 |
| Gaussian Naive Bayes | 213.879 | 400.151 | 1.587,53 | 3.024,66 | 34,42 |
| Dummy | 614.030 | 0 | 4.612,19 | 0,00 | 100,00 |

### Cristo Rei — São Leopoldo

[Oito mapas GeoTIFF](https://drive.google.com/file/d/1ih1_ti5svuc-ZIq-zOiuEa1ymYFjf239/view) · [Figuras do atlas e comparativos](https://drive.google.com/file/d/1qXn85ESzOWwFRIenR2kj4gxWdUmidjDw/view)

| Modelo | Seg. árvore | Seg. gramínea | Árvore prevista (ha) | Gramínea prevista (ha) | Pixels árvore (%) |
|---|---:|---:|---:|---:|---:|
| Random Forest | 313.056 | 22.572 | 2.458,37 | 206,04 | 92,27 |
| SVM RBF | 307.263 | 28.365 | 2.414,78 | 249,63 | 90,63 |
| Regressão logística | 202.965 | 132.663 | 1.480,80 | 1.183,61 | 55,58 |
| Extra Trees | 266.191 | 69.437 | 2.135,16 | 529,25 | 80,14 |
| KNN | 279.068 | 56.560 | 2.197,07 | 467,34 | 82,46 |
| HistGradientBoosting | 270.225 | 65.403 | 2.077,61 | 586,80 | 77,98 |
| Gaussian Naive Bayes | 242.730 | 92.898 | 1.974,53 | 689,88 | 74,11 |
| Dummy | 335.628 | 0 | 2.664,41 | 0,00 | 100,00 |

## 6. Discussão científica e ameaças à validade

**Area1 e Sagrada Família.** O polígono de treino está quase integralmente dentro da imagem regional de Sagrada Família, e a evidência espectral documenta pixels multiespectrais coincidentes na sobreposição. Por isso, os 510 pontos originais **não podem ser reutilizados como teste externo de Sagrada**. Para avaliação da transferência, excluir **Area1 + buffer de 25 m + segmentos intersectantes**, usando rótulos próprios obtidos independentemente.

**Centro de Novo Hamburgo.** Há **colapso divergente de predição**: SVM RBF, Gaussian Naive Bayes e Dummy atribuem 100% dos pixels válidos a árvore; KNN e regressão logística atribuem 0%. O relatório anterior identifica 100% dos segmentos do Centro fora da faixa do brilho de treino. Isso sustenta **deslocamento de domínio (domain shift)** e torna impróprio usar suas áreas previstas como inventário confiável de vegetação. Comparar escalas radiométricas e aquisição Jilin-1; eventual normalização harmonizada seria **novo experimento**, com protocolo e validação próprios, não correção oportunista dos mapas.

**Lomba Grande e Cristo Rei.** Os modelos diferem consideravelmente na proporção prevista. A diferença pode refletir fisionomia urbana, distribuição dos atributos, tratamento de sombra, distribuição de NDVI em números digitais, divisão de copas pelo Quickshift, bordas de janela ou diferenças de sensor. Sem rótulos externos, não é possível separar erro do modelo de variação real de vegetação.

**Validade do binário.** Os segmentos classificados como “árvore” ou “gramínea” não têm garantia de serem realmente vegetação: superfícies não vegetadas precisam ser representadas explicitamente por máscara ou classe adicional para inferir cobertura da paisagem inteira. “Área de árvore prevista” não é “área arborizada comprovada”.

**Incerteza sobre sobreajuste.** A regularização, a seleção aninhada e o embargo reduzem riscos conhecidos na Area1. Eles não provam ausência de underfitting/overfitting nem de erro de transferência. O [diagnóstico com F1 treino×teste e sensibilidade de embargo](./AUDITORIA_F1_ELEVADO_BASES_EQUILIBRADAS_2026-11-13.md) pertence a baterias com amostras/níveis de evidência diferentes; não substitui teste cego das quatro regiões.

**Integridade da entrada Area1.** A [auditoria de 13/11](./AUDITORIA_INDEPENDENTE_2026-11-13.md) registrou divergência entre o tamanho atual informado no Drive para `AOI_NEW_MULTI.tif` e o tamanho anotado no manifesto antigo. Antes de republicar uma reexecução como reprodução bit a bit, conferir **SHA-256** da origem e a evidência `bandas_verificadas_jilin.json`, sem sobrepor o raster anterior. A causa dessa divergência não foi estabelecida.

## 7. Validação geográfica externa: objetivo ainda não comprovado

Os quatro pacotes externos de **200 pontos cegos** (800 no total) estão disponíveis para anotação humana e devem permanecer distintos do treino. Não foi localizado conjunto com anotações humanas suficientes para estimar F1 externo. Os arquivos de F1 interno obtido com 250+250 segmentos locais e referências sugeridas por IA **não são métricas de transferência** do modelo congelado da Area1.

Critério de conclusão: conferir os **rótulos independentes**, exclusão geométrica em Sagrada, deduplicação por segmento, cálculo de F1-macro, precisão, revocação, matrizes de confusão e análise de cobertura fora da vegetação. O [script de avaliação](./avaliar_regiao.py) deve bloquear métricas quando não houver duas classes suficientemente rotuladas.

O conjunto de métricas da origem **não deve ser copiado** para Sagrada Família, Centro, Lomba Grande ou Cristo Rei.

## 8. Registro objetivo do que está e não está concluído

| Objetivo | Estado baseado nos artefatos encontrados |
|---|---|
| Localizar os 510 pontos originais | Confirmada presença dos arquivos no Drive; contagem 257/253 documentada pela execução prévia |
| Reconstruir 505 segmentos e treinar oito modelos | Artefatos e métricas reais **pré-existentes**; não retreinados hoje |
| Identificar ordem espectral | Evidência técnica registrada por produto e hash; não recalculada hoje |
| Gerar mapas dos oito modelos em cinco áreas | Cinco pacotes com 40 GeoTIFFs **pré-existentes** |
| Gerar tabelas científicas e atlas | Tabela de 40 linhas rechecadas **nesta rodada**, atlas existente no Drive |
| Revalidar 40 rasters no pixel nesta rodada | **Não executado nesta sessão** |
| Reexecutar Colab autenticado nesta rodada | **Não disponível no ambiente conectado nesta sessão** |
| F1-macro externo das quatro áreas | **Pendente de referências humanas independentes** |
| Concluir generalização geográfica com evidência quantitativa | **Ainda não comprovada** |

## 9. Materiais de reprodução

- [Notebook A0–A4](https://colab.research.google.com/github/BrenoBragaGalvao/mestrado-arvores-urbanas/blob/feature/validacao-geografica-externa/experimentos/validacao_externa_regioes/proposta1_cinco_areas_colab.ipynb) para ambiente autenticado com o Drive.
- [Pasta principal da execução](https://drive.google.com/drive/folders/1JAcdZwUNqgFfsaJwNqOcsJsUypNqr2mY); [atlas visual completo](https://drive.google.com/file/d/1NRkUKDa2_Tx46SPJEvTbYpnTEnefYsEv/view); [relatório anterior](https://drive.google.com/file/d/17OPMv9DjUqcwYQVenxPU1Ec5qG9rRJ-I/view).
- [CSV de resultados em precisão original](./RESULTADOS_CONSOLIDADOS_CINCO_AREAS_8_MODELOS_2026-11-13.csv) (as tabelas acima são apenas formatadas para leitura).
- [PR #6](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/pull/6): manter em **draft** até terminar a validação científica e a auditoria do arquivo multiespectral de origem.

**Síntese científica para a dissertação:** A execução demonstrou a **viabilidade operacional da transferência de modelos congelados da Area1**, com produção de inferências georreferenciadas nas quatro regiões externas. O desempenho interno foi estimado com validação espacial aninhada na origem, e a análise exploratória da transferência revelou forte instabilidade no Centro. **A capacidade de generalização, entendida como desempenho preditivo mensurado fora da origem, não está comprovada** até que referências independentes permitam avaliar as predições. A comparação com modelos treinados localmente é exploratória e não estima generalização da Area1.
