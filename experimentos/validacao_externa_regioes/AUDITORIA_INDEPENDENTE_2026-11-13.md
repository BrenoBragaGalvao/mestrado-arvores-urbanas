# Auditoria independente complementar — Proposta 1 (13/11/2026)

## Escopo e natureza da verificação

Esta auditoria é uma **verificação complementar de artefatos produzidos anteriormente**, não uma nova execução do Google Colab, não um novo treinamento e **não uma validação externa**. Foram examinados os arquivos existentes na [pasta de resultados do Drive](https://drive.google.com/drive/folders/1JAcdZwUNqgFfsaJwNqOcsJsUypNqr2mY), preservando dados originais, saídas históricas e a branch `main`.

### Verificações feitas diretamente sobre os pacotes

- Cinco ZIPs `*_mapas.zip`: CRC de todas as entradas aprovado; cada pacote contém oito `classificacao_*.tif`.
- Os **40 GeoTIFFs** foram abertos para verificar dimensões em relação ao manifesto de cada área, CRS **EPSG:31982**, resolução **0,5 × 0,5 m** e uma banda classificatória por arquivo.
- Para o **SVM RBF em cada uma das cinco áreas**, foram lidos todos os blocos de pixels para recontar classes `0`, `1` e `2`. As contagens de árvores e gramíneas coincidiram exatamente com `resumo_classes_previstas.csv`, e a soma coincidiu com `verificacao_resultados.json`.
- O ZIP `Area1_modelos_corrigidos_e_validacao.zip` contém os **oito arquivos .joblib**, a base tabular de 505 segmentos, saídas de validação espacial aninhada e manifestos. Isso comprova presença dos artefatos, **não a reprodução independente do treinamento**.
- `Tabelas_Figuras_e_Reproducao.zip` contém as métricas, o relatório, ambiente e versões, logs e tabelas para as cinco imagens.
- Os quatro ZIPs de rotulação cega contêm **200 amostras CSV e 200 recortes RGB cada**. Os 800 campos `classe_verificada` inspecionados estavam vazios; IDs das amostras não se repetem dentro de cada região. O pacote de Sagrada Família registra exclusão da Area1, buffer de 25 m e **134.445 segmentos interceptantes excluídos**, conforme manifesto. A verificação independente de exclusão geométrica de todos os pontos ainda não foi refeita nesta auditoria.
- O pacote de auditoria espectral contém XMLs de origem Jilin-1, com `FUSMethod=B-G-R-NIR`, e evidências de correspondência de canais com os rasters. O vínculo por hash foi apresentado pela execução anterior; **aqui não foram recalculados os hashes de todos os rasters brutos**.

## Recontagem independente dos pixels SVM RBF

| Área | Segmentos declarados | Pixels árvore (recontados) | Pixels gramínea (recontados) | Pixels válidos |
|---|---:|---:|---:|---:|
| Area1 · Caxias do Sul | 131.776 | 43.862.986 | 3.097.951 | 46.960.937 |
| Sagrada Família · Caxias do Sul | 318.830 | 96.952.248 | 10.197.643 | 107.149.891 |
| Centro · Novo Hamburgo | 317.756 | 106.687.278 | 0 | 106.687.278 |
| Lomba Grande · Novo Hamburgo | 614.030 | 126.045.052 | 58.442.631 | 184.487.683 |
| Cristo Rei · São Leopoldo | 335.628 | 96.591.354 | 9.985.080 | 106.576.434 |
| **Total** | **1.718.020** | **470.138.918** | **81.723.305** | **551.862.223** |

Os valores acima são **predições de um classificador específico**, não contagens de árvores reais nem métricas de acurácia. Classes `1=árvore prevista` e `2=gramínea prevista`; `0=sem predição`. Em particular, o SVM RBF classificou **100% dos pixels válidos do Centro como árvore**, reforçando a necessidade de validação externa e cautela frente à mudança de domínio.

## Resultados internos registrados, não recalculados nesta auditoria

A execução corrigida da Area1 documenta **510 pontos originais**, **505 segmentos únicos**, separações externas espaciais de **250 m e 500 m** (cinco folds por escala), subdivisões internas para hiperparâmetros e **embargo geométrico de 25 m**. Na tabela `validacao_area1_comparacao.csv`, SVM RBF apresenta F1-macro médio de **0,8586** (250 m) e **0,8689** (500 m). Esses valores são de **validação espacial interna** e não estimam F1-macro nas quatro regiões externas. Os resultados históricos permanecem metodologicamente distintos.

## Pendência de rastreabilidade a conferir

Existe diferença entre o tamanho de `AOI_NEW_MULTI.tif` apresentado pela **metainformação do arquivo original no Drive** (**244.532.352 bytes**) e o tamanho mencionado em `resumo_execucao_treinamento.json` (**237.256.804 bytes**). **A causa não foi identificada.** Antes da redação final da dissertação, recalcular o SHA-256 da origem atual e confrontá-lo com `7ea21cf98989b2257a58764e8a23e06e2ab3776eb79d27fb738b938131f221db`, preservando ambos os arquivos; se diferirem, investigar a versão efetivamente processada. Diferença no tamanho **não demonstra, por si só, divergência nos pixels ou erro de treinamento**.

## Limitações científicas pendentes

1. Rotular, por examinadores humanos independentes e cegos às previsões, as 800 amostras externas (preferencialmente com controle de desacordo e revisão), sem transferir rótulos da Area1.
2. Confirmar geometricamente a exclusão de todos os pontos amostrais da Sagrada Família e dos segmentos que interceptem Area1 + 25 m; a execução anterior registra a exclusão, mas esta verificação complementar não a refez.
3. Calcular F1-macro externo, precisão, revocação e confusão por área/modelo **somente** após rótulos independentes suficientes, documentando casos `outro`/`incerto`, desenho amostral e classes avaliáveis.
4. Interpretar os mapas de duas classes como **predições condicionadas**, não inventários de cobertura do solo. Pixels de edifícios, pavimento, água ou solo exposto podem receber `árvore` ou `gramínea`. Áreas em hectares são áreas **previstas**, não áreas de vegetação verificadas.
5. Investigar o deslocamento radiométrico entre sensores/regiões, especialmente no Centro, e deixar explícito que o índice calculado com números digitais não corresponde necessariamente a NDVI de reflectância calibrada.
6. Reexecutar o treinamento/validação em ambiente isolado de reprodução se for exigida comprovação independente de métricas, versões e hiperparâmetros. A inspeção de artefatos não substitui a reexecução do Colab.

**Conclusão operacional:** os arquivos analisados sustentam que existem oito modelos salvos e mapas para cinco áreas, e a checagem raster independente reforça a integridade dos mapas SVM; a **generalização geográfica permanece cientificamente não comprovada**. O PR deve permanecer em rascunho até essas pendências serem tratadas.
