# Árvores urbanas: segmentação, classificação e proximidade com infraestrutura elétrica

**Pesquisa de mestrado — Breno Braga Galvão** | Python • Google Colab • Sensoriamento remoto • GeoPandas • Machine Learning

> **Status:** metodologia em desenvolvimento, resultados preliminares. Este repositório mantém **somente o código atual, documentação e diagrama metodológico**. Os dados geoespaciais volumosos permanecem no Google Drive.

## Objetivos da pesquisa

**Proposta 1 — Identificar e caracterizar árvores urbanas.** Segmentar imagens de alta resolução, identificar objetos vegetados e distinguir **árvores de gramíneas** usando **NDVI, brilho HSV e bordas de Canny**, com **K-Means** e **Random Forest**. Preservar polígonos para calcular a área projetada das copas.

**Proposta 2 — Analisar a proximidade das árvores com a infraestrutura elétrica.** Selecionar árvores por uma **estimativa empírica de altura** e calcular sua proximidade com **postes** em 1 m, 3 m e 5 m. A avaliação de proximidade com **linhas/cabos de energia** é uma etapa futura, pois o conjunto Area1 atual não contém essas geometrias.

## Comece por aqui

| Arquivo | Finalidade |
|---|---|
| **[`Segmentacao_area_completa_2026.ipynb`](Segmentacao_area_completa_2026.ipynb)** | **Notebook principal e único**, preparado para Google Colab |
| [`data/README.md`](data/README.md) | Arquivos geoespaciais exigidos, estrutura da pasta `Area1` e CRS |
| [`docs/experimento_area_completa_2026-10-29.md`](docs/experimento_area_completa_2026-10-29.md) | Registro da rodada de outubro: parâmetros, resultados e limitações |
| [`docs/allometria.md`](docs/allometria.md) | Fundamentação e limites da estimativa experimental da altura |
| [`docs/pipeline_17_etapas.png`](docs/pipeline_17_etapas.png) | Diagrama conceitual das 17 etapas, **não** imagem da área antiga |
| [`requirements-colab.txt`](requirements-colab.txt) | Bibliotecas necessárias |
| `.gitignore` | Evita a publicação de rasters, GeoPackages, saídas e arquivos temporários |

O notebook anterior foi retirado da árvore atual de arquivos para evitar confusão. **Seu histórico continua recuperável pelos commits antigos do Git.**

## Como executar no Google Colab

1. Abra o **[notebook principal](Segmentacao_area_completa_2026.ipynb)** no Google Colab.
2. Tenha no seu Google Drive a pasta `Area1`, com os arquivos do [Drive do projeto](https://drive.google.com/drive/folders/1hvCcpETqIPc37aNp3oJLVFTss3nejCdf), ou extraia nela o ZIP recebido. Um link compartilhado isolado **não monta automaticamente os arquivos no Colab**: adicione um atalho para a pasta no *Meu Drive* ou copie os arquivos para sua estrutura.
3. Por padrão, o notebook espera os dados no seguinte caminho (altere a variável `DATA_DIR` se necessário):

   ```text
   MyDrive/Projetos/Segmentacao_Breno/
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

4. Execute as células **na ordem**. Prefira um ambiente com **RAM alta**: a imagem integral tem cerca de **50,6 milhões de pixels** e a segmentação Quickshift pode consumir muitos recursos.
5. Verifique os arquivos na pasta `outputs/`: `features_stack.tif`, `matriz_confusao.png`, `metricas_classificacao.json`, `arvores_estimadas_maiores_7m.gpkg`, `resumo_proximidade_postes.csv` e GeoPackages de proximidade quando houver resultados.

**Verificações realizadas:** teste técnico com recorte real de **1.024 × 1.024 pixels** para Quickshift, K-Means, rótulos, NDVI, brilho, Canny e Random Forest. **Ainda não foi executado o notebook completo na imagem integral**; não se afirma que toda a rotina terminou no Colab. O notebook já trata alguns casos de resultados vazios e processa as características em blocos para economizar memória.

## Fluxo metodológico (17 etapas)

![Diagrama conceitual do fluxo de 17 etapas](docs/pipeline_17_etapas.png)

O diagrama é uma **visão metodológica geral**. Eventuais referências a linhas de energia representam o objetivo amplo da pesquisa; o **experimento Area1 implementa apenas a análise espacial de postes**.

| Etapas | Procedimentos |
|---|---|
| 1–3 | Ler RGB, multiespectral e área de interesse; aplicar Quickshift; gerar polígonos |
| 4–6 | Extrair estatísticas RGB/NIR por objeto, aplicar K-Means de seis clusters e selecionar candidatos à vegetação |
| 7–10 | Associar rótulos de árvores e gramíneas, preparar NDVI, brilho HSV e bordas Canny |
| 11–12 | Treinar Random Forest (500 árvores), validar e classificar os segmentos |
| 13–15 | Calcular a área das copas, estimar empiricamente a altura e selecionar objetos acima de 7 m |
| 16–17 | Sobrepor árvores selecionadas e postes e avaliar proximidades de 1, 3 e 5 metros |

### Ajustes na versão principal

- Cálculo de NDVI, brilho e bordas em **blocos**, reduzindo o pico de memória na etapa de características.
- Deduplicação de amostras: **um rótulo por segmento**, descartando segmentos com rótulos conflitantes. Isso evita a repetição de um mesmo objeto nos conjuntos de treino e teste.
- Separação treino/teste **estratificada por classe** (80%/20%, `random_state=42`).
- A etapa espacial recebe **somente segmentos previstos como árvore**.
- Resultados e visualizações são salvos no **Drive**, não enviados ao repositório.
- O código não tenta analisar linhas de transmissão/distribuição ausentes dos dados.

A escolha do **cluster 3** como candidato à vegetação foi preservada do experimento original. Esse número é circunstancial e exige inspeção a cada nova base; o rótulo de um cluster não tem significado fixo.

## Resultados preliminares documentados

Os valores a seguir vieram das **saídas salvas no notebook fornecido em outubro de 2026**, antes dos ajustes de deduplicação e processamento da versão atual. **Não são os resultados de uma nova execução do notebook publicado agora.**

| Métrica | Experimento inicial | Experimento com área maior (arquivo recebido) |
|---|---:|---:|
| Registros rotulados (pares objeto–rótulo) | 133 | **458** |
| Amostras de treinamento | 106 | **366** |
| Amostras de teste | 27 | **92** |
| Acurácia arredondada | 0,81 | **0,87** |
| F1 da classe árvore | 0,80 | **0,85** |
| F1 da classe gramínea | 0,83 | **0,88** |

**Cautela na interpretação:** os conjuntos de teste diferem; portanto, esses resultados **não demonstram, por si só, um ganho estatisticamente comprovado**. O experimento original contou pares objeto–rótulo, que podem se repetir para um mesmo segmento. Como o notebook principal atual deduplica os objetos e usa divisão estratificada, as métricas obtidas na próxima execução podem diferir das apresentadas acima.

## Alometria e proximidade

A relação usada para estimar altura é a configuração **C3**:

```text
altura_estimada_m = 2.5 * area_m2 ** 0.4
```

Selecionam-se objetos classificados como **árvore** com altura estimada **maior que 7 m** para a análise de proximidade espacial.

Essa equação é **uma adaptação empírica experimental do projeto** inspirada na literatura de relações entre altura e dimensão da copa. **Não** é uma fórmula publicada literalmente na fonte referenciada e **não** foi validada com alturas medidas em campo. Veja [`docs/allometria.md`](docs/allometria.md).

A distância entre a copa e o **poste** é calculada em **2D**, no CRS métrico das imagens (**EPSG:31982**). Isso **não** prova interferência em cabos nem classifica risco elétrico operacional.

## Dados e boas práticas

O conjunto `Area1` contém rasters RGB e RGB+NIR, os componentes de `AOI_new.shp`, pontos rotulados em `Arvores.gpkg` e `Grama.gpkg` e a camada `postes.gpkg`. Não contém `Linhas.shp`. Os vetores de árvores, gramíneas e postes estão em **EPSG:4674** na origem e são reprojetados para **EPSG:31982** nas etapas métricas.

Os rasters de entrada têm **0,5 m/pixel**. As origens das grades RGB e multiespectral diferem ligeiramente; aplicações que exijam grande precisão devem verificar o alinhamento antes de interpretar valores por objeto.

**Não subir ao GitHub:** arquivos `.tif`, `.gpkg`, `.shp`, ZIP dos dados ou produtos pesados. Eles continuam no [Google Drive](https://drive.google.com/drive/folders/1hvCcpETqIPc37aNp3oJLVFTss3nejCdf), respeitando o controle de acesso dos respectivos proprietários.

## Próximas etapas científicas

Ampliar o número de experimentos e bases reais, comparar métodos (por exemplo SVM e outros classificadores), realizar testes de ablação das três características, adotar validação espacial independente e verificar a estimativa de altura com medições reais (MAE, RMSE e R²). Fortalecer a revisão de literatura para explicitar quais lacunas a abordagem busca preencher.

---

**Autor:** Breno Braga Galvão • Pesquisa acadêmica em desenvolvimento.
