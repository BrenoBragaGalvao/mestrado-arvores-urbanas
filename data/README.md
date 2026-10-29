# Dados geoespaciais — experimento Area1

Esta pasta `data/` no **GitHub contém somente documentação**. Os dez arquivos reais utilizados pelo notebook estão no [Google Drive — `Projetos/Segmentacao_Breno/Area1`](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6).

O notebook atual [`Segmentacao_area_completa.ipynb`](../Segmentacao_area_completa.ipynb), restaurado do original de 116 células, lê **caminhos absolutos** com prefixo:

```text
/content/drive/MyDrive/Projetos/Segmentacao_Breno/Area1/
```

## Arquivos necessários

| Arquivo | Uso no notebook |
|---|---|
| `AOI_RGB_NEW.tif` | Imagem RGB para Quickshift |
| `AOI_NEW_MULTI.tif` | Bandas RGB + infravermelho próximo (NIR) |
| `AOI_new.shp` | Geometria da área de interesse |
| `AOI_new.shx` | Índice geométrico do shapefile |
| `AOI_new.dbf` | Tabela de atributos do shapefile |
| `AOI_new.prj` | Referência espacial do shapefile |
| `AOI_new.cpg` | Codificação de texto do shapefile |
| `Arvores.gpkg` | Rótulos de árvores |
| `Grama.gpkg` | Rótulos de gramíneas |
| `postes.gpkg` | Pontos de postes para proximidade |

O lote `Area1` não contém uma camada de linhas/cabos de energia.

## Características espaciais observadas

- Imagens raster: **6.942 × 7.294 pixels**, aproximadamente **0,5 m/pixel**, CRS **EPSG:31982**.
- `AOI_new.shp`: **EPSG:31982**.
- `Arvores.gpkg`, `Grama.gpkg` e `postes.gpkg`: CRS original **EPSG:4674**. O código converte camadas vetoriais para o CRS de análise antes de certas operações espaciais.
- As grades RGB e multiespectral têm uma pequena diferença de origem. Isso exige atenção ao analisar valores espectrais em conjunto.

## Organização e saída

```text
Meu Drive/
└── Projetos/
    └── Segmentacao_Breno/
        ├── Area1/                   # dez arquivos de entrada
        └── outputs/                 # pasta de organização, não referenciada automaticamente
```

No notebook original **não existe variável `DATA_DIR`**. Os caminhos de entrada aparecem diretamente nas células. Os arquivos `polygons.json`, `polygons_arvores.json`, `features_stack.tif` e `arvores_segmentadas.json` são gravados com **nomes relativos** e ficam no diretório corrente do Colab, normalmente `/content`, a menos que o ambiente tenha sido configurado de outra forma.

O processamento integral pode consumir bastante memória. Distância 2D a postes não mede proximidade a fios/cabos, e a altura estimada é experimental, não observada.
