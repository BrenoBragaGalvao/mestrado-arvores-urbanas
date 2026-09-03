# Dados do projeto

Os dados geoespaciais usados neste projeto são mantidos fora do repositório por
causa de seu tamanho. No Google Colab, o notebook monta o Google Drive e espera
encontrar os arquivos sob:

```text
MyDrive/
└── mestrado-arvores-urbanas/
    ├── data/
    │   ├── raw/
    │   │   ├── AOI.tif
    │   │   ├── AOI_MULTI.tif
    │   │   ├── AOI.shp
    │   │   ├── Grama.shp
    │   │   ├── Arvores.shp
    │   │   ├── Linhas.shp
    │   │   └── Postes.shp
    │   └── interim/
    └── outputs/
```

## Arquivos de entrada

| Arquivo | Finalidade |
| --- | --- |
| `AOI.tif` | Imagem RGB usada na segmentação e nas visualizações. |
| `AOI_MULTI.tif` | Imagem multiespectral com as bandas RGB e infravermelho próximo. |
| `AOI.shp` | Polígono da área de interesse. |
| `Grama.shp` | Amostras vetoriais da classe grama. |
| `Arvores.shp` | Amostras vetoriais da classe árvore. |
| `Linhas.shp` | Geometrias das linhas de energia. |
| `Postes.shp` | Geometrias dos postes. |

O diretório `data/interim/` recebe artefatos intermediários, como o raster de
atributos. O diretório `outputs/` recebe os resultados vetoriais da execução.
Esses diretórios são criados automaticamente pelo notebook quando necessário.

## Armazenamento e versionamento

Rasters, vetores, modelos treinados, resultados e demais arquivos pesados **não
devem ser versionados no GitHub**. Os arquivos de trabalho devem permanecer no
Google Drive, enquanto este repositório mantém somente código, notebooks,
configuração e documentação. As regras correspondentes estão no `.gitignore`.

## Observação sobre shapefiles

Um shapefile não é composto apenas pelo arquivo `.shp`. Para cada camada, mantenha
no mesmo diretório os arquivos auxiliares com o mesmo nome-base, especialmente:

- `.shx`, com o índice das geometrias;
- `.dbf`, com a tabela de atributos;
- `.prj`, com a definição do sistema de referência;
- `.cpg`, com a codificação de caracteres, quando disponível.

Por exemplo, `AOI.shp`, `AOI.shx`, `AOI.dbf`, `AOI.prj` e `AOI.cpg` devem ser
armazenados juntos em `data/raw/` no Google Drive.
