# Plano de experimentos — somente os dados existentes em Area1

**Regra:** não solicitar ou incorporar novas imagens, bases públicas, rótulos, medições de campo ou geometrias de linhas elétricas. Trabalhar exclusivamente com os arquivos já utilizados no notebook.

## Preservação
- `Segmentacao_area_completa.ipynb`: referência original, não editar.
- `Segmentacao_area_completa_v2_experimentos.ipynb`: cópia independente para a evolução dos experimentos.
- `README.md`: não editar sem autorização expressa.
- Script auxiliar E1 em `experimentos/e1_auditoria_amostras.py`, sem mudanças nas células existentes.

## Sequência
| ID | Situação | Objetivo | Como avaliar com Area1 |
|---|---|---|---|
| 0 | Concluído | Preservar notebook original e cópia V2 | Comparação dos blobs na criação |
| E1 | Código preparado; **não executado** | Verificar segmentos repetidos, rótulos conflitantes e compartilhamento entre treino/teste; reavaliar RF | `df` e `gdf_arvore_seg_filter` do notebook; 5 sementes, F1, acurácia balanceada |
| E2 | **Código implementado na V2; não executado** | Validar independência espacial na mesma AOI | Blocos de 250/500 m, faixa de exclusão de 25 m, até 10 partições por escala, F1 e acurácia balanceada |
| E3 | **Código implementado na V2; não executado** | Comparar classificadores sobre mesmas partições | RF (500 árvores), SVM RBF com padronização, regressão logística e Dummy majoritário; mesmas partições espaciais 250/500 m, embargo 25 m, 3 atributos, acurácia balanceada/F1 |
| E4 | **Código implementado na V2; não executado** | Verificar contribuição de atributos | 7 combinações não vazias de brilho HSV, bordas Canny e NDVI; RF, SVM, regressão logística e Dummy majoritário; partições E2/E3 de 250/500 m com exclusão 25 m; diferenças pareadas de F1-macro, acurácia balanceada e recall |
| E5 | **Pilotos parciais executados com Area1 (4 recortes); E5 integral pendente** | Avaliar sensibilidade de parâmetros | Quickshift: 5 configurações em até 4 janelas fixas de 256×256 px; K-Means: K=4/6/8 na mesma amostra de até 1.500 segmentos originais com 8 atributos RGB/NIR; tempo, distribuição, ARI, silhouette, memória de arrays |
| E6 | **Código implementado na V2; não executado** | Auditar a proximidade planimétrica a postes | 1, 3 e 5 m; candidatos C3>7 sem filtro de classe, candidatos árvore e gramínea; `sjoin_nearest` nos dois sentidos para contar polígonos e postes distintos; gráfico comparativo |
| E7 | **Código implementado na V2; não executado** | Analisar sensibilidade da alometria | Recalcular e conferir 12 expressões históricas (C1–C6, potencial/linear); limiares 5/7/9 de índice; filtros com/sem classe árvore; 1/3/5 m de postes; Jaccard e contagens únicas; gráficos |
| E8 | Pendente | Consolidar resultados e discussão dos gaps | Tabelas, limitações e relação com métodos da literatura |

## Limitações científicas
- Acurácia histórica de 0,87 sobre 92 registros de teste não é resultado novo nem comprova generalização.
- Registros objeto-rótulo podem repetir o mesmo segmento. O E1 investiga isso, mas mesmo o teste sem duplicação **não elimina dependência espacial**.
- Os arquivos atuais incluem postes, não cabos; a análise trata de **proximidade em planta a postes**, não de risco elétrico confirmado.
- Não há medidas reais de altura nos arquivos documentados; os modelos C1–C6 permitem **análise de sensibilidade**, não validação de altura.
- Se validação de altura/cabos for inviável com estes dados, registrar a limitação explicitamente na dissertação em vez de inventar medidas.

## Como executar E1 no Colab
Após terminar as células originais da **V2** (com o Drive já montado e usando apenas `Area1`):

```python
!wget -q -O /content/e1_auditoria_amostras.py https://raw.githubusercontent.com/BrenoBragaGalvao/mestrado-arvores-urbanas/main/experimentos/e1_auditoria_amostras.py
%run -i /content/e1_auditoria_amostras.py
```

O `wget` baixa apenas **código**, não dados de pesquisa. O script usa os objetos `df` e `gdf_arvore_seg_filter` produzidos pelo notebook e imprime os resultados no Colab. Esses resultados **ainda não foram executados ou confirmados**.

## Como executar E2 no Colab

1. Abra [`Segmentacao_area_completa_v2_experimentos.ipynb`](../Segmentacao_area_completa_v2_experimentos.ipynb) no Colab.
2. Monte o Drive existente e execute as células originais para produzir `df` e `gdf_arvore_seg_filter` com os mesmos arquivos de `Area1`.
3. Execute as **duas últimas células de código E2**, começando em **E2a** (preparação dos segmentos e geometrias) e terminando em **E2b** (separações espaciais).
4. Registre quantas partições foram válidas, blocos, tamanhos de treino/teste, amostras excluídas pela faixa de 25 m e as métricas. Caso alguma partição não contenha as duas classes, reporte-a como descartada.

**Estado atual:** a implementação foi publicada, mas nenhuma execução completa ou métrica E2 foi verificada. As células usam somente os dados originais já disponíveis e não solicitam novos dados. A validação por blocos dentro de `Area1` é uma análise espacial interna, não substitui uma validação em localidade externa.

## Como executar E3 no Colab

1. Abra a [V2 experimental](../Segmentacao_area_completa_v2_experimentos.ipynb) no Colab.
2. Execute o notebook original incorporado à V2 com a pasta `Area1` já existente; em seguida, execute **E2a** para reconstruir a base de segmentos únicos e geometrias projetadas.
3. Execute **E3a** para comparar, em cada partição idêntica, Random Forest, SVM RBF, regressão logística e classificador Dummy (classe majoritária). SVM e regressão logística ajustam a padronização exclusivamente nos registros de treinamento.
4. Execute **E3b** para obter diferenças pareadas de F1-macro e gráficos por tamanho de bloco.
5. Caso E2b também tenha sido executada, E3a confere se os valores do Random Forest coincidem exatamente entre os protocolos.

**Estado E3:** código publicado, ainda **não há execução confirmada com os arquivos originais de `Area1` nem resultados novos verificados**. As partições de teste são internas à mesma área e podem se repetir, de modo que as médias e os desvios-padrão apresentados são exploratórios, não provas de generalização externa nem testes de significância independentes.

**Etapa seguinte implementada:** E4, ablação de NDVI, brilho HSV e bordas Canny, preservando dados, particionamentos espaciais e modelos de referência.

## Como executar E4 no Colab

1. Abra a [V2 experimental](../Segmentacao_area_completa_v2_experimentos.ipynb) no Google Colab, monte o Drive e execute as células do fluxo original sobre os **arquivos já existentes** da pasta `Area1`.
2. Execute **E2a**, responsável pela construção de `base_e2` com geometrias projetadas e segmentos únicos. As execuções de E2b e E3 são opcionais para E4; se E3 estiver executada, haverá uma checagem de igualdade das métricas do conjunto com três características.
3. Execute **E4a**: sete subconjuntos não vazios de `mean_intensity` (brilho HSV), `mean_edges` (bordas Canny) e `mean_ndvi` (NDVI), com **Random Forest, SVM RBF, regressão logística e Dummy majoritário**. O Dummy é ajustado uma única vez por partição, pois sua previsão não depende dos atributos.
4. Execute **E4b** para calcular diferenças de F1-macro por partição em relação à combinação completa, a variação ao retirar cada atributo e gráficos para blocos de 250 e 500 metros.
5. Registre a quantidade de partições válidas e descartadas, além da média e desvio-padrão *descritivos* das métricas por modelo e subconjunto de atributos.

**Estado E4:** notebook atualizado e publicado; **não foram executados** os dados reais no Colab nesta etapa, portanto não existem métricas novas verificadas. Essa comparação continua sendo uma validação espacial interna de classificação árvore/gramínea, não uma comprovação da acurácia de altura ou do risco elétrico.

**Etapa seguinte implementada:** E5 — testes exploratórios de sensibilidade do Quickshift e do K-Means, sem reprocessamento completo da imagem para cada configuração.

## Como executar E5 no Colab

1. Abra a [V2 experimental](../Segmentacao_area_completa_v2_experimentos.ipynb) e execute a sequência do notebook original com os arquivos já existentes de `Area1` no Drive.
2. Execute **E5a**, que seleciona de forma determinística até quatro janelas de `256 × 256` pixels perto das referências existentes de árvores/gramíneas, aplicando `(kernel_size,max_dist,ratio)` em cinco configurações: `(2,5,0.04)`, `(3,3,0.04)`, **`(3,5,0.04)` original**, `(3,8,0.04)` e `(4,5,0.04)`. Registra número/tamanho de segmentos, fração de segmentos de menos de 10 pixels, duração e bytes dos arrays retidos.
3. Execute **E5b**, que obtém até 1.500 polígonos fixos da segmentação original; extrai médias e desvios-padrão de quatro bandas da imagem multiespectral original; compara `KMeans(n_clusters=4|6|8, random_state=42, n_init=10)` na **mesma amostra**. Registra inércia, silhouette amostral, ARI com a partição de seis clusters, tempo e tabulação exploratória frente a rótulos existentes.
4. Registre a quantidade real de janelas e segmentos utilizáveis, mensagens de erro e valores somente **após executar** o Colab; os testes não geram novas medidas de altura nem classes anotadas.

**Interpretação e limites:** os resultados de Quickshift nas janelas **não** validam a segmentação da imagem completa; mudar a segmentação modifica a identidade dos objetos e exigiria refazer extração de atributos e associação com rótulos para medir F1/accuracy diretamente. Os números dos clusters K-Means são arbitrários; ARI/silhouette medem estrutura do agrupamento e não acurácia de detecção. Amostras rotuladas que se intersectam podem não ser independentes. Os tempos dependem do ambiente e os bytes dos arrays não são medida exaustiva de RAM/pico de memória.

**Estado E5 (31/10/2026):** pilotos locais com os dados reais executados em quatro janelas (20 execuções Quickshift) e com 779 segmentos para K-Means. Os dados e as limitações estão em [resultados_piloto_area1_2026-10-31.md](resultados_piloto_area1_2026-10-31.md). **Esses resultados não substituem a execução integral da E5 da V2 nem produzem resultados para E1–E4 ou E6–E7.**

**Etapa seguinte implementada:** E6 — auditoria da proximidade a postes nas distâncias de 1, 3 e 5 m, com e sem o filtro `predicted_classe == 'arvore'`, contando localizações e segmentos distintos.

## Como executar E6 no Colab

1. Abra a [V2 experimental](../Segmentacao_area_completa_v2_experimentos.ipynb) e execute o fluxo original com a pasta `Area1` já existente, até criar `tree_polys`, `filter_tree` e `Postes` após reprojeção e recorte para a área de interesse.
2. Execute **E6a**, que copia a seleção de segmentos C3 > 7, distingue as previsões `arvore` e `grama` e realiza `gpd.sjoin_nearest` nos dois sentidos (polígono→poste e poste→polígono), com raio máximo de 5 metros.
3. Confira a quantidade de segmentos com C3 > 7, distribuição das classes do RF e quantidade de pontos distintos de postes. Coordenadas iguais de postes são contadas como **uma localização**, evitando inflar os totais.
4. Execute **E6b**, que prepara a tabela de comparação entre seleção histórica e seleção filtrada por árvore, calcula as diferenças em segmentos/postes e produz gráficos para 1, 3 e 5 metros. As contagens são de IDs únicos e devem ser não decrescentes conforme aumenta o raio.
5. Anote os números resultantes **somente após executar** o notebook com os arquivos reais. A E6 independe de E1–E5 e não modifica `filter_tree` nem o Random Forest histórico.

**Interpretação:** `Power_tree_size_C3 > 7` é um limiar de estimativa empírica de porte, e não uma medida de altura real. `predicted_classe == 'arvore'` representa uma previsão do classificador, não confirmação de campo. As distâncias são de polígonos a **pontos de postes**, não de copas aos cabos energizados; não se pode afirmar risco elétrico operacional a partir delas. Postes próximos de ambas as classes podem ser contabilizados em ambos os subconjuntos e, portanto, seus totais não devem ser somados para reproduzir a categoria geral.

**Estado E6:** **código publicado, sem nova execução integral ou resultados reais verificados**. O experimento só utiliza os dados da `Area1`, já existentes no projeto.

**Etapa E7 implementada:** análise de sensibilidade das 12 expressões alométricas e dos limiares de índice, sem alegar medição ou validação de altura.

## Como executar E7 no Colab

1. Abra a [V2 experimental](../Segmentacao_area_completa_v2_experimentos.ipynb) e execute o fluxo histórico com os arquivos **já existentes** da pasta `Area1`, até criar `tree_polys` (com `area`, `predicted_classe` e C1–C6 nas formas potencial/linear) e `Postes` após reprojeção e recorte da AOI.
2. Execute **E7a**: valida áreas geométricas e CRS, confirma os valores das **12 expressões originais**, deduplica localizações de postes e constrói uma única relação objeto–poste até 5 m usando interseção espacial com buffers seguida da distância geométrica exata.
3. Execute **E7b**: compara limiares **5, 7 e 9** dos índices empíricos para as versões **C1–C6 × potencial/linear**; em cada cenário considera tanto todos os candidatos quanto apenas os previstos como árvores, contabilizando segmentos e postes distintos em **1, 3 e 5 m**. Compara conjuntos selecionados e suas diferenças com a **referência C3 potencial > 7** usando Jaccard. Se a E6 já tiver sido executada, confere possíveis divergências entre os resultados de referência.
4. Execute **E7c**: visualize a quantidade de segmentos classificados como árvore próximos de postes por expressão (limiar 7, raio 5 m) e a sensibilidade do modelo C3 aos diferentes limiares.
5. Registre os resultados de `tabela_e7` **somente após a execução real no Colab**. O código não altera `tree_polys`, `filter_tree`, `Postes` ou a classificação existente e não grava arquivos de entrada.

**Estado E7:** notebook V2 publicado com E7a/E7b/E7c, **sem execução integral dos dados de `Area1` ou métricas verificadas até o momento**. A matriz contém 12 expressões × 3 limiares × 2 cenários de classe × 3 distâncias, isto é, **216 linhas previstas**, condicionadas a dados e geometrias válidos.

**Limites científicos:** `C1–C6` são **estimativas empíricas não calibradas**, e os limiares 5/7/9 são critérios numéricos para sensibilidade — **não alturas observadas em metros**. Nenhuma contagem, Jaccard ou distância a poste permite inferir erro da estimativa de altura ou interferência com cabos. Para essa dissertação, não apresentar MAE/RMSE/R² de altura com esses dados, pois não há alturas reais documentadas.

**Próxima etapa:** E8 — consolidação científica dos resultados **depois da execução** das etapas preparadas. A publicação de código, sozinha, não responde à exigência do orientador de apresentar resultados de testes em dados reais. Antes de redigir conclusões de desempenho, executar E1–E7 com `Area1`, verificar erros, salvar métricas e registrar limitações.

## Registro de execução parcial em 31/10/2026

Foram conferidos os dez arquivos já existentes em `Area1` no Google Drive. Com eles, foram executadas e documentadas **20 combinações janela × Quickshift** (4 recortes de 256×256 pixels × 5 parâmetros) e a análise K-Means de **779 segmentos** extraídos dos mesmos recortes (K=4,6,8). As métricas confirmadas e as ressalvas constam do [relatório de resultados preliminares](resultados_piloto_area1_2026-10-31.md).

**E1–E4, E6–E7 continuam com código preparado e aguardando execução integral.** A etapa E8 deverá usar somente métricas reais verificadas, nunca confundir a média de segmentos, silhouette ou ARI dos recortes com acurácia de classificação da imagem completa. É necessário executar a V2 no Colab com `Area1` antes de declarar concluída a validação experimental solicitada pelo orientador.

## Execução sequencial derivada (31/10/2026)

Foram realizados **experimentos adicionais derivados por 223 recortes de 256×256 px**, cobrindo os **510 pontos de referência existentes** na `Area1`, sem novos dados. Essa bateria inclui auditoria de duplicados E1 (505 objetos rotulados únicos), dez partições espaciais E2, classificadores E3 (RF/SVM/LogReg/Dummy), sete ablações E4, sensibilidade K-Means E5, proximidade E6 e 216 cenários alométricos E7. Os resultados estão em [execucao_sequencial_derivada_area1_2026-10-31.md](execucao_sequencial_derivada_area1_2026-10-31.md), e scripts/CSV/gráficos foram entregues em pacote reproduzível na conversa.

**Distinção obrigatória:** esta foi uma implementação **derivada**, com Quickshift aplicado separadamente por recorte e sem a pré-seleção histórica do cluster 3 nos testes de classificação. Portanto, **não significa que o notebook V2 foi executado integralmente**, e não autoriza comparação direta com seus 0,87 históricos. O estado de E1–E7 na tabela acima continua descrevendo a **V2, cujo código está preparado e cuja execução integral permanece pendente**.

**Próxima tarefa científica:** executar no ambiente Colab, com memória suficiente e sem novos dados, o notebook V2 integral sobre a `Area1`; conferir os registros e comparar resultados sob protocolos correspondentes. Não reivindicar validação de altura nem risco elétrico sem dados que os suportem.
