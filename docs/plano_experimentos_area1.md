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
| E4 | Pendente | Verificar contribuição de atributos | 7 combinações não vazias de NDVI, HSV e Canny, mesmas partições e modelos |
| E5 | Pendente | Avaliar sensibilidade de parâmetros | Variar K-Means / segmentação Quickshift no mesmo raster; registrar custo e memória |
| E6 | Pendente | Testar análise de proximidade a postes | 1, 3 e 5 m; resultados com/sem filtro `predicted_classe == 'arvore'`, contando objetos únicos |
| E7 | Pendente | Analisar sensibilidade da alometria | Comparar C1–C6 e limiares de porte; **sem** alegar acurácia de altura |
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

**Próxima etapa após executar/avaliar E3:** E4, ablação das características NDVI, brilho HSV e bordas Canny. Deve manter os mesmos dados, particionamentos espaciais e métricas, sem modificar o notebook original ou o README.
