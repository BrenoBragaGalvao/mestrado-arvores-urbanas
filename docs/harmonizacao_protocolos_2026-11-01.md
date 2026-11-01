# Harmonização metodológica dos experimentos — 01/11/2026

> **Escopo:** comparação de algoritmos com **métricas homogêneas e a mesma base experimental derivada**. Não é uma reprodução do Quickshift monolítico nem da acurácia histórica obtida com 458 pares.

## Por que os números históricos e atuais eram diferentes?

No protocolo histórico documentado no notebook, `train_test_split(..., test_size=0.2, random_state=42)` e `RandomForestClassifier(n_estimators=500, random_state=42)` geraram uma acurácia reportada de **0,87** em **458 registros** (366 treino, 92 teste). Na bateria E3c posterior, foram utilizados **505 segmentos rotulados únicos** de um Quickshift independente por quadrantes e uma separação espacial por blocos.

Mudaram simultaneamente a **origem dos segmentos, a base supervisionada, a separação treino/teste e a métrica destacada**. Portanto, **0,87 de acurácia não pode ser interpretado como maior ou menor que 0,8656 de F1-macro**.

## Experimento controlado executado

A harmonização utiliza **somente os 505 segmentos da bateria derivada da Area1**, mantendo os atributos brilho HSV, bordas Canny e NDVI. Os oito modelos são avaliados **nas mesmas divisões e com as mesmas métricas dentro de cada protocolo**.

- **Novo:** 40 ajustes, oito classificadores × cinco divisões aleatórias 80/20 (sementes 42, 2026, 43, 44 e 45), sem estratificação, com segmentos previamente deduplicados. A semente 42 reproduz a **regra** histórica na base nova, não as amostras históricas.
- **Reaproveitado:** 240 ajustes E3c anteriormente executados, com blocos de 250/500 m, cinco divisões por escala e embargos geométricos de 0/25/50 m. Foram rechecadas a população, as divisões de 250 m e a primeira divisão de 500 m, e reexecutados **seis resultados pontuais** (RF, SVM e logística) sem divergência numérica significativa. A maioria dos 240 ajustes foi **reutilizada**, não reexecutada nesta harmonização.
- **Teste da proximidade:** entre 71 e 85 objetos de treinamento estavam a até 25 m das geometrias de teste nas cinco divisões aleatórias. Isso evidencia ausência de embargo espacial, **não** compartilhamento de IDs entre treino/teste ou inflação causalmente comprovada.

### Resultado principal: F1-macro médio dos mesmos 505 segmentos

| Modelo | Aleatório 80/20 | Espacial 250 m, embargo 25 m | Espacial 500 m, embargo 25 m |
|---|---:|---:|---:|
| SVM (RBF) | **0,8945** | **0,8987** | **0,8668** |
| Regressão logística | 0,8887 | 0,8928 | 0,8664 |
| KNN (7) | 0,8905 | 0,8874 | 0,8502 |
| Extra Trees | 0,8824 | 0,8790 | 0,8629 |
| Random Forest | 0,8827 | 0,8656 | 0,8530 |
| HistGradientBoosting | 0,8609 | 0,8556 | 0,8524 |
| Gaussian Naive Bayes | 0,8608 | 0,8555 | 0,8398 |
| Dummy (maioria) | 0,3229 | 0,2980 | 0,2799 |

| Modelo | Acurácia média aleatória | Acurácia espacial 250 m / 25 m | Acurácia espacial 500 m / 25 m |
|---|---:|---:|---:|
| Random Forest | 0,8832 | 0,8697 | 0,8591 |
| SVM (RBF) | 0,8950 | 0,9022 | 0,8716 |
| Regressão logística | 0,8891 | 0,8964 | 0,8712 |

**Nota:** cinco divisões por protocolo, não cinco amostras independentes. Dentro de cada protocolo, a comparação dos oito modelos é pareada. **Entre protocolos**, as amostras de teste mudam; a diferença de médias não é efeito causal isolado do método de separação.

### Reproduzir a regra histórica do RF no novo conjunto (sem reproduzir o resultado histórico)

No conjunto derivado de **505 segmentos**, executando o RF com os parâmetros originais e o split aleatório da semente **42**, foram obtidos **404 treino, 101 teste**, acurácia **0,9010**, F1-macro **0,9009**, F1-árvore **0,8980** e F1-grama **0,9038**. Isso é **novo resultado**, não uma atualização da acurácia histórica **0,87** baseada em 458 pares.

### Efeito descritivo do embargo mantendo o teste fixo por divisão espacial

| Bloco | Modelo | 0 m | 25 m | 50 m |
|---|---|---:|---:|---:|
| 250 m | RF | 0,8807 | 0,8656 | 0,8694 |
| 250 m | SVM | 0,9026 | 0,8987 | 0,8990 |
| 500 m | RF | 0,8566 | 0,8530 | 0,8572 |
| 500 m | SVM | 0,8688 | 0,8668 | 0,8647 |

Dentro da mesma rodada espacial, o embargo altera o **conjunto de treinamento**, mantendo os mesmos objetos de teste. A ausência de monotonicidade é uma observação descritiva, não um resultado estatisticamente generalizável.

## O que podemos concluir?

1. A comparação **entre classificadores dentro do mesmo protocolo** agora usa métricas compatíveis e o mesmo conjunto de objetos derivados.
2. SVM apresenta F1-macro médio maior que RF nas três configurações ilustradas, mas sem prova de superioridade universal ou significância estatística.
3. A execução histórica do conjunto de 458 pares **não foi reproduzida** e não pode ser usada como baseline numérico diretamente comparável. Sua reprodução exata exigiria conservar os mesmos segmentos, atributos e partição do ensaio histórico.
4. Como não há rótulos para **fundo urbano**, altura real ou geometria de **cabos**, os resultados não estabelecem taxa operacional de falsos positivos nem risco elétrico.

## Como reproduzir

O pacote `harmonizacao_metodologica_2026-11-01.zip` contém o **script Python efetivamente executado**, as três entradas derivadas do pacote E3c, 280 linhas de métricas harmonizadas (40 novas e 240 reutilizadas), verificações dos protocolos, resultados pontualmente recalculados, resumo, gráfico e manifesto de hashes. Não contém os rasters pesados originais. O script usa somente dados previamente extraídos da `Area1`.

**Nota de proveniência:** os números do pacote harmonizado e da bateria E3c foram produzidos por Quickshift independente em quadrantes de 256 × 256 pixels, e **não** pelo fluxo monolítico inteiro da V2. A discussão final da dissertação deve manter essa distinção.


---

## Complemento E9 — comparação pareada da escala de segmentação

Foi executado posteriormente um experimento E9 que compara, **nos mesmos 505 pontos de referência e nas mesmas divisões de teste**, o Quickshift contínuo aplicado a 119 regiões de 512 × 512 px com Quickshift independente em quatro quadrantes de 256 × 256 px. Foram **320 avaliações** em 20 protocolos, envolvendo os mesmos oito classificadores.

O Random Forest obteve F1-macro médio de **0,8906 vs. 0,8835** (blocos de 250 m) e **0,8657 vs. 0,8566** (blocos de 500 m), nas condições contínuo versus quadrantes, com embargo entre pontos de 25 m. Entretanto, o SVM apresentou desempenho maior com quadrantes, demonstrando que o efeito da escala de segmentação depende do classificador.

**Limite mantido:** o teste E9 isola a escala em recortes de 512 px; não reproduz o Quickshift monolítico sobre todo o raster, o filtro global K-Means cluster 3 nem os 458 pares históricos. Por isso, **a acurácia 0,87 não se tornou diretamente comparável** com E9.

Consulte a [documentação e o fluxograma completos do E9](comparacao_controlada_segmentacao_512_vs_256_2026-11-01.md).
