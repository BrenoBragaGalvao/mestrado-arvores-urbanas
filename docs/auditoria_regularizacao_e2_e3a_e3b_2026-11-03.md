# Auditoria de regularização e sobreajuste — E2, E3A e E3B (03/11/2026)

**Status:** reexecução concluída sobre bases **derivadas** da Area1; **não** substitui os testes originais da V2, não mede desempenho em uma segunda AOI e não elimina universalmente overfitting. O código reprodutível foi integrado à V2 como nova etapa opcional, sem alterar as células dos experimentos existentes.

## Proveniência

- Fonte: pacote `AUDITORIA_REGULARIZACAO_E2_E3A_E3B_2026-11-03.zip`, gerado em 03/11/2026, com `E3c_base_rotulada_812.csv`, `E3c_geometrias_rotuladas_812.gpkg`, `amostras_comuns.csv`, `particoes_auditadas.csv` e resultados por rodada.
- 505 exemplos rotulados para E2; 505 referências comuns para E3A/E3B. As geometrias de E2 não são as mesmas geometrias do E9.
- 3 experimentos × 2 receitas pré-definidas (moderada/forte) × 8 classificadores × 2 escalas espaciais (250 e 500 m) × 5 divisões = **480 ajustes finais**, com os mesmos grupos de teste dentro de cada comparação.
- Embargo de 25 m **entre geometrias** em E2 e **entre pontos de referência** em E3A/E3B; nenhuma sobreposição direta de IDs nos 30 testes.
- `StandardScaler` de SVM, regressão logística e KNN é ajustado exclusivamente nos dados de treinamento em cada rodada.
- As duas receitas são fixadas antes desta reexecução, mas foram concebidas **após o conhecimento dos resultados anteriores**. Portanto a análise é exploratória, não validação cega independente.
- O script `experimentos/v2_auditoria_regularizacao.py` foi reexecutado com os arquivos do pacote acima e reproduziu o F1-macro médio **exatamente** (diferença máxima 0,0000 nas 48 médias de experimento × receita × modelo).

## Receita moderada — F1-macro médio de TESTE

| Classificador | E2 250 m | E2 500 m | E3A 250 m | E3A 500 m | E3B 250 m | E3B 500 m |
|---|---:|---:|---:|---:|---:|---:|
| Regressão logística | 0,8879 | 0,8666 | 0,9110 | 0,8546 | **0,9219** | **0,8688** |
| SVM RBF | 0,8908 | 0,8619 | 0,9055 | **0,8572** | 0,9179 | 0,8621 |
| KNN (25) | **0,8972** | 0,8533 | 0,8950 | 0,8440 | 0,9110 | 0,8571 |
| Extra Trees | 0,8266 | 0,8335 | 0,8454 | 0,8195 | 0,8577 | 0,8352 |
| Random Forest | 0,8220 | 0,8240 | 0,8415 | 0,8393 | 0,8356 | 0,8286 |
| HistGradientBoosting | 0,8325 | 0,8246 | 0,8352 | 0,8214 | 0,8610 | 0,8194 |
| Gaussian Naive Bayes | 0,7986 | 0,7400 | 0,8234 | 0,7472 | 0,8251 | 0,7514 |
| Dummy | 0,2980 | 0,2799 | 0,2847 | 0,2791 | 0,2847 | 0,2791 |

**Nota:** o melhor resultado em E3A/500 m é SVM (0,8572), não regressão logística. Os valores são médias de cinco partições por escala, não cinco conjuntos externos independentes.

## Receita forte — comparação treino e teste da regressão logística

| Experimento | F1-macro treino | F1-macro teste | Diferença |
|---|---:|---:|---:|
| E2 — 812 quadrantes (256) | 0,8987 | 0,8748 | 0,0239 |
| E3A — 119 recortes (512) | 0,8915 | 0,8850 | 0,0065 |
| E3B — 119 recortes (4 × 256) | 0,8954 | 0,8921 | 0,0033 |

Médias das dez divisões por experimento. Diferença próxima de zero não é certificado de ausência de sobreajuste; há rodadas individuais com diferenças superiores a 0,05.

## Random Forest — regularização não eliminou sobreajuste

| Experimento | Receita | F1 treino | F1 teste | Diferença |
|---|---|---:|---:|---:|
| E2 | Moderada | 0,8861 | 0,8230 | 0,0630 |
| E2 | Forte | 0,8322 | 0,7455 | 0,0867 |
| E3A | Moderada | 0,8864 | 0,8404 | 0,0460 |
| E3A | Forte | 0,8268 | 0,7601 | 0,0667 |
| E3B | Moderada | 0,8888 | 0,8321 | 0,0568 |
| E3B | Forte | 0,8242 | 0,7502 | 0,0740 |

A receita forte reduziu o desempenho tanto de treinamento como de teste do RF. Isso não é evidência de melhora geral de generalização; pode ser subajuste.

## Como reproduzir no notebook V2

Acesse [`Segmentacao_area_completa_v2_experimentos.ipynb`](../Segmentacao_area_completa_v2_experimentos.ipynb), seção **Auditoria adicional — regularização e sobreajuste**, e execute a célula depois que E9 e a rota progressiva dos 812 quadrantes forem concluídas.

**Atenção às duas rotas do script:**

1. `--modo evidencias`: usa os quatro arquivos derivados do pacote de 03/11/2026 para **reproduzir numericamente estas tabelas**. Requer que o pacote esteja disponível no Drive e extraído. E2 usa embargo geométrico (como a reexecução anterior).
2. `--modo v2`: usa apenas as saídas geradas pelas células atuais da V2, isto é, `outputs/v2_progressivo_256/rotulos_sem_duplicacao.csv` e `outputs/e9_reexecucao_v2/`. **O E2 desta rota usa distâncias entre centroides**, enquanto as tabelas históricas E3c usavam geometrias completas; os números obtidos **podem ser diferentes**. E9 mantém embargo entre pontos. A execução no Colab não foi realizada nesta atualização.

O script exporta `avaliacoes_480_ajustes.csv`, `resumo_todos_modelos.csv`, `resumo_por_escala.csv`, `auditoria_particoes.csv` e `manifesto.json` em pasta nova. Ele **não sobrescreve** os resultados antigos.

## Conclusão metodológica

Os resultados apontam melhor relação entre F1 de treino e teste na regressão logística e no SVM em diversos cenários. Ainda há sobreajuste residual em modelos de árvores; os oito classificadores não estão comprovadamente livres de overfitting. A seleção de um modelo com base em testes já examinados introduz risco de viés de seleção. As métricas descrevem somente generalização espacial interna na mesma Area1; desempenho em outra imagem independente permanece não testado.
