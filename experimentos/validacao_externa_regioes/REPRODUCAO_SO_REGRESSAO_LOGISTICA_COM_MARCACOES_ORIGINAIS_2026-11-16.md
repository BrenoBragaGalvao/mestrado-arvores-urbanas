# Proposta 1 — Regressão Logística treinada novamente com as mesmas marcações originais de Area1

## Pedido do pesquisador

**Usar exclusivamente as árvores e gramíneas que foram anotadas inicialmente na Area1, e aplicar o modelo resultante às cinco imagens, sem treinamento local nas outras quatro.**

## Trabalho executado nesta reprodução

1. Foram acessados os GeoPackages de referência `Arvores.gpkg` (**257 pontos**) e `Grama.gpkg` (**253 pontos**) da Area1. Ambos continham geometrias de tipo Point em EPSG:4674.
2. A matriz de **505 segmentos Quickshift únicos**, previamente extraída dessas marcações originais, foi relida. Distribuição: 257 árvores e 248 gramíneas; cinco marcações do conjunto original não acrescentam segmentos independentes. SHA-256 do CSV de atributos: `a31c197321b8c10ad67cd16ffadf315f8481311a73f1c044e7e050c7179e3c82`, idêntico ao do manifesto de treinamento.
3. Foi **executado um novo `fit`**, apenas com esses 505 segmentos e atributos `mean_intensity` (HSV), `mean_edges` (Canny) e `mean_ndvi`, usando `Pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=3000, random_state=42))`.
4. A nova Regressão Logística reproduziu numericamente o modelo salvo anteriormente: médias e escalas de normalização, coeficientes, intercepto, classes, probabilidades e predições das 505 amostras coincidiram (tolerância de 1e-12).
5. Para cada uma das cinco áreas, foi verificado que os GeoTIFFs anteriores usaram o mesmo **hash de manifesto do conjunto de modelos** (`1be37acffa0480cec3030296cb292676330ada4494f9cde3aba08b518b0d2661`), os mesmos três atributos, a ordem espectral [3, 2, 1, 4], a segmentação Quickshift com `kernel_size=3, max_dist=5, ratio=0.04, rng=42` e resolução de 0,5 m em EPSG:31982.
6. Todos os cinco mapas de Regressão Logística existentes foram **relidos pixel a pixel**, e as contagens 1/2 de árvore/gramínea coincidiram com a tabela consolidada. Como o modelo refeito é matematicamente equivalente ao existente, os mapas prévios foram **reutilizados**, sem repetir o processamento bruto de imagens multigigabyte.

**Escopo explícito:** esta rodada realmente refez o ajuste matemático da Regressão Logística a partir da matriz original validada, mas **não reconstruiu agora a matriz de atributos a partir dos pixels brutos** e **não gerou de novo as cinco inferências raster**. O novo modelo foi comprovado equivalente ao que gerou os cinco rasters disponibilizados. Nenhuma imagem/ponto local foi usado para ajustar parâmetros.

## Resultado dos cinco mapas do mesmo classificador

| Região | Segmentos árvore | Segmentos gramínea | Pixels árvore | Pixels gramínea | % pixels árvore | Área árvore prevista (ha) |
|---|---:|---:|---:|---:|---:|---:|
| Area1 — Caxias do Sul | 54.520 | 77.256 | 18.295.672 | 28.665.265 | 38,96 | 457,39 |
| Sagrada Família | 161.057 | 157.773 | 49.131.084 | 58.018.807 | 45,85 | 1.228,28 |
| Centro — Novo Hamburgo | 0 | 317.756 | 0 | 106.687.278 | 0,00 | 0,00 |
| Lomba Grande | 317.655 | 296.375 | 94.628.092 | 89.859.591 | 51,29 | 2.365,70 |
| Cristo Rei — São Leopoldo | 202.965 | 132.663 | 59.231.986 | 47.344.448 | 55,58 | 1.480,80 |

Esses são **valores previstos**, e não coberturas vegetais confirmadas. O classificador binário também atribui uma das duas classes a ruas e telhados. O caso do Centro evidencia mudança de domínio e classificação degenerada (tudo gramínea), a ser discutida como limite do experimento.

## Avaliação científica

A execução corrigida anterior avaliou a Area1 espacialmente, com **F1-macro 250m = 0,8376** e **500m = 0,8567**, em cinco divisões por escala. Valores do README histórico (0,8879 e 0,8666) referem-se a outro protocolo e não são resultados externos.

**Quatro F1-macro externos = não avaliados**; ainda são necessários rótulos humanos independentes nos quatro conjuntos de 200 pontos. As coordenadas originais da Area1 **não devem ser deslocadas artificialmente** para as outras ortoimagens para produzir falsos rótulos. O uso da mesma base de treino é a transferência do modelo congelado, não a relocalização de marcações.

## Referências

- [Pasta dos pontos originais da Area1](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6)
- [Pacote original de oito modelos e validação](https://drive.google.com/file/d/1Hsn1WQxic6150_fXrqXpkLkaePkTIEl-/view)
- [Cinco pacotes de mapas já auditados](https://drive.google.com/drive/folders/1JAcdZwUNqgFfsaJwNqOcsJsUypNqr2mY)
- [Auditoria completa de mapas de 16/11](./AUDITORIA_FINAL_TRANSFERENCIA_CINCO_AREAS_2026-11-16.md)
- [Protocolo de avaliação externa](./avaliar_regiao.py)

**Controle de versões:** registro apenas na `feature/validacao-geografica-externa`. PR #6 mantido em draft, e `main` preservada.
