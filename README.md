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

O projeto investiga uma abordagem orientada a objetos: a imagem é segmentada em regiões espacialmente coerentes e cada objeto é descrito por características espectrais, radiométricas e estruturais. Além de apoiar a discriminação entre árvores e gramíneas, essa representação conserva polígonos georreferenciados úteis à análise de proximidade com linhas de energia.

## Propostas de pesquisa

- **Proposta 1:** combinar NDVI + brilho + bordas para distinguir árvores e gramíneas.
- **Proposta 2:** localizar árvores em proximidade com a rede elétrica.

## Contribuições metodológicas

As propostas abaixo representam a **contribuição metodológica investigada** e os **elementos de originalidade da abordagem**. Sua avaliação comparativa ainda está em desenvolvimento; portanto, não se pressupõe superioridade em relação a outros métodos.

### Combinação complementar de características

A descrição dos objetos integra fontes de informação complementares:

- **NDVI:** informação espectral associada à resposta da vegetação;
- **brilho HSV:** informação radiométrica derivada da intensidade;
- **bordas de Canny:** heterogeneidade estrutural observada no interior dos objetos.

O trabalho **não propõe um novo índice espectral**. A investigação concentra-se na combinação dessas características já estabelecidas para discriminar classes de vegetação em uma unidade de análise orientada a objetos.

### Estratégia híbrida

- **K-Means:** realiza a pré-seleção não supervisionada de objetos candidatos a vegetação;
- **Random Forest:** executa a classificação supervisionada dos candidatos em **árvore** ou **gramínea**.

Essa organização busca reduzir o espaço inicial de análise antes da classificação, sem antecipar conclusões sobre ganhos de desempenho.

### Preservação da geometria

Os objetos permanecem representados como polígonos georreferenciados ao longo do fluxo. Essa estrutura permite obter ou investigar:

- área;
- proxy de porte;
- interseção;
- distância;
- proximidade com linhas de energia.

## Fluxo metodológico

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 42, "rankSpacing": 48, "curve": "basis"}}}%%
flowchart TD
    A("🛰️ Imagem aérea RGB + multiespectral") --> B("🧩 Segmentação Quickshift")
    B --> C("Objetos segmentados")
    C --> D("📊 Estatísticas espectrais RGB–NIR")
    D --> E("K-Means")
    E --> F("🌱 Pré-seleção de vegetação")
    F --> G("🏷️ Amostras árvore / gramínea")
    G --> H("Extração das características")

    H --> I("🌿 NDVI")
    H --> J("💡 Brilho / Intensidade HSV")
    H --> K("◻️ Bordas de Canny")

    I --> L("Características por objeto")
    J --> L
    K --> L
    L --> M("🌲 Random Forest")
    M --> N("Classificação árvore × gramínea")
    N --> O("🌳 Árvores detectadas")
    O --> P("🗺️ Análise espacial")
    P --> Q("⚡ Proximidade com linhas de energia")

    classDef etapa fill:#EAF4FF,stroke:#8BBBE8,stroke-width:1.5px,color:#173B63;
    classDef caracteristica fill:#F4F9FF,stroke:#8BBBE8,stroke-width:1.5px,color:#173B63;
    classDef destaque fill:#D8ECFF,stroke:#629FD6,stroke-width:2px,color:#102F50,font-weight:bold;

    class A,B,C,D,F,G,H,L,N,O,P etapa;
    class I,J,K caracteristica;
    class E,M,Q destaque;
    linkStyle default stroke:#8AA9C4,stroke-width:1.5px;
```

## Resultados atuais

> **Resultados do experimento inicial atualmente documentado.**

| Indicador | Valor |
| --- | ---: |
| Objetos rotulados | 133 |
| Treinamento | 106 |
| Teste | 27 |
| Acurácia global | 0,81 |

| Classe | Precisão | Recall | F1-score |
| --- | ---: | ---: | ---: |
| Árvores | 0,83 | 0,77 | 0,80 |
| Gramíneas | 0,80 | 0,86 | 0,83 |

A segmentação inicial produziu **15.633 objetos**, dos quais **3.002** foram selecionados como candidatos de vegetação. Esses números descrevem apenas o experimento inicial e não devem ser interpretados como avaliação conclusiva da metodologia.

As seguintes análises estão planejadas ou em execução:

- estudo de ablação das características;
- comparação entre configurações RGB e RGB–NIR;
- comparação do Random Forest com SVM;
- validação cruzada estratificada.

Nenhum resultado dessas análises é antecipado neste documento.

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
| 📦 `requirements-colab.txt` | Dependências do ambiente |
| 📘 `README.md` | Documentação principal |
| 🚫 `.gitignore` | Arquivos não versionados |
| 📂 `data/README.md` | Orientações sobre os dados |

O **GitHub** concentra o código e a documentação versionados, enquanto o **Google Drive** armazena os dados geoespaciais pesados e os produtos do processamento. Essa separação evita incorporar arquivos volumosos ao histórico do repositório.

## Dados e armazenamento

Estrutura esperada no Google Drive:

```text
MyDrive/
└── mestrado-arvores-urbanas/
    ├── data/
    │   ├── raw/
    │   └── interim/
    └── outputs/
```

| Diretório | Finalidade |
| --- | --- |
| 📥 `data/raw/` | Dados originais |
| ⚙️ `data/interim/` | Produtos intermediários |
| 📤 `outputs/` | Resultados finais |

### Dados de entrada

| Arquivo | Função |
| --- | --- |
| `AOI.tif` | Imagem RGB |
| `AOI_MULTI.tif` | Imagem multiespectral RGB + NIR |
| `AOI.shp` | Área de interesse |
| `Arvores.shp` | Amostras de árvores |
| `Grama.shp` | Amostras de gramíneas |
| `Linhas.shp` | Linhas de energia |
| `Postes.shp` | Referência cartográfica dos postes |

> **Nota:** cada Shapefile depende de arquivos auxiliares, como `.shx`, `.dbf`, `.prj` e `.cpg`. Quando disponíveis, mantenha todos os componentes junto ao respectivo arquivo `.shp` em `data/raw/`.

## Como executar

1. Organize os dados no Google Drive conforme a estrutura indicada acima.
2. Abra [`Segmentacao_classificacao.ipynb`](Segmentacao_classificacao.ipynb), a partir do GitHub, no Google Colab.
3. Monte o Google Drive na sessão do Colab.
4. Instale as dependências:

   ```python
   !pip install -r requirements-colab.txt
   ```

5. Execute as células do notebook na ordem apresentada.
6. Verifique os produtos gerados em `data/interim/` e `outputs/`.

## Status do projeto

> **Em desenvolvimento.** A metodologia, os experimentos comparativos e a validação estão sendo aprimorados no contexto da pesquisa de mestrado.

## Autor

**Breno Braga Galvão**

Projeto desenvolvido no contexto de pesquisa acadêmica de mestrado.
