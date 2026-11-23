# Estado de execução — F1-macro da Regressão Logística nos mesmos 600 pontos cegos (500 m)

**Data:** 17/11/2026.

## Escopo congelado

- 200 pontos de Sagrada Família, 200 de Lomba Grande, 200 de Cristo Rei (600 totais), **exatamente os mesmos 600 da primeira avaliação CHMv2**.
- Referência externa: pseudo-rótulo CHMv2 conservador, altura máxima no raio de 5 m **≤0,5 m = gramínea candidata**, **≥5 m = árvore candidata**, intermediários excluídos. Resultam 179, 183 e 181 pontos válidos, respectivamente.
- Apenas **Regressão Logística** e **F1-macro agregado**, organizada em blocos espaciais de **500 m**. Modelos A (505 segmentos únicos da Area1) e C (371 segmentos originais retidos pelo filtro CHMv2 da Area1), congelados.
- Não usar os 1.500 candidatos homogêneos do experimento auxiliar para substituir pontos de teste.
- Não usar rótulos externos CHMv2 para treinamento ou ajuste de parâmetros.

## F1 anterior A nos 600 pontos exatos (já confirmado)

| Região | F1-macro A CHMv2 | N válido |
|---|---:|---:|
| Sagrada Família | 0,7597 | 179 |
| Lomba Grande | 0,7785 | 183 |
| Cristo Rei | 0,8042 | 181 |

**F1 do modelo C nos mesmos 600:** NÃO CALCULADO até concluir a reconstrução espectral; qualquer preenchimento seria inventado.

## Avanço técnico conferido nesta execução

1. Recuperados e congelados os **600 pares (ponto, segmento)**, pseudo-rótulos CHMv2 e predições originais A em `600_pontos_cegos_CHMv2_congelados.csv`.
2. Recuperados **diretamente dos três GeoTIFFs `segmento_id.tif` originais**, validados, os **600 footprints exatos** (280.906 pixels no total) e gravados com índices comprimidos em `600_pontos_mascaras_quickshift_originais.csv`. Isso dispensa repetir Quickshift ou obter os pacotes de mapas por URL pública.
3. `avaliar_600_pontos_C_vs_A_500m.py` recupera atributos NDVI, brilho HSV e bordas Canny a partir dos originais multiespectrais por quadrante de 256 px e aplica as equações numéricas congeladas de A e C. A execução compara as previsões reconstruídas de A com as 600 previsões já guardadas e **marca divergências antes de aceitar F1 novo**.
4. Verificada a disponibilidade dos três pacotes originais no Drive conectado, mas eles têm ~1,7 GB, 3,1 GB e 1,56 GB; o conector bloqueia download bruto acima de **256 MiB**.
5. Num primeiro teste, um runner GitHub Actions conseguiu transferir **1.771.082.301 bytes** da imagem original de Sagrada. As tentativas posteriores receberam a página de **cota de download do Google Drive** (*“Too many users have viewed or downloaded this file recently”*), atingindo todas as três imagens externas. Não há base espectral suficiente nos arquivos locais para os 600 segmentos.
6. Foi adicionado modo `CHM_ORIGINAIS_DRIVE` ao código para executar em **Colab com o Google Drive autenticado**, sem depender do endpoint público bloqueado. A fonte dos ZIP/RAR não é alterada.

## Próxima execução válida

Executar o notebook `Proposta1_Comparacao_F1_600_Pontos_500m_Colab.ipynb` (entregue ao usuário) numa sessão Colab com Drive montado em `/content/drive/MyDrive`. As entradas esperadas são:

- `Imagens do Mestrado/SAGRADA_FAMÍLIA_CAXIAS DO SUL.zip`
- `Imagens do Mestrado/LOMBA_GRANDE_NOVO_HAMBURGO.zip`
- `Imagens do Mestrado/CRISTO_REI_SÃO_LEOPOLDO.rar`

O código gera `COMPARACAO_F1_MACRO_500m_600_PONTOS.csv`, `600_pontos_mesmos_atributos_e_previsoes.csv` e `manifesto_comparacao.json`.

**Não declarar melhora de generalização até comparar A e C nos mesmos 600 pontos e auditar possíveis divergências das predições A.** Mesmo após o cálculo, o resultado externo é F1 de concordância com referência automática CHMv2, não F1 validado por anotação humana.

**Versionamento:** não alterar `main` ou sobrescrever A, manter o PR #6 em rascunho.
