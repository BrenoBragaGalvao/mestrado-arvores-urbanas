# Combinação de Características de Brilho, Bordas e NDVI para Detecção de Árvores Urbanas e Avaliação de Proximidade com Linhas de Energia

**Abordagem orientada a objetos para detecção de árvores urbanas em imagens multiespectrais de alta resolução e análise espacial de proximidade com infraestrutura elétrica.**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)
![Google Colab](https://img.shields.io/badge/Google_Colab-compatível-F9AB00?style=flat-square&logo=googlecolab&logoColor=white)
![Machine Learning](https://img.shields.io/badge/Machine_Learning-Random_Forest-4C72B0?style=flat-square)
![Remote Sensing](https://img.shields.io/badge/Remote_Sensing-multiespectral-5B8C5A?style=flat-square)
![Geospatial Analysis](https://img.shields.io/badge/Geospatial_Analysis-orientada_a_objetos-2A6F97?style=flat-square)
![Status](https://img.shields.io/badge/Status-Em_desenvolvimento-E9A23B?style=flat-square)

## Visão geral

A proximidade entre vegetação arbórea e redes de distribuição de energia pode favorecer interferências na infraestrutura, interrupções do fornecimento e riscos à segurança. O acompanhamento dessas áreas é, portanto, relevante para orientar inspeções, manejo e planejamento preventivo.

Levantamentos de campo, inspeções aéreas e aquisições LiDAR podem fornecer informações detalhadas, mas envolvem custos, logística e restrições operacionais que dificultam sua aplicação frequente em grandes áreas. Neste contexto, imagens multiespectrais de alta resolução constituem uma fonte complementar para localizar e caracterizar a vegetação urbana.

O projeto investiga uma abordagem orientada a objetos: a imagem é segmentada em regiões espacialmente coerentes e cada objeto é descrito por características espectrais, radiométricas e estruturais.

Além de apoiar a discriminação entre árvores e gramíneas, essa representação conserva polígonos georreferenciados, possibilitando o cálculo da área da copa, a estimativa empírica da altura e a análise de proximidade com linhas de energia.

## Propostas de pesquisa

- **Proposta 1:** combinar NDVI + brilho + bordas para distinguir árvores e gramíneas.
- **Proposta 2:** localizar árvores em proximidade com a rede elétrica.

## Contribuições metodológicas

As propostas abaixo representam a **contribuição metodológica investigada** e os **elementos de originalidade da abordagem**.

Sua avaliação comparativa ainda está em desenvolvimento; portanto, não se pressupõe superioridade em relação a outros métodos.

### Combinação complementar de características

A descrição dos objetos integra fontes de informação complementares:

- **NDVI:** informação espectral associada à resposta da vegetação;
- **brilho HSV:** informação radiométrica derivada da intensidade;
- **bordas de Canny:** informação estrutural relacionada à ocorrência de bordas no interior dos objetos.

O trabalho **não propõe um novo índice espectral**.

A investigação concentra-se na combinação dessas características já estabelecidas para discriminar classes de vegetação em uma unidade de análise orientada a objetos.

### Estratégia híbrida

- **K-Means:** realiza a pré-seleção não supervisionada de objetos candidatos à vegetação;
- **Random Forest:** executa a classificação supervisionada dos candidatos em **árvore** ou **gramínea**.

Essa organização busca reduzir o espaço inicial de análise antes da classificação, sem antecipar conclusões sobre ganhos de desempenho.

### Preservação da geometria

Os objetos permanecem representados como polígonos georreferenciados ao longo do fluxo.

Essa estrutura permite realizar:

- cálculo da área da copa;
- estimativa empírica da altura;
- interseção espacial;
- cálculo de distância;
- análise de proximidade com linhas de energia e postes.

## Fluxo metodológico

<p align="center">
  <img src="docs/pipeline_17_etapas.webp" alt="Fluxo detalhado das 17 etapas da metodologia" width="100%">
</p>

<p align="center">
  <em>Figura — Fluxo detalhado das 17 etapas da metodologia proposta, desde a preparação dos dados e segmentação dos objetos até a classificação árvore–gramínea, estimativa da altura e avaliação de proximidade com a infraestrutura elétrica.</em>
</p>

O processamento foi organizado em **17 etapas encadeadas**:

1. preparação dos dados RGB, RGB–NIR e vetoriais;
2. segmentação da imagem por **Quickshift**;
3. conversão dos segmentos em polígonos georreferenciados;
4. cálculo de estatísticas espectrais RGB–NIR por objeto;
5. agrupamento não supervisionado por **K-Means** em 6 clusters;
6. seleção do agrupamento associado à vegetação;
7. associação das amostras rotuladas de **árvores** e **gramíneas**;
8. cálculo das características adicionais: **NDVI, brilho HSV e bordas de Canny**;
9. composição da pilha de características;
10. construção da tabela de treinamento;
11. treinamento e validação do **Random Forest com 500 árvores de decisão**;
12. classificação dos candidatos em **árvore** ou **gramínea**;
13. seleção dos objetos classificados como árvore e cálculo da área da copa;
14. estimativa empírica da altura a partir da área da copa;
15. seleção das árvores com altura estimada superior a **7 m**;
16. sobreposição das árvores selecionadas com linhas de energia e postes;
17. análise de interseção e proximidade em distâncias de **1 m, 3 m e 5 m**.

## Estimativa empírica da altura

Após a classificação pelo Random Forest, apenas os objetos classificados como **árvore** seguem para a etapa de análise espacial.

Inicialmente é calculada a área da copa de cada objeto. Em seguida, essa área é utilizada na relação empírica:

$$
\widehat{H} = 2{,}5A^{0{,}4}
$$

em que:

- **A** representa a área da copa;
- **\(\widehat{H}\)** representa a altura estimada.

A relação estabelece uma estimativa empírica da altura a partir da área da copa.

Ela não representa uma medição direta realizada em campo.

## Critério de seleção

Após a estimativa da altura, foi utilizado o seguinte critério:

$$
\widehat{H} > 7\,m
$$

Dessa forma, somente os objetos classificados como árvore e com **altura estimada superior a 7 m** seguem para a análise de proximidade com a infraestrutura elétrica.

O limiar de 7 m funciona como um **critério operacional de seleção** dentro do fluxo metodológico atual.

## Análise de proximidade

As árvores selecionadas são sobrepostas aos dados vetoriais da infraestrutura elétrica:

- `Linhas.shp` — linhas de energia;
- `Postes.shp` — referência cartográfica dos postes.

A análise espacial considera:

- interseção com a infraestrutura;
- distância de até **1 m**;
- distância de até **3 m**;
- distância de até **5 m**.

A análise é realizada em **duas dimensões**, considerando a geometria projetada dos objetos.

## Resultados atuais

> **Resultados do experimento inicial atualmente documentado.**

| Indicador | Valor |
| --- | ---: |
| Objetos segmentados | 15.633 |
| Candidatos à vegetação | 3.002 |
| Objetos rotulados | 133 |
| Treinamento | 106 |
| Teste | 27 |
| Acurácia global | 0,81 |

### Desempenho por classe

| Classe | Precisão | Recall | F1-score |
| --- | ---: | ---: | ---: |
| Árvores | 0,83 | 0,77 | 0,80 |
| Gramíneas | 0,80 | 0,86 | 0,83 |

A segmentação inicial produziu **15.633 objetos**, dos quais **3.002** foram selecionados como candidatos à vegetação.

O conjunto rotulado utilizado no experimento inicial possui **133 objetos**, sendo **106 destinados ao treinamento** e **27 ao teste**.

A configuração inicial utilizando **NDVI + brilho HSV + bordas de Canny** apresentou **acurácia global de 81%** no conjunto de teste.

Esses valores descrevem apenas o experimento inicial e não devem ser interpretados como avaliação conclusiva da metodologia.

## Próximas etapas

As próximas etapas da pesquisa incluem:

- ampliar a quantidade de testes e experimentos;
- comparar os resultados com outras técnicas de classificação;
- utilizar novos conjuntos de dados reais para validação;
- ampliar a revisão bibliográfica, identificando limitações e lacunas dos métodos existentes;
- buscar bases de dados públicas e dados utilizados em outros trabalhos para ampliar os experimentos;
- avaliar separadamente a contribuição das características NDVI, brilho HSV e bordas de Canny;
- comparar configurações **RGB** e **RGB + NIR**;
- comparar o **Random Forest** com outros classificadores, como **SVM**;
- aplicar estratégias de validação mais robustas;
- validar a relação utilizada para estimativa da altura.

O objetivo dessas etapas é fortalecer a validação experimental e demonstrar de forma comparativa onde a abordagem proposta contribui em relação às técnicas existentes.

## Tecnologias

| Área | Tecnologias |
| --- | --- |
| Linguagem | Python |
| Execução | Google Colab |
| Rasters | Rasterio |
| Dados vetoriais | GeoPandas, Shapely |
| Processamento | NumPy, Pandas |
| Imagens | scikit-image |
| Machine Learning | scikit-learn |
| Visualização | Matplotlib, Seaborn |
| Versionamento | GitHub + Codex |
| Dados pesados | Google Drive |

As dependências do ambiente estão registradas em [`requirements-colab.txt`](requirements-colab.txt).

## Estrutura do projeto

| Item | Finalidade |
| --- | --- |
| 📓 `Segmentacao_classificacao.ipynb` | Notebook principal da metodologia |
| 🖼️ `docs/pipeline_17_etapas.webp` | Fluxo visual detalhado das 17 etapas |
| 📦 `requirements-colab.txt` | Dependências do ambiente |
| 📘 `README.md` | Documentação principal |
| 🚫 `.gitignore` | Arquivos não versionados |
| 📂 `data/README.md` | Orientações sobre os dados |

O **GitHub** concentra o código e a documentação versionados, enquanto o **Google Drive** armazena os dados geoespaciais pesados e os produtos do processamento.

Essa separação evita incorporar arquivos volumosos ao histórico do repositório.

## Dados e armazenamento

Estrutura esperada no Google Drive:

```text
MyDrive/
└── mestrado-arvores-urbanas/
    ├── data/
    │   ├── raw/
    │   └── interim/
    └── outputs/