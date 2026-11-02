# V3 — Comparação de alturas estimadas Meta/WRI e ETH Zurich para os mesmos 257 pontos

**Execução registrada:** 2026-11-02T23:34:32.725940+00:00.

**Fontes:** [Meta/WRI CHMv2](https://registry.opendata.aws/dataforgood-fb-forestsv2/) e
[ETH Global Canopy Height 2020](https://langnico.github.io/globalcanopyheight/). Ambas
são **mapas de altura modelada do dossel**, não medidas de campo da mesma árvore.

**Origem ETH dos dados:** COG oficial ETH Zurich (https://libdrive.ethz.ch/index.php/s/cO8or7iOe5dT2Rt/download?path=%2F3deg_cogs&files=ETH_GlobalCanopyHeight_10m_2020_S30W054_Map.tif).

| Indicador | Meta/WRI (pixel de ~1 m) | ETH Zurich (pixel de ~10 m) |
|---|---:|---:|
| Pontos com estimativa disponível | 257 | 139 |
| Mediana (m) | 2.00 | 14.00 |
| Média (m) | 4.61 | 14.28 |
| Estimativas nulas (zero) | 107 | 0 |

**Pares válidos:** 139 dos 257; **ambos positivos:** 101.

**Comparação pareada correta (139 pontos):** as medianas do conjunto completo (Meta: 2 m em 257 pontos; ETH: 14 m em 139 pontos) **não devem ser comparadas diretamente**, porque o universo de pontos é diferente. Restringindo a análise aos **mesmos 139 pontos com estimativas das duas fontes**, os resultados são:

| Indicador — somente os 139 pontos pareados | Meta/WRI CHMv2 (pixel ~1 m) | ETH Zurich 2020 (pixel ~10 m) |
|---|---:|---:|
| Mediana de altura prevista | **6,00 m** | **14,00 m** |
| Média de altura prevista | **6,68 m** | **14,28 m** |
| Valor zero | **38 pontos** | **0 pontos** |

Os **118 pontos sem valor na ETH** correspondem a pixels de **NoData** (código 255 na fonte), não a alturas zero. Dessa forma, a cobertura ETH nos pontos originais é **139/257 = 54,1%**, e a diferença entre as duas fontes só pode ser calculada nos 139 pares. A diferença mediana ponto a ponto (**ETH − Meta**) é **+8 m** e a correlação Pearson nos mesmos pontos é **0,399**. Excluindo os pares com altura zero em uma das fontes, restam **101 pares positivos** (Pearson **0,553**).

A estimativa Meta por máximo em raio de 5 m foi preservada no CSV para análise de sensibilidade, mas **pode corresponder a outra árvore**. Na amostra pareada de 139 pontos, sua mediana é **8 m**, e não equivale diretamente à escala da ETH. Por isso, a comparação principal usa o **valor do pixel da coordenada** em ambas as fontes.

**Interpretação científica:** a ETH estimou valores mais elevados nessa amostra, mas isso **não comprova maior precisão da ETH nem erro da Meta**. Os modelos usam sensores, datas de referência, escalas e máscaras distintas. O pixel ETH de ~10 m pode reunir várias árvores ou superfícies urbanas, enquanto o Meta de ~1 m pode cair na borda da copa. São duas previsões com divergências substanciais e **não observações de altura real**.


**Diferença mediana ETH − Meta:** 8.00 m;
**diferença absoluta mediana entre fontes:** 8.00 m.
Correlação Pearson entre estimativas pareadas: 0.39892518634217783.
Correlação Spearman entre estimativas pareadas: 0.3281504483971268.

**Atenção:** as duas fontes usam modelos, datas e resoluções diferentes. A comparação
de pixels não mede a altura real de 257 árvores nem a precisão individual de cada
produto. O máximo da Meta em 5 m consta do CSV para sensibilidade, mas pode representar
outro indivíduo e não é diretamente comparável ao pixel de 10 m da ETH.
Não calcular MAE/RMSE interpretando um dos mapas como verdade de campo.

**Arquivos:** [tabela pareada](v3_meta_eth_alturas_estimadas_257_arvores.csv);
[resumo estruturado](v3_meta_eth_resumo_257.json);
[dispersão](v3_meta_eth_dispersao.png).
