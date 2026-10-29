# Combinação de Características de Brilho, Bordas e NDVI para Detecção de Árvores Urbanas e Avaliação de Proximidade com Linhas de Energia

**Abordagem orientada a objetos para detecção de árvores urbanas em imagens multiespectrais de alta resolução e análise espacial de proximidade com infraestrutura elétrica.**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)
![Google Colab](https://img.shields.io/badge/Google_Colab-compatível-F9AB00?style=flat-square&logo=googlecolab&logoColor=white)
![Machine Learning](https://img.shields.io/badge/Machine_Learning-Random_Forest-4C72B0?style=flat-square)
![Remote Sensing](https://img.shields.io/badge/Remote_Sensing-multiespectral-5B8C5A?style=flat-square)
![Geospatial Analysis](https://img.shields.io/badge/Geospatial_Analysis-orientada_a_objetos-2A6F97?style=flat-square)
![Status](https://img.shields.io/badge/Status-Em_desenvolvimento-E9A23B?style=flat-square)

## Atualização — experimento da área completa (29/10/2026)

O experimento foi ampliado para uma **área maior da imagem**, mantendo as duas propostas de pesquisa: (1) discriminar árvores e gramíneas por **NDVI + brilho HSV + bordas**, após Quickshift/K-Means; e (2) localizar árvores próximas à infraestrutura elétrica.

**Resultados registrados no notebook recebido (antes da correção do filtro espacial):**

| Indicador | Área completa (29/10/2026) | Experimento inicial |
|---|---:|---:|
| Registros rotulados (pares objeto–rótulo) | **458** | 133 |
| Treinamento | **366** | 106 |
| Teste | **92** | 27 |
| Acurácia global (arredondada) | **0,87** | 0,81 |
| F1 da classe árvore | **0,85** | 0,80 |
| F1 da classe gramínea | **0,88** | 0,83 |

**Esses valores vieram das saídas salvas no notebook fornecido; não foram reexecutados neste commit.** Os conjuntos de teste são distintos e não permitem concluir que o desempenho melhorou de forma estatisticamente comprovada. A coleção de 458 *pares objeto–rótulo* pode incluir múltiplas interseções com um mesmo segmento.

**Arquivos para reprodução:**

- [Notebook organizado da área completa — 2026](Segmentacao_area_completa_2026.ipynb) — use este para os novos experimentos; execução em Google Colab com RAM alta.
- [Registro metodológico e resultados (29/10/2026)](docs/experimento_area_completa_2026-10-29.md).
- [Dados e nomes exatos do lote Area1](data/README.md) — rasters e vetores mantidos no [Google Drive](https://drive.google.com/drive/folders/1hvCcpETqIPc37aNp3oJLVFTss3nejCdf).
- [Notebook anterior](Segmentacao_classificacao.ipynb) — preservado como registro da etapa inicial.

**Limites da proposta 2:** a versão de dados recebida contém **postes**, mas não linhas/cabos; portanto, a análise efetivamente implementada é de *proximidade a postes* em 1, 3 e 5 metros. O notebook organizado corrige o filtro para levar à alometria **somente segmentos classificados como árvore**; os quantitativos de proximidade exigem reexecução após a correção. A relação área–altura C3 permanece **empírica, sem validação de campo**.

## Visão geral

A proximidade entre vegetação arbórea e redes de distribuição de energia pode favorecer interferências na infraestrutura, interrupções do fornecimento e riscos à segurança. O acompanhamento dessas áreas é, portanto, relevante para orientar inspeções, manejo e planejamento preventivo.

Levantamentos de campo, inspeções aéreas e aquisições LiDAR podem fornecer informações detalhadas, mas envolvem custos, logística e restrições operacionais que dificultam sua aplicação frequente em grandes áreas. Neste contexto, imagens multiespectrais de alta resolução constituem uma fonte complementar para localizar e caracterizar a vegetação urbana.

O projeto investiga uma abordagem orientada a objetos: a imagem é segmentada em regiões espacialmente coerentes e cada objeto é descrito por características espectrais, radiométricas e estruturais.

Além de apoiar a discriminação entre árvores e gramíneas, essa representação conserva polígonos georreferenciados, possibilitando o cálculo da área da copa, uma estimativa empírica da altura e a análise de proximidade com linhas de energia.

## Propostas de pesquisa

- **Proposta 1:** combinar NDVI + brilho + bordas para distinguir árvores e gramíneas.
- **Proposta 2:** localizar árvores em proximidade com a rede elétrica.

## Contribuições metodológicas

As propostas abaixo representam a **contribuição metodológica investigada** e os **elementos de originalidade da abordagem**. Sua avaliação comparativa ainda está em desenvolvimento; portanto, não se pressupõe superioridade em relação a outros métodos.

### Combinação complementar de características

A descrição dos objetos integra fontes de informação complementares:

- **NDVI:** informação espectral associada à resposta da vegetação;
- **brilho HSV:** informação radiométrica derivada da intensidade;
- **bordas de Canny:** informação estrutural relacionada à ocorrência de bordas no interior dos objetos.

O trabalho **não propõe um novo índice espectral**. A investigação concentra-se na combinação dessas características já estabelecidas para discriminar classes de vegetação em uma unidade de análise orientada a objetos.

### Estratégia híbrida

- **K-Means:** realiza a pré-seleção não supervisionada de objetos candidatos à vegetação;
- **Random Forest:** executa a classificação supervisionada dos candidatos em **árvore** ou **gramínea**.

Essa organização busca reduzir o espaço inicial de análise antes da classificação, sem antecipar conclusões sobre ganhos de desempenho.

### Preservação da geometria

Os objetos permanecem representados como polígonos georreferenciados ao longo do fluxo. Essa estrutura permite realizar:

- cálculo da área da copa;
- estimativa empírica da altura;
- interseção espacial;
- cálculo de distância;
- análise de proximidade com linhas de energia e postes.

## Fluxo metodológico

<p align="center">
  <img src="docs/pipeline_17_etapas.png" alt="Fluxo detalhado das 17 etapas da metodologia" width="100%">
</p>

<p align="center">
  <em>Figura — Fluxo detalhado das 17 etapas da metodologia proposta, desde a preparação dos dados e segmentação dos objetos até a classificação árvore–gramínea, estimativa empírica da altura e avaliação de proximidade com a infraestrutura elétrica.</em>
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

## Fundamentação alométrica e estimativa empírica da altura

A fundamentação alométrica foi inspirada nos modelos **crown width–tree height (CW–H)** avaliados por Chatziathanasiou, Kitikidou e Milios (2024). O artigo testa diferentes formas de regressão entre largura da copa e altura total da árvore e inclui, entre elas, o modelo potencial:

$$
\widehat{CW}=b_0H^{b_1}
$$

No presente projeto, a segmentação fornece a **área projetada da copa** dos objetos, e não uma largura de copa medida em campo. Por isso, a forma funcional potencial foi **adaptada empiricamente** para relacionar a área do objeto a uma estimativa de altura:

$$
\widehat{H}=aA^b
$$

O notebook explora diferentes pares de coeficientes e formas linear/potencial. A configuração atualmente adotada no fluxo é a **C3**, com:

- **a = 2,5**;
- **b = 0,4**.

Assim, a relação utilizada no fluxo atual é:

$$
\widehat{H}=2{,}5A^{0{,}4}
$$

em que:

- **A** representa a área projetada do objeto/copa;
- **H estimado** representa uma estimativa empírica da altura;
- **2,5** e **0,4** são os coeficientes da configuração C3 adotada no experimento atual.

> **Importante:** a equação apresentada acima **não foi publicada diretamente por Chatziathanasiou et al. (2024)**. O artigo fornece a fundamentação para a relação alométrica CW–H e para o uso de uma forma funcional potencial. A transformação **área da copa → altura estimada** e os coeficientes **2,5** e **0,4** correspondem a uma adaptação experimental deste projeto e ainda precisam de validação independente com alturas reais medidas em campo.

A descrição detalhada das configurações testadas e da fundamentação está em [`docs/allometria.md`](docs/allometria.md).

### Referência da fundamentação alométrica

**Chatziathanasiou, S.; Kitikidou, K.; Milios, E.** Crown Width–Tree Height Models for *Magnolia grandiflora*, *Prunus cerasifera*, and *Acer negundo* Growing in Cities in Northeastern Greece. *Land*, 2024, 13, 1579. DOI: `10.3390/land13101579`.

## Critério de seleção

Após a estimativa empírica da altura, foi utilizado o seguinte critério operacional:

$$
\widehat{H}>7\,m
$$

Dessa forma, somente os objetos classificados como árvore e com **altura estimada superior a 7 m** seguem para a análise de proximidade com a infraestrutura elétrica.

O limiar de **7 m** funciona como um **critério operacional de seleção** dentro do fluxo metodológico atual.

## Análise de proximidade

As árvores selecionadas são sobrepostas aos dados vetoriais da infraestrutura elétrica:

- `Linhas.shp` — linhas de energia, **não incluídas no lote Area1 de 29/10/2026**;
- `postes.gpkg` — geometria dos postes **efetivamente utilizada no experimento atual**.

A análise espacial considera:

- interseção com a infraestrutura;
- distância de até **1 m**;
- distância de até **3 m**;
- distância de até **5 m**.

A análise é realizada em **duas dimensões**, considerando a geometria projetada dos objetos.

## Resultados do experimento inicial (histórico)

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

A segmentação inicial (não a da área completa de 29/10/2026) produziu **15.633 objetos**, dos quais **3.002** foram selecionados como candidatos à vegetação.

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
- validar a relação área da copa–altura com alturas reais medidas em campo e métricas como **RMSE, MAE e R²**.

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
| 📓 `Segmentacao_area_completa_2026.ipynb` | **Notebook atualizado** para reproduzir o experimento com a área completa |
| 📓 `Segmentacao_classificacao.ipynb` | Notebook anterior, mantido para histórico |
| 🖼️ `docs/pipeline_17_etapas.png` | Fluxo visual detalhado das 17 etapas |
| 📐 `docs/allometria.md` | Fundamentação, adaptação e configurações da relação alométrica |
| 📊 `docs/experimento_area_completa_2026-10-29.md` | Métricas, parâmetros e limites do experimento atualizado |
| 📦 `requirements-colab.txt` | Dependências do ambiente |
| 📘 `README.md` | Documentação principal |
| 🚫 `.gitignore` | Arquivos não versionados |
| 📂 `data/README.md` | Orientações sobre os dados |

O **GitHub** concentra o código e a documentação versionados, enquanto o **Google Drive** armazena os dados geoespaciais pesados e os produtos do processamento. Essa separação evita incorporar arquivos volumosos ao histórico do repositório.

## Dados e armazenamento

Os rasters e arquivos vetoriais do lote **Area1** não são versionados devido ao tamanho. Eles estão na pasta do [Google Drive fornecido pelo autor](https://drive.google.com/drive/folders/1hvCcpETqIPc37aNp3oJLVFTss3nejCdf), além do ZIP encaminhado em 29/10/2026. Consulte [`data/README.md`](data/README.md) para lista e instruções.

### Como executar o notebook atualizado no Colab

1. Obtenha a pasta `Area1` no Drive ou extraia o ZIP enviado (mantendo os 10 arquivos na mesma pasta).
2. No Google Drive da sessão do Colab, mantenha-a em `MyDrive/Projetos/Segmentacao_Breno/Area1/` ou ajuste a variável `DATA_DIR` no notebook.
3. Abra [`Segmentacao_area_completa_2026.ipynb`](Segmentacao_area_completa_2026.ipynb) no Google Colab e autorize a montagem do Drive.
4. Execute as células na ordem. Prefira uma sessão com RAM alta; o processamento da área inteira pode ser demorado.
5. Consulte os relatórios de classificação impressos e os arquivos criados em `MyDrive/Projetos/Segmentacao_Breno/outputs/`.
6. Registre os novos resultados após a correção do filtro espacial e compare-os com os valores históricos, considerando as limitações científicas descritas.

**Importante:** as áreas (m²) e distâncias (m) pressupõem um CRS projetado métrico (neste lote, EPSG:31982). A imagem RGB e a multiespectral têm pequeno deslocamento entre transformações; revise o alinhamento em análises de alta precisão.

## Status do projeto

> **Em desenvolvimento.** A metodologia, os experimentos comparativos e a validação estão sendo aprimorados no contexto da pesquisa de mestrado.

Os resultados apresentados atualmente devem ser considerados **preliminares**.

## Autor

**Breno Braga Galvão**

Projeto desenvolvido no contexto de pesquisa acadêmica de mestrado.
