# V3 — Cruzamento exploratório de C3 e altura de dossel Meta/WRI (257 pontos da Area1)

## Escopo e rastreabilidade

Este teste **foi realmente executado em 2 de novembro de 2026**, em um GitHub Actions runner, sem login no Earth Engine. Todos os **257 pontos originais** de `Arvores.gpkg` foram amostrados no produto público [Meta/WRI CHMv2 2026](https://registry.opendata.aws/dataforgood-fb-forestsv2/), baseado em imagens ópticas de alta resolução e IA DINOv3. Artigo: [Brandt et al. (2026), *Scientific Data*](https://doi.org/10.1038/s41597-026-07882-0).

- **Pontos:** [CSV de coordenadas extraídas de `Arvores.gpkg`](../../dados_v3/pontos_area1_257.csv).
- **Mapa amostrado:** [CHMv2, COG público do quadrante `2103121330`](https://dataforgood-fb-data.s3.us-east-1.amazonaws.com/forests/v2/global/dinov3_global_chm_v2_ml3/chm/2103121330.tif), projeção EPSG:3857, pixel de aproximadamente **1,19 m** em coordenadas projetadas.
- **Programa reexecutável:** [Script Python de amostragem](../../experimentos/v3_amostrar_altura_publica.py) e [workflow GitHub Actions](../../.github/workflows/v3_alturas_meta.yml).
- **Resultados originais da amostragem:** [CSV Meta/WRI CHMv2 com 257 linhas](v3_meta_chmv2_estimativas_257_arvores.csv) e [resumo JSON](v3_meta_chmv2_resumo.json).
- **Índice de comparação:** C3 = `2,5 × A^0,4`, onde A é a **área do superpixel Quickshift de 256 px**, extraída na execução exploratória anterior da V3. **Não é área de copa individual comprovada.**
- **Tabela pareada:** [257 pontos — índice C3, área do segmento e alturas Meta](v3_comparacao_c3_meta_257.csv).

## Resultados

| Medida | Resultado |
|---|---:|
| Pontos georreferenciados analisados | **257/257** |
| Altura do dossel prevista no pixel do ponto — mediana | **2,000 m** |
| Altura prevista máxima em raio de 5 m — mediana | **6,000 m** |
| Valor zero no pixel exato | **107/257 (41,634%)** |
| Valor zero mesmo na vizinhança de 5 m | **42/257 (16,342%)** |
| Índice C3 dos superpixels — mediana | **16,981 (índice, NÃO metros)** |
| Superpixels Quickshift tocando borda do quadrante | **79/257 (30,739%)** |
| Correlação de Pearson C3 × altura Meta no pixel | **r = 0,019** |
| Correlação de Spearman C3 × altura Meta no pixel | **ρ = -0,000** |
| Correlação de Pearson C3 × máximo Meta em 5 m | **r = 0,014** |
| Correlação de Spearman C3 × máximo Meta em 5 m | **ρ = -0,001** |

**Leitura preliminar:** nesta correspondência por ponto, não foi observada associação linear ou monotônica relevante entre o **índice C3 baseado em superpixels** e as **estimativas externas de altura do dossel**. Esses coeficientes não validam nem invalidam isoladamente a fórmula como modelo alométrico, pois não comparam grandezas calibradas da mesma árvore. Não realizamos testes de significância nem consideramos os pontos espacialmente independentes.

## Por que apareceram tantos zeros?

O raster CHMv2 é `uint8` sem valor formal `nodata` associado ao quadrante consultado; portanto, **0 é um valor numérico fornecido pelo modelo**, não uma célula sem cobertura. Ele pode estar relacionado a ausência de copa detectada no pixel, deslocamento de georreferenciamento, mudança temporal da arborização, limite do produto ou rótulo pontual que não coincide com o topo de uma copa. **Não é prova de inexistência de árvore.**

O valor **máximo até 5 m** foi calculado apenas como teste de sensibilidade ao posicionamento do ponto. Não significa que aquela altura seja da árvore marcada: pode captar vegetação próxima, inclusive de outro indivíduo.

## Limites científicos e próximos testes

1. **C3 não mede altura**: usa um superpixel Quickshift, que pode abranger gramíneas, sombra ou partes diferentes de uma copa, e os coeficientes não foram calibrados com alturas medidas em Caxias do Sul.
2. **CHMv2 também é uma previsão**, não medição dos mesmos indivíduos. O produto utiliza cenas de diferentes datas; grande parte do material de origem é de 2018–2020. Isso pode divergir da data da imagem Area1 e do cadastro dos pontos.
3. **Geometria e bordas**: 79 superpixels (30,739%) tocam bordas de janelas; isso pode afetar a área calculada e os índices.
4. **Amostragem por ponto versus copa**: o pixel central pode estar fora da copa. Recomenda-se verificar visualmente amostras discordantes e, se viável, delimitar copas individuais e utilizar medidas externas de validação.
5. **Risco elétrico**: nenhum desses resultados mede cabos elétricos, nem identifica risco real. A proximidade a postes continua exploratória.

**Conclusão permitida:** obtivemos uma referência externa modelada para todos os pontos, mas **a fórmula C3 ainda não tem validação empírica como estimativa de altura em metros**. Os resultados indicam a necessidade de revisar a geometria dos objetos e os pressupostos da alometria antes de tratar os índices como alturas.

