# V3 — Auditoria exploratória da alometria em Caxias do Sul

## Questão levantada na qualificação
As estimativas de porte da fórmula original são numericamente plausíveis diante das faixas de altura de árvores documentadas para Caxias do Sul?

A V3 é **independente** do notebook original e da V2. Usa apenas os arquivos **já existentes** em Area1: AOI_RGB_NEW.tif e Arvores.gpkg. Não solicita novos dados. A lista externa de espécies é bibliografia municipal, e não um novo rótulo para as árvores da imagem.

## Evidência municipal
O [Plano Diretor de Arborização Urbana de Caxias do Sul](https://caxias.rs.gov.br/servicos/meio-ambiente/plano-diretor-de-arborizacao-urbana-pdau) disponibiliza [Anexo 1 com o porte das espécies](https://gcpstorage.caxias.rs.gov.br/documents/2020/09/c2d2ec2b-dfb4-4646-aadd-01eced79a722.pdf).

| Espécie | Porte descrito | Observação |
|---|---|---|
| Pitangueira (*Eugenia uniflora*) | 6–12 m | Pode apresentar menor porte na arborização |
| Araucária (*Araucaria angustifolia*) | 20–50 m | Faixa de espécie, não medição de indivíduo |
| Quaresmeira (*Tibouchina sellowiana*) | 4–15 m | Na arborização local raramente passa de 8 m |
| Caroba (*Jacaranda micrantha*) | 10–25 m | Espécie presente na lista municipal |
| Jacarandá-mimoso (*Jacaranda mimosifolia*) | 12–15 m | Faixa de espécie |
| Tipuana (*Tipuana tipu*) | 12–16 m | Faixa de espécie |

As faixas vêm de espécies diferentes. **Não há identificação botânica ou medida de altura nos 257 pontos originais**; não atribuímos espécie a cada ponto nem interpretamos a faixa local como medição na Area1.

## Método
O [notebook V3](../Segmentacao_area_completa_v3_alometria_caxias.ipynb) aciona [um script independente](../experimentos/v3_alometria_caxias.py). O script lê apenas as bandas RGB e os pontos de Arvores.gpkg, segmenta **em janelas de 256 pixels**, registra o superpixel que contém cada ponto e sua área em m², assinalando os que tocam a borda da janela. Reproduz as seis fórmulas experimentais C1–C6 (potencial e linear), com destaque para o índice C3 = 2,5 × A^0,4 e seu corte histórico maior que 7. Há opção de repetir com janelas de 512 pixels.

**Superpixel Quickshift não equivale a uma copa individual delimitada.** Os coeficientes C1–C6 não foram ajustados às alturas reais desta região e não são os coeficientes de artigos externos. O índice C3 não tem validação como altura em metros. A publicação [Chatziathanasiou et al. (2024)](https://doi.org/10.3390/land13101579) investiga relação largura de copa–altura em três espécies de cidades gregas, mas não calibra a fórmula original da Area1.

## Execução inicial com arquivos reais da Area1
Na execução exploratória de 256 px sobre os arquivos RGB e Arvores.gpkg já presentes no Drive, obtivemos:

| Indicador | Resultado |
|---|---:|
| Pontos originais de árvores | **257** |
| Pontos vinculados a superpixel | **257** |
| Janelas únicas processadas | **114** |
| Segmentos associados que tocam borda | **79 (30,7%)** |
| Área mediana do superpixel | **120,25 m²** |
| Mediana do índice C3, não altura | **16,98** |
| Amplitude do índice C3, não altura | **7,34–29,40** |
| Índice C3 maior que 7 | **257 de 257** |

Esses valores descrevem um **índice obtido de áreas de superpixels**, não alturas reais. Em especial, **não podemos afirmar que a altura mediana seja 16,98 m**, nem que 100% das árvores reais tenham altura superior a 7 m. Os 257 pontos também não equivalem ao conjunto histórico de candidatos do cluster 3.

A [tabela de referências regionais](v3_referencias_alturas_caxias.csv) registra as faixas bibliográficas, com fonte e número de página. O [resumo de execução](v3_resumo_exploratorio.json) guarda métricas agregadas e as restrições interpretativas.

## Reproduzir no Colab
Montar o Google Drive e executar, sem alterar os arquivos originais:

~~~bash
python experimentos/v3_alometria_caxias.py --area /content/drive/MyDrive/Area1 \
  --out /content/v3_resultados_alometria --tile 256
~~~

Se a pasta Area1 estiver em outro local do Drive, ajustar apenas --area. Rodar com --tile 512 é um teste adicional de sensibilidade da segmentação.

## Estimativas externas de altura por ponto no Google Earth Engine (V3)

Para responder à pergunta sobre a altura das **257 árvores de referência**, foi preparado o [script de extração GEE](../experimentos/v3_alturas_dossel_google_earth_engine.py), sem alterar as imagens ou os pontos originais da Area1. O script lê **Arvores.gpkg**, mantém seus IDs e consulta duas referências públicas de altura de **dossel estimada por modelos**:

| Fonte | Resolução aproximada | Uso e ressalva |
|---|---|---|
| [Meta/WRI — High Resolution Canopy Height Maps](https://gee-community-catalog.org/projects/meta_trees/) | **1 m** | Preferência para árvores urbanas individuais, mas os valores são **previsões**, não alturas medidas. O mapa pode ter deslocamentos, ruído e datas de imagem diferentes. |
| [ETH Zurich — Global Canopy Height 2020](https://langnico.github.io/globalcanopyheight/) | **10 m** | Referência secundária científica, com resolução insuficiente para separar algumas árvores vizinhas. O produto também fornece estimativas de incerteza. |

**Não foram obtidos 257 valores medidos nesta etapa:** a consulta numérica exige uma sessão **autenticada do Google Earth Engine** em um projeto habilitado. O script está pronto para rodar no Colab com esse acesso e **não contém alturas inventadas**.

Exemplo, após instalar `earthengine-api`, `geopandas` e `pandas`, montar o Drive e habilitar o projeto Google Cloud:

~~~bash
python experimentos/v3_alturas_dossel_google_earth_engine.py \
  --area /content/drive/MyDrive/Area1 \
  --out /content/v3_alturas_gee \
  --project SEU_ID_DE_PROJETO_GEE \
  --fontes ambas
~~~

Saídas previstas, **somente depois de executar com sucesso**: `v3_alturas_dossel_estimadas_257_pontos.csv` com 257 linhas (inclusive pontos sem cobertura, marcados como ausentes), e `v3_alturas_dossel_resumo.json`. É possível anexar os índices da V3 pelo argumento `--indices-v3 CAMINHO/CSV` quando o CSV contiver `ponto_id` e `indice_potencial_C3`.

**Interpretação:** altura do dossel em um pixel georreferenciado **não comprova a altura da árvore individual** à qual o ponto foi associado. A comparação entre a C3 e os produtos Meta/ETH é uma análise de **concordância com outras estimativas modeladas**, não uma validação de campo ou certificação de exatidão (MAE/RMSE perante observações reais). As datas, diferenças de resolução, alinhamento geográfico e trechos sem cobertura devem ser documentados antes de tirar conclusões.

## Conclusão permitida
A V3 examina **sensibilidade e plausibilidade numérica exploratória**, pesquisando faixas de porte locais. Sem **copas individualizadas, espécies identificadas e alturas de referência dos mesmos indivíduos**, **não é possível validar o acerto das alturas** (nem calcular MAE, RMSE, R²). Altura não foi medida. A análise de proximidade a postes continua horizontal e exploratória; não comprova risco elétrico.
