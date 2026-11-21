# Proposta 1 — Auditoria independente da padronização das cinco imagens (17/11/2026)

**Objeto:** regressão logística treinada **somente** com os 257 pontos originais de `Arvores.gpkg` e 253 de `Grama.gpkg` da Area1, e aplicada sem novo treinamento a Area1, Sagrada Família, Centro de Novo Hamburgo, Lomba Grande e Cristo Rei. **Nenhum dado original, raster ou modelo anterior foi alterado.**

## Resultado geral

A execução local de 17/11/2026 auditou os arquivos ZIP disponíveis de treinamento e dos cinco mapas, abriu e recontou os pixels dos **cinco GeoTIFFs de regressão logística** com `rasterio`, examinou os **XMLs Jilin-1** dos produtos PSH e verificou os **quatro pacotes QGIS de 200 referências externas**. Os rasters têm resolução nominal **0,5 m** e CRS **EPSG:31982**, com códigos de predição `1=arvore`, `2=grama`, `0=sem predição`. As contagens reproduzem as tabelas guardadas no pacote de resultados.

Além disso, a montagem das 510 referências originais retornou **505 segmentos únicos** (257 árvore e 248 gramínea). Com `StandardScaler()+LogisticRegression(C=0.1,max_iter=3000,random_state=42)`, o novo ajuste nos **mesmos 505 vetores de atributos históricos** produziu **diferença numérica zero** em coeficientes e médias do scaler, e **previsões idênticas** às do `regressao_logistica.joblib` previamente arquivado. SHA-256 do modelo: `2b05ce70f24eacf08753466715934bcceccfe13c9a202d1a178689141022293c`. Isso **não significa** que os grandes rasters externos tenham sido reprojetados, resegmentados ou processados novamente nesta auditoria.

O multiespectral atual da Area1, arquivo GeoTIFF `uint16` com 4 bandas, tem SHA-256 **`7ea21cf98989b2257a58764e8a23e06e2ab3776eb79d27fb738b938131f221db`**, coincidente com o registro da execução corrigida. O `ColorInterp` em GDAL não prevalece sobre a confirmação espectral independente registrada no `bandas_verificadas_jilin.json` quando a ordem do produto de origem é outra; usar a ordem documentada **R,G,B,NIR = 3,2,1,4** na cadeia validada.

## Quantitativos comprovados (Experimento A — modelo e mapas preservados)

| Imagem | Segmentos árvore | Segmentos gramínea | % pixels árvore | % pixels gramínea |
|---|---:|---:|---:|---:|
| Area1 | 54.520 | 77.256 | 38,96% | 61,04% |
| Sagrada Família | 161.057 | 157.773 | 45,85% | 54,15% |
| **Centro — Novo Hamburgo** | **0** | **317.756** | **0,00%** | **100,00%** |
| Lomba Grande | 317.655 | 296.375 | 51,29% | 48,71% |
| Cristo Rei | 202.965 | 132.663 | 55,58% | 44,42% |

São **predições em segmentos** e proporções de pixels de uma **classificação binária**, não inventário real de cobertura arbórea. Ruas, telhados e outras superfícies válidas também são forçadas a uma das duas classes.

## Validação interna da Area1 — execução corrigida (cinco divisões espaciais por escala)

| Escala | F1-macro médio | Desvio-padrão entre divisões | Acurácia média |
|---|---:|---:|---:|
| 250 m | **0,8376** | 0,0631 | 0,8404 |
| 500 m | **0,8567** | 0,0521 | 0,8619 |

Médias recalculadas do CSV `area1_aninhada_divisoes.csv` no ZIP `Area1_modelos_corrigidos_e_validacao.zip`. Esses resultados **não substituem nem são comparáveis diretamente** aos valores do README histórico **0,8879** e **0,8666**, que pertencem a outra bateria.

## Diagnóstico radiométrico das cinco imagens

| Imagem | Mediana brilho HSV V | % segmentos fora do intervalo de brilho das referências Area1 |
|---|---:|---:|
| Area1 | 0,014270 | 33,81% |
| Sagrada Família | 0,012172 | 28,36% |
| **Centro** | **0,160964** | **100,00%** |
| Lomba Grande | 0,008761 | 10,80% |
| Cristo Rei | 0,010048 | 24,38% |

A média de brilho HSV nos **505 segmentos de treinamento** é `0,0107253`, desvio-padrão `0,0013568` e máximo `0,0166699`. A mediana no Centro é aproximadamente **15×** maior que a média do treinamento. O classificador atribui coeficiente positivo de **1,54064** ao brilho já padronizado na decisão de gramínea. Assim, a escala das entradas do Centro produz um **deslocamento de domínio** muito grande e explica a predição degenerada em 100% gramínea. O número zero **não é erro de contagem**, porém **não é estimativa confiável de inexistência de árvores**.

## Descoberta da auditoria dos XMLs Jilin-1

O pacote `Auditoria_espectral_e_sobreposicao.zip` contém metadados PSH do fornecedor Jilin-1 com **`AbsCalibrationGain` e `AbsCalibrationBias` de quatro bandas**, além de `DataBits`, `RadiometricMethod=REL` e `FUSMethod=B-G-R-NIR`.

| Região (sensor) | Bits | AbsCalibrationGain na ordem B,G,R,NIR | AbsCalibrationBias na ordem B,G,R,NIR |
|---|---:|---|---|
| Centro (PMS03) | 16 | 0.004216, 0.003932, 0.006515, 0.010486 | 0.225934, -0.039235, 0.333449, 0.763029 |
| Sagrada Família (PMSR2) | 12 | 0.104669, 0.073641, 0.052772, 0.035538 | 1.589489, 1.278448, 0.940444, 0.794275 |
| Lomba Grande (PMSR3) | 12 | 0.104082, 0.075333, 0.052695, 0.035304 | 1.975902, 1.598464, 1.281063, 0.626867 |
| Cristo Rei (PMSL3) | 12 | 0.105552, 0.076065, 0.052793, 0.035422 | 2.003799, 1.613983, 1.283432, 0.628966 |

**Limite técnico decisivo:** tais coeficientes pertencem aos **produtos PSH originais**, e não foi comprovado que a escala/offset/bandas dos **ortomosaicos processados** pelo PCI Geomatica conservam diretamente esses mesmos valores. Portanto **NÃO aplicamos ganhos nem biases aos mosaicos**, **NÃO dividimos brilho por 16** e **NÃO geramos mapas corrigidos sem uma cadeia radiométrica defensável**. A existência dos coeficientes muda o plano de verificação: confrontar pixels pareados do produto PSH com o ortomosaico, por banda e por cena, para documentar a transformação já aplicada.

## Revisão externa e embargo de Sagrada Família

Os quatro pacotes `*_QGIS_rotulacao_cega.zip` contém **200 pontos cada**, IDs únicos e projetos QGIS; **0/800** têm `classe_verificada` preenchida. Não foi calculado F1 externo.

Conferência geométrica executada **novamente** em Sagrada com o shapefile original da Area1, buffer de 25 m e o `segmento_id.tif`: **0/200** pontos dentro da zona excluída, **0/200** segmentos amostrados intersectando-a, **0/200** segmentos duplicados e **0/200** IDs inválidos. O teste encontrou **134.445** segmentos totais intersectando a zona de exclusão pelo método de rasterização adotado. Esta checagem não implica referência de classe validada.

## Estado das entregas solicitadas

| Etapa | Estado |
|---|---|
| Auditoria e integridade dos originais disponíveis | **Concluída** |
| Auditabilidade/identidade do modelo de regressão logística | **Concluída** |
| Cinco mapas existentes, CRC e contagem por pixel | **Concluída** |
| Auditoria de banda e diferenças radiométricas por metadados | **Concluída em diagnóstico** |
| Harmonização física e comprovada dos **ortomosaicos** | **Bloqueada: exige verificar PSH→mosaico e origem de cada cena** |
| Reprocessamento completo de cinco grandes ortoimagens para Experimento B | **Não executado** (rasters RGB+multiespectrais integrais externos não estavam montados no ambiente local; pacotes no Drive chegam a ~3,1 GB) |
| Validação humana das quatro regiões externas | **Pendente: 0/800 confirmados** |
| F1-macro externo naquelas quatro regiões | **Indisponível até rótulos independentes** |

**Plano de conclusão:** (1) obter arquivos PSH e rasters integrais de cada área; (2) demonstrar a cadeia de calibração por bandas e sensores; (3) se aplicável, criar **Experimento B** separado com os mesmos 510 pontos de treinamento, todos os atributos reconstruídos para as cinco imagens e versão nova do modelo; (4) comparar as predições A/B sem inferir que mais árvores = melhor qualidade; (5) concluir revisão humana cega dos 800 pontos e calcular F1 externo.

**Regra de versionamento:** preservar todas as entradas, CSVs e GeoTIFFs do Experimento A; não alterar `main`; manter PR #6 em **draft**. O código de auditoria e tabelas gerados fora do repositório foram armazenados no pacote de entrega da sessão de 17/11/2026.
