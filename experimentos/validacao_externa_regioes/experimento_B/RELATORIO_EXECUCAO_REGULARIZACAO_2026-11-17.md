# Experimento B — Regressão Logística / validação espacial Area1 (17/11/2026)

**Execução real e completa da etapa de seleção na Area1; aplicação cartográfica integral externa ainda pendente.**

## Entradas e isolamento científico

Somente **510 pontos originais** Area1 (257 árvore, 253 gramínea), associados aos **505 segmentos Quickshift únicos** (257 árvore, 248 gramínea). A base `rotulos_sem_duplicacao.csv` original teve SHA-256 `a31c197321b8c10ad67cd16ffadf315f8481311a73f1c044e7e050c7179e3c82`. Geometrias `E3c_geometrias_rotuladas_812.gpkg` foram utilizadas para embargo **poligonal real** de 25 metros.

Configurações: 22 candidatas de Regressão Logística com `StandardScaler`, `RobustScaler`, `QuantileTransformer`, L1/L2, C em 0,03/0,1/1 e pesos opcionais. Foram feitas **5 divisões espaciais externas por escala (250/500 m), 3 divisões internas por fold**, sem acessar os rótulos externos CHMv2 para selecionar modelo. Os resultados estão nos CSVs do pacote de reprodução.

## Comparação pareada no mesmo protocolo Area1

| Escala | A fixo (C=0,1, StandardScaler) | B seleção aninhada | Delta B − A | DP B | Gap treino − teste B |
|---|---:|---:|---:|---:|---:|
| 250 m | **0,837553** | 0,829454 | −0,008099 | 0,073685 | 0,028349 |
| 500 m | **0,854234** | 0,853689 | −0,000545 | 0,050086 | 0,010295 |

**Conclusão:** a nova seleção de modelos **não melhorou** o F1-macro espacial interno. O valor histórico do Experimento A 0,856714 (500 m) veio de outra estratégia de seleção por fold; a tabela pareada aqui usa A fixo C=0,1.

**Modelo final B selecionado apenas na Area1:** `StandardScaler() + LogisticRegression(penalty='l1', solver='liblinear', C=1.0, class_weight='balanced', max_iter=4000)`. Arquivo `modelo_B_area1_congelado.joblib` SHA256 `dd5ebd8b1d57bfca952ae23b36d24c6f104e14ac338db0fccb396dda8990cb98`. Ambiente: scikit-learn 1.8.0; numpy 2.3.5; pandas 2.2.3; shapely 2.1.2.

## Diagnóstico externo (sem usar rótulos)

Foi possível aplicar o B aos vetores já extraídos em **500 segmentos auxiliares por região**, sem usar seus rótulos (a seleção local por RGB com IA não é referência confirmada). As classes A e B diferiram em 1/500 em Sagrada Família, 2/500 em Lomba Grande e 2/500 em Cristo Rei. Isso indica previsões bastante semelhantes nesse conjunto restrito, não mede F1 externo.

## F1 geográfico CHMv2 do novo modelo B

| Região | A, F1 CHMv2 conservador | B, F1 CHMv2 | N de referências CHMv2 |
|---|---:|---|---:|
| Sagrada Família | 0,759747 | **Não calculado** | 179 |
| Lomba Grande | 0,778504 | **Não calculado** | 183 |
| Cristo Rei | 0,804240 | **Não calculado** | 181 |

**Por que não há F1 B?** Existem as alturas/pseudo-rótulos CHMv2 de 600 pontos e os rasters de classificação + `segmento_id.tif`, porém os pacotes de mapas não incluem as **três características espectrais de cada segmento**. Também não estavam localmente disponíveis as ortoimagens RGB+multiespectrais integrais das três regiões (a resolução RGB dos arquivos auxiliares é reduzida). Não se pode derivar o resultado B de um mapa binário A. Não inventar mapas ou F1 de B.

## Como concluir

O pacote reproduzível disponível no Drive inclui:
- `experimento_b_validar.py`: seleção de configurações com embargo geométrico;
- `aplicar_B_com_segmentos.py`: recebe o `segmentos.csv.gz` completo da execução original mais `segmento_id.tif`, produz GeoTIFF, novo CSV de predições e F1 de concordância CHMv2 no mesmo conjunto de 200 pontos por região;
- `testes_B.py`: teste sintético de rasterização **aprovado**;
- modelo B e A, bases rotuladas, 10 folds, seleção interna, ranking dos 22 candidatos, diagnóstico de 1500 segmentos e arquivos CHMv2.

[**Pacote integral do Experimento B**](https://drive.google.com/file/d/15MQpuskdZalHbMbmx2NDnEAMBCECqgky/view) | [**Planilha**](https://docs.google.com/spreadsheets/d/1jeHqZLz0UzbC18MYSFJCXjJDyowe7EQu/edit) | [**PDF**](https://drive.google.com/file/d/1jim0V2xtzKpG0Io3ELYFxvafqY-BEHHS/view) | [**Pasta do Drive**](https://drive.google.com/drive/folders/12-XgA4rtQ3r0wzlB9NFzScBd_8nMZQUQ)

## Radiometria

A bateria B4 de calibração física **não foi executada**: faltam as ortoimagens externas integrais e a correspondência PSH → mosaico; não se aplicaram escalas arbitrárias. A viabilidade de uma melhoria radiométrica **não foi testada** nesta etapa.

**Restrições:** não alterar `main`, deixar PR #6 em draft, preservar Experimento A e diferenciar validação interna de concordância automática CHMv2, que não é verdade de campo/humana.
