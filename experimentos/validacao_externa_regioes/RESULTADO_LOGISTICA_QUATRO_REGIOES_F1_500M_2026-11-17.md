# Proposta 1 — Regressão Logística em quatro regiões (17/11/2026)

## Escopo desta execução

- **Incluídas:** Area1 (Caxias do Sul), Sagrada Família (Caxias do Sul), Lomba Grande (Novo Hamburgo) e Cristo Rei (São Leopoldo).
- **Excluída desta bateria:** Centro de Novo Hamburgo; seus experimentos e mapas históricos não foram apagados.
- **Base exclusiva de treinamento:** os 257 pontos originais de `Arvores.gpkg` e os 253 de `Grama.gpkg` da Area1; associação espacial a **505 segmentos Quickshift únicos**.
- **Classificador único:** `StandardScaler` + `LogisticRegression(C=0.1, max_iter=3000, random_state=42)`.
- **SHA-256 do modelo congelado original:** `2b05ce70f24eacf08753466715934bcceccfe13c9a202d1a178689141022293c`.
- **Sem treinamento nas regiões externas**, sem seleção de modelo pelos dados externos, sem alteração dos mapas históricos e sem nova calibração radiométrica nesta sessão.

## Tabela 1 — classificações preexistentes verificadas

| Região | Segmentos previstos árvore | Segmentos previstos gramínea | Pixels árvore | Pixels gramínea |
|---|---:|---:|---:|---:|
| Area1 | 54.520 | 77.256 | 38,96% | 61,04% |
| Sagrada Família | 161.057 | 157.773 | 45,85% | 54,15% |
| Lomba Grande | 317.655 | 296.375 | 51,29% | 48,71% |
| Cristo Rei | 202.965 | 132.663 | 55,58% | 44,42% |

Essas são **predições**. Uma classificação binária árvore/gramínea atribui uma dessas classes até a pixels válidos não vegetados. Não são hectares comprovados de cobertura vegetal.

## Tabela 2 — desempenho da Regressão Logística

| Imagem | F1-macro interno 250 m | F1-macro 500 m | Tipo de avaliação |
|---|---:|---:|---|
| **Area1** | **0,8376** | **0,8567** | Interna: 5 divisões espaciais por escala |
| Sagrada Família | Não aplicável | **Pendente** | Externa: 500 m; 0/200 referências verificadas |
| Lomba Grande | Não aplicável | **Pendente** | Externa: 500 m; 0/200 referências verificadas |
| Cristo Rei | Não aplicável | **Pendente** | Externa: 500 m; 0/200 referências verificadas |

O README histórico registra **0,8879 / 0,8666** para Area1 sob outro protocolo; a bateria corrigida é **0,8376 / 0,8567**. Não confundir.

**Interpretação da coluna externa de 500 m:** os pontos de referência independentes foram originalmente selecionados distribuindo um ponto por bloco de **250 m** e **reagrupados** agora em blocos de **500 m**. Isso define agrupamento para estimativa de incerteza espacial, **não** uma validação cruzada externa com retreinamento. Para Sagrada, Lomba e Cristo, a métrica será o F1 sobre os segmentos de referências humanas independentes, com confiança por bootstrap espacial em blocos 500 m se os rótulos forem suficientes.

## Auditoria real dos 600 pontos externos

A sessão reabriu os ZIPs das três regiões, leu diretamente `segmento_id.tif` e `classificacao_regressao_logistica.tif` em todas as 600 coordenadas, validou **200 amostras por região** com IDs únicos e não nulos, criou formulários cegos e manteve a tabela de previsões **separada dos materiais destinados ao revisor**.

| Região | Pontos reservados | Blocos distintos de 500 m | Amostras com referência humana confirmada | Predições árvore nos 200 | Predições gramínea nos 200 |
|---|---:|---:|---:|---:|---:|
| Sagrada Família | 200 | 78 | 0 | 111 | 89 |
| Lomba Grande | 200 | 140 | 0 | 106 | 94 |
| Cristo Rei | 200 | 107 | 0 | 112 | 88 |
| **Total** | **600** | **325** (soma por região) | **0** | **329** | **271** |

Essas 600 previsões são apenas saídas de inferência amostradas nos mapas; **não** são classes verdadeiras nem podem gerar F1-macro sem rotulagem independente.

**Sagrada Família:** foi conferida novamente a sobreposição do polígono original da Area1 com buffer de **25 m** e os segmentos rasterizados: nenhum dos **200 pontos** ou **200 segmentos amostrados** intersectou a área excluída. Isso permite uma futura avaliação cega independente nesses pontos, mas não a substitui.

## Arquivos de saída

Foi criado pacote de entrega na sessão de **17/11/2026** com:
- `REGRESSAO_LOGISTICA_4_REGIOES_TABELAS_F1_500m.xlsx` — Tabelas 1 e 2, folds internos, amostras, protocolos e fontes.
- `RELATORIO_CIENTIFICO_4_REGIOES_LOGISTICA_F1_500m.pdf` — relatório científico.
- `ATLAS_REGRESSAO_LOGISTICA_4_REGIOES.pdf` — quatro páginas de um atlas histórico revisado, excluindo Centro.
- `MAPAS_4_REGIOES_REGRESSAO_LOGISTICA.zip` — quatro GeoTIFFs originais do modelo congelado.
- Três ZIPs QGIS **cegos** com 200 pontos/recortes cada e coluna `bloco_500m`, sem previsões.
- Arquivos privados separados de previsões extraídas dos GeoTIFFs, para aplicação **após** revisão.
- Modelo `.joblib` original, manifesto de treinamento e originais `.gpkg` da Area1.
- Códigos executáveis para reproduzir o agrupamento espacial e avaliar os rótulos após revisão.

No repositório, o script [`validar_logistica_quatro_regioes_500m.py`](./validar_logistica_quatro_regioes_500m.py) fornece cálculo de F1 externo e estimativas de incerteza por bootstrap de grupos espaciais.

**Testes executados:** nove verificações automatizadas passaram. Rótulos **sintéticos de teste do software não foram usados como resultados científicos**.

## Pendência científica que impede concluir F1 externo

Os campos `classe_verificada` dos **600 pontos** estão vazios. Para concluir as três linhas externas da Tabela 2 é imprescindível que um revisor humano independente consulte os recortes RGB e contexto multiespectral, atribua `arvore`, `grama`, `outro` ou `incerto`, registre identidade/data da revisão, e só então as previsões sejam comparadas a esses rótulos. A planilha de F1 externo deve permanecer **pendente** até essa etapa; não usar rótulos preliminares sugeridos por IA.

## Fontes e preservação

- [Area1 — arquivos originais no Drive](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6).
- [Execução de cinco áreas anterior — manter íntegra](https://drive.google.com/drive/folders/1JAcdZwUNqgFfsaJwNqOcsJsUypNqr2mY).
- [Auditoria de cinco áreas em 17/11/2026](./AUDITORIA_PADRONIZACAO_CINCO_IMAGENS_2026-11-17.md).
- [Reprodução de regressão logística original](./RELATORIO_REGRESSAO_LOGISTICA_EXCLUSIVA_5_IMAGENS_2026-11-16.md).

**Não houve nova inferência dos grandes ortomosaicos, nova rotulagem humana ou harmonização física dos sensores nesta rodada.** O PR #6 permanece draft e a `main` preservada.
