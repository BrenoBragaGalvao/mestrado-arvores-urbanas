# E9 — medição de memória nos mesmos 119 recortes da Area1

## Resultado real, não estimado

A execução de perfilamento utilizou **os dois rasters originais da Area1** (AOI_RGB_NEW.tif e AOI_NEW_MULTI.tif) e **510 pontos** dos arquivos Arvores.gpkg e Grama.gpkg. Cada referência foi localizada na grade raster; a deduplicação dos quadrantes de **512 × 512 pixels a partir da origem da imagem** identificou **119 regiões**, sendo quatro de tamanho menor na borda.

As duas estratégias processaram **exatamente os mesmos 30.650.368 pixels** contidos nessas 119 janelas. Para cada região, foram calculados os mapas de **NDVI, brilho HSV e bordas Canny**; em seguida aplicou-se Quickshift com os mesmos parâmetros do E9 (kernel_size=3, max_dist=5, ratio=0.04, rng=42), contínuo na janela inteira ou independentemente nos quatro quadrantes. Também foram extraídas as médias dos três atributos por segmento. As janelas foram processadas sequencialmente em cada estratégia.

| Indicador observado | Quickshift contínuo, até 512 × 512 | Quickshift em até quatro partes de 256 × 256 |
|---|---:|---:|
| Regiões originais comparadas | 119 | 119 |
| Referências que determinam os recortes | 510 | 510 |
| Pixels percorridos nos recortes | 30.650.368 | 30.650.368 |
| Memória residente inicial do processo | 185,87 MiB | 185,87 MiB |
| **Pico de memória residente (RSS)** | **467,19 MiB** | **456,80 MiB** |
| **Pico adicional ao RSS inicial** | **281,32 MiB** | **270,94 MiB** |
| Segmentos gerados | **91.984** | **90.673** |
| Duração observada do processo | 202,48 s | 186,05 s |

**Diferença do pico RSS total:** 10,3828125 MiB menor em quatro 256 do que em 512 contínuo, correspondendo a **2,22%** do pico no contínuo.

**Diferença do pico acima da linha de base:** 10,37890625 MiB, correspondendo a **3,69%** do incremento no contínuo.

As contagens de **91.984 e 90.673 segmentos coincidem exatamente com os números já registrados no protocolo original de E9**. Isso oferece uma verificação adicional de que as janelas e as configurações de Quickshift correspondem às documentadas, sem constituir uma repetição das avaliações de classificação.

## Como a memória foi medida

- Cada braço executou em um **processo Python separado**, com imports das mesmas bibliotecas e abertura dos mesmos rasters.
- A medição observou o *high-water mark* de RSS do processo por meio de resource.getrusage(resource.RUSAGE_SELF).ru_maxrss no Linux. O indicador foi convertido de KiB para MiB. A linha de base foi registrada após importações e abertura dos rasters, antes de processar a primeira janela.
- O consumo medido **abrange a execução de leitura de dados raster, mapas de atributos, Quickshift, cálculo de médias, alocações temporárias e caches do processo**; não é uma medida isolada da função Quickshift e não representa memória máxima necessária para processar 119 recortes simultaneamente.
- As 119 regiões foram lidas e processadas **uma após a outra** em cada processo. Os dois processos foram lançados no mesmo ambiente com capacidade de executar múltiplos núcleos, sem pressão de memória agregada no limite de RAM. A comparação de tempo não foi desenhada como benchmark controlado de velocidade; evitamos inferir superioridade de velocidade.
- Ambiente utilizado: Linux com limite de memória do contêiner de **4 GiB**; Python **3.13.5**, numpy **2.3.5**, scikit-image **0.26.0** e rasterio **1.5.0**. Os resultados de RSS podem mudar se houver alterações de sistema operacional, versões, bibliotecas, caches ou número de processos simultâneos.
- Os picos correspondem ao uso máximo residente durante a passagem pelos 119 recortes, **não à média de 119 picos individuais**. Dividir um recorte em quatro não implica automaticamente diminuir o pico total do processo na razão de quatro vezes.

## Limitações e interpretação para a dissertação

A motivação para utilizar quadrantes menores foi evitar o alto consumo de memória do Quickshift global na imagem inteira. Esta medição do E9 mostra, nesse ambiente e protocolo específicos, uma **redução modesta no pico total de memória (2,22%)** ao usar quatro quadrantes. A comparação científica de classificação no E9 permanece em seus próprios resultados de F1-macro e **não foi reexecutada por este teste de memória**.

O teste não reproduz Quickshift global sobre os aproximadamente 50,6 milhões de pixels do raster completo. Também não demonstra que a divisão em quadrantes economiza a mesma proporção de memória em outros equipamentos, tamanhos ou conjuntos de dados.

**Origem das evidências:** execução real dos mesmos arquivos Area1, com logs, 119 observações por estratégia, arquivos JSON de pico RSS e script de medição. Não há extrapolação de uma única janela para todas as janelas.
