# E10 — teste real de viabilidade no ambiente disponível (02/11/2026)

## Procedimento efetivamente realizado

Os dez arquivos originais da pasta Area1 do Google Drive foram obtidos para uma sessão local temporária. Os rasters foram abertos com rasterio e os vetores foram lidos com geopandas; o raster RGB tem **6.942 × 7.294 pixels**, três bandas uint8, EPSG:31982; o raster multiespectral tem quatro bandas uint16.

Testamos a chamada **sem simplificações de parâmetros** ao método quickshift do scikit-image 0.26.0: `quickshift(rgb, kernel_size=3, max_dist=5, ratio=0.04)`.

| Janela (pixels) | Resultado | Tempo observado |
|---|---|---|
| 512 × 512 | Concluiu; 754 segmentos no recorte testado | 1,5 s |
| 1.024 × 1.024 | Concluiu; 3.073 segmentos | 5,83 s |
| 2.048 × 2.048 | Concluiu; 11.823 segmentos | 25,12 s |
| 6.942 × 7.294 | **Não concluiu**; MemoryError durante a preparação das matrizes | 7,8 s até o erro |

A tentativa integral foi executada com limite de endereço virtual de **3,5 GB** para impedir encerramento do processo e respeitar o limite real da sessão (**4 GiB de memória do cgroup**). A exceção registrada foi: `MemoryError: Unable to allocate 1.13 GiB for an array with shape (7294, 6942, 3) and data type float64`.

No teste de 2.048 × 2.048, a memória residente máxima foi cerca de **687 MB**. Esses números medidos em recortes **não comprovam** a memória exata requerida para a execução global; indicam a necessidade de mais RAM e provável inviabilidade da execução global neste ambiente.

A versão de Quickshift com float32 invocada diretamente na rotina Cython também foi testada em uma janela de 512 × 512, mas **não é reprodução exata**: 754 segmentos no método padrão versus 755 com float32. Não substituir o experimento global original por essa variante silenciosamente.

## Evidência histórica do método original

Foi consultado também o notebook já presente no Google Drive, `Segmentação_breno_imagem_completa.ipynb` (28,9 MB), com saídas de uma execução histórica. Esse notebook apresenta **458 linhas** na tabela final dos atributos, sendo **92** observações de teste do Random Forest e acurácia arredondada de **0,87**. Entretanto, a saída renderizada do notebook contém apenas uma **visualização truncada** da tabela (cabeça e cauda), não um CSV íntegro de 458 linhas. Portanto, ela **não permite treinar os oito classificadores historicamente idênticos sem reconstruir os dados**.

## Conclusão verificada

Acesso às entradas e pilotos reais confirmados. **Não** foi concluído Quickshift global, K-Means global, cluster 3 nem a avaliação de oito classificadores nesse mesmo pipeline. **Não** há novas métricas E10. Para reproduzir o original seria necessário ambiente com mais RAM e uma nova execução controlada; isso não faz parte da comparação por janelas da V2. A comparação por recortes da V2/E9 permanece separada.
