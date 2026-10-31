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
| E3 | Pendente | Comparar classificadores sobre mesmas partições | RF atual vs SVM e modelo simples; mesmas 3 características e métricas |
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
