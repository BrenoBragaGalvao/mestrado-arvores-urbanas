# Árvores urbanas: segmentação, classificação e proximidade de postes

**Pesquisa de mestrado — Breno Braga Galvão**  
Python • Google Colab • Sensoriamento remoto • GeoPandas • Aprendizado de máquina

> **Situação (29/10/2026):** o notebook principal é a versão original fornecida pelo autor, restaurada no GitHub com **116 células (85 de código e 31 de texto)**. A execução integral atual da imagem real ainda precisa ser confirmada. Este README descreve o **código realmente presente** no repositório, e não a antiga versão simplificada.

## Comece pelo notebook

- [**Abrir `Segmentacao_area_completa.ipynb` no Google Colab](https://colab.research.google.com/github/BrenoBragaGalvao/mestrado-arvores-urbanas/blob/main/Segmentacao_area_completa.ipynb)
- [Consultar o notebook no GitHub](Segmentacao_area_completa.ipynb)
- [Original completo no Google Drive](https://drive.google.com/file/d/1TIgMWSOGHENy9nkiaG5b1BcFKA5f5d_i/view) — preserva também as imagens e saídas ricas das execuções anteriores. A cópia do GitHub preserva todas as células de código e texto e as saídas textuais, mas não as imagens/HTML históricos incorporados.

**Importante:** abrir o notebook pelo link do GitHub carrega uma cópia no Colab. Executar ou editar células não envia automaticamente alterações ou resultados de volta ao GitHub.

## Objetivos

1. **Identificar árvores e gramíneas:** segmentar a imagem RGB em objetos, utilizar características espectrais e de textura e classificar os segmentos com Random Forest.
2. **Estudar a proximidade com postes:** estimar experimentalmente uma medida de altura a partir da área projetada dos polígonos e analisar distâncias planimétricas de 1, 3 e 5 metros até os postes.

A base atual **contém postes, não geometrias de cabos/linhas de energia**. A proximidade calculada não equivale à interferência comprovada na rede elétrica.

## Dados e execução no Colab

Os dados reais **não estão no GitHub**. Estão no [Google Drive, pasta `Area1`](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6) e o código original utiliza caminhos **absolutos**, no formato:

```text
/content/drive/MyDrive/Projetos/Segmentacao_Breno/
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
└── outputs/                 # criada para organização; não usada automaticamente pelo código
```

Para executar:

1. Abra o [notebook do GitHub no Colab](https://colab.research.google.com/github/BrenoBragaGalvao/mestrado-arvores-urbanas/blob/main/Segmentacao_area_completa.ipynb).
2. Conecte seu Google Drive com a célula já existente `drive.mount('/content/drive')`.
3. Verifique as bibliotecas necessárias em [`requirements-colab.txt`](requirements-colab.txt); o notebook instala `rasterio` na primeira célula e usa também `seaborn` para alguns gráficos. O arquivo de requisitos é uma referência e **não é instalado automaticamente** quando o notebook é aberto pelo GitHub.
4. Execute as células na ordem. A imagem inteira tem cerca de 50,6 milhões de pixels; a segmentação Quickshift e a criação de arrays completos podem exigir **RAM alta**.

**Onde ficam as saídas?** O notebook original escreve `polygons.json`, `polygons_arvores.json`, `features_stack.tif` e `arvores_segmentadas.json` usando **caminhos relativos**. Assim, eles vão para o diretório de trabalho da sessão Colab (normalmente `/content`), **não automaticamente** para `Segmentacao_Breno/outputs`. Arquivos locais do ambiente Colab podem desaparecer ao encerrar a sessão. O notebook apresenta gráficos e relatórios na própria saída das células.

Veja [`data/README.md`](data/README.md) para descrição dos arquivos e dos sistemas de coordenadas.

## Etapas efetivamente presentes no código

1. Abrir imagem RGB e AOI; segmentar com **Quickshift** (`kernel_size=3`, `max_dist=5`, `ratio=0.04`) e criar polígonos.
2. Extrair médias e desvios-padrão das bandas RGB/NIR para os polígonos; executar **K-Means de 6 grupos** (`random_state=42`, `n_init=10`) e prosseguir com o **cluster 3**. O número do cluster é específico da execução e requer inspeção antes de generalizar.
3. Associar rótulos de `Arvores.gpkg` e `Grama.gpkg` por interseção espacial; extrair **NDVI, brilho HSV e bordas Canny**.
4. Dividir as amostras em **80% treino / 20% teste**, `random_state=42`, **sem estratificação e sem etapa explícita de deduplicação**; treinar **Random Forest de 500 árvores** e apresentar relatório de classificação e matriz de confusão.
5. Classificar os segmentos candidatos, calcular suas áreas e experimentar **seis configurações (C1–C6)** de modelos potencial e linear para a estimativa de altura.
6. Usar a configuração potencial **C3: `2.5 * area ** 0.4`**, selecionar objetos com valor estimado **acima de 7 m**, carregar os postes e realizar junções de proximidade a **1, 3 e 5 m**.

**Atenção metodológica:** no código original, o filtro espacial por C3 e 7 m **não inclui** a condição `predicted_classe == 'arvore'`. Portanto, objetos que receberam previsão `grama` podem passar para a análise de proximidade. Também **não há** processamento em blocos: as imagens são trabalhadas integralmente em memória. Estas características estão documentadas aqui, **sem alteração do notebook**.

O [diagrama das 17 etapas](docs/pipeline_17_etapas.png) é **conceitual**; não deve ser tratado como garantia de correspondência literal com todas as células do notebook original.

## Resultados anteriores e limites de interpretação

| Indicador | Execução antiga | Saída histórica do notebook fornecido |
|---|---:|---:|
| Registros rotulados (pares objeto–rótulo) | 133 | 458 |
| Treino | 106 | 366 |
| Teste | 27 | 92 |
| Acurácia arredondada | 0,81 | 0,87 |
| F1 árvore | 0,80 | 0,85 |
| F1 gramínea | 0,83 | 0,88 |

Os números da última coluna foram **extraídos de saídas históricas já salvas** no arquivo fornecido; **não representam a execução que está acontecendo agora no Colab**. A união espacial de segmentos com rótulos pode produzir múltiplos registros do mesmo objeto, e os conjuntos de avaliação das duas rodadas são diferentes. Não se deve interpretar a diferença de acurácia como ganho experimental comprovado.

A relação de altura **C3 é empírica e ainda não validada com medições reais**. Veja [`docs/allometria.md`](docs/allometria.md) e o [registro do experimento de 29/10/2026](docs/experimento_area_completa_2026-10-29.md). A análise de distância é bidimensional em CRS métrico e não demonstra risco elétrico.

## Documentação e versionamento

| Item | Função |
|---|---|
| [`Segmentacao_area_completa.ipynb`](Segmentacao_area_completa.ipynb) | Notebook original de 116 células, usado para execução |
| [`data/README.md`](data/README.md) | Dados necessários, CRS e localização |
| [`docs/allometria.md`](docs/allometria.md) | Discussão e limitações da estimativa experimental de altura |
| [`docs/experimento_area_completa_2026-10-29.md`](docs/experimento_area_completa_2026-10-29.md) | Registro metodológico e resultados históricos |
| [`docs/pipeline_17_etapas.png`](docs/pipeline_17_etapas.png) | Diagrama conceitual |
| [`requirements-colab.txt`](requirements-colab.txt) | Bibliotecas utilizadas |
| [`.gitignore`](.gitignore) | Exclui do versionamento dados geoespaciais grandes, resultados e temporários |

Os diretórios de testes sintéticos e do GitHub Actions **foram removidos**; não há testes automáticos configurados no estado atual do repositório. A aprovação histórica desses testes de uma versão anterior **não valida** o notebook original nem a execução integral da imagem atual.

Os arquivos `.tif`, `.gpkg`, `.shp` e outros produtos grandes devem continuar no Google Drive, não no GitHub.

**Autor:** Breno Braga Galvão • Pesquisa acadêmica em desenvolvimento.
