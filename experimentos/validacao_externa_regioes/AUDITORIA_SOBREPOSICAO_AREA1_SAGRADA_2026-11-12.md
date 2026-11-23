# Auditoria de sobreposição — Area1 × Sagrada Família

**Data:** 12/11/2026  
**Fontes:** arquivos originais `AOI_new.shp`, `AOI_new.prj`, `Arvores.gpkg`, `Grama.gpkg` da [pasta privada da Area1](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6); metadados RGB de Sagrada Família, observados na [execução real de auditoria do raster](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/actions/runs/43292319271). Nenhuma coordenada individual de ponto foi publicada.

## Resultado geográfico

| Verificação | Resultado |
|---|---:|
| Pontos de árvores lidos de `Arvores.gpkg` | **257** |
| Pontos de gramíneas lidos de `Grama.gpkg` | **253** |
| Total de pontos de referência | **510** |
| Pontos contidos no polígono original `AOI_new.shp` | **510 / 510** |
| Pontos contidos no retângulo geográfico RGB de Sagrada Família | **510 / 510** |
| Pontos originais localizados em Centro, Lomba Grande ou Cristo Rei | **0** (regiões geograficamente distintas) |
| Área do polígono AOI original (aprox.) | **12,137 km²** |
| Área AOI coberta pelo retângulo RGB de Sagrada Família (aprox.) | **11,877 km²** |
| Fração da área do polígono AOI coberta pela imagem Sagrada (aprox.) | **97,86%** |
| Fração do **retângulo delimitador** da Area1 coberta pelo RGB de Sagrada | **96,44%** |

## Método da auditoria

1. Foram lidos os registros geográficos binários dos dois GeoPackages originais, totalizando 257 + 253 geometrias de tipo **Point**, ambos com `srs_id=4674` (SIRGAS 2000, coordenadas geográficas).
2. As coordenadas foram convertidas para o referencial projetado **SIRGAS 2000 / UTM zona 22S** (EPSG:31982), correspondente ao `AOI_new.prj` e ao raster RGB regional, usando as fórmulas do sistema Transverse Mercator com elipsoide GRS80.
3. O shapefile da Area1 contém **um polígono com 31 vértices**; foi aplicada a regra de ponto dentro do polígono para cada uma das 510 referências.
4. Para medir o quanto da Area1 é coberto por Sagrada Família, o polígono foi intersectado com o **retângulo de abrangência espacial** dos pixels RGB e foram comparadas as áreas planas em metros quadrados. Não foram comparados valores RGB pixel a pixel.
5. A função reproduzível [`auditar_sobreposicao_area1.py`](auditar_sobreposicao_area1.py) foi incluída no fluxo do Colab para repetir a verificação com **GeoPandas/Rasterio** e registrar o JSON de auditoria. **Essa execução GeoPandas no Colab ainda não foi realizada** nesta sessão.

## Implicações científicas

- A análise fortalece a hipótese de que a Area1 foi escolhida como **subárea geográfica de Sagrada Família**. **Não prova que os dois rasters tenham os mesmos pixels nem igual origem radiométrica**.
- Os **510 pontos são adequados à fonte de treinamento da Area1**, respeitadas as regras de rotulação por segmento (historicamente 505 segmentos únicos), mas **nenhum deles é uma referência independente para medir generalização** em Sagrada Família.
- A nova avaliação da Sagrada Família precisa separar **geograficamente a porção fora da Area1 e seu buffer de 25 m**. Mesmo nessa porção, o F1-macro requer **novos rótulos independentes**, não os 510 originais.
- Nas outras três regiões, é válido aplicar os modelos treinados com os 510 pontos da Area1, mas **os próprios pontos não podem ser movidos entre cidades**. Precisaremos de rótulos locais independentes para estimar F1.
- Os percentuais de área são aproximações com base nos limites e polígonos auditados; para uma publicação final, confrontar a saída da rotina GeoPandas no Colab e a equivalência dos pixels de origem.

**Status:** comparação geográfica e cobertura dos 510 pontos calculadas diretamente a partir dos arquivos originais conectados. A equivalência pixel a pixel, a reexecução dos 505 segmentos e as métricas de classificação continuam pendentes.
