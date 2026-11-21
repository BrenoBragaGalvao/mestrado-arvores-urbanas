# Proposta 1 — verificação independente dos F1 elevados (13/11/2026)

Esta é uma **nova auditoria executada com arquivos reais**, não uma reexecução no Google Colab nem validação externa. Os experimentos foram feitos em ambiente local a partir dos ZIPs privados do Drive, sem publicar coordenadas ou referências individuais no GitHub.

## Execuções concluídas

- **400 ajustes reproduzidos:** 5 imagens × 10 divisões (cinco por bloco de 250 m e cinco por 500 m) × 8 classificadores, aplicando as receitas **moderada/forte** efetivamente selecionadas e as três características `mean_intensity`, `mean_edges` e `mean_ndvi`. Os 400 F1-macro de **teste espacial interno** coincidiram numericamente com os CSVs `Metricas_por_divisao.csv`.
- Calculados **F1 no treino, F1 no teste e a diferença (treino − teste)** por divisão, região, algoritmo e escala. Os resultados permitem analisar possíveis sobreajustes com mais precisão do que comparar CV interna × teste.
- **800 ajustes adicionais** com o mesmo teste e os **hiperparâmetros previamente escolhidos**, impondo novos embargos por **distância entre pontos** de 50 m e 100 m, sem reaproveitar o teste na seleção. São novos experimentos de sensibilidade, que não substituem o protocolo geométrico histórico.
- Auditadas as 40 divisões das quatro regiões: **nenhum segmento ou mancha (`mancha_id`) repetido entre treino/teste**; distâncias mínimas entre pontos excederam 25 m em todas elas.
- Reabertos os GeoTIFFs de `segmento_id.tif` das regiões e os **800 pontos de teste reservados**: todos os 800 apontaram para segmentos únicos não utilizados no treinamento local. Os 500 IDs de cada base local coincidiram com os IDs do raster.
- Na **Sagrada Família**, conferiu-se adicionalmente o polígono da Area1 + buffer de 25 m sobre o raster de segmentos: **nenhum dos 200 segmentos reservados para teste intercepta essa área**. Essa checagem não substitui a rotulação independente.
- Preparados quatro **ZIPs de revisão CEGA no QGIS** com 500 pontos por região, raster RGB de contexto e 500 recortes de imagem cada. As sugestões de IA foram retiradas do GeoPackage destinado ao anotador, mantendo `classe_verificada` vazia.

## F1 treino × teste: SVM RBF

| Área | Treino 250 m | Teste 250 m | Treino 500 m | Teste 500 m |
|---|---:|---:|---:|---:|
| Area1 | 0,8848 | 0,8659 | 0,8872 | 0,8652 |
| Sagrada Família | 0,9761 | 0,9556 | 0,9745 | 0,9649 |
| Centro | 0,9773 | 0,9454 | 0,9768 | 0,9779 |
| Lomba Grande | 0,9720 | 0,9752 | 0,9755 | 0,9799 |
| Cristo Rei | 0,9919 | 0,9928 | 0,9937 | 0,9912 |

O SVM não apresenta um gap grande e sistemático nesta base, mas **isso não demonstra que os rótulos sugeridos pela IA estão corretos** nem que haja transferência geográfica válida. Em 250 m no Centro, observou-se maior gap de F1: Random Forest **0,0906**; HistGradientBoosting **0,0794**; Gaussian Naive Bayes **0,0576**. Em Lomba Grande, Gaussian Naive Bayes apresentou **0,0588** no bloco 500 m.

## SVM RBF: mesmo teste, distância mínima de 25 m × 100 m (blocos 250 m)

| Área | Protocolo 25 m | Sensibilidade 100 m |
|---|---:|---:|
| Area1 | 0,8659 | 0,8599 |
| Sagrada Família | 0,9556 | 0,9556 |
| Centro | 0,9454 | 0,9454 |
| Lomba Grande | 0,9752 | 0,9733 |
| Cristo Rei | 0,9928 | 0,9928 |

Os resultados quase invariantes de SVM ao ampliar o buffer por pontos são compatíveis com **amostras facilmente separáveis nesta seleção**, não com uma garantia de qualidade da classificação de toda a cena urbana. A sensibilidade é uma **análise adicional**, não um novo F1 externo.

## Conclusão científica

1. Não há evidência de um **overfitting extremo generalizado** nos modelos SVM treinados localmente; a auditoria encontrou gaps maiores em alguns outros classificadores.
2. Os valores de F1 próximos de 0,99 nas áreas externas são **exploratórios**, pois os 2.000 rótulos de treinamento locais vieram de interpretação RGB assistida por IA, foram selecionados preferencialmente em manchas homogêneas e **não têm confirmação humana**. A mediana da fração dos segmentos dentro das manchas sugeridas foi 100% em cada região.
3. Os 800 pontos de teste geográfico continuam sem referência independente, logo **F1 externo e generalização não comprovados**.
4. A validação espacial foi checada por IDs e pontos, mas os limites **poligonais completos dos segmentos de treino e teste** devem ser inspecionados para certificar todos os buffers geométricos em futuras publicações.
5. **Os resultados históricos, modelos originais e a branch `main` não foram modificados.** Os quatro pacotes de revisão precisam passar por anotação independente no QGIS, sem acesso às sugestões de IA.

### Artefatos privados no Drive

Pasta de auditoria: [Auditoria Overfitting — Revisão Cega](https://drive.google.com/drive/folders/1ku0ShLjIJUohJ1xCz3sLuFLRNjKNrp5J). Contém CSVs de 400 ajustes reproduzidos, 800 ajustes de sensibilidade e verificação raster dos 800 pontos. Os arquivos QGIS de revisão foram criados como entregas separadas para não misturar sugestões preliminares com verdade-terreno.

**Nota:** os ajustes de sensibilidade com 50/100 m são avaliados com o mesmo conjunto de teste e receitas selecionadas anteriormente; não foi feita uma nova busca de hiperparâmetros a partir de 50/100 m. A leitura dos GeoTIFFs de IDs confirma exclusão por segmentos no teste reservado, mas não reconstitui todos os polígonos dos 2.000 pontos de treinamento para inspeção de embargo de cada dobra.
