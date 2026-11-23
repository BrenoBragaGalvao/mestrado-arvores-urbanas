# Proposta 1 — Regressão Logística com treino filtrado pelo CHMv2

**Execução:** 17/11/2026. **Regiões:** Area1, Sagrada Família, Lomba Grande, Cristo Rei. **Centro excluído.**

## Seleção dos 510 pontos originais

Da base original de **510 pontos** (257 árvores e 253 gramíneas), associados a **505 segmentos Quickshift únicos**, foram retidos **371 segmentos** que concordaram com o Meta/WRI CHMv2: **160 árvores** (altura máxima em raio de 5 m >=5 m) e **211 gramíneas** (altura máxima <=0,5 m).

Separados **139 pontos**: 83 com altura intermediária, 52 discordantes e 4 duplicatas restantes conforme critério de priorização do motivo. O mapeamento de pontos para segmentos foi feito por proximidade geométrica, com distância máxima <16 m e verificação da classe original.

Os rótulos originais foram preservados, e o CHMv2 atuou exclusivamente como filtro; não foram inventados rótulos humanos nem pontos externos de treinamento.

## F1-macro da Area1 (protocolo pareado)

| Blocos | Modelo A treinado na base completa | Modelo filtrado treinado só com pontos CHMv2 concordantes | F1 filtrado testado apenas nos pontos retidos (tendência otimista) |
|---|---:|---:|---:|
| 250 m | 0.8376 | 0.8398 | 0.8887 |
| 500 m | 0.8542 | 0.8410 | 0.8907 |

Cinco divisões por escala, 25 m de embargo **geométrico**, separação espacial fixa de treino/teste, mesma receita Regressão Logística C=0,1 e StandardScaler. **O teste primário da Area1 contém todos os segmentos originais reservados no fold**, inclusive os que o CHMv2 rejeitou; portanto o novo F1 250/500 representa desempenho sobre a população original de referências.

## F1-macro externo em 500 candidatos por região (avaliação auxiliar, NÃO é o teste cego de 200)

| Região | Candidatos com pseudo-rótulo CHMv2 | A (base completa) | Retreino filtrado | Diferença |
|---|---:|---:|---:|---:|
| Sagrada Família | 488 | 0.9528 | 0.9569 | +0.0041 |
| Lomba Grande | 482 | 0.9454 | 0.9394 | -0.0060 |
| Cristo Rei | 492 | 0.9817 | 0.9898 | +0.0081 |

### Limitação central

As **1.500 amostras candidatas externas** já tinham sido selecionadas anteriormente em manchas de vegetação homogêneas e interpretadas preliminarmente por IA. O CHMv2 concorda fortemente com esses rótulos iniciais e os F1 podem ser artificialmente altos devido ao protocolo de escolha dos pontos. Esses números NÃO substituem a avaliação geográfica realizada nos **600 pontos cegos** (200 por região).

Os 600 pontos cegos possuem alturas CHMv2 e previsões do **modelo A** já calculadas (F1 0,7597 / 0,7785 / 0,8042), mas não têm a matriz completa NDVI + HSV + Canny associada às suas IDs nesta entrega. **Por isso não foi recalculado o F1 do novo modelo filtrado nesses 600 pontos**. Preencher essa lacuna requer reextrair características espectrais em cada um desses 600 segmentos nas ortoimagens e congelar a referência. Não extrapolar os valores dos 500 candidatos para esses 200 testes.

### Conclusão metodológica

A filtragem CHMv2 manteve 371/510 referências originais e produziu resultados parecidos com a base completa. O F1 da Area1 subiu ligeiramente em 250 m e caiu em 500 m. Nas amostras fáceis externas, dois resultados aumentaram e um diminuiu. Isso **não comprova melhora geral da capacidade de generalização geográfica**.

### Artefatos e reproducibilidade

- `2010_pontos_alturas_chmv2.csv`: alturas efetivamente extraídas de dois mosaicos CHMv2, incluindo os 510 pontos originais e 1500 candidatos externos.
- `RESULTADOS/auditoria_510_originais_chmv2.csv`: classes humanas originais, altura automática e motivo de retenção/exclusão.
- `RESULTADOS/base_filtrada_area1.csv`: 371 segmentos para treino e seus três atributos.
- `RESULTADOS/regressao_logistica_Area1_filtrada_CHMv2.joblib`: modelo final refitado somente com os pontos retidos.
- `RESULTADOS/validacao_espacial_area1_A_vs_filtrado.csv`: dez divisões espaciais pareadas; tests com geometrias.
- `RESULTADOS/f1_externo_CANDIDATOS_500_A_vs_filtrado.csv`: 3 × 500 candidatos com pseudorreferência CHMv2.
- `RESULTADOS/comparacao_pareada_1500_candidatos_IC.csv`: ICs de diferença F1 via bootstrap espacial 500m.
- `RESULTADOS/pontos_originais_retidos_371_CHMv2.gpkg` e `pontos_originais_separados_139_CHMv2.gpkg`: camadas QGIS com pontos originais.

Fonte Meta/WRI CHMv2: https://registry.opendata.aws/dataforgood-fb-forestsv2/
Repositório: https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas