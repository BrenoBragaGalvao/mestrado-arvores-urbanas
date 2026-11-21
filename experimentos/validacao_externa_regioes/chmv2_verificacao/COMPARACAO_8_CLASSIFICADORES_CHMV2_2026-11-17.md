# Comparação de oito classificadores — Area1 e três regiões externas (17/11/2026)

**Escopo:** Area1 (treinamento e validação espacial internos), Sagrada Família, Lomba Grande e Cristo Rei (transferência sem retreinamento). Centro de Novo Hamburgo excluído.

**Execução real:** leitura ponto-a-ponto de **24 mapas GeoTIFF de classificação** (8 modelos × 3 regiões externas), extraídos de `sagrada_familia_caxias_mapas.zip`, `lomba_grande_novo_hamburgo_mapas.zip` e `cristo_rei_sao_leopoldo_mapas.zip`. Para cada região, os mesmos 200 pontos originais de avaliação CHMv2 foram amostrados com rasterio em **EPSG:31982**. A extração da Regressão Logística coincidiu **600/600** com as previsões anteriormente guardadas. Nenhuma classe de avaliação entrou no treinamento ou reajuste do modelo.

**Regra conservadora CHMv2:** máximo de altura num raio de 5 m; altura até 0,5 m = candidata a gramínea; altura a partir de 5 m = candidata a árvore; intermediários = incertos, excluídos para **todos** os modelos da região. Os três conjuntos possuem **179, 183 e 181 pontos** (543 no total), respectivamente.

| Classificador | Area1 F1 interno 250 m | Area1 F1 interno 500 m | Sagrada CHMv2 | Lomba CHMv2 | Cristo Rei CHMv2 | Média simples externa |
|---|---:|---:|---:|---:|---:|---:|
| **Regressão Logística** | 0,8376 | 0,8567 | **0,7597** | 0,7785 | **0,8042** | **0,7808** |
| Extra Trees | 0,7804 | 0,7899 | 0,5468 | **0,7989** | 0,5426 | 0,6294 |
| HistGradientBoosting | 0,7687 | 0,7932 | 0,5943 | 0,6265 | 0,6167 | 0,6125 |
| KNN | 0,8473 | 0,8558 | 0,4778 | 0,6885 | 0,4958 | 0,5540 |
| Gaussian Naive Bayes | 0,7250 | 0,7287 | 0,3876 | 0,7490 | 0,3753 | 0,5040 |
| SVM RBF | **0,8586** | **0,8689** | 0,4171 | 0,6265 | 0,4335 | 0,4924 |
| Random Forest | 0,7801 | 0,8057 | 0,4134 | 0,5419 | 0,4369 | 0,4641 |
| Dummy (controle) | 0,3051 | 0,2853 | 0,3035 | 0,2621 | 0,3466 | 0,3041 |

**Leitura:** o SVM RBF apresenta maior F1 interno na Area1, mas a Regressão Logística tem maior concordância CHMv2 em Sagrada e Cristo Rei e a maior média das três áreas externas. Extra Trees supera Regressão Logística **apenas em Lomba Grande**, por **+0,0204**. Uma reamostragem pareada de 10.000 iterações por blocos de 500 m em Lomba deu IC 95% aproximado **[-0,0338, +0,0744]** para a diferença Extra Trees menos Regressão Logística; inclui zero, portanto não comprova superioridade consistente.

**Análise da regra simples:** repetir a avaliação com pseudo-rótulos `0 m = gramínea; >0 m = árvore` mantém Regressão Logística em primeiro lugar em Sagrada e Cristo Rei e Extra Trees em primeiro em Lomba, embora mude os valores absolutos.

**Limitações científicas:** os F1 internos da Area1 e os F1 de concordância externa com CHMv2 têm naturezas diferentes; não tratá-los como mesmo protocolo. O CHMv2 não oferece rótulos humanos, e zero m pode decorrer de falhas da estimativa de altura. Não usar resultados externos para selecionar ou refinar parâmetros do modelo depois de consultá-los. Comparação diagnóstica de modelos congelados é válida; seleção formal para generalização precisa de avaliação independente adicional. O problema das superfícies não vegetadas na classificação binária também permanece.

**Recomenda-se manter a Regressão Logística como principal** com base nas evidências atualmente existentes, e usar SVM e Extra Trees como comparadores de ablação/robustez. Não há demonstração de ganho geral pela substituição do classificador.

Fontes dos modelos Area1: `Area1_modelos_corrigidos_e_validacao.zip` (`validacao_aninhada_area1/area1_resumo_oito_modelos.csv`). Fonte externa: `600_pontos_mais_CHM.csv`, obtido da execução do CHMv2 registrada no PR #6, e os GeoTIFFs das três regiões. Nenhum dado original e nenhum arquivo `main` foram alterados.
