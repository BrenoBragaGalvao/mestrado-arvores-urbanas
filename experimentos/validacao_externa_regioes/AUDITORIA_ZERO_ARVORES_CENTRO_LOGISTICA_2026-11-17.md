# Diagnóstico técnico — Regressão Logística: zero árvores no Centro de Novo Hamburgo

**Data:** 17/11/2026. **Escopo:** examinar o resultado de **0 árvores previstas e 317.756 segmentos previstos como gramíneas** no Centro, sem alterar o modelo, os dados, as previsões ou os rótulos.

## Achado

**O zero é efetivamente produzido pelo modelo, não por erro de tabela ou de contagem.** A Regressão Logística treinada exclusivamente com os `Arvores.gpkg` (257 pontos) e `Grama.gpkg` (253 pontos) da Area1 — 505 segmentos rotulados únicos após associação Quickshift — está sendo aplicada **fora do domínio radiométrico do treinamento**.

Conferências independentes nos pacotes do projeto:

- `Area1_modelos_corrigidos_e_validacao.zip`: `regressao_logistica.joblib`, SHA-256 **`2b05ce70f24eacf08753466715934bcceccfe13c9a202d1a178689141022293c`**, contendo `StandardScaler()` + `LogisticRegression(C=0.1, max_iter=3000, random_state=42)`.
- Classes do classificador na ordem `arvore, grama`, atributos na ordem `mean_intensity, mean_edges, mean_ndvi`. Coeficientes para **grama**: `[1,54064174, -1,19504082, 1,04975774]` em coordenadas padronizadas; intercepto `-0,08053043`.
- Média de **brilho HSV V** nos 505 segmentos originais da Area1: `0,01072533`; desvio-padrão `0,00135683`; intervalo das referências `[0,00700023, 0,01666991]`.
- Mediana entre **317.756 segmentos do Centro**: `0,16096441` (**~15× a média da origem**, **110,73 desvios-padrão** acima dela). **100%** desses segmentos estão fora do intervalo de brilho de treinamento.
- Para o vetor de medianas dos atributos no Centro, o *logit* de gramínea é aproximadamente **+162,16**, dominado pelo brilho padronizado. A decisão do modelo é gramínea com probabilidade numericamente próxima a 100%.
- Os dados Jilin-1 auditados indicam produto de **16 bits** para o Centro (PMS03) e **12 bits** para Sagrada Família (PMSR2, cujo raster engloba a Area1). Os números digitais de aquisição não foram harmonizados como refletância. A diferença de profundidade radiométrica **é explicação plausível, não prova de que uma divisão por 16 seja calibração correta**.
- `centro_novo_hamburgo_mapas.zip`: manifesto e `classificacao_regressao_logistica.tif` confirmam `arvore=0`, `grama=317.756`; resolução de 0,5 m e EPSG:31982. As bandas R/G/B/NIR estão declaradas na ordem `3/2/1/4`.
- Reaberto o GeoTIFF e consultado diretamente em coordenadas de **500 segmentos candidatos** contidos no `Amostras_treino.csv` de `03_centro_novo_hamburgo_250_por_classe.zip`: **500 de 500** retornam código `2=grama`; o pipeline carregado retorna `grama` para os 500 vetores. Os 250 candidatos preliminares árvore + 250 gramínea foram sugeridos por IA e têm **0 rótulos humanos verificados**; não constituem verdade-terreno.

## Experimento de sensibilidade — **NÃO USAR COMO CORREÇÃO**

Nos mesmos 500 candidatos, mantendo o classificador e as outras duas features, dividir somente `mean_intensity` por 16 mudou a saída de **0 para 500 previsões de árvore**. Isso mostra **instabilidade extrema de domínio**. Uma simples mudança de escala não cria evidência de acurácia. Não atribuir novas quantidades aos mapas oficiais nem calcular F1 a partir desse teste.

## Comparação radiométrica das cinco imagens

| Região | Brilho mediano | % segmentos fora da faixa de brilho do treino | Segmentos árvore previstos | Segmentos gramínea previstos |
|---|---:|---:|---:|---:|
| Area1 | 0,014270 | 33,81% | 54.520 | 77.256 |
| Sagrada Família | 0,012172 | 28,36% | 161.057 | 157.773 |
| **Centro — Novo Hamburgo** | **0,160964** | **100,00%** | **0** | **317.756** |
| Lomba Grande | 0,008761 | 10,80% | 317.655 | 296.375 |
| Cristo Rei | 0,010048 | 24,44% | 202.965 | 132.663 |

## Recomendações obrigatórias antes de aceitar o mapa do Centro

1. Obter ou localizar parâmetros reais de calibração radiométrica por produto Jilin-1; verificar ganho, deslocamento, faixa de DN e semântica dos bits. A variável brilho atual é calculada a partir de números digitais convertidos para HSV; o NDVI também foi calculado sobre DN, sem calibração de reflectância.
2. Implantar uma **segunda bateria claramente versionada**, com pré-processamento radiométrico padronizado para todas as imagens. Reextrair as três features da Area1, revalidar espacialmente e treinar **exclusivamente com os mesmos 510 pontos originais da Area1**, congelando o novo modelo para aplicação às quatro regiões externas.
3. Preservar os cinco mapas, os resultados anteriores e o modelo original como **Experimento A**; salvar todo novo processamento como **Experimento B**, sem sobrescrever históricos.
4. Não usar percentuais de árvores como substitutos do F1. Continuam pendentes as referências humanas independentes dos **800 pontos cegos** das quatro regiões; em Sagrada Família excluir a Area1 + 25 m e os segmentos intersectantes.
5. Considerar restringir classificação a vegetação confirmada ou definir classe de não vegetação, pois a tarefa binária hoje força ruas, telhados e água a receberem uma das duas classes.

**Estado honesto:** defeito de generalização **diagnosticado em profundidade** e resultado zero confirmado; **a correção calibrada e o F1 externo ainda não foram realizados**. Manter PR #6 em draft e `main` intocada.
