# Auditoria complementar — transferência dos oito classificadores da Area1 às cinco imagens (16/11/2026)

## Objetivo

Conferir, sem alterar `main`, os resultados da **bateria treinada exclusivamente com os originais `Arvores.gpkg` e `Grama.gpkg` da Area1**, aplicada a Area1, Sagrada Família, Centro (Novo Hamburgo), Lomba Grande e Cristo Rei. Não misturar com o experimento exploratório de 250+250 referências sugeridas por IA em cada região externa.

**Natureza da intervenção de 16/11:** auditoria REAL de artefatos preexistentes e elaboração de relatório, planilha e atlas. **Não houve novo treinamento de modelos ou execução de Colab nesta sessão**, nem rotulação humana dos pontos de teste. Os oito modelos e os 40 mapas já existiam no Drive.

## Conferências efetivamente executadas

1. **Pontos originais:** os arquivos GeoPackage do pacote de treinamento original foram abertos diretamente. `Arvores.gpkg` contém **257 pontos** e `Grama.gpkg` **253 pontos**, ambos em EPSG:4674; sua associação à grade raster resultou anteriormente em **505 segmentos rotulados únicos**. O pacote de oito modelos documenta 505 segmentos, oito modelos `.joblib`, atributos `mean_intensity`, `mean_edges`, `mean_ndvi`, e treinamento exclusivamente na Area1.
2. **Integridade multiespectral:** arquivo atual `AOI_NEW_MULTI.tif` recuperado do Drive possui **244.532.352 bytes** e SHA-256 **`7ea21cf98989b2257a58764e8a23e06e2ab3776eb79d27fb738b938131f221db`**, exatamente igual ao hash da evidência `bandas_verificadas_jilin.json` e ao `configuracao_execucao.json` no pacote de mapas da Area1. A divergência entre esse tamanho e **237.256.804 bytes** em um manifesto antigo representa um registro de versão anterior; o hash atual confirma o arquivo associado à evidência corrigida, não a reprodução bit a bit de toda a execução.
3. **Leitura integral de 40 GeoTIFFs:** para cada um dos oito arquivos `classificacao_*.tif` em cada uma das cinco regiões, reabriram-se os pixels por blocos; todas as contagens das classes **0/1/2** coincidiram exatamente com `resumo_classes_previstas.csv`, com total de pixels e grade. Todos os rasters auditados estão em **EPSG:31982**, resolução de **0,5 m** e passaram no teste de integridade ZIP.
4. **Totais:** cinco imagens, **1.718.020 segmentos** com predição, **551.862.223 pixels classificados** (as duas classes), **40 mapas consistentes, zero divergências**. As regiões Area1 e Sagrada se sobrepõem, portanto os hectares não formam território único.
5. **Rótulos de validação:** os quatro pacotes `*_QGIS_rotulacao_cega.zip` contêm **200 amostras** cada; os **800 campos `classe_verificada` estão vazios**. F1-macro, precisão e acurácia externos **não disponíveis**, pois não há verdade-terreno independente confirmada.
6. **Sagrada Família:** verificaram-se o polígono real da Area1, sua faixa de **25 m**, os identificadores de segmento e os 200 pontos de teste cego. **0/200 pontos** dentro da zona excluída e **0/200 segmentos selecionados** intersectam a zona; os 200 IDs de segmento são únicos. Nesta recontagem por rasterização geométrica encontraram-se **134.415 segmentos que tocam a zona**, enquanto um manifesto anterior registrava **134.445** — diferença de 30 a reconciliar pela regra exata de rasterização da fronteira. A separação dos **200 pontos selecionados** foi verificada diretamente e não depende dessa diferença de totais.
7. **Deslocamento de domínio:** no Centro, **100%** dos segmentos apresentam `mean_intensity` fora do intervalo min–max da Area1; para `mean_ndvi`, **69,01%**. SVM RBF e Gaussian Naive Bayes atribuem **100% dos pixels válidos** do Centro a árvore, e KNN e regressão logística **0%** — resultado instável incompatível com a interpretação de hectares previstos como inventário arbóreo.

## Resultado por imagem

| Região | Segmentos válidos | Pixels classificados | Oito mapas | F1 externo |
|---|---:|---:|---|---|
| Area1 | 131.776 | 46.960.937 | Confirmados | Não aplicável (origem) |
| Sagrada Família | 318.830 | 107.149.891 | Confirmados | Não avaliado |
| Centro | 317.756 | 106.687.278 | Confirmados | Não avaliado |
| Lomba Grande | 614.030 | 184.487.683 | Confirmados | Não avaliado |
| Cristo Rei | 335.628 | 106.576.434 | Confirmados | Não avaliado |

O F1-macro **interno** da Area1 para o SVM RBF permanece **0,8586** (blocos 250 m) e **0,8689** (blocos 500 m). Esses valores não devem ser copiados para as outras imagens.

## Arquivos finais entregues

Todos em [pasta Drive da entrega de 16/11/2026](https://drive.google.com/drive/folders/1HslLAnqQN8tmKN1CjbaHl3m_H2aRPac-):

- [Relatório científico PDF, com cinco tabelas](https://drive.google.com/file/d/1zVJhSHTkUgEwzMb9cVQaiAN-WnehIv8X/view).
- [Atlas PDF comparativo, com RGB + os oito classificadores em cinco imagens](https://drive.google.com/file/d/1DGDSPgYbKIKdBjnG1v056qDt23J8ElqB/view).
- [Planilha Excel com 40 resultados, métricas internas, domínio, auditoria dos mapas e status externo](https://docs.google.com/spreadsheets/d/198QJj4LP_oOrPYBve2ziGJIdceF328CP/edit).
- [ZIP de entrega científica compacta](https://drive.google.com/file/d/1FiadFeBp8Fr-ZO_zv1cm3WqGxeHZ7BRO/view).
- [Tabela CSV das 40 predições](https://drive.google.com/file/d/10m3SQxSMuECLoeluwM6pCcQ4hvi71nuY/view).
- [Recontagem pixel a pixel dos 40 GeoTIFFs](https://drive.google.com/file/d/1SoFGXwU0XGxMfDnOSX0w0020bgpjpY_q/view).
- [Distribuição espectral](https://drive.google.com/file/d/1ZO63uMtaM_qlcnNYrneDDm4Hancp73Yg/view).
- [Auditoria geométrica de Sagrada](https://drive.google.com/file/d/1tRvwn-bF5oMTKadXM02wGbAQbfGtuJZm/view).
- Cinco ZIPs de mapas GeoTIFF e quatro ZIPs para rotulação QGIS **copiados**, sem alteração, para a mesma pasta.

## O que não foi possível concluir automaticamente

- Rótulos humanos e independentes para os 800 pontos externos. Não atribuir rótulos automaticamente nem confundir consenso dos modelos com verdade-terreno.
- F1-macro externo por algoritmo e por área, precisão, revocação, matriz de confusão externa; depende da anotação independente.
- Declaração de generalização comprovada ou de quantidades verdadeiras de árvores/gramíneas na paisagem: os modelos binários também classificam pavimento, telhado e solo exposto em uma dessas classes.

**Resumo científico:** a viabilidade operacional da transferência foi documentada com 40 mapas íntegros; a generalização geográfica permanece **não testada com referências independentes**. Recomenda-se revisão cega no QGIS e avaliação externa usando os modelos congelados. Manter o PR em rascunho e a `main` intacta.
