# E10 — comparação ponta a ponta com o método original (02/11/2026)

## Status

**Código implementado e publicado; execução integral ainda não validada.** Nenhuma métrica nova de E10 está disponível neste registro.

- [Notebook independente V3](../Segmentacao_area_completa_v3_comparacao_ponta_a_ponta.ipynb)
- [Script de avaliação E10](../experimentos/e10_original_vs_v2.py)
- Entradas: somente os dez arquivos já existentes na pasta Area1, e checkpoints derivados da V2 quando disponíveis.

## Etapa A — reconstrução do pipeline global

O notebook usa Quickshift **global** no raster RGB completo (6.942 × 7.294 pixels), com kernel_size=3, max_dist=5 e ratio=0.04. Depois executa vetorização, recorte pela AOI, oito estatísticas RGB/NIR por segmento, K-Means de seis grupos (semente 42, n_init=10), seleção do **cluster 3**, associação às referências e extração das três médias originais: NDVI, brilho HSV e bordas Canny.

**Cuidados históricos:** o código original força IDs de Quickshift para uint16. Se o ID máximo for maior que 65535, há colisão; a V3 corrige para int32 e registra explicitamente que, nesse cenário, não é uma réplica literal da implementação histórica. Também registra versões das bibliotecas e a acurácia do RF obtida com o mesmo protocolo aleatório 80/20, semente 42 e 500 árvores.

## Etapa B — oito modelos no mesmo ambiente

Random Forest (500), SVM RBF, regressão logística, KNN (7), Extra Trees (300), HistGradientBoosting, Gaussian Naive Bayes e Dummy (classe majoritária), com as mesmas três características e os mesmos exemplos por partição. A padronização de SVM, logística e KNN é ajustada **apenas com o treino**.

O script gera dois relatórios distintos: avaliação histórica sobre **pares objeto–rótulo**, potencialmente duplicados, e avaliação sobre **segmentos deduplicados**. As métricas são acurácia, acurácia balanceada, F1-macro, F1, precisão e recall de árvores e MCC. É incorreto equiparar médias entre essas populações.

## Etapa C — comparação pareada original × V2

Se houver checkpoints de quadrantes de 256 pixels em outputs/v2_progressivo_256/tiles, o script recupera os atributos da V2 por ID estável de ponto de referência. O conjunto comum contém somente as referências que sobreviverem à deduplicação de cada braço; os **mesmos IDs** serão usados no treino e teste de ambos.

Protocolos: sorteio 80/20 com semente 42; cinco divisões espaciais por blocos de 250 m e 500 m (quando válidas), semente 2026, com **embargo de 25 m entre pontos de referência**, não entre polígonos completos. Identificadores de segmentos compartilhados por treino/teste em qualquer braço são retirados do treino de ambos. Os resultados de E10 não equivalem ao embargo geométrico do E3c publicado.

Se os checkpoints V2 estiverem ausentes ou incompletos, o manifesto registra a condição; não se deve declarar uma comparação integral. A V2 por quadrantes continua sendo um pipeline diferente, não Quickshift global.

## Cobertura × classificação

Relatar separadamente: referências da Area1 efetivamente cobertas pelo cluster 3, cobertura por classe, segmentos deduplicados e conflitos, referências comuns aos pipelines, e métricas condicionais aos exemplos presentes. A boa acurácia entre candidatos não significa que todos os 510 pontos tenham recebido candidatos.

## Evidências após uma execução real

No Drive, em Projetos/Segmentacao_Breno/outputs/e10_original_vs_v2:

- historico_oito_modelos.csv — oito classificadores sobre pares originais.
- pares_originais.csv — dados de entrada e IDs de referência.
- cobertura_por_classe.csv — cobertura, separada de F1.
- metricas.csv e resumo.csv — avaliações efetivamente calculadas.
- referencias_comuns_original.csv, referencias_comuns_v2.csv, folds_comuns.csv e deltas_f1_pareados.csv — gerados somente quando existir avaliação pareada válida.
- manifesto.json — versões, parâmetros de execução, tamanho das populações, verificações e estado dos checkpoints.

## Limites e próximos cuidados

O Quickshift global sobre aproximadamente 50,6 milhões de pixels pode requerer dezenas de GiB de memória e falhar mesmo em Colab com RAM alta. **A disponibilidade de código não comprova sua execução.** Não substituir segmentação global por quadrantes para declarar reprodução histórica. As diferenças de origem dos rasters e versões das bibliotecas também devem ser verificadas. Não existem medidas de altura real nem geometria dos cabos nesta base; essas afirmações continuam fora do escopo.

**Situação científica:** E10 preparada. Execução global, tabela final dos oito classificadores e deltas ponta a ponta ainda dependem de rodar as células e validar o manifesto.
