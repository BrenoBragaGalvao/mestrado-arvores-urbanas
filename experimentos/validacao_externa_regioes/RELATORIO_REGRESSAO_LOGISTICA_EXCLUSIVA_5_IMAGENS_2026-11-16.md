# Proposta 1 — Regressão Logística exclusiva da Area1 em cinco imagens

> Consolidação verificada em **16/11/2026**. Estes resultados reabrem **um modelo preexistente e cinco GeoTIFFs preexistentes**, sem novo treinamento nesta rodada. A acurácia/F1 externos permanecem pendentes.

## Pergunta de pesquisa

Um único modelo de Regressão Logística treinado com os **257 pontos de árvores** de `Arvores.gpkg` e **253 pontos de gramíneas** de `Grama.gpkg` (Area1; 505 segmentos únicos após deduplicação por Quickshift) consegue discriminar as duas classes em Sagrada Família, Centro de Novo Hamburgo, Lomba Grande e Cristo Rei **sem utilizar amostras de treinamento dessas imagens**?

## Modelo congelado conferido

`sklearn.pipeline.Pipeline([StandardScaler(), LogisticRegression(C=0.1, max_iter=3000, random_state=42)])`

- Objeto binário original: `regressao_logistica.joblib` do [arquivo de modelos Area1](https://drive.google.com/file/d/1Hsn1WQxic6150_fXrqXpkLkaePkTIEl-/view).
- **SHA-256 do joblib:** `2b05ce70f24eacf08753466715934bcceccfe13c9a202d1a178689141022293c`.
- Ordem de features: `mean_intensity` (HSV V), `mean_edges` (Canny), `mean_ndvi` (vermelho banda 3 e NIR banda 4 de DN, não refletância calibrada).
- Segmentação Quickshift em janelas de até 256 × 256 pixels. Saída de 0,5 m por pixel e EPSG:31982.
- O `StandardScaler` faz parte do pipeline salvo: **não reajustar scaler com dados externos**.
- Nenhum dos rótulos locais 250+250 sugeridos por IA foi utilizado para treinar o modelo deste experimento.

## Cinco imagens — predições do mesmo modelo

| Imagem | Segmentos árvore | Segmentos gramínea | Pixels árvore | Pixels gramínea | Árvore prevista (ha) | Gramínea prevista (ha) | Árvore prevista (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Area1 | 54.520 | 77.256 | 18.295.672 | 28.665.265 | 457,39 | 716,63 | 38,96 |
| Sagrada Família | 161.057 | 157.773 | 49.131.084 | 58.018.807 | 1.228,28 | 1.450,47 | 45,85 |
| Centro — Novo Hamburgo | 0 | 317.756 | 0 | 106.687.278 | 0,00 | 2.667,18 | 0,00 |
| Lomba Grande | 317.655 | 296.375 | 94.628.092 | 89.859.591 | 2.365,70 | 2.246,49 | 51,29 |
| Cristo Rei | 202.965 | 132.663 | 59.231.986 | 47.344.448 | 1.480,80 | 1.183,61 | 55,58 |

A contagem acima foi reavaliada por **leitura raster dos cinco GeoTIFFs originais**, conferindo códigos 0/1/2, CRS, resolução, integridade e consistência de contagens. Área calculada como pixels de cada classe × 0,25 m² ÷ 10.000. **Essas áreas são predições binárias: segmentos não vegetados também podem receber uma das duas classes.**

Os cinco mapas e as figuras estão disponíveis em pacotes pré-existentes da [pasta de resultados no Drive](https://drive.google.com/drive/folders/1JAcdZwUNqgFfsaJwNqOcsJsUypNqr2mY). A auditoria de rasters completa está descrita em [AUDITORIA_FINAL_TRANSFERENCIA_CINCO_AREAS_2026-11-16.md](./AUDITORIA_FINAL_TRANSFERENCIA_CINCO_AREAS_2026-11-16.md).

## Único F1-macro medido nesta bateria: validação interna da Area1

| Blocos espaciais | F1-macro médio (± DP) | Acurácia média | Precisão árvore | Revocação árvore |
|---|---:|---:|---:|---:|
| 250 m | **0,8376 ± 0,0631** | 0,8404 | 0,8086 | 0,8633 |
| 500 m | **0,8567 ± 0,0521** | 0,8619 | 0,8721 | 0,8650 |

As médias usam cinco divisões por escala, embargo geométrico de 25 m e seleção de hiperparâmetros dentro do treinamento, conforme `area1_aninhada_divisoes.csv` no pacote dos oito modelos. Os valores **0,8879 e 0,8666 do README histórico** pertencem a outra execução: não devem substituir os valores da bateria de transferência corrigida.

| Região | F1 externo independente | Estado |
|---|---|---|
| Sagrada Família | **Não avaliado** | 200 pontos de teste cego sem rótulos humanos |
| Centro | **Não avaliado** | 200 pontos de teste cego sem rótulos humanos |
| Lomba Grande | **Não avaliado** | 200 pontos de teste cego sem rótulos humanos |
| Cristo Rei | **Não avaliado** | 200 pontos de teste cego sem rótulos humanos |

Os blocos de 250/500 m qualificam **a validação interna da Area1**, não são números a preencher automaticamente nas quatro imagens de transferência.

## Análise científica

1. **Instabilidade no Centro.** A regressão logística atribuiu 100% dos pixels válidos a gramínea. O resultado implica severo deslocamento de domínio e invalida o uso direto desse mapa como inventário de vegetação. Comparar radiometria, histogramas de brilho HSV, NDVI (em DN) e possível máscara explícita de vegetação.
2. **Sobreposição com Sagrada Família.** Antes de estimar F1 externo, excluir os pontos dentro da Area1 + 25 m e os segmentos que tocam o recorte/buffer, para evitar vazamento de referências da origem.
3. **Demais áreas.** Predições aparentemente equilibradas não implicam alta acurácia; validar contra referências independentes. A classificação binária não distingue asfalto, concreto, solo, água, sombra etc.

## Reprodutibilidade e ação necessária para o F1 externo

- [Código para reconstrução do treinamento e aplicações](./executar_proposta1_cinco_areas.py).
- [Notebook de execução no Colab](./proposta1_cinco_areas_colab.ipynb).
- [Preparação/exportação da revisão humana cega](./preparar_rotulacao.py).
- [Cálculo de métricas externas após anotação](./avaliar_regiao.py).
- [Evidência radiométrica por imagem](./bandas_verificadas_jilin.json).
- [Auditoria anterior dos 40 mapas](./AUDITORIA_FINAL_TRANSFERENCIA_CINCO_AREAS_2026-11-16.md).

Abrir os quatro projetos QGIS correspondentes aos 800 pontos reservados, verificar classes `arvore`, `grama`, `outro` ou `incerto` **sem visualizar predições**, salvar os novos GeoPackages e exportar as referências `Arvores.gpkg` / `Grama.gpkg` locais com `preparar_rotulacao.py exportar`. Somente depois executar `avaliar_regiao.py` e extrair o F1 da Regressão Logística; registrar amostras de outras coberturas separadamente.

**Estado de conclusão:** treinamento único já existente e inspecionado; cinco GeoTIFFs verificados; avaliação espacial interna disponível; **generalização geográfica quantitativa ainda não comprovada**.

**Precauções de versão:** branch `feature/validacao-geografica-externa`; manter `main` inalterada e o PR #6 em draft até a conclusão dos testes externos.