# Relatório de execução parcial com dados reais — Area1 (31/10/2026)

## Escopo e advertência
Este registro documenta **testes efetivamente executados** em ambiente Python local usando somente os dados já presentes em `Projetos/Segmentacao_Breno/Area1` no Google Drive. **Não é uma execução integral da V2 no Google Colab.** As métricas abaixo são de pilotos em quatro janelas, não dos experimentos E1–E7 completos.

## Dados originais conferidos
- RGB: `AOI_RGB_NEW.tif`, **7.294 × 6.942 pixels**, três bandas, resolução 0,5 m, EPSG:31982.
- Multiespectral: `AOI_NEW_MULTI.tif`, quatro bandas, mesmas dimensões e resolução; as duas grades diferem levemente em origem (aproximadamente 0,0204 m em X e 0,2296 m em Y).
- AOI: 1 polígono, área aproximada de **12,1372 km²**.
- Referências: **257 pontos de árvores** e **253 pontos de gramíneas**.
- Postes: **15.260 registros** na camada de origem; 7.722 pontos dentro do retângulo de extensão do RGB, **não necessariamente dentro do polígono AOI**.

Ambiente local: Python 3.13.5; Rasterio 1.5.0; GeoPandas 1.1.2; scikit-image 0.26.0; scikit-learn 1.8.0.

## E5a — Quickshift, sensibilidade em quatro recortes

Foram usadas quatro janelas fixas de **256 × 256 pixels** em regiões próximas aos rótulos já existentes: (row0,col0) = (6262,1555), (1545,2946), (3016,3906), (2973,3062). Aplicamos cinco configurações às quatro janelas: **20 execuções**.

| kernel_size | max_dist | ratio | segmentos: média | segmentos: desvio-padrão | tempo médio (s) |
|---:|---:|---:|---:|---:|---:|
| 2 | 5 | 0,04 | 308,00 | 20,67 | 0,123 |
| 3 | 3 | 0,04 | 469,00 | 48,63 | 0,238 |
| **3 (original)** | **5** | **0,04** | **186,25** | **19,77** | **0,235** |
| 3 | 8 | 0,04 | 124,00 | 3,92 | 0,234 |
| 4 | 5 | 0,04 | 136,00 | 11,34 | 0,391 |

**Leitura científica:** a granularidade da segmentação é sensível aos parâmetros; nenhum destes indicadores demonstra, isoladamente, melhoria de precisão na identificação de árvores. Tempos de recortes não equivalem a tempos do raster integral.

## E5b — K-Means nos mesmos recortes (piloto adicional)

A partir da segmentação Quickshift original `(3,5,0.04)`, criamos **779 segmentos** nesses quatro recortes e extraímos, para todos eles, médias e desvios-padrão nas quatro bandas RGB/NIR já existentes (8 atributos). Os mesmos 779 registros foram agrupados com `KMeans(random_state=42,n_init=10)`.

| K | Inércia | Silhouette amostral (até 500) | ARI versus K=6 |
|---:|---:|---:|---:|
| 4 | 160.196.986,47 | 0,3664 | 0,3483 |
| **6 (original)** | **109.496.281,18** | **0,3564** | **1,0000** |
| 8 | 86.279.342,69 | 0,3391 | 0,5940 |

Nas quatro janelas, as referências preexistentes associaram-se a **18 segmentos**, sendo **10 árvores** e **8 gramíneas**. Não foram criadas novas anotações. Isso não permite concluir superioridade de nenhum K em classificação; silhouette mede separação interna dos grupos e ARI mede concordância entre partições do mesmo conjunto. **IDs dos clusters não representam categorias fixas.**

## Estado verificado das etapas

| Etapa | Execução real verificada |
|---|---|
| E1: auditoria do treinamento | Não executada na AOI inteira |
| E2: partição espacial | Não executada na AOI inteira |
| E3: RF versus SVM e baselines | Não executada na AOI inteira |
| E4: ablação dos três atributos | Não executada na AOI inteira |
| **E5: sensibilidade de parâmetros** | **Pilotos parciais E5a/E5b executados; E5 integral não executado** |
| E6: proximidade com postes | Não executada com as previsões integrais |
| E7: alometria | Não executada com os segmentos integrais |
| E8: consolidação | Parcial: resultados piloto e limites documentados |

## Próxima condição para validação científica da dissertação

O notebook V2 depende dos objetos `df`, `gdf_arvore_seg_filter`, `tree_polys` e `Postes` produzidos pelo fluxo completo. O RGB possui cerca de **50,6 milhões de pixels**; o runtime local disponível nesta execução tem aproximadamente **5,8 GiB de RAM** e não é uma sessão Google Colab do pesquisador. **A execução integral da V2 não foi concluída nem suas métricas E1–E7 verificadas.**

A próxima atividade necessária é executar a V2 com os **mesmos arquivos Area1** no Colab, inspecionar possíveis erros e registrar saídas reais para E1–E7. Só depois disso será possível produzir comparações completas para a banca.

**Limites:** não confundir acurácia histórica 0,87 com validação espacial nova; índices C1–C6 não são medidas de altura e distâncias a postes não comprovam risco elétrico ou interferência nos cabos.

Nenhum dado adicional foi solicitado. Os notebooks `Segmentacao_area_completa.ipynb` e `Segmentacao_area_completa_v2_experimentos.ipynb`, e o `README.md`, foram preservados nesta execução.
