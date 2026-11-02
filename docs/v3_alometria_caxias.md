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
O [notebook V3](../Alometria_caxias_v3.ipynb) aciona [um script independente](../experimentos/v3_alometria_caxias.py). O script lê apenas as bandas RGB e os pontos de Arvores.gpkg, segmenta **em janelas de 256 pixels**, registra o superpixel que contém cada ponto e sua área em m², assinalando os que tocam a borda da janela. Reproduz as seis fórmulas experimentais C1–C6 (potencial e linear), com destaque para o índice C3 = 2,5 × A^0,4 e seu corte histórico maior que 7. Há opção de repetir com janelas de 512 pixels.

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

## Fonte externa exclusiva: Meta/WRI CHMv2 (257 pontos)

A V3 passa a utilizar **somente o produto Meta/WRI CHMv2** para estimar a **altura modelada do dossel** nos pontos de referência de árvores da Area1. Os 257 valores por ponto foram efetivamente extraídos do [GeoTIFF público `2103121330.tif`](https://dataforgood-fb-data.s3.us-east-1.amazonaws.com/forests/v2/global/dinov3_global_chm_v2_ml3/chm/2103121330.tif), sem autenticação, pelo [script reprodutível](../experimentos/v3_amostrar_altura_publica.py). A amostragem considera o valor do **pixel exato** e, separadamente, o **máximo dentro de 5 m**.

**Dados e metodologia:** [análise estatística dos 257 pontos](v3_alturas_publicas/v3_analise_comparativa.md), [CSV original com C3 e alturas Meta](v3_alturas_publicas/v3_comparacao_c3_meta_257.csv), [dados Meta brutos](v3_alturas_publicas/v3_meta_chmv2_estimativas_257_arvores.csv), [resumo JSON](v3_alturas_publicas/v3_meta_chmv2_resumo.json).

| Indicador | Resultado Meta/WRI na Area1 |
|---|---:|
| Pontos amostrados | **257/257** |
| Mediana da previsão no pixel exato | **2 m** |
| Mediana do máximo estimado em 5 m | **6 m** |
| Valores zero no pixel | **107 (41,6%)** |
| Valores zero em todo o raio de 5 m | **42 (16,3%)** |
| Correlação Pearson C3 × previsão Meta no pixel | **r = 0,019** |
| Correlação Pearson C3 × máximo Meta no raio de 5 m | **r = 0,014** |

A previsão Meta/WRI **não é uma medição direta de altura individual**. Zero no pixel não demonstra inexistência de árvore; o máximo em 5 m pode corresponder a outro indivíduo. **C3 continua um índice não calibrado**, calculado sobre superpixels, e não deve ser interpretado como altura real em metros.

### Execução e reprodução no notebook V3

Abra [`Alometria_caxias_v3.ipynb`](../Alometria_caxias_v3.ipynb). Execute os índices alométricos com os arquivos originais da Area1, então carregue o CSV Meta/WRI já incluído no repositório. O próprio notebook verifica os **257 IDs**, gera uma tabela consolidada com as previsões e os índices e calcula correlações e um gráfico de dispersão. A atualização da fonte externa por COG é **opcional** e fica desativada por padrão.

Referências externas: [Meta/WRI — AWS Open Data](https://registry.opendata.aws/dataforgood-fb-forestsv2/) · [Brandt et al. (2026), *Scientific Data*](https://doi.org/10.1038/s41597-026-07882-0). O artigo relata **MAE aproximado de 3,0 m** no protocolo de validação SatLidar v2; esse erro **não é uma estimativa de precisão local para a Area1**.

## Conclusão permitida
A V3 examina **sensibilidade e plausibilidade numérica exploratória**, pesquisando faixas de porte locais. Sem **copas individualizadas, espécies identificadas e alturas de referência dos mesmos indivíduos**, **não é possível validar o acerto das alturas** (nem calcular MAE, RMSE, R²). Altura não foi medida. A análise de proximidade a postes continua horizontal e exploratória; não comprova risco elétrico.
