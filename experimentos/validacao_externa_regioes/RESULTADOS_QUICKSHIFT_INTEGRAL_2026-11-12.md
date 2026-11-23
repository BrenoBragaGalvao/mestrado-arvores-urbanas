# Segmentação Quickshift integral — quatro imagens regionais

**Data:** 12/11/2026  
**Situação:** quatro regiões **integralmente segmentadas** com rasters RGB reais. Não houve treinamento supervisionado, classificação árvore/grama, validação independente nem cálculo de F1-macro nesta execução.

**Evidência primária:** [GitHub Actions — Segmentação Quickshift integral das quatro regiões, execução 43296756137](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/actions/runs/43296756137). Os **quatro jobs da matriz concluíram com sucesso** e publicaram os resumos completos como artefatos.

## Resultado executado, sem estimativas

| Código | Área | Dimensões RGB (pixels) | Quadrantes 256 px | Segmentos Quickshift produzidos | Pixels válidos |
|---|---|---:|---:|---:|---:|
| A1 | Sagrada Família — Caxias do Sul | 10.456 × 10.422 | **1.681 / 1.681** | **332.005** | 108.972.432 |
| A2 | Centro — Novo Hamburgo | 10.554 × 10.502 | **1.764 / 1.764** | **356.503** | 110.838.108 |
| A3 | Lomba Grande — Novo Hamburgo | 16.409 × 17.423 | **4.485 / 4.485** | **1.715.280** | 285.894.007 |
| A4 | Cristo Rei — São Leopoldo | 10.530 × 10.410 | **1.722 / 1.722** | **360.708** | 109.617.300 |
| **Total A1–A4** | Quatro rasters regionais | — | **9.652 / 9.652** | **2.764.496** | **615.321.847** |

**Comparação histórica, não reexecutada nesta workflow:** a Area1 original (A0) possui 6.942 × 7.294 pixels e o estudo V2 registrou **812 quadrantes e 168.133 segmentos**. Esses valores são **históricos**, não resultados novos de 12/11/2026. Considerando A0 apenas como linha contextual, as cinco áreas somam **10.464 quadrantes** e **2.932.629 segmentos** (soma descritiva de protocolos executados em momentos distintos).

## Configuração aplicada

- Quickshift com `kernel_size=3`, `max_dist=5`, `ratio=0.04`, `rng=42`.
- Divisão de cada imagem RGB em janelas de **até 256 × 256 pixels**, inclusive nas bordas.
- Cada janela é segmentada independentemente, com segmentação obtida do **raster verdadeiro**, e a quantidade de segmentos é somada por quadrante.
- Foi produzida uma pré-visualização reduzida da imagem RGB com contornos internos das segmentações. Não se deve confundir esta prévia com o mapa georreferenciado completo de rótulos.
- Nenhum dos arquivos brutos de centenas de megabytes/gigabytes foi adicionado ao repositório.
- O processamento ocorreu em runners temporários independentes. Os arquivos `resultado_quickshift.json`, `quickshift_por_quadrante.csv` e `preview_quickshift.png` foram empacotados e **copiados de volta para a pasta de resultados no Google Drive**, via conexão autorizada.

## Artefatos para conferência e reprodução

- **A1 — Sagrada Família — Caxias do Sul:** [ZIP de resultados (JSON + CSV + prévia PNG)](https://drive.google.com/file/d/1jyoCEK0xrlllurvzm-kqjcCtQ936UsjB/view) — 1.681 quadrantes, 332.005 segmentos; 266,44 segundos de processamento segmentador no runner.
- **A2 — Centro — Novo Hamburgo:** [ZIP de resultados (JSON + CSV + prévia PNG)](https://drive.google.com/file/d/1hu9mvHg1TOXyOIggZLm2s3SiqNenOTS3/view) — 1.764 quadrantes, 356.503 segmentos; 367,12 segundos de processamento segmentador no runner.
- **A3 — Lomba Grande — Novo Hamburgo:** [ZIP de resultados (JSON + CSV + prévia PNG)](https://drive.google.com/file/d/14eJvGZ6SUhHBgxcO_xrMGG0TRa8ULcFB/view) — 4.485 quadrantes, 1.715.280 segmentos; 1.333,9 segundos de processamento segmentador no runner.
- **A4 — Cristo Rei — São Leopoldo:** [ZIP de resultados (JSON + CSV + prévia PNG)](https://drive.google.com/file/d/1bB9lS4y9QaqgldV19J8Z5d2jpZg4YkQB/view) — 1.722 quadrantes, 360.708 segmentos; 490,88 segundos de processamento segmentador no runner.

**Pasta de destino:** `Meu Drive/Projetos/Segmentacao_Breno/outputs/validacao_externa_regioes`.

O script reprodutível está em [`segmentar_regiao_completa.py`](segmentar_regiao_completa.py); o workflow de execução em [`.github/workflows/quickshift-integral-quatro-regioes.yml`](../../.github/workflows/quickshift-integral-quatro-regioes.yml). O workflow ficou configurado para disparo manual após a primeira execução integral, evitando downloads repetidos não intencionais.

## Observações científicas obrigatórias

1. Os **2.764.496 segmentos Quickshift não estão rotulados**. Não são árvores encontradas, gramíneas identificadas, acertos ou amostras de referência.
2. **Nenhum dos oito modelos supervisionados foi treinado nem aplicado nesta execução integral**. Seus códigos de treinamento e inferência estão preparados, mas dependem da base privada da Area1 e da confirmação das bandas multiespectrais.
3. A quarta banda dos TIFFs regionais ainda **não foi documentalmente confirmada como NIR**; não publicar resultados de NDVI como se estivessem espectralmente verificados.
4. Os 510 pontos de referência originais **não são rótulos independentes** da imagem de Sagrada Família: a [auditoria de sobreposição](AUDITORIA_SOBREPOSICAO_AREA1_SAGRADA_2026-11-12.md) constatou que todos estão cobertos pelo raster RGB regional e pelo polígono da Area1.
5. O protocolo científico para avaliar generalização permanece: **(a)** reconstruir e validar os 505 segmentos rotulados da Area1; **(b)** selecionar parâmetros por validação interna e treinar os oito classificadores com a Area1; **(c)** transferir os modelos fixos às novas áreas; **(d)** coletar/verificar rótulos independentes; **(e)** medir F1-macro externo apenas quando houver referências suficientes.
6. A Area1 geográfica não é região de teste cego quando faz parte da base de treinamento. A porção de Sagrada Família sobreposta ao treinamento — acrescida de um buffer de 25 m — deve ser excluída de qualquer métrica externa.

**Conclusão desta etapa:** a **segmentação Quickshift integral de A1–A4 foi comprovada**, e os artefatos correspondentes estão disponíveis no Drive. Não foi comprovada generalização de classificação dos oito algoritmos, pois a inferência supervisionada e o teste com rótulos externos não ocorreram.
