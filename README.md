# Projeto de Mestrado — Identificação de Árvores Urbanas e Análise Exploratória de Porte e Proximidade com a Rede Elétrica

**Pesquisador:** Breno Braga Galvão  
**Área de treinamento:** Area1, Caxias do Sul (RS)  
**Repositório:** `BrenoBragaGalvao/mestrado-arvores-urbanas`  
**Documento:** apresentação científica do projeto — branch `feature/validacao-geografica-externa`  
**Atualização documental:** 20 de novembro de 2026

<a id="resumo"></a>
## Resumo executivo

Esta pesquisa investiga como imagens de sensoriamento remoto podem contribuir para caracterizar a vegetação urbana e produzir indicadores espaciais úteis ao planejamento. O trabalho tem **duas propostas distintas e complementares**:

| Proposta | Pergunta científica | Situação documentada |
|---|---|---|
| **1 — Identificação de árvores e gramíneas** | Um classificador treinado em uma única área consegue discriminar essas duas classes e apresentar concordância com referências automáticas em outras regiões? | **Fase experimental computacional concluída e reproduzida**; validação visual humana independente **pendente** |
| **2 — Porte e proximidade com a rede elétrica** | A geometria dos segmentos, alturas modeladas de dossel e distâncias a postes permitem construir indicadores exploratórios? | **Estudos exploratórios executados**; sem alturas medidas em campo nem demonstração de risco elétrico |

Na **Proposta 1**, a imagem é segmentada por **Quickshift** em janelas de até **256 × 256 pixels**. Os segmentos são descritos por **brilho HSV, bordas Canny e NDVI**. O modelo final escolhido é a **Regressão Logística original**, treinada exclusivamente na Area1 com **510 pontos de referência** (257 árvores e 253 gramíneas), que correspondem a **505 segmentos rotulados únicos**. A avaliação final utiliza blocos espaciais de **500 m**.

### Resultados principais da Proposta 1

| Região | F1-macro médio (30 avaliações) | Desvio-padrão | Procedimento |
|---|---:|---:|---|
| **Area1 — Caxias do Sul** | **0,8421** | 0,0389 | 30 divisões espaciais com ajuste do modelo em cada treino |
| **Sagrada Família — Caxias do Sul** | **0,7584** | 0,0330 | 30 reamostragens de blocos; modelo congelado |
| **Lomba Grande — Novo Hamburgo** | **0,7794** | 0,0337 | 30 reamostragens de blocos; modelo congelado |
| **Cristo Rei — São Leopoldo** | **0,7961** | 0,0377 | 30 reamostragens de blocos; modelo congelado |

![Gráfico das quatro médias de F1-macro, com desvio-padrão e identificação dos protocolos](docs/proposta1_f1_macro_30_avaliacoes_500m.svg)

> **Como ler esses números:** na Area1, os 30 F1 resultam de **30 separações de treinamento e teste**. Nas três regiões externas, são **30 reamostragens dos mesmos pontos e previsões**, mantendo o classificador treinado na Area1. Portanto, **não houve 120 treinamentos nem 120 testes independentes**. Os F1 externos medem **concordância com pseudo-rótulos automáticos do Meta/WRI CHMv2**, e **não** acurácia validada por interpretação humana. As avaliações internas e externas têm referências diferentes e não devem ser tratadas como uma competição numérica sob condições idênticas.

O [relatório de encerramento experimental da Proposta 1](experimentos/validacao_externa_regioes/PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md) registra o protocolo, a auditoria de reprodução e a limitação ainda pendente.

---

## Índice

- [Resumo executivo](#resumo)
- [1. Introdução e objetivos da pesquisa](#sec-1)
  - [1.1. Contextualização e problema de pesquisa](#sec-1-1)
  - [1.2. Objetivo geral e objetivos específicos](#sec-1-2)
  - [1.3. As duas propostas e suas contribuições](#sec-1-3)
- [2. Áreas de estudo e dados utilizados](#sec-2)
  - [2.1. Localização e função das quatro regiões](#sec-2-1)
  - [2.2. Imagens RGB e multiespectrais](#sec-2-2)
  - [2.3. Amostras de árvores e gramíneas](#sec-2-3)
  - [2.4. Dados auxiliares: CHMv2 e postes](#sec-2-4)
- [3. Visão geral da metodologia](#sec-3)
  - [3.1. Fluxograma completo](#sec-3-1)
  - [3.2. Etapas de processamento](#sec-3-2)
  - [3.3. Relação entre as duas propostas](#sec-3-3)
- [4. Proposta 1 — Identificação de árvores e gramíneas](#sec-4)
  - [4.1. Objetivo e justificativa](#sec-4-1)
  - [4.2. Segmentação Quickshift](#sec-4-2)
  - [4.3. NDVI, brilho HSV e Canny](#sec-4-3)
  - [4.4. Regressão Logística e treinamento na Area1](#sec-4-4)
  - [4.5. Validação espacial: 500 m e 30 avaliações](#sec-4-5)
  - [4.6. Resultados nas quatro regiões](#sec-4-6)
  - [4.7. Matrizes de confusão e F1-macro](#sec-4-7)
  - [4.8. Discussão da transferência geográfica](#sec-4-8)
  - [4.9. Reprodutibilidade, limitações e conclusão](#sec-4-9)
- [5. Proposta 2 — Porte das árvores e proximidade com a rede elétrica](#sec-5)
  - [5.1. Objetivo e fundamentação](#sec-5-1)
  - [5.2. Alturas modeladas pelo CHMv2](#sec-5-2)
  - [5.3. Equações alométricas](#sec-5-3)
  - [5.4. Resultados e comparações](#sec-5-4)
  - [5.5. Proximidade horizontal com postes](#sec-5-5)
  - [5.6. Limitações e situação atual](#sec-5-6)
- [6. Discussão geral e contribuições científicas](#sec-6)
  - [6.1. Principais resultados](#sec-6-1)
  - [6.2. Contribuições e limites](#sec-6-2)
- [7. Conclusões e trabalhos futuros](#sec-7)
- [8. Reprodutibilidade e código-fonte](#sec-8)
  - [8.1. Organização do repositório](#sec-8-1)
  - [8.2. Notebooks e scripts](#sec-8-2)
  - [8.3. Evidências e documentos](#sec-8-3)
- [9. Referências científicas e fontes dos dados](#sec-9)
- [Apêndice — Experimentos históricos e análises complementares](#apendice)

---

<a id="sec-1"></a>
## 1. Introdução e objetivos da pesquisa

<a id="sec-1-1"></a>
### 1.1. Contextualização e problema de pesquisa

A identificação da vegetação urbana por imagem pode apoiar diagnósticos de arborização, mas é difícil separar **copas arbóreas** de **vegetação herbácea** quando há variações de sombra, iluminação, textura, limites de copa e características radiométricas. Além disso, um classificador pode funcionar bem na área de treinamento e apresentar desempenho distinto em outra imagem ou cidade.

Em uma segunda frente, estimar **porte arbóreo** por áreas segmentadas exige cautela: **um superpixel não é necessariamente a copa de uma única árvore**. As estimativas públicas de altura do dossel e as distâncias horizontais a postes ajudam a explorar indicadores, mas não substituem observação de campo ou geometria tridimensional de cabos.

**Problemas investigados:** (i) em que medida um modelo supervisionado de duas classes se transfere entre imagens; e (ii) o que é possível — e o que não é — inferir sobre porte e proximidade usando as informações disponíveis.

<a id="sec-1-2"></a>
### 1.2. Objetivo geral e objetivos específicos

**Objetivo geral:** investigar o uso de segmentação de imagens e atributos espectrais/espaciais para caracterizar a vegetação urbana, além de avaliar exploratoriamente indicadores de porte e proximidade com elementos da infraestrutura elétrica.

**Objetivos específicos:**

1. Segmentar a imagem RGB da Area1 em janelas computacionalmente viáveis, por **Quickshift**.
2. Associar pontos conhecidos de árvores e gramíneas aos segmentos e extrair **NDVI, brilho HSV e bordas Canny**.
3. Treinar e validar espacialmente **a Regressão Logística original** com os dados exclusivos da Area1.
4. Examinar a **concordância** das previsões do modelo em três regiões externas com pseudo-rótulos Meta/WRI CHMv2, incluindo análise de variabilidade espacial.
5. Investigar relações exploratórias entre **área de segmentos, índices alométricos e alturas modeladas** e examinar distâncias horizontais a postes.
6. Documentar limites, rastreabilidade e condições necessárias para validação independente.

<a id="sec-1-3"></a>
### 1.3. As duas propostas e suas contribuições

A **Proposta 1** produz resultados de **classificação binária supervisionada** e avalia o comportamento do modelo fora de sua área de treinamento. A **Proposta 2** analisa **geometria de segmentos e estimativas modeladas de dossel** e retoma um ensaio histórico de distância a postes. São investigações relacionadas à vegetação urbana, mas **não formam uma comprovação integrada de risco elétrico**.

A fase computacional da Proposta 1 está encerrada. A Proposta 2 tem experimentos exploratórios documentados e **não deve ser descrita como validação de alturas reais ou de interferência com fios**.

<a id="sec-2"></a>
## 2. Áreas de estudo e dados utilizados

<a id="sec-2-1"></a>
### 2.1. Localização e função das quatro regiões

| Região | Município / estado | Função no protocolo final |
|---|---|---|
| **Area1** | Caxias do Sul — RS | Origem dos pontos humanos de referência, treinamento do modelo e 30 divisões espaciais internas |
| **Sagrada Família** | Caxias do Sul — RS | Avaliação externa; pontos de teste selecionados **fora da Area1 e do buffer de 25 m** |
| **Lomba Grande** | Novo Hamburgo — RS | Avaliação externa em outra região |
| **Cristo Rei** | São Leopoldo — RS | Avaliação externa em outra cidade |

**Centro de Novo Hamburgo:** participou de experimentos anteriores com cinco imagens, mas **não compõe a bateria final de quatro regiões**. Seus dados e relatórios permanecem preservados nos documentos históricos.

A [auditoria de sobreposição entre Area1 e Sagrada Família](experimentos/validacao_externa_regioes/AUDITORIA_SOBREPOSICAO_AREA1_SAGRADA_2026-11-12.md) explica por que a exclusão espacial era necessária. O nome das duas regiões não deve sugerir independência sem essa exclusão.

<a id="sec-2-2"></a>
### 2.2. Imagens RGB e multiespectrais

Na Area1, os dois rasters cumprem papéis distintos:

| Arquivo | Conteúdo | Aplicação |
|---|---|---|
| `AOI_RGB_NEW.tif` | Três canais visíveis (RGB) | Segmentação Quickshift |
| `AOI_NEW_MULTI.tif` | Quatro canais multiespectrais | Extração e alinhamento dos atributos |

| Propriedade verificada na Area1 | Valor |
|---|---|
| Dimensão do raster | **6.942 × 7.294 pixels** |
| Resolução nominal | **0,50 m por pixel** |
| Retângulo da imagem | **12,66 km²** (aprox.) |
| Polígono irregular da Area1 | **12,14 km²** (aprox.) |
| Referência espacial de análise | **EPSG:31982 — SIRGAS 2000 / UTM 22S** |

![Esquema da extensão retangular da imagem e do polígono Area1](docs/aoi_retangulo_area1_esquema.svg)

*Figura 1 — O retângulo do raster não equivale à área efetiva do polígono de estudo.*

**Rastreabilidade das bandas:** a [auditoria dos produtos Jilin-1](experimentos/validacao_externa_regioes/AUDITORIA_BANDAS_JILIN.md) identificou, nas ortoimagens multiespectrais relevantes, a ordem física **azul, verde, vermelho e infravermelho próximo**. A extração utiliza os índices **3, 2, 1 e 4** para obter R, G, B e NIR. O alinhamento entre a grade RGB e a multiespectral precisa ser respeitado antes de extrair valores de cada segmento.

**Restrição radiométrica:** o NDVI do experimento é calculado a partir de **valores digitais**, sem calibração documentada para reflectância de superfície. Portanto, não se deve interpretar seus valores como perfeitamente comparáveis entre sensores, datas ou condições de iluminação. A equivalência radiométrica é uma limitação da transferência.

Os arquivos originais são mantidos fora do GitHub: [documentação da Area1 e acesso ao Drive](data/README.md).

<a id="sec-2-3"></a>
### 2.3. Amostras de árvores e gramíneas

| Base da Area1 | Pontos de origem | Segmentos únicos usados na avaliação |
|---|---:|---:|
| `Arvores.gpkg` | 257 | 257 |
| `Grama.gpkg` | 253 | 248 |
| **Total** | **510** | **505** |

A diferença decorre da **associação espacial dos pontos aos segmentos e da deduplicação**: mais de um ponto pode referenciar o mesmo objeto segmentado. Os pontos originais não foram transferidos para outras cidades, nem substituídos pelos rótulos CHMv2 para treinar o modelo principal.

Na avaliação externa, foram reservados **200 pontos por região** (600 ao todo). Apenas os casos com pseudo-rótulo conservador CHMv2 de árvore ou gramínea entraram no cálculo do F1: **179** em Sagrada, **183** em Lomba Grande e **181** em Cristo Rei.

<a id="sec-2-4"></a>
### 2.4. Dados auxiliares: CHMv2 e postes

O **Meta/World Resources Institute Canopy Height Map v2 (CHMv2)** é um mapa de **altura de dossel modelada**, e não um levantamento de campo. Na Proposta 1, seus valores servem como **pseudo-rótulos automáticos** para a comparação externa; na Proposta 2, são usados como **estimativas de altura** nos pontos das árvores da Area1. Essas duas utilizações não devem ser confundidas.

O `postes.gpkg` contém **pontos de postes** da Area1, utilizados no estudo histórico de proximidade horizontal. Não existe, nos dados de entrada descritos no [inventário da Area1](data/README.md), uma camada que represente a posição tridimensional dos **cabos condutores**.

<a id="sec-3"></a>
## 3. Visão geral da metodologia

<a id="sec-3-1"></a>
### 3.1. Fluxograma completo da pesquisa

O diagrama abaixo representa **os fluxos efetivamente adotados**, separando os resultados finais da Proposta 1 das análises exploratórias da Proposta 2:

```mermaid
flowchart TD
  A["Area1: RGB, RGB + NIR e pontos de referência"] --> B["Quickshift: 812 janelas de até 256 × 256 pixels"]
  B --> C["Associar e deduplicar: 505 segmentos rotulados"]
  A --> D["Extrair NDVI, brilho HSV e bordas Canny"]
  C --> E["Tabela de atributos dos segmentos"]
  D --> E
  E --> F["Regressão Logística original + StandardScaler, C = 0,1"]
  F --> G["Area1: 30 divisões espaciais de 500 m, com embargo de 25 m"]
  F --> H["Modelo final congelado aplicado às 3 regiões externas"]
  H --> I["200 pontos fixos por região"]
  J["Meta/WRI CHMv2: pseudo-rótulos automáticos"] --> K["Concordância F1-macro nos pontos elegíveis"]
  I --> K
  K --> L["30 reamostragens espaciais por região"]
  A --> M["Proposta 2: área de superpixels e 257 referências de árvores"]
  J --> N["Estimativas de altura de dossel para a Area1"]
  M --> O["Índices C1–C6 e 11 famílias alométricas"]
  N --> O
  O --> P["Comparação exploratória com controle constante"]
  Q["Pontos de postes"] --> R["Distâncias horizontais históricas: 1, 3 e 5 m"]
  M --> R
  classDef dados fill:#edf3fa,stroke:#6e90af,color:#163247;
  classDef modelo fill:#e9f7ef,stroke:#4b956a,color:#19442f;
  classDef cautela fill:#fff5e6,stroke:#b89b63,color:#654714;
  class A,J,Q dados;
  class F,G,H,I,K,L,M,O,P,R modelo;
  class N cautela;
```

*Figura 2 — O CHMv2 não é utilizado para treinar a Regressão Logística original. Na Proposta 2, a altura continua sendo uma **estimativa modelada**. O estudo de distâncias a postes não mede risco elétrico.*

<a id="sec-3-2"></a>
### 3.2. Etapas de processamento das imagens

| Etapa | O que é feito | Resultado |
|---|---|---|
| 1. Preparação | Conferir rasters, resolução, bandas e alinhamento | Imagens compatíveis com o processamento |
| 2. Segmentação | Aplicar Quickshift em janelas menores | Segmentos ou *superpixels* |
| 3. Rotulação da Area1 | Associar pontos existentes e deduplicar objetos | 505 segmentos rotulados |
| 4. Atributos | Calcular médias de NDVI, HSV e Canny | Vetores numéricos por segmento |
| 5. Classificação | Padronizar atributos e treinar Regressão Logística | Previsão binária árvore/gramínea |
| 6. Avaliação interna | 30 separações espaciais na Area1 | F1-macro e variabilidade entre divisões |
| 7. Aplicação externa | Aplicar **o mesmo modelo final** às três regiões | Previsões congeladas em locais distintos |
| 8. Concordância externa | Comparar pontos elegíveis ao CHMv2 e reamostrar blocos | F1-macro descritivo e variabilidade espacial |

A reprodução das **tabelas derivadas** não equivale a recomputar toda a segmentação dos grandes ortomosaicos. As duas possibilidades exigem conjuntos de arquivos e recursos diferentes.

<a id="sec-3-3"></a>
### 3.3. Relação entre as duas propostas

**Compartilham:** a Area1, imagens de sensoriamento remoto, segmentos Quickshift e o contexto de vegetação urbana.

**Não compartilham o mesmo alvo:** a Proposta 1 prevê **classe de vegetação**; a Proposta 2 compara **estimativas de porte** e **proximidade horizontal a postes**. Um segmento classificado como “árvore” **não é automaticamente uma copa individual** e não implica altura ou interferência em fios.

<a id="sec-4"></a>
## 4. Proposta 1 — Identificação de árvores e gramíneas

**Estado:** processamento, avaliação espacial e verificação de reprodução computacional **concluídos**; auditoria cega de rótulos humanos externos **ainda pendente**.

<a id="sec-4-1"></a>
### 4.1. Objetivo e justificativa da metodologia

A proposta busca distinguir **árvores** e **gramíneas** com um classificador treinado em exemplos previamente conhecidos na Area1 e investigar se as previsões permanecem coerentes fora da área de origem.

A tarefa é **binária**. Na aplicação de um modelo de duas classes a toda a imagem, pixels de asfalto, telhados, solo exposto ou sombra podem receber uma das classes disponíveis. Assim, **mapas de predição não são automaticamente inventários confiáveis de cobertura vegetal**.

<a id="sec-4-2"></a>
### 4.2. Segmentação Quickshift — por que 812 janelas?

O **Quickshift** agrupa pixels visualmente semelhantes em **segmentos** ou *superpixels*. Ele **não reconhece árvores sozinho**: a classe é aprendida posteriormente, com os pontos de referência e seus atributos.

A imagem RGB da Area1 tem **6.942 × 7.294 pixels**; uma tentativa de segmentar tudo de uma vez esbarrou em limitação de memória. O processamento adotado divide a grade em **812 janelas de até 256 × 256 pixels** (28 × 29 posições, com bordas menores), aplicando Quickshift separadamente. A resolução dos pixels originais é preservada.

| Conceito | Significado no experimento |
|---|---|
| **Pixel** | Unidade da imagem; aproximadamente 0,5 × 0,5 m na Area1 |
| **Janela de 256 × 256 pixels** | Unidade computacional em que o Quickshift segmenta |
| **Segmento** | Grupo de pixels semelhantes; não equivale necessariamente a uma árvore |
| **Bloco de 500 m** | Unidade geográfica para separar ou reamostrar avaliações; **não** é o recorte Quickshift |
| **Embargo de 25 m** | Exclusão, no treino, de segmentos geometricamente próximos aos de teste |

O projeto preserva [o relatório sobre a tentativa de processamento global e a memória](docs/e10_teste_execucao_local.md) e [a comparação de estratégias de segmentação](docs/comparacao_controlada_segmentacao_512_vs_256.md).

<a id="sec-4-3"></a>
### 4.3. Atributos NDVI, brilho HSV e bordas Canny

Para cada segmento, extraímos um vetor com três médias, nesta ordem:

| Nome na base | Atributo | Informação representada |
|---|---|---|
| `mean_intensity` | **Brilho HSV (V)** | Intensidade/brilho dos pixels |
| `mean_edges` | **Bordas Canny** | Frequência local de bordas e transições |
| `mean_ndvi` | **NDVI** | Contraste relativo entre infravermelho próximo e vermelho |

**NDVI** (*Normalized Difference Vegetation Index*) é calculado por:

$$
NDVI = \frac{NIR - R}{NIR + R}
$$

em que **NIR** é o canal do infravermelho próximo e **R** o vermelho. Na fonte multiespectral Jilin-1 documentada, vermelho é a **banda 3** e NIR a **banda 4**. A relação foi calculada sobre **valores digitais não convertidos para reflectância**, o que exige cuidado em interpretações físicas e comparações radiométricas.

**HSV** transforma a representação das cores para matiz (*Hue*), saturação (*Saturation*) e valor (*Value*). O experimento usa a componente **V**, ligada ao brilho. **Canny** identifica transições locais de intensidade/bordas. Juntos, os três atributos fornecem sinais complementares, mas **nenhum garante, isoladamente, a identificação botânica**.

Esses atributos são calculados **antes da inferência**. A avaliação histórica de sua contribuição está preservada na [ablação dos atributos](docs/e4b_ablação_aninhada_2026-11-03.md).

<a id="sec-4-4"></a>
### 4.4. Regressão Logística e treinamento na Area1

A configuração final adotada é:

```python
make_pipeline(
    StandardScaler(),
    LogisticRegression(
        C=0.1,
        penalty="l2",
        max_iter=3000,
        random_state=42,
    ),
)
```

**Por que mantê-la?** É uma abordagem relativamente simples, reproduzível e interpretável, adequada a uma base rotulada pequena e a três atributos numéricos. Ela foi mantida após as comparações e tentativas complementares, **não** porque todos os experimentos alternativos tenham demonstrado ganhos.

- **Treinamento:** exclusivamente nos **505 segmentos únicos da Area1**, derivados de **510 pontos originais**.
- **Padronização:** o `StandardScaler` estima média e escala **somente a partir do treino**, inclusive dentro de cada divisão espacial.
- **Regularização L2:** controla a magnitude dos coeficientes; o parâmetro é mantido **fixo em C=0,1**.
- **Inferência externa:** usa o **modelo final congelado**, sem reajustar parâmetros, padronizador ou classes com os pontos das regiões externas.

A comparação dos **oito classificadores** e as variantes **B/C/D** foram preservadas como **histórico**, não como a metodologia adotada ao encerrar esta proposta ([Apêndice](#apendice)).

<a id="sec-4-5"></a>
### 4.5. Validação espacial — blocos de 500 m e 30 avaliações

**Area1 — 30 divisões com retreinamento.** Os segmentos são agrupados em células geográficas de **500 m**. Em cada divisão, aproximadamente 20% dos **grupos** ficam reservados para teste; a porcentagem efetiva de segmentos pode diferir. Do conjunto de treino são excluídos segmentos cujas geometrias estejam a **25 m ou menos** dos objetos de teste. O `StandardScaler` e a Regressão Logística são ajustados **exclusivamente no treino remanescente**. O F1-macro é calculado sobre o teste. A tabela final resume **30 F1-macro**, não as “épocas” de uma rede neural.

**Regiões externas — 30 reamostragens espaciais, sem retreinamento.** Em cada região, foram previamente reservados **200 pontos fixos**. Após excluir os sem referência CHMv2 elegível, os pontos são agrupados por blocos de **500 m**. Cada reamostragem sorteia **blocos com reposição** e inclui os pontos desses blocos; o **mesmo modelo** e as **mesmas previsões** são mantidos. Calcula-se novamente o F1-macro no conjunto reamostrado.

| Critério | Area1 | Três regiões externas |
|---|---|---|
| Fonte de referência | Pontos rotulados originais da Area1 | Pseudo-rótulos automáticos Meta/WRI CHMv2 |
| O modelo é treinado nesta etapa? | **Sim**, em cada divisão interna | **Não**, permanece congelado |
| Unidade espacial | 500 m, com embargo de 25 m | Bootstrap de blocos de 500 m |
| Número de avaliações | 30 divisões | 30 reamostragens **por região** |
| Interpretação da variação | Sensibilidade às separações espaciais de treino/teste | Sensibilidade à composição espacial da mesma amostra |

**Atenção:** 30 reamostragens **não criam 30 conjuntos externos independentes**. As médias internas e externas descrevem protocolos distintos. Os quantis de apenas 30 reamostragens também **não devem ser apresentados como intervalos de confiança formais**.

<a id="sec-4-6"></a>
### 4.6. Resultados das quatro regiões

Os números abaixo foram conferidos com os CSVs de 30 avaliações e 90 reamostragens descritos no [relatório técnico de encerramento](experimentos/validacao_externa_regioes/PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md).

| Região | Média do F1-macro | Desvio-padrão | F1 da avaliação anterior |
|---|---:|---:|---:|
| **Area1** | **0,8421** | 0,0389 | 0,8542 — média de apenas 5 divisões |
| **Sagrada Família** | **0,7584** | 0,0330 | 0,7597 — F1 agregado dos pontos elegíveis |
| **Lomba Grande** | **0,7794** | 0,0337 | 0,7785 — F1 agregado dos pontos elegíveis |
| **Cristo Rei** | **0,7961** | 0,0377 | 0,8042 — F1 agregado dos pontos elegíveis |

![Médias de F1-macro de 30 avaliações nas quatro regiões](docs/proposta1_f1_macro_30_avaliacoes_500m.svg)

*Figura 3 — O ponto de comparação é a média das 30 avaliações; a barra de dispersão representa **± 1 desvio-padrão**, não intervalo de confiança. A Area1 e as regiões externas utilizam referências e procedimentos distintos.*

O desvio da Area1 de **0,8542** para **0,8421** ocorre ao ampliar o resumo de **5 para 30 divisões** com o mesmo tipo de modelo, e **não significa que a Regressão Logística foi trocada**. Nas regiões externas, as diferenças entre F1 agregado e média bootstrap decorrem da reamostragem dos blocos.

**Não se deve escolher retrospectivamente outro limiar ou modelo com base nas respostas desses pontos externos e depois tratá-los como um teste independente.**

<a id="sec-4-7"></a>
### 4.7. Matrizes de confusão e interpretação do F1-macro

Nas duas classes deste experimento, uma **matriz de confusão** compara a classe de referência (linha) e a classe prevista (coluna). Para uma classe considerada positiva:

- **VP:** positivos corretamente previstos; **FP:** previstos como positivos, mas pertencentes à outra classe; **FN:** positivos não detectados.
- **Precisão:** `VP / (VP + FP)`; **revocação (*recall*):** `VP / (VP + FN)`.
- **F1 da classe:** média harmônica de precisão e revocação, `2 × precisão × revocação / (precisão + revocação)`.
- **F1-macro:** média **não ponderada** dos F1 das classes **árvore** e **gramínea**. Penaliza o desempenho ruim em qualquer das duas classes.

**Matrizes reais dos conjuntos externos completos, antes das 30 reamostragens** (linhas: referência CHMv2; colunas: previsão da Regressão Logística):

| Região | Árvore → árvore | Árvore → gramínea | Gramínea → árvore | Gramínea → gramínea | F1-macro agregado |
|---|---:|---:|---:|---:|---:|
| **Sagrada Família** | 69 | 9 | 34 | 67 | 0,7597 |
| **Lomba Grande** | 61 | 4 | 36 | 82 | 0,7785 |
| **Cristo Rei** | 83 | 13 | 22 | 63 | 0,8042 |

| Região | F1 árvore | F1 gramínea | Pontos elegíveis |
|---|---:|---:|---:|
| Sagrada Família | 0,7624 | 0,7571 | 179 |
| Lomba Grande | 0,7531 | 0,8039 | 183 |
| Cristo Rei | 0,8259 | 0,7826 | 181 |

As duas tabelas acima representam **cada conjunto externo original de pontos elegíveis**, e **não** a matriz média das 30 reamostragens. Somar as matrizes de divisões/reamostragens repetidas seria contar os mesmos objetos várias vezes; não fazemos essa interpretação.

<a id="sec-4-8"></a>
### 4.8. Discussão da transferência geográfica

Entre as regiões **externas**, Cristo Rei apresentou a maior média de concordância com o CHMv2, seguida por Lomba Grande e Sagrada Família. Isso é um resultado **descritivo deste conjunto de pseudo-rótulos**. Não permite concluir, por si só, que um município tem árvores mais fáceis de reconhecer ou que o modelo é mais preciso em campo naquele município.

Possíveis explicações a serem **investigadas**, sem tratá-las como demonstradas, incluem diferenças de iluminação, sombras, geometria dos segmentos, composição vegetal, distribuição dos pontos e características radiométricas dos mosaicos.

Em **Sagrada Família**, a proximidade geográfica e a sobreposição de origem com a Area1 exigiram exclusão espacial dos pontos de teste. O [registro de auditoria](experimentos/validacao_externa_regioes/AUDITORIA_SOBREPOSICAO_AREA1_SAGRADA_2026-11-12.md) documenta essa precaução.

A classificação binária da imagem inteira **não separa todas as coberturas urbanas**. O caso histórico de **Centro de Novo Hamburgo**, excluído da comparação final, ilustra a possibilidade de forte mudança de domínio; não deve ser escondido nem convertido em resultado de F1 sem referência adequada.

<a id="sec-4-9"></a>
### 4.9. Reprodutibilidade, limitações e conclusão

A fase computacional foi auditada: uma execução independente, com **modelo original e bases derivadas congelados**, reproduziu **byte a byte** estes quatro arquivos de referência:

1. `area1_30_divisoes_500m.csv` — 30 separações espaciais internas.
2. `externas_90_reamostragens_blocos_500m.csv` — 90 reamostragens externas.
3. `externas_f1_original_sem_reamostragem.csv` — F1 e matrizes nos conjuntos completos.
4. `TABELA_FINAL_MEDIAS_30_AVALIACOES_500M.csv` — médias e desvios-padrão.

A reprodução confirmada parte dos **atributos, pontos e geometrias derivados**; para reproduzir desde os pixels originais é necessário acessar os ortomosaicos RGB/NIR e executar as etapas anteriores de alinhamento e Quickshift. Os detalhes e a rastreabilidade disponíveis no repositório estão no [registro científico de encerramento](experimentos/validacao_externa_regioes/PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md) e na [documentação técnica externa](experimentos/validacao_externa_regioes/README.md).

**Limitação mais relevante:** os rótulos CHMv2 são **automáticos**, não verificados por revisor humano independente. Uma amostra **cega de 180 recortes RGB** (60 por região externa) foi preparada para auditoria, mas **sua anotação humana ainda está pendente**. Portanto, não se afirma validação de campo, acurácia humana confirmada ou ausência de erros sistemáticos no CHMv2.

**Conclusão da Proposta 1:** a **fase de modelagem, avaliação e reprodução computacional foi encerrada** com a Regressão Logística original e quatro médias documentadas. A validade da transferência para **rótulos humanos independentes** continua uma questão em aberto.

<a id="sec-5"></a>
## 5. Proposta 2 — Porte das árvores e proximidade com a rede elétrica

**Estado:** estudos exploratórios realizados e documentados; **não** há calibração local por altura de campo, medição tridimensional dos cabos ou demonstração de risco elétrico.

<a id="sec-5-1"></a>
### 5.1. Objetivo e fundamentação

A Proposta 2 pergunta se características geométricas de segmentos (especialmente sua área) podem ser relacionadas à **altura modelada do dossel** e servir de ponto de partida para indicadores exploratórios de porte. Uma análise histórica complementar observa a **distância horizontal até postes**.

**Alometria** estuda relações matemáticas entre dimensões. Aqui é indispensável distinguir:

- A área **A de um superpixel Quickshift**, que pode conter parte de uma copa, mais de uma copa ou outros objetos.
- A **largura real de copa**, medida em estudos dendrométricos, **não disponível** nos 257 pontos.
- A **altura de dossel modelada pelo CHMv2**, **não equivalente** à altura real individual.

As seis configurações empíricas **C1–C6** do notebook original são hipóteses próprias do experimento, e **não** coeficientes transferidos de literatura já calibrada para Caxias do Sul.

<a id="sec-5-2"></a>
### 5.2. Estimativas de altura pelo Meta/WRI CHMv2

O raster público de referência foi `2103121330.tif`, pertencente ao [conjunto CHMv2 de Meta/WRI](https://registry.opendata.aws/dataforgood-fb-forestsv2/). Os **257 pontos de árvores** da Area1 foram consultados de duas maneiras: valor **do pixel exato** e **máximo modelado em raio de 5 m**.

| Indicador documentado | Resultado |
|---|---:|
| Referências de árvores amostradas | **257/257** |
| Mediana da estimativa no pixel exato | **2 m** |
| Mediana do máximo estimado em raio de 5 m | **6 m** |
| Pixels com valor modelado zero | **107/257** |
| Pontos com máximo zero em todo o raio de 5 m | **42/257** |

**Interpretar com cautela:** zero no pixel não prova ausência da árvore, e o máximo a 5 m pode pertencer a outro indivíduo. A resolução espacial do mapa **não é uma medida de erro vertical**. O procedimento e os [257 valores originais](docs/v3_alturas_publicas/v3_meta_chmv2_estimativas_257_arvores.csv) são documentados em [alometria V3](docs/v3_alometria_caxias.md).

**Comparação complementar ETH Zürich:** somente **139/257** pontos possuíam previsão disponível no raster ETH de aproximadamente 10 m; nos mesmos 139 pontos, as medianas eram **6 m no pixel Meta** e **14 m no pixel ETH**. Isso demonstra **divergência entre modelos**, e não que algum deles seja mais preciso. Consulte a [análise pareada](docs/v3_alturas_publicas/v3_meta_eth_comparacao_257.md).

<a id="sec-5-3"></a>
### 5.3. Equações alométricas e modelos avaliados

Foram estudadas **onze famílias de curvas**: linear, logarítmica, inversa, quadrática, cúbica, potencial, composta, curva-S, logística, crescimento e exponencial. As **formas matemáticas** foram adaptadas do estudo de **Chatziathanasiou, Kitikidou e Milios (2024)**, considerando também a **correção editorial de 2026**. Não foram aplicados os coeficientes das árvores gregas como se fossem calibrados para a Area1.

A transformação geométrica de entrada foi o **diâmetro circular equivalente**:

$$
D_{eq} = 2\sqrt{\frac{A}{\pi}}
$$

em que **A** é a área projetada de um **superpixel**. **`D_eq` não é uma largura de copa individual medida.** As curvas foram ajustadas para prever as **estimativas do CHMv2**, não alturas reais.

![Onze famílias de equações adaptadas em comparação com o CHMv2](docs/v3_alturas_publicas/figura_11_familias_equacoes_legivel_v2.svg)

*Figura 4 — Famílias funcionais investigadas; algumas são reparametrizações da mesma forma exponencial. Os coeficientes originais das espécies estudadas na Grécia não foram transpostos.*

O notebook histórico também definiu índices **C1–C6** nas formas potencial e linear. Um exemplo é **C3 potencial = 2,5 × A^0,4**. Seu valor, inclusive quando ultrapassa 7, é **índice empírico**, não altura individual comprovada em metros. Consulte [as configurações originais](docs/allometria.md).

<a id="sec-5-4"></a>
### 5.4. Resultados e comparações

Os testes das **onze famílias** usaram validação espacial de **cinco divisões por escala** (250 e 500 m) e embargo de 25 m, comparando previsões fora do treinamento com o CHMv2. O erro foi medido por **MAE em metros em relação à referência modelada**, não em relação a uma altura medida em campo.

| Referência CHMv2 | Blocos de teste | Controle constante (MAE) | Melhor família adaptada observada (MAE) | Resultado |
|---|---:|---:|---:|---|
| Pixel exato | 250 m | **4,578 m** | Cúbica: 4,584 m | Controle melhor |
| Pixel exato | 500 m | **4,451 m** | Curva-S: 4,505 m | Controle melhor |
| Máximo em 5 m | 250 m | **4,778 m** | Inversa: 4,802 m | Controle melhor |
| Máximo em 5 m | 500 m | **4,665 m** | Curva-S: 4,731 m | Controle melhor |

A [tabela auditada com todos os cenários](docs/v3_alturas_publicas/v3_11_familias_meta_relatorio.md) registra as demais famílias, a seleção interna e as limitações. **Nenhuma das onze famílias superou o controle constante**, e esse é um resultado científico relevante: **a área do superpixel, isoladamente, não demonstrou capacidade suficiente de prever a variação da altura modelada** neste conjunto.

**Exemplo individual, sem escolha retrospectiva pelo desempenho:** para a primeira árvore da tabela original, o CHMv2 estimou **16 m no pixel** e **17 m no máximo em 5 m**; a previsão espacial fora do treino da curva-S foi **2,98 m** para o alvo de pixel. A discrepância é **em relação ao CHMv2**, não à altura real. Os valores das [257 árvores e 74 colunas](docs/v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv) permitem examinar cada caso sem depender de amostras escolhidas à mão.

<a id="sec-5-5"></a>
### 5.5. Análise de proximidade horizontal com postes

Na implementação histórica, candidatos selecionados a partir de **Quickshift + K-Means (cluster 3)** receberam índices empíricos C1–C6. O filtro **C3 potencial > 7** foi usado para selecionar candidatos; **não exigia necessariamente** uma previsão “árvore” do Random Forest.

A análise empregou os pontos `postes.gpkg` para examinar distâncias **horizontais** de **1, 3 e 5 m**. São medidas planimétricas (2D) entre geometrias; **não medem distância ao cabo elétrico, folga vertical, nível de tensão ou risco operacional**. Sem geometria dos condutores, alturas individuais confiáveis e critérios técnicos apropriados, a análise é **exploratória**, não um laudo sobre interferência na rede.

A metodologia histórica está preservada no [notebook original](Segmentacao_area_completa.ipynb) e na [descrição dos índices empíricos](docs/allometria.md).

<a id="sec-5-6"></a>
### 5.6. Limitações e situação atual da Proposta 2

**O que foi efetivamente feito:** cálculo de índices geométricos, amostragem de **257** alturas modeladas Meta/WRI, comparação de **onze famílias** com controles e análises históricas de distância a postes.

**O que não foi comprovado:** altura real dos indivíduos, delimitação botânica de copas, precisão local dos mapas Meta/ETH, superioridade de famílias alométricas sobre o controle constante ou risco elétrico a partir dos pontos de postes.

**Situação:** existe uma **base exploratória documentada** que pode motivar coleta de dados de campo ou novas hipóteses, mas não uma validação operacional de altura e segurança elétrica.

<a id="sec-6"></a>
## 6. Discussão geral e contribuições científicas

<a id="sec-6-1"></a>
### 6.1. Principais resultados

- **Proposta 1:** a Regressão Logística original foi avaliada por **30 divisões espaciais** na Area1 (média **0,8421**) e apresentou **concordância média** com referências automáticas CHMv2 entre **0,7584 e 0,7961** nas três regiões externas. Isso caracteriza o comportamento do modelo **sob o protocolo documentado**, não precisão humana confirmada em novos locais.
- **Proposta 2:** a avaliação de **onze famílias alométricas** contra alturas modeladas CHMv2 **não melhorou o controle constante**; índices derivados de superpixel e distância a postes não bastam, isoladamente, para estimar altura real ou risco elétrico.

<a id="sec-6-2"></a>
### 6.2. Contribuições e limites

**Contribuições metodológicas:** segmentação em janelas sem reduzir a resolução dos pixels, explicitação da origem e deduplicação das referências, controle espacial na Area1, manutenção de um modelo único congelado para transferência, auditoria de bandas e descrição reproduzível da variabilidade de métricas. A documentação também separa claramente **resultados finais** de **explorações históricas**.

**Limites:** a validade externa foi medida com **pseudo-rótulos CHMv2**, a radiometria das imagens não passou por calibração física comum, a classe binária não abrange todas as coberturas urbanas e o estudo alométrico não possui medidas de altura de campo.

<a id="sec-7"></a>
## 7. Conclusões e trabalhos futuros

A **fase experimental computacional da Proposta 1 está encerrada**, com um modelo original preservado, médias de 30 avaliações por região e reprodução dos resultados derivados verificada. A auditoria visual humana independente dos **180 recortes selecionados** continua pendente; o README **não confunde essa preparação com validação humana concluída**.

A **Proposta 2 permanece exploratória**: os experimentos descrevem relações e restrições, sem converter índices em alturas reais ou distância horizontal a postes em risco elétrico.

**Trabalhos futuros pertinentes**, sem alterar os resultados atuais: completar a anotação cega; considerar novas referências independentes de vegetação; documentar calibração radiométrica se houver novos ensaios; medir alturas/copas em campo; e, para qualquer análise elétrica operacional, obter a geometria dos cabos e os critérios técnicos aplicáveis.

<a id="sec-8"></a>
## 8. Reprodutibilidade e código-fonte

<a id="sec-8-1"></a>
### 8.1. Organização do repositório

```text
mestrado-arvores-urbanas/
├── README.md
├── README_versao_outubro.md           # documentação histórica preservada
├── data/README.md                     # inventário e acesso aos dados brutos
├── docs/                              # figuras, relatórios e resultados derivados
│   ├── proposta1_f1_macro_30_avaliacoes_500m.svg
│   ├── v3_alometria_caxias.md
│   └── v3_alturas_publicas/           # resultados e figuras da Proposta 2
├── experimentos/
│   ├── validacao_externa_regioes/
│   │   ├── PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md
│   │   ├── README.md
│   │   ├── chmv2_verificacao/
│   │   └── ...                        # scripts de treinamento, aplicação e auditoria
│   └── v3_testar_11_modelos_artigo_meta.py
├── Segmentacao_area_completa.ipynb    # notebook histórico original
├── Segmentacao_area_completa_v2_experimentos.ipynb
└── Alometria_caxias_v3.ipynb
```

Os **ortomosaicos de grande volume e os arquivos privados** da Area1 não estão incluídos como blobs no GitHub. O [inventário técnico dos dados](data/README.md) informa os arquivos necessários e seus caminhos usuais no Google Drive.

<a id="sec-8-2"></a>
### 8.2. Notebooks, scripts e execução

| Artefato | Finalidade | Situação |
|---|---|---|
| [Encerramento experimental da Proposta 1](experimentos/validacao_externa_regioes/PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md) | Protocolo final, 30 + 90 avaliações, rastreabilidade e limites | **Referência principal** |
| [README técnico da validação externa](experimentos/validacao_externa_regioes/README.md) | Histórico das rotinas e da transferência entre regiões | Complementar |
| [Execução integrada das cinco imagens](experimentos/validacao_externa_regioes/proposta1_cinco_areas_colab.ipynb) | Preparação, treinamento e aplicação de múltiplos modelos | **Histórico**, não alterar resultados finais |
| [Auditoria das bandas](experimentos/validacao_externa_regioes/AUDITORIA_BANDAS_JILIN.md) | Proveniência da ordem B, G, R e NIR | Evidência |
| [Verificação dos 600 pontos CHMv2](experimentos/validacao_externa_regioes/chmv2_verificacao/600_pontos_cegos_CHMv2_congelados.csv) | Pontos congelados e identificadores para referência externa | Dados derivados |
| [Validação de Regressão Logística com revisão humana](experimentos/validacao_externa_regioes/validar_logistica_quatro_regioes_500m.py) | **Somente após preenchimento humano** de rótulos cegos; não produz automaticamente os F1 CHMv2 finais | Protocolo independente pendente |
| [Notebook de alometria V3](Alometria_caxias_v3.ipynb) | Índices de superpixel e consulta a alturas modeladas | Proposta 2 |
| [Onze famílias e comparação com controle](experimentos/v3_testar_11_modelos_artigo_meta.py) | Validação espacial das formas alométricas | Proposta 2 |

**Condição de reprodução:** os F1 finais de 30 avaliações são derivados de **atributos e referências já extraídos**. A reprodução portátil foi confirmada com um pacote específico de código, geometria, modelo e CSVs congelados, **distribuído separadamente**; o presente repositório não deve ser apresentado como se incluísse automaticamente todo esse pacote ou os ortomosaicos originais. O [relatório de encerramento](experimentos/validacao_externa_regioes/PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md) distingue as etapas efetivamente reproduzidas das que dependem de imagens brutas.

**Segurança e privacidade:** não compartilhar no repositório credenciais do Google Drive/Colab, senhas, tokens, chaves ou dados privados de localização que não foram autorizados à publicação.

<a id="sec-8-3"></a>
### 8.3. Arquivos de resultados e documentação

| Material | Consulta |
|---|---|
| Relatório principal e métricas finais | [Proposta 1 — encerramento experimental](experimentos/validacao_externa_regioes/PROPOSTA1_ENCERRAMENTO_EXPERIMENTAL_30_AVALIACOES_500M.md) |
| Estudo dos 257 pontos e CHMv2 | [Alometria V3](docs/v3_alometria_caxias.md) |
| Tabela completa das 257 árvores e modelos | [CSV de 74 colunas](docs/v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv) |
| Onze famílias, controles e resultados | [Relatório científico de comparação](docs/v3_alturas_publicas/v3_11_familias_meta_relatorio.md) |
| Comparação Meta/WRI × ETH nos mesmos pontos | [Análise dos 139 pares](docs/v3_alturas_publicas/v3_meta_eth_comparacao_257.md) |
| Documentação histórica integral | [README anterior](README_versao_outubro.md) |
| Histórico de cinco imagens | [README técnico da validação externa](experimentos/validacao_externa_regioes/README.md) |

<a id="sec-9"></a>
## 9. Referências científicas e fontes dos dados

**Fonte da altura modelada:**

- Brandt, J. et al. (2026). *CHMv2: Improvements in Global Canopy Height Mapping using DINOv3*. **Scientific Data**. DOI: [10.1038/s41597-026-07882-0](https://doi.org/10.1038/s41597-026-07882-0).
- Meta / World Resources Institute. *Version 2 High Resolution Canopy Height Maps*. [AWS Registry of Open Data](https://registry.opendata.aws/dataforgood-fb-forestsv2/).
- ETH Zürich. *Global Canopy Height 2020*. [Documentação do conjunto de dados](https://langnico.github.io/globalcanopyheight/). Usado apenas em comparação complementar de duas fontes modeladas.

**Modelagem alométrica e contexto local:**

- Chatziathanasiou, S.; Kitikidou, K.; Milios, E. (2024). *Crown Width–Tree Height Models for Magnolia grandiflora, Prunus cerasifera, and Acer negundo Growing in Cities in Northeastern Greece*. **Land**, 13(10), 1579. DOI: [10.3390/land13101579](https://doi.org/10.3390/land13101579).
- Chatziathanasiou, S.; Kitikidou, K.; Milios, E. (2026). *Correction* ao artigo de 2024. **Land**, 15(3), 473. DOI: [10.3390/land15030473](https://doi.org/10.3390/land15030473).
- Prefeitura de Caxias do Sul. [Plano Diretor de Arborização Urbana — PDAU](https://caxias.rs.gov.br/servicos/meio-ambiente/plano-diretor-de-arborizacao-urbana-pdau). As faixas de porte de espécies são referências bibliográficas, **não rótulos botânicos nem alturas medidas nos 257 pontos**.

**Documentação técnica e fontes primárias do próprio estudo:** [rastreabilidade espectral Jilin-1](experimentos/validacao_externa_regioes/AUDITORIA_BANDAS_JILIN.md), [dados e projeções da Area1](data/README.md), [arquivo de experimentos anteriores](README_versao_outubro.md), [resultados da Proposta 2](docs/v3_alturas_publicas/v3_11_familias_meta_relatorio.md).

<a id="apendice"></a>
## Apêndice — Experimentos anteriores e análises complementares

As abordagens abaixo foram **investigadas e preservadas para rastreabilidade**, mas **não** devem ser confundidas com a escolha final da **Regressão Logística original, C=0,1, com 30 avaliações por região**.

| Estudo histórico ou complementar | Onde consultar | Por que não compõe a tabela principal |
|---|---|---|
| Oito classificadores, cinco divisões de 250/500 m | [Validações aninhadas](experimentos/reexecutar_tabelas_aninhadas_v2.py) e [documentação anterior](README_versao_outubro.md) | Modelos e protocolos de avaliação distintos |
| Experimento B — seleção de parâmetros | [Pasta do experimento B](experimentos/validacao_externa_regioes/experimento_B/) | Não demonstrou melhoria consistente no modelo final |
| Experimento C — filtragem das amostras pelo CHMv2 | [Relatório C](experimentos/validacao_externa_regioes/chmv2_verificacao/EXPERIMENTO_C_FILTRAGEM_510_AREA1_RESULTADOS_2026-11-17.md) | Substitui a base original por uma filtrada; não foi adotado |
| Experimento D — limiares e robustez espectral | [Relatório D](experimentos/validacao_externa_regioes/chmv2_verificacao/EXPERIMENTO_D_REGRESSAO_ORIGINAL_LIMIAR_DRIFT_2026-11-17.md) | Ganhos não consistentes na transferência |
| Quickshift global + K-Means + Random Forest | [Notebook histórico](Segmentacao_area_completa.ipynb) | Outra abordagem; acurácia histórica 0,87 em 92 testes não é F1 espacial |
| Segmentação de 119 recortes, 512 e 256 pixels | [Notebook de experimentos](Segmentacao_area_completa_v2_experimentos.ipynb) e [comparação de recortes](docs/comparacao_controlada_segmentacao_512_vs_256.md) | Outra configuração de segmentação |
| Centro de Novo Hamburgo e mapas das cinco imagens | [Relatório das cinco áreas](experimentos/validacao_externa_regioes/RELATORIO_REGRESSAO_LOGISTICA_EXCLUSIVA_5_IMAGENS_2026-11-16.md) | Centro ficou fora do fechamento em quatro regiões |
| Índices C1–C6 e primeiras quinze árvores | [Arquivo das 257 árvores](docs/v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv) | Índices empíricos e análises detalhadas da Proposta 2 |

<details>
<summary><strong>Expandir a tabela histórica dos oito classificadores</strong></summary>

#### A.1. Comparação histórica dos oito classificadores

**Registro histórico — não é a tabela final:** os F1 abaixo provêm de outra bateria de avaliação, com configurações e ajuste de parâmetros próprios. **Não confundir a regressão logística dessa tabela (0,8666 em 500 m) com a Regressão Logística original fixa C=0,1 nas 30 divisões (0,8421).**

A tabela apresenta **exclusivamente a bateria histórica documentada com segmentos derivados dos 812 quadrantes de até 256 × 256 pixels**. São **505 segmentos rotulados únicos**, os três atributos **NDVI + HSV + Canny** e cinco divisões espaciais por escala, com embargo de **25 m entre geometrias**. Os classificadores foram ordenados pela média de seus resultados nas duas escalas, apenas para facilitar a leitura.

| Classificador | F1-macro — blocos de 250 m | F1-macro — blocos de 500 m |
|---|---:|---:|
| Regressão logística | 0,8879 | **0,8666** |
| SVM RBF | 0,8908 | 0,8619 |
| KNN (25/35) | **0,8931** | 0,8481 |
| Extra Trees | 0,8266 | 0,8335 |
| HistGradientBoosting | 0,8325 | 0,8246 |
| Random Forest | 0,8220 | 0,8240 |
| Gaussian Naive Bayes | 0,7986 | 0,7400 |
| Dummy (referência simples) | 0,2980 | 0,2799 |

**Por que o F1-macro muda entre blocos de 250 e 500 m?** Porque o tamanho do bloco altera **quais exemplos ficam no treino e no teste** e, portanto, a dificuldade da avaliação. Esses blocos não alteram o tamanho dos quadrantes Quickshift.

**Como interpretar os resultados?** Valores maiores indicam melhor equilíbrio entre as classes árvore e gramínea nos testes. Cada coluna representa o **F1-macro médio de cinco divisões espaciais**, e não uma acurácia na imagem inteira nem uma estimativa de altura.

**O que descobrimos?** Com blocos de **250 m**, o maior resultado foi do **KNN (25/35): 0,8931**. Com blocos de **500 m**, liderou a **regressão logística: 0,8666**. **Nenhum algoritmo foi o melhor nas duas escalas.**

**Quais resultados podemos comparar diretamente?** Na configuração dos 812 quadrantes, os oito classificadores compartilham a mesma base rotulada, os atributos e as divisões externas **dentro de cada escala**. A comparação de HSV + Canny versus NDVI + HSV + Canny também utiliza esse protocolo supervisionado. Os resultados históricos do Quickshift global e das configurações com 119 recortes **não são comparações diretas**, pois diferem em segmentação, construção dos exemplos e/ou protocolos. [Consultar o histórico integral](README_versao_outubro.md).


</details>

<details>
<summary><strong>Expandir o registro histórico das estratégias de controle de sobreajuste</strong></summary>

#### A.2. Análise histórica de sobreajuste

**Overfitting** (sobreajuste) ocorre quando o modelo aprende particularidades dos dados de treinamento e pode apresentar desempenho inferior em exemplos reservados. Foram adotados os seguintes cuidados:

1. **Deduplicação:** uso de **505 segmentos rotulados únicos** e verificação de separação entre identificadores de treino e teste.
2. **Validação espacial:** blocos de **250 e 500 m**, cinco divisões por escala, com **exclusão geométrica de 25 m** entre exemplos próximos.
3. **Escolha interna dos parâmetros:** comparação de receitas de regularização **moderada e forte** por **três divisões internas dos dados de treinamento**, sem usar os testes externos para escolher parâmetros de cada rodada.
4. **Padronização sem vazamento:** quando necessária, a transformação é ajustada apenas nos exemplos de treinamento, dentro de um pipeline.
5. **Auditoria:** registro dos resultados tanto de treino quanto de teste para verificar a diferença entre eles.

**F1-macro médio de treino e teste de quatro modelos representativos nos 812 quadrantes** (média das dez divisões espaciais, reunindo cinco de 250 m e cinco de 500 m):

| Experimento | Classificador | F1 treino | F1 teste | Diferença |
|---|---|---:|---:|---:|
| **812 quadrantes de 256 px** | Regressão logística | 0,9011 | 0,8773 | +0,0239 |
| **812 quadrantes de 256 px** | SVM RBF | 0,9110 | 0,8764 | +0,0347 |
| **812 quadrantes de 256 px** | Random Forest | 0,8861 | 0,8230 | +0,0630 |
| **812 quadrantes de 256 px** | HistGradientBoosting | 0,8998 | 0,8286 | +0,0712 |

**O que o resultado mostra?** A diferença entre treino e teste ainda é maior em **Random Forest** e **HistGradientBoosting** do que em alguns outros modelos. As medidas de validação e regularização ajudam a **reduzir o risco**, mas **não comprovam ausência total de sobreajuste**.

**Limitação de generalização:** todos os exemplos pertencem à mesma **Area1**. A avaliação mede **generalização espacial interna**; não demonstra desempenho em outra cidade ou imagem independente. Além disso, os conjuntos externos já foram examinados em etapas anteriores da pesquisa, o que limita interpretações retrospectivas de seleção de modelos.




</details>

<details>
<summary><strong>Expandir a tabela histórica das primeiras quinze árvores (Proposta 2)</strong></summary>

#### A.3. Quinze árvores — tabela histórica detalhada

A tabela apresenta as **15 primeiras árvores na ordem original**, sem selecionar exemplos pelos resultados. As **três primeiras colunas** são a contagem, a **Meta pixel** e a **Meta 5 m**; depois vêm as previsões da **logarítmica, inversa, curva-S e cúbica** em blocos de **250 m** e os índices históricos **C1 potencial e C3 potencial** (as versões `I = a × A^b` do notebook original). As previsões das quatro famílias são **OOF (teste espacial)**; C1 e C3 **não são alturas calibradas em metros** e não representam as variantes lineares.

| Árvore | **Meta pixel (m)** | **Meta 5 m (m)** | Log. pixel (m) | Log. 5 m (m) | Inversa pixel (m) | Inversa 5 m (m) | Curva-S pixel (m) | Curva-S 5 m (m) | Cúbica pixel (m) | Cúbica 5 m (m) | C1 potencial (índice) | C3 potencial (índice) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16,00 | 17,00 | 3,02 | 5,97 | 2,98 | 5,97 | 2,98 | 5,97 | 3,21 | 5,97 | 23,95 | 22,81 |
| 2 | 0,00 | 6,00 | 3,02 | 5,97 | 2,98 | 5,97 | 2,98 | 5,97 | 3,24 | 5,97 | 24,62 | 23,17 |
| 3 | 10,00 | 13,00 | 3,40 | 6,50 | 3,56 | 6,58 | 3,46 | 6,57 | 3,25 | 6,39 | 9,66 | 13,58 |
| 4 | 19,00 | 20,00 | 3,04 | 5,97 | 2,98 | 5,97 | 2,98 | 5,97 | 3,51 | 5,97 | 31,34 | 26,60 |
| 5 | 0,00 | 2,00 | 3,86 | 6,87 | 3,87 | 6,89 | 3,87 | 6,89 | 3,66 | 6,72 | 15,13 | 17,55 |
| 6 | 0,00 | 2,00 | 2,93 | 6,11 | 3,11 | 6,13 | 2,94 | 6,13 | 3,08 | 6,26 | 6,02 | 10,36 |
| 7 | 0,00 | 0,00 | 3,98 | 6,98 | 3,93 | 6,96 | 3,97 | 6,96 | 3,87 | 6,89 | 17,15 | 18,84 |
| 8 | 0,00 | 0,00 | 3,98 | 6,97 | 3,93 | 6,96 | 3,97 | 6,96 | 3,86 | 6,88 | 17,09 | 18,81 |
| 9 | 3,00 | 6,00 | 4,17 | 7,13 | 4,03 | 7,05 | 4,11 | 7,06 | 4,30 | 7,23 | 20,65 | 20,96 |
| 10 | 6,00 | 9,00 | 3,73 | 6,77 | 3,79 | 6,82 | 3,77 | 6,81 | 3,51 | 6,60 | 13,38 | 16,36 |
| 11 | 0,00 | 3,00 | 4,14 | 7,11 | 4,01 | 7,04 | 4,09 | 7,05 | 4,21 | 7,16 | 19,99 | 20,57 |
| 12 | 5,00 | 6,00 | 3,35 | 6,45 | 3,52 | 6,54 | 3,41 | 6,53 | 3,22 | 6,37 | 9,14 | 13,15 |
| 13 | 10,00 | 10,00 | 2,15 | 5,14 | 2,24 | 5,13 | 2,17 | 5,13 | 2,22 | 5,33 | 5,72 | 10,06 |
| 14 | 1,00 | 8,00 | 2,39 | 5,40 | 2,50 | 5,47 | 2,44 | 5,46 | 2,29 | 5,39 | 8,13 | 12,31 |
| 15 | 6,00 | 9,00 | 2,77 | 5,83 | 2,79 | 5,86 | 2,79 | 5,85 | 2,60 | 5,67 | 14,23 | 16,94 |

**Resultados completos:** A tabela acima apresenta as 15 primeiras árvores. Para consultar os **257 pontos avaliados e os resultados de todos os modelos**, incluindo os testes com blocos espaciais de 250 m e 500 m, acesse a [**tabela completa — 257 pontos e 74 colunas**](docs/v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv).

Por exemplo, na **árvore 1**, a Meta indica **16 m no pixel e 17 m no raio de 5 m**, enquanto os modelos logarítmico, inverso, curva-S e cúbico retornam valores bastante inferiores nos testes espaciais. Isso mostra que, apesar de terem sido testadas diversas famílias, **os modelos ainda não recuperam de forma confiável a variação individual das alturas modeladas pela Meta**. Os índices **C1 potencial** e **C3 potencial** apresentam valores maiores, mas não equivalem automaticamente a metros de altura real; as variantes lineares existem no notebook original e não são as colunas desta tabela.


</details>

**Arquivos preservados:** os experimentos e códigos originais permanecem no repositório; as tabelas acima são documentação histórica. O gráfico de 30 avaliações e o fluxograma principal representam os **resultados e o escopo atualmente adotados**.

**Situação de publicação:** esta revisão se aplica exclusivamente à branch `feature/validacao-geografica-externa`. Não altera a `main`, não executa merge do PR #6, não muda a Proposta 2 e não atualiza automaticamente o portal hospedado na pasta `docs`.
