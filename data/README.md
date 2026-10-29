# Dados geoespaciais — experimento Area1 (29/10/2026)

Este repositório **não armazena** os arquivos raster e GeoPackage, devido ao tamanho e ao versionamento. O material foi fornecido pelo autor em um ZIP e na seguinte [pasta compartilhada no Google Drive](https://drive.google.com/drive/folders/1hvCcpETqIPc37aNp3oJLVFTss3nejCdf).

## Arquivos presentes no ZIP

| Arquivo | Papel no processamento |
|---|---|
| `Area1/AOI_RGB_NEW.tif` | Imagem RGB para segmentação Quickshift |
| `Area1/AOI_NEW_MULTI.tif` | Imagem multiespectral RGB + NIR para características |
| `Area1/AOI_new.shp` | Polígono da área de interesse |
| `Area1/AOI_new.shx` | Índice das geometrias do shapefile |
| `Area1/AOI_new.dbf` | Atributos do shapefile |
| `Area1/AOI_new.prj` | Referência espacial do shapefile |
| `Area1/AOI_new.cpg` | Codificação do shapefile |
| `Area1/Arvores.gpkg` | Polígonos rotulados como árvores |
| `Area1/Grama.gpkg` | Polígonos rotulados como gramíneas |
| `Area1/postes.gpkg` | Camada de postes para análise de proximidade |

**Não há no ZIP arquivo de geometria das linhas/cabos de energia.**

## Requisitos espaciais verificados

- Rasters: **6.942 × 7.294 pixels**, pixel de **0,5 m**, CRS **EPSG:31982**.
- `AOI_new.shp`: **EPSG:31982**.
- `Arvores.gpkg`, `Grama.gpkg` e `postes.gpkg`: **EPSG:4674**, reprojetados no notebook para **EPSG:31982**.
- Raster RGB e multiespectral possuem pequena diferença de origem; para análises de precisão, examine o alinhamento entre grades.

## Preparação no Google Colab

O notebook atualizado [`Segmentacao_area_completa_2026.ipynb`](../Segmentacao_area_completa_2026.ipynb) utiliza por padrão:

```text
MyDrive/
└── Projetos/
    └── Segmentacao_Breno/
        ├── Area1/
        │   ├── AOI_RGB_NEW.tif
        │   ├── AOI_NEW_MULTI.tif
        │   ├── AOI_new.shp
        │   ├── AOI_new.shx
        │   ├── AOI_new.dbf
        │   ├── AOI_new.prj
        │   ├── AOI_new.cpg
        │   ├── Arvores.gpkg
        │   ├── Grama.gpkg
        │   └── postes.gpkg
        └── outputs/
```

Se a pasta estiver em outro lugar, **altere `DATA_DIR`** na primeira célula. O notebook salva a pilha de características e GeoPackages em `outputs/`. Esses produtos também não devem ser enviados ao GitHub.

O processamento da área completa requer bastante memória; execução no Colab com RAM alta é recomendada. Não se deve interpretar altura estimada como altura observada nem proximidade bidimensional ao poste como prova de interferência com cabos energizados.

## Histórico

O experimento inicial utilizava outros nomes de arquivos (`AOI.tif`, `AOI_MULTI.tif`, `Postes.shp`, etc.). **Esses nomes não correspondem ao lote Area1 recebido em 29/10/2026.** O notebook inicial foi mantido no histórico de versionamento; para a nova rodada, use os nomes acima.
