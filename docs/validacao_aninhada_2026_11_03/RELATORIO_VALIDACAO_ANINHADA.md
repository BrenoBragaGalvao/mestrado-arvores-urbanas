# Validação espacial aninhada — E2, E3A e E3B (03/11/2026)

## Pergunta

O treinamento supervisionado de árvores versus gramíneas consegue estimar desempenho espacial sem usar informações do teste para escolher algoritmos ou hiperparâmetros? O sobreajuste foi eliminado?

**Resposta:** a seleção de modelos passou a ocorrer apenas nas divisões internas dos dados de treinamento, o que reduz o risco de *vazamento de seleção*. **Não foi demonstrada ausência de overfitting**: algumas diferenças treino–teste continuam relevantes, sobretudo com blocos de 500 m. O mesmo conjunto de dados da Area1 já havia participado de avaliações anteriores; portanto esta é uma validação interna retrospectiva, não um teste geográfico externo cego.

## Por que havia sinais de overfitting?

1. O Random Forest original conseguia F1-macro ≈ 1,0 no treinamento em algumas avaliações, mas apresentava menor F1 nos testes. Profundidade/complexidade elevadas e pequena quantidade de exemplos rotulados favorecem ajuste a peculiaridades dos dados.
2. Apenas 505 objetos rotulados foram usados em cada uma das baterias recentes, provenientes **da mesma área/imagem RGB + NIR**. Apesar de serem objetos diferentes, exemplares próximos podem compartilhar iluminação, vegetação, textura e aquisição; a separação por ID não garante independência espacial.
3. A comparação de muitos classificadores, combinações de atributos e regularizações sobre divisões de teste já conhecidas aumenta o risco de escolher uma configuração otimista por acaso. Isso se chama **sobreajuste ao procedimento de avaliação** ou *viés de seleção*.
4. Quanto maior a distância geográfica avaliada, mais difícil pode ser generalizar, mas a mudança de blocos também modifica quais amostras entram em cada teste. Uma queda de F1 não identifica isoladamente a causa.

## O que foi executado

- Três configurações: E2 — base rotulada derivada de 812 quadrantes de 256 × 256 px; E3A — 119 recortes de até 512 × 512 px; E3B — as mesmas 119 regiões segmentadas em quatro quadrantes de 256 × 256 px.
- 505 amostras supervisionadas por configuração, com classes árvore/gramínea; E2 e E3A/E3B são **bases geométricas diferentes**, embora tenham o mesmo total de registros.
- **30 separações externas** já registradas nos ensaios anteriores: 5 por blocos de 250 m e 5 por blocos de 500 m para cada configuração.
- **540 ajustes internos** (3 divisões internas × 6 candidatos × 30 divisões externas) e **30 ajustes externos** finais após escolher modelo/parâmetros no treinamento.
- Candidatos definidos antes desta etapa: regressão logística com C = 0,02 ou 0,1; SVM RBF com C = 0,05 ou 0,2; KNN com k = 25 ou 35. **Apenas esses três algoritmos** participaram da seleção aninhada; o Random Forest e os demais oito classificadores permanecem na auditoria anterior, sem alegação de que tenham sido corrigidos por esta etapa.
- Em cada divisão externa, agrupamentos geográficos internos e embargo de 25 m excluem vizinhos do treino interno. **E2 usa distância entre geometrias completas; E3A/E3B usam distância entre pontos de referência.** Escalonamento de atributos de SVM/KNN/logística aprende somente com a respectiva amostra de treino pelo `Pipeline`.
- **Não houve IDs compartilhados entre treino e teste, nem blocos externos compartilhados, nas 30 divisões.** O código também audita o embargo externo.
- Não foram descartados resultados desfavoráveis nem alterados os resultados históricos.

## Resultados observados — seleção aninhada (F1-macro)

| Configuração | F1 médio treino | F1 médio teste externo | Diferença | Rodadas com diferença positiva maior que 0,05 |
|---|---:|---:|---:|---:|
| E2 — 812 quadrantes (256 px) | 0,9057 | 0,8788 | +0,0269 | 3/10 |
| E3A — 119 recortes (512 px) | 0,8980 | 0,8873 | +0,0107 | 3/10 |
| E3B — 119 recortes (4 × 256 px) | 0,9038 | 0,8919 | +0,0120 | 2/10 |

**Valores arredondados; médias de dez divisões por experimento.** O F1 de teste descreve exclusivamente o desempenho nos exemplos externos de cada divisão, e não em nova imagem de fora da Area1.

### Sensibilidade à escala dos blocos

| Experimento | Bloco | F1 treino | F1 teste | Diferença |
|---|---:|---:|---:|---:|
| E2 | 250 m | 0,9000 | 0,8911 | +0,0089 |
| E2 | 500 m | 0,9114 | 0,8664 | +0,0449 |
| E3A | 250 m | 0,8892 | 0,9165 | −0,0273 |
| E3A | 500 m | 0,9068 | 0,8580 | +0,0488 |
| E3B | 250 m | 0,8989 | 0,9168 | −0,0178 |
| E3B | 500 m | 0,9087 | 0,8670 | +0,0418 |

Diferenças negativas podem ocorrer por variação na dificuldade dos exemplos de teste. Diferença média próxima de zero **não** garante generalização, pois médias podem esconder diferenças grandes de rodadas individuais.

## O que esta etapa corrige e o que não corrige

**Corrige/mitiga:** seleção de hiperparâmetros feita apenas no treinamento; impedimento de IDs repetidos nas divisões; grupos geográficos disjuntos; exclusão espacial; padronização interna ao `Pipeline`; métricas completas publicadas, sem escolha retrospectiva pela pontuação externa da mesma rodada.

**Não resolve completamente:** dependência espacial residual dentro da mesma imagem; ausência de outros locais/épocas/sensores; resultados externos já observados em trabalhos anteriores; overfitting que ainda aparece nos 8 de 30 testes com diferença positiva superior a 0,05. Mesmo a validação aninhada **não garante** que um classificador generalize fora dessa área.

**Limitação importante de reprodução:** a reexecução auditada e este relatório usam as geometrias históricas do pacote de evidências para E2. O `--modo v2` do script lê a saída da versão progressiva V2 e usa somente centroides para E2; seus resultados futuros podem ser diferentes. A própria V2 ainda requer execução no Colab para reproduzir essa outra rota. Não combinar métricas das duas rotas como equivalentes.

## Como interpretar na dissertação

Evite a frase “eliminamos todo o overfitting”. Prefira: **“Adotamos validação espacial aninhada e regularização para reduzir o risco de sobreajuste e de viés de seleção. Persistiram diferenças entre treinamento e teste em algumas divisões; a generalização independente permanece não demonstrada.”**

## Evidências e reprodução

- Script: [`experimentos/validacao_aninhada_espacial_v2.py`](../../experimentos/validacao_aninhada_espacial_v2.py).
- Saídas: `avaliacoes_externas_aninhadas.csv` (30 resultados externos), `avaliacoes_validacao_interna.csv` (540 avaliações internas), `selecao_apenas_treino.csv` (180 candidatos e decisões), `resumo_aninhado.csv`, `resumo_por_escala.csv` e `manifesto.json`.
- Para reexecutar os números deste documento: use `--modo evidencias --entradas DIRETORIO_EXTRAIDO --out DIRETORIO_SAIDA`. Os arquivos de entrada históricos vieram do pacote de evidências da Area1 e devem estar disponíveis nesse diretório.
- Para nova avaliação diretamente na V2: use `--modo v2 --e2 rotulos_sem_duplicacao.csv --e9 DIRETORIO_E9 --out DIRETORIO_SAIDA`. Esta rota só deve ser considerada concluída quando as saídas efetivas da V2 existirem.