# Execução sequencial derivada — Area1 (31/10/2026)

## Escopo, reprodutibilidade e limites

Foi executada uma **nova bateria de testes com os dez arquivos já existentes na pasta `Area1`**, sem solicitar imagens, rótulos, alturas medidas ou geometria de cabos adicionais.

**Importante: NÃO foi uma execução integral, célula a célula, do notebook `Segmentacao_area_completa_v2_experimentos.ipynb`.** Para não ultrapassar a memória local, aplicou-se o Quickshift original `kernel_size=3, max_dist=5, ratio=0.04` a **223 recortes independentes de 256×256 pixels**, correspondentes a todas as janelas que continham os **510 pontos de referência existentes**. Esses recortes representam uma fração do raster completo; seus limites cortam segmentos e alteram a geometria dos objetos.

O pipeline derivado não aplicou o filtro fixo de `kmeans_cluster == 3` na classificação E1–E4. O K-Means foi recalculado na amostra de recortes e os IDs dos seus clusters não são diretamente comparáveis aos IDs históricos. As métricas **não podem ser comparadas diretamente** à acurácia histórica 0,87 do notebook original. Treino e teste continuam restritos à mesma área geográfica, mesmo com bloqueio espacial.

## E1 — Auditoria dos rótulos

- **40.842** segmentos extraídos, dos quais **40.551** apresentaram os oito atributos RGB/NIR finitos para K-Means.
- **510** associações ponto–segmento; **505** segmentos rotulados únicos após retirar cinco registros duplicados; **257** árvores e **248** gramíneas.
- **0** segmentos com conflito de classe; **3** IDs de segmento compartilhados em uma divisão aleatória por registros simulada nessa base derivada (semente 42).
- Random Forest de 500 árvores, cinco separações estratificadas distintas: **F1-macro médio 0,8909**, desvio-padrão **0,0426**. Esses testes não têm independência espacial.

## E2 e E3 — Validação espacial e comparação dos modelos

Blocos de **250/500 m**, cinco partições por escala, com exclusão de objetos de treinamento em até **25 m** dos objetos de teste. Foram **dez partições válidas**, sem exclusões de rodadas.

| Bloco | Modelo | F1-macro médio | Desvio-padrão |
|---:|---|---:|---:|
| 250 m | Random Forest (500) | 0,8627 | 0,0322 |
| 250 m | SVM RBF | 0,8946 | 0,0278 |
| 250 m | Regressão logística | **0,8981** | 0,0119 |
| 250 m | Dummy majoritário | 0,2903 | 0,0429 |
| 500 m | Random Forest (500) | 0,8499 | 0,0524 |
| 500 m | SVM RBF | **0,8970** | 0,0508 |
| 500 m | Regressão logística | 0,8963 | 0,0468 |
| 500 m | Dummy majoritário | 0,2899 | 0,0435 |

Os modelos receberam as mesmas partições de teste. SVM e regressão logística padronizaram os atributos **somente a partir do treino**. As diferenças acima são **descritivas, não provas estatísticas de superioridade nem resultados da V2 integral**.

## E4 — Ablação dos atributos

Foram testadas as **sete combinações não vazias** de NDVI, brilho HSV e bordas Canny, nos mesmos dez testes espaciais, com RF, SVM e regressão logística. A combinação completa apresentou o maior F1-macro médio entre as combinações estudadas para esses três classificadores. A seleção da melhor configuração no próprio conjunto avaliado é exploratória.

## E5 — Sensibilidade de Quickshift e K-Means

- Quickshift: piloto anterior com **20 execuções** (quatro recortes × cinco configurações), já documentado em [resultados_piloto_area1_2026-10-31.md](resultados_piloto_area1_2026-10-31.md).
- K-Means recalculado sobre **40.551 segmentos válidos** dos 223 recortes: silhouette amostral **0,3611 (K=4)**, **0,3314 (K=6)**, **0,3011 (K=8)**. ARI relativo a K=6: **0,3480 / 1,0000 / 0,6037**.
- Silhouette mede agrupamento, **não acurácia de classificação**.

## E6 — Sensibilidade da proximidade com postes

Foram localizados **7.594** postes dentro da AOI. Com o índice empírico **C3 potencial > 7**, obtiveram-se, nos recortes, **39.951 segmentos candidatos**, ou **35.996** quando exigida a previsão `arvore`. As contagens únicas próximas a postes foram:

| Critério | Raio | Segmentos próximos | Postes distintos próximos |
|---|---:|---:|---:|
| C3 > 7, todas as classes | 1 m | 3.594 | 2.398 |
| C3 > 7, todas as classes | 3 m | 6.181 | 2.462 |
| C3 > 7, todas as classes | 5 m | 8.839 | 2.535 |
| C3 > 7 e previsão árvore | 1 m | 3.401 | 2.323 |
| C3 > 7 e previsão árvore | 3 m | 5.832 | 2.429 |
| C3 > 7 e previsão árvore | 5 m | 8.327 | 2.514 |

Esses números são de **segmentos dos recortes**, não de árvores distintas fisicamente verificadas. O RF foi reajustado a todos os segmentos rotulados disponíveis para gerar previsões espaciais exploratórias.

## E7 — Alometria: 216 cenários

Compararam-se as 12 expressões C1–C6 (potencial/linear), índices de limiar 5/7/9, com e sem filtro de árvore, em distâncias planimétricas de 1/3/5 m a postes. Foram geradas **216 linhas de sensibilidade**, com seleção de segmentos, proximidade e índice de Jaccard relativo a C3 potencial > 7.

Os coeficientes empíricos **não são calibração de altura com medições reais**; não há MAE/RMSE/R² de altura validado. Proximidade 2D a postes **não prova interferência em cabos ou risco elétrico**. Os recortes podem truncar copas.

## E8 — Consolidação e trabalho ainda necessário

Esta execução por recortes disponibilizou dados reais, métricas pareadas e a documentação da metodologia derivada. Os scripts, gráficos, JSON, CSV e relatório completo são fornecidos em pacote reproduzível ao pesquisador.

**Pendente:** executar integralmente a **V2 no Colab** com o raster completo, gerando suas variáveis e resultados efetivos de E1–E7, conferindo eventuais erros. A bateria derivada não substitui essa exigência do orientador. Revisão bibliográfica, hipóteses e contribuição científica devem distinguir claramente o que os testes suportam do que a ausência de alturas medidas e de cabos impossibilita validar.

Nenhum notebook nem `README.md` foi alterado durante esta bateria.