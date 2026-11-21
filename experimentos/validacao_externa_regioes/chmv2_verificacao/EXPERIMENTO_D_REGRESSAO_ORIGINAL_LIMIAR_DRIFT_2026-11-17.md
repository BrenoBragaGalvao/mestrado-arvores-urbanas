# Experimento D — tentativa de melhorar a Regressão Logística original (500 m)

**Data:** 17/11/2026. **Objetivo:** preservar o classificador original treinado na Area1 (510 pontos, 505 segmentos Quickshift únicos) e testar intervenções sem retreiná-lo com CHMv2 ou regiões externas.

## Procedimento

- Modelo **A original**: `StandardScaler + LogisticRegression(C=0.1,max_iter=3000,random_state=42)`; atributos `mean_intensity`, `mean_edges`, `mean_ndvi`; limiar inicial 0,500 para a classe gramínea.
- **Limiar otimizado:** busca de limiar 0,25–0,75, passo 0,025, escolhida **só com Area1**. Validação espacial aninhada de 500 m, 5 divisões externas × 3 internas, embargo geométrico de 25 m; em cada divisão externa o limiar é selecionado nas divisões internas. **Limiar final congelado = 0,575**, escolhido por CV espacial de 500 m usando Area1 inteira, sem rótulos externos.
- **Clip p01/p99:** truncamento de NDVI, brilho HSV e bordas Canny nos percentis 1% e 99%, calculados **só sobre os dados de treinamento da Area1**. Aplicado apenas na entrada do modelo original, sem alterar sua padronização e coeficientes; não é calibração radiométrica física.
- Os **400 pontos externos** com atributos disponíveis, 200 Sagrada e 200 Lomba, foram recuperados do ZIP que o pesquisador executou no Colab. O modelo A foi reproduzido com **zero divergências em 400** em relação aos mapas originais. Os pseudo-rótulos de avaliação são Meta/WRI CHMv2, não validação humana.

## Resultados: F1-macro de 500 m

| Região | A original | Limiar fonte | Clip p01/p99 |
|---|---:|---:|---:|
| **Area1 — CV espacial interno** | **0,8542** | **0,8651** | 0,8542 |
| Sagrada Família — 179/200 elegíveis CHMv2 | **0,7597** | 0,7314 | 0,7424 |
| Lomba Grande — 183/200 elegíveis CHMv2 | 0,7785 | 0,7152 | **0,7843** |
| Cristo Rei | 0,8042 (histórico) | **Não executado** | **Não executado** |

**Atenção:** o F1 Area1 0,8651 é a média de cinco testes espaciais aninhados, com limiares escolhidos de modo independente em cada fold; não é uma avaliação externa do limiar final 0,575. As métricas externas são de **concordância com pseudo-rótulos CHMv2** e não são diretamente equivalentes ao F1 interno Area1. Foram usados os mesmos pontos externos para comparar as variações, sem qualquer seleção baseada nos rótulos externos.

### Intervalos de confiança da diferença para o modelo A original

Bootstrap pareado por blocos de **500 m** com **10.000** reamostragens. Refletem incerteza amostral, mas **não** os erros do CHMv2.

| Região | Intervenção | Δ F1 | IC 95% |
|---|---|---:|---|
| Sagrada Família | Limiar 0,575 | −0,0283 | [−0,0524; −0,0060] |
| Sagrada Família | Clip p01/p99 | −0,0174 | [−0,0706; +0,0366] |
| Lomba Grande | Limiar 0,575 | −0,0633 | [−0,0995; −0,0315] |
| Lomba Grande | Clip p01/p99 | +0,0058 | [−0,0109; +0,0264] |

## Auditoria espectral

Entre os 200 segmentos por região, o brilho HSV ultrapassou o intervalo mínimo-máximo das amostras de treinamento da Area1 em **20,5% de Sagrada** e **10,5% de Lomba**. O NDVI ultrapassou em **25,5%** e **2,0%**, respectivamente. A diferença das distribuições reforça a necessidade de auditoria de radiometria de origem, mas **não comprova** quais fatores de calibração deveriam ser usados nos ortomosaicos.

## Decisão

**Manter o modelo A original** como principal. Os testes não mostram ganho consistente de generalização. Não promover a nova variante por ganhos locais observados depois de consultar os pseudo-rótulos externos. Para uma validação conclusiva, completar Cristo Rei e revisar referências externas de maneira independente; correções radiométricas exigem metadados/cadeia original confiáveis.

**Reprodutibilidade:** base e modelo imutáveis `Area1_modelos_corrigidos_e_validacao.zip`; dados externos `resultado_final_600_pontos_500m-20261117T200128Z-1-001.zip` (fornecido no chat). Códigos e planilhas com tabelas por divisão, atributos e matrizes foram gerados em pacote separado para o pesquisador. **Nenhum arquivo histórico ou branch main foi alterado.**
