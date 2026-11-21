# Proposta 1 — Resultados calculados de concordância com Meta/WRI CHMv2 (17/11/2026)

**Execução real:** [GitHub Actions run #44135492871](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/actions/runs/44135492871), sucesso. O job baixou e abriu os CHMv2 públicos `2103121330.tif` e `2103123110.tif`, amostrou **600 pontos de teste externos**, extraiu altura do pixel e máximo e mediana no raio horizontal de 5 m, cruzou com **previsões congeladas** da Regressão Logística treinada **somente na Area1** e calculou as métricas. **Nenhum modelo foi retreinado, nenhum ponto foi rotulado por humano nesta execução.**

## Tabela 2 — Regressão Logística

| Imagem | F1-macro 250 m | F1-macro 500 m | Protocolo |
|---|---:|---:|---|
| Area1 (Caxias do Sul) | **0,8376** | **0,8567** | Validação espacial interna da Area1 (protocolo corrigido) |
| Sagrada Família | Não aplicável | **0,7597** | Concordância externa com pseudo-rótulos CHMv2, regra B |
| Lomba Grande | Não aplicável | **0,7785** | Concordância externa com pseudo-rótulos CHMv2, regra B |
| Cristo Rei | Não aplicável | **0,8042** | Concordância externa com pseudo-rótulos CHMv2, regra B |

**Nunca apresentar os três F1 externos como acurácia validada por campo/humano**. Eles comparam o modelo com uma estimativa independente de altura, com falso-zero e cobertura urbana não vegetada, e não com verdade-terreno humana. Os blocos 500 m organizam a amostragem externa, mas **não constituem cinco folds de retreino**. O F1 da Area1 deriva de validação espacial interna e difere conceitualmente dos externos.

## Estratégias: comparar sensibilidade aos pseudo-rótulos

- A0: altura **máxima** CHMv2 na vizinhança horizontal de 5 m = **0 m** → candidata gramínea, **maior que 0** → candidata árvore. Ambos podem estar errados, sobretudo o zero com NoData.
- A05: corte **0,5 m**, numericamente igual a A0 no raster uint8 inteiro.
- B: altura máxima = **0 m** → candidata gramínea, **altura ≥5 m** → candidata árvore; alturas 1 a 4 m → incertas, excluídas. O **5 m** é limiar vertical experimental, distinto do **raio horizontal de 5 m** usado para amostrar o CHMv2. O zero continua ambíguo mesmo em B.

| Região | F1 A0 simples | F1 B conservadora | N total | N avaliados B | Excluídos B | Blocos 500 m |
|---|---:|---:|---:|---:|---:|---:|
| Sagrada Família | **0,7193** | **0,7597** | 200 | 179 | 21 | 78 |
| Lomba Grande | **0,7591** | **0,7785** | 200 | 183 | 17 | 140 |
| Cristo Rei | **0,7606** | **0,8042** | 200 | 181 | 19 | 107 |
| **Total** | 600 pseudo-rótulos | **543 pseudo-rótulos incluídos** | **600** | **543** | **57** | — |

As taxas de inclusão da regra B são **89,5%**, **91,5%** e **90,5%**, respectivamente.

## Matrizes de confusão B

Ordem de linhas (pseudo-referência CHMv2) e de colunas (classificador LR): **árvore, gramínea**.

- Sagrada Família (n=179): `[[69, 9], [34, 67]]` ⇒ F1-macro **0,7597465**, acurácia de concordância **0,7597765**.
- Lomba Grande (n=183): `[[61, 4], [36, 82]]` ⇒ F1-macro **0,7785040**, acurácia de concordância **0,7814208**.
- Cristo Rei (n=181): `[[83, 13], [22, 63]]` ⇒ F1-macro **0,8042397**, acurácia de concordância **0,8066298**.
- Total (n=543): `[[213, 26], [92, 212]]` ⇒ F1-macro agrupado **0,782688**. Não confundir esse agregado com validação externa humana.

## Fonte e integridade dos rasters

- Meta/WRI CHMv2 público: [AWS Data for Good](https://registry.opendata.aws/dataforgood-fb-forestsv2/), [espelho COG com zeros potencialmente NoData](https://source.coop/tge-labs/meta-chm-v2).
- `2103121330.tif` — EPSG:3857, pixel 1,19432857 m, uint8, sem NoData explícito, **254.215.030 bytes**, SHA-256 `b19bf9828015d7b3df781f5901769171d9d887624d6e5a2d7f1b0e4ed9fc9045`.
- `2103123110.tif` — EPSG:3857, pixel 1,19432857 m, uint8, sem NoData explícito, **221.497.684 bytes**, SHA-256 `382d24d7760c8fe3ead22eb3c63376f2dce9849949c27e9b922e6d36681b7089`.
- A rotina transforma o centro dos pixels para EPSG:31982 antes de verificar o raio horizontal real de 5 m; os 600 registros continham altura utilizável segundo o tratamento do raster, embora zero seja ambíguo.

## Artefatos verificáveis

- [Planilha final no Drive: seis abas, 600 pontos, alturas, matrizes e F1](https://docs.google.com/spreadsheets/d/1bnfcR-4wdijTLj9IT1W5DK099aQ2HFY1/edit).
- [Relatório científico resumido](https://drive.google.com/file/d/1_XLIAIKZrws6cwi4KQ9ZOZNA9GYDfAaX/view).
- [CSV real com 600 amostras, alturas e pseudo-rótulos](https://drive.google.com/file/d/12XkzXM7CIoyGvlCUWyWjhC4v7Bb_Oi-J/view).
- [Pacote bruto JSON+CSV do workflow](https://drive.google.com/file/d/1olcgZK-f0oftrjjzcV5HB9X8WdY7AJM-/view).
- [Script reprodutível](./executar_chmv2_github_actions.py), [GitHub Actions workflow](../../../.github/workflows/chmv2-f1-quatro-regioes.yml).

**Ressalva essencial:** o [README do mestrado](../../../README.md#sec-4-2-1) documenta 42 de 257 pontos originais de **árvore** com CHMv2 = 0 em toda a vizinhança de 5 m. Uma referência automática de gramínea baseada em zero não é válida como verdade-terreno sem verificação independente. Os resultados aqui fornecem **análise complementar de concordância/proxy** e evidência exploratória de transferência, **não validação externa conclusiva**.

**Histórico preservado:** modelo LR e GeoTIFFs A anteriores, `main` intacta, PR #6 em draft.
