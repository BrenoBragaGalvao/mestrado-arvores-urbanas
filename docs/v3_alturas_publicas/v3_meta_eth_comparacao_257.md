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
