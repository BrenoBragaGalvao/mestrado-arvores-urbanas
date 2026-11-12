# Validação geográfica externa — implantação reprodutível

**Situação:** código implementado em branch isolada. **Nenhum F1-macro externo foi produzido nesta etapa.** A auditoria do conteúdo *interno* dos pacotes ZIP/RAR e o processamento completo dependem de execução no Colab ou em computador com armazenamento para arquivos de vários GB.

**Não altera:** `README.md` principal, os notebooks antigos, a Area1, os gráficos, as tabelas históricas e a Proposta 2.

## Objetivo

Treinar os oito classificadores exclusivamente com **segmentos rotulados da Area1 (Caxias do Sul)**, selecionar regularização por **validação espacial interna** sobre esses dados e aplicar os modelos, **sem retreinamento nas regiões de teste**, a Centro e Lomba Grande (Novo Hamburgo) e Cristo Rei (São Leopoldo). Só calcular métricas externas se existirem rótulos locais independentes.

O nome `SAGRADA_FAMÍLIA_CAXIAS DO SUL.zip` **não prova** que seu conteúdo corresponda à Area1. Compare rasters, CRS, grade, cobertura e, quando possível, pixels.

## Fontes conectadas e checagens já feitas

- [Pasta das novas imagens no Google Drive](https://drive.google.com/drive/u/1/folders/1cUNFdo2w3V-ldPnxA9N_vnjmQtOrVHyd): quatro arquivos regionais de **1,56 GB a 3,12 GB** e um ZIP de imagens de baixa resolução. A listagem e seus tamanhos foram conferidos no Drive.
- [Dados originais da Area1](https://drive.google.com/drive/folders/1asqPz9xFr7dlnK1ggvrwftXEbkhvwjg6): foram verificados dois rasters, arquivos do AOI, arquivos de referências `Arvores.gpkg`, `Grama.gpkg` e `postes.gpkg`.
- [Fonte e tamanhos verificados](fontes_drive.json): **não contém inventário interno dos pacotes**, nem confirma bandas, rótulos e sobreposição geográfica.
- Código existente: [notebook V2](../../Segmentacao_area_completa_v2_experimentos.ipynb), [receitas auditadas dos oito modelos](../v2_auditoria_regularizacao.py).

**Ausência de NIR e de rótulos nas novas regiões permanece INDETERMINADA** até a leitura interna dos arquivos. O novo código não calcula NDVI quando NIR estiver ausente.

## Como executar — Google Colab

Abra [validacao_externa_colab.ipynb](validacao_externa_colab.ipynb) no Colab. Ele instala os requisitos, monta o Drive e apresenta as etapas na ordem correta. A conta de Google utilizada no Colab deve ter acesso aos arquivos: caso estejam apenas em «Compartilhados comigo», crie um **atalho em Meu Drive** e ajuste os caminhos. Os pacotes são grandes: selecione **uma região por vez**.

Procedimento na linha de comando, equivalente ao notebook:

### 1. Verificar o conteúdo antes de processar

```bash
python experimentos/validacao_externa_regioes/auditar_pacotes.py \
  --arquivos "/content/arquivos_novos" \
  --extraidos "/content/extraidos" \
  --extrair \
  --rgb-area1 "/content/drive/MyDrive/Projetos/Segmentacao_Breno/Area1/AOI_RGB_NEW.tif" \
  --out "/content/auditoria"
```

A auditoria:

- Lista membros de ZIP/RAR, tamanhos e extensões sem presumir a estrutura dos arquivos.
- Extrai em diretórios separados (ZIP com verificações de segurança; RAR exige ferramenta externa como `unrar`/`7z`).
- Inspeciona CRS, bandas, dimensões, resolução, geotransformação e geometrias.
- Para Sagrada Família, calcula correspondência de cobertura com a Area1; `--comparar-pixels` permite verificar se os valores de pixels coincidem em grades iguais. Identidade pelo nome não é aceita.

O relatório de auditoria deve ser **revisado antes de selecionar** os caminhos de RGB, RGB+NIR e AOI para as fases seguintes.

### 2. Treinar e congelar os modelos na Area1

Entrada original do notebook 812 quadrantes:

`/content/drive/MyDrive/Projetos/Segmentacao_Breno/outputs/v2_progressivo_256/rotulos_sem_duplicacao.csv`

Este CSV **não estava disponível nas pastas do Drive examinadas nem no GitHub** no momento da implementação. Se ele ainda não existir em sua sessão, é necessário executar a etapa correspondente do notebook V2 para produzi-lo. O CSV de métricas não serve para treinar.

```bash
python experimentos/validacao_externa_regioes/treinar_area1.py \
  --area1-csv "/content/drive/MyDrive/Projetos/Segmentacao_Breno/outputs/v2_progressivo_256/rotulos_sem_duplicacao.csv" \
  --geometrias "/caminho/para/E3c_geometrias_rotuladas_812.gpkg" \
  --out "/content/modelos_area1"
```

- O arquivo de geometrias permite embargo de **25 m por geometria**. Se não estiver disponível, a opção `--permitir-embargo-centroides` habilita uma **aproximação diferente**, que será registrada no manifesto. Nunca apresentar os protocolos como idênticos.
- Para o modelo final de transferência, são feitos **3 sorteios internos por escala (250 m e 500 m)**, utilizando apenas a Area1, e selecionada uma das duas receitas históricas de regularização por classificador.
- Os 8 modelos finais são ajustados com os exemplos rotulados da Area1, depois da validação interna. O teste externo geográfico não participa do ajuste nem da escolha de parâmetros.
- O F1 interno dessa nova seleção **não substitui os F1 históricos**. O teste espacial histórico da Area1 também já foi visto durante o desenvolvimento e **não é teste cego**.

### 3. Aplicar à região (sem rótulos locais)

Após a auditoria, selecione manualmente o TIFF RGB e um TIFF de **pelo menos 4 bandas RGB+NIR**, garantindo a ordem das bandas.

```bash
python experimentos/validacao_externa_regioes/aplicar_regiao.py \
  --regiao centro_novo_hamburgo \
  --rgb "/caminho/rgb.tif" \
  --multi "/caminho/rgb_nir.tif" \
  --modelos "/content/modelos_area1" \
  --out "/content/resultados/centro"
```

A aplicação:

1. Processa raster em **janelas de até 256 × 256 pixels**, calculando automaticamente a quantidade de janelas (não são sempre 812).
2. Extrai média do brilho HSV, média de bordas Canny sobre **NIR/10000** e média de NDVI, seguindo o notebook dos quadrantes.
3. Executa os **oito modelos fixos** e exporta `classificacao_*.tif` por classificador, `segmento_id.tif`, `segmentos.csv.gz`, imagens RGB e sobreposições reduzidas e manifesto de execução.
4. Registra separadamente cada janela processada em `tiles/`. Se interromper, execute o **mesmo comando com `--retomar`** e sem mudar os rasters ou os modelos.
5. Se as grades raster forem diferentes, o script interrompe: usar `--alinhar-multiespectral` apenas depois da auditoria, registrando que ocorreu reprojeção/interpolação. Não tratar essa correção como transformação do protocolo original.

Se faltar NIR, **não substitua por valores fictícios** nem apresente métricas comparáveis. Um protocolo RGB-only precisaria de extração e treinamento próprios na Area1, incluindo a definição consistente de bordas sem NIR.

### 4. Avaliar F1-macro quando houver rótulos locais independentes

```bash
python experimentos/validacao_externa_regioes/avaliar_regiao.py \
  --regiao centro_novo_hamburgo \
  --predicoes "/content/resultados/centro" \
  --arvores "/caminho/Arvores.gpkg" \
  --grama "/caminho/Grama.gpkg" \
  --out "/content/metricas/centro"
```

A avaliação georreferencia os pontos, identifica o segmento correspondente, remove referências conflitantes em um mesmo segmento e **deduplica por segmento** antes de calcular F1-macro, acurácia, acurácia balanceada, relatório por classe e matriz de confusão. Exige pelo menos 5 segmentos únicos por classe (mínimo técnico, **não garantia de validade estatística**). Registra exclusões e contagens. Se os rótulos faltarem, **nenhuma métrica externa é calculada**.

Os dados de referência das novas regiões **não podem** ser utilizados na seleção dos modelos da Area1.

## Organização gerada

| Saída | Significado |
|---|---|
| `auditoria_pacotes.json` | Conteúdo e metadados efetivamente inspecionados após acesso aos arquivos. |
| `modelos_area1/*.joblib` | Modelos treinados somente na Area1, com manifesto de parâmetros e origem. |
| `predicoes/REGIAO/classificacao_*.tif` | Predição por classificador (1 = árvore, 2 = gramínea, 0 = sem classificação). |
| `predicoes/REGIAO/segmento_id.tif` | IDs geográficos para vincular pontos a segmentos. |
| `predicoes/REGIAO/segmentos.csv.gz` | Características extraídas sem carregar a imagem inteira na RAM. |
| `metricas/REGIAO/metricas_externas.csv` | Métricas externas **somente se existirem referências independentes**. |
| `metricas/REGIAO/matrizes_confusao.csv` | Matriz por classificador e região, quando validada. |

## Limitações e próximas condições

1. **Pacotes ZIP/RAR grandes:** não foram descompactados neste ambiente. Sem inspeção interna, não podemos dizer quais regiões dispõem de NIR, rótulos, AOI ou postes.
2. **Ausência de base de treinamento disponível nesta sessão:** o CSV de 505 segmentos rotulados precisa ser localizado no Drive de execução ou reproduzido pelo notebook antigo.
3. **Sem métricas externas:** resultados antigos da Area1 não são novos testes externos.
4. **Sem projeção de porte ou risco elétrico nesta etapa:** a Proposta 2 permanece preservada; ela depende de dados de postes/alturas e não mede risco a cabos.
5. **Compatibilidade espectral:** a ordem RGB+NIR, calibração radiométrica, diferença de sensores, resolução e eventual alinhamento precisam ser auditados. Sem essa compatibilidade, a comparação direta do F1 pode não ser válida.
6. **Dados geográficos sensíveis a vazamento:** rótulos da região de teste não podem influenciar treinamento ou hiperparâmetros. As previsões da região podem ser geradas sem usar rótulos.

## Testes automatizados

```bash
python -m pip install -r experimentos/validacao_externa_regioes/requirements.txt
python -m compileall -q experimentos/validacao_externa_regioes
python -m pytest -q experimentos/validacao_externa_regioes/testes
```

Os testes geram **dados sintéticos**, apenas para conferir funcionamento de partes do código. Não representam resultados científicos em Novo Hamburgo, São Leopoldo ou Caxias.

**Critério de publicação:** acrescente ao README principal a seção «Validação da metodologia em outras regiões geográficas» *somente depois de processar os rasters, conferir os rótulos locais e verificar as métricas realmente obtidas*. Não altere os números do estudo original.
