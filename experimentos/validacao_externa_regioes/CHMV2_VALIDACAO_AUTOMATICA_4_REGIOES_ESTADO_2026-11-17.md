# Proposta 1 — Meta/WRI CHMv2 para validação exploratória em quatro regiões

**Data:** 17/11/2026. **Escopo fixo:** Area1, Sagrada Família, Lomba Grande e Cristo Rei. Centro de Novo Hamburgo fora do escopo desta bateria.

## Execução realmente realizada nesta etapa

1. Reutilizados os 510 pontos originais da Area1: `Arvores.gpkg` (257) e `Grama.gpkg` (253). A Regressão Logística foi **mantida congelada**, sem CHMv2 no treinamento e sem pontos externos no ajuste.
2. Recuperados os 600 pontos cegos externos: 200 Sagrada, 200 Lomba Grande e 200 Cristo Rei, associados por `amostra_id` às respectivas previsões do modelo congelado.
3. Calculadas as quadkeys zoom 10 dos **600 pontos**, após reprojeção das coordenadas EPSG:31982 para WGS84:
   - `2103121330.tif`: Area1 e Sagrada Família;
   - `2103123110.tif`: Lomba Grande e Cristo Rei.
   Os arquivos correspondentes devem ser obtidos da fonte oficial [CHMv2 — Meta/WRI](https://registry.opendata.aws/dataforgood-fb-forestsv2/) ou seu espelho público e a existência do objeto precisa ser verificada ao baixar.
4. Conferidas as coordenadas dos 200 pontos de Sagrada contra a área original da Area1 + buffer de 25 m: nenhum ponto invade a exclusão; a auditoria de segmentos cruzados permanece documentada no protocolo original da revisão cega.
5. Preparados 600 registros com referências CHMv2 vazias, GeoPackages cegos e CSVs de previsões em arquivos separados. **Nenhuma altura foi inventada.**
6. Implementado e testado em cinco testes sintéticos um script que lê o valor do pixel e máximo/mediana em raio horizontal de 5 m **no terreno em EPSG:31982** a partir de GeoTIFF CHMv2 em EPSG:3857, aplica regras A0/A05/B, audita os 510 pontos conhecidos da Area1 e calcula F1 de concordância com pseudo-rótulos e matrizes de confusão nas três regiões externas.
7. Produzido notebook Google Colab e pacote de entrada reutilizável com fontes originais para executar essa etapa com acesso HTTPS aos arquivos CHMv2.

## Limitação principal: sem novas alturas reais nesta execução

**Os dois GeoTIFFs CHMv2 não estavam montados no ambiente e o download direto do bucket público/espelho não pôde ser concluído nesta sessão.** Portanto, **não existe F1-macro externo calculado nesta entrega**. O notebook/código podem executar a análise quando os rasters forem de fato acessíveis; nenhum valor numérico externo deve ser publicado até isso ocorrer.

O README do mestrado relata que **107 das 257 árvores originais** têm CHMv2 pixel zero e **42** têm máximo zero na vizinhança de 5 metros. Assim, altura 0 não comprova gramínea, e altura positiva não comprova árvore. O CHMv2 pode conter no-data codificado como 255 ou zero ambíguo conforme a distribuição, devendo sempre verificar metadados/máscara do produto lido.

## Procedimentos quando os GeoTIFFs estiverem disponíveis

- A0: CHMv2 máximo no raio de 5m = 0, candidata a gramínea; maior que 0, candidata a árvore.
- A05: máximo <= 0,5m candidata a gramínea; maior que 0,5m candidata a árvore.
- B: máximo <= 0,5m gramínea candidata; >= 5m árvore candidata; intervalo intermediário incerto.
- Separar pontos `incerto`/`outra cobertura`/`sem dado`; expor taxa de descarte e tamanho de amostra por classe.
- Confrontar as regras com os **510 rótulos originais da Area1** para medir suas inconsistências antes de interpretar métricas externas.
- Comparar os pseudo-rótulos das amostras com as previsões congeladas. F1 reportado como **concordância com pseudo-rótulos CHMv2**, não com verdade-terreno humana.
- Somente selecionar novas amostras se a cobertura das duas classes nos 200 pontos por região se mostrar insuficiente; se isso ocorrer, documentar separadamente a seleção e seu potencial viés.

## Status da tabela solicitada

| Região | F1 interno 250 m | F1 interno 500 m | F1 CHMv2 500 m |
|---|---:|---:|---|
| Area1 | 0,8376 | 0,8567 | Não aplicável (origem) |
| Sagrada Família | Não aplicável | Não aplicável | **Pendente de alturas Meta** |
| Lomba Grande | Não aplicável | Não aplicável | **Pendente de alturas Meta** |
| Cristo Rei | Não aplicável | Não aplicável | **Pendente de alturas Meta** |

Os F1 internos acima são da **execução corrigida** da Area1. A série histórica do README original, `0,8879` e `0,8666`, pertence a outra bateria.

### Entregas concretas

- [Pasta de resultados no Google Drive](https://drive.google.com/drive/folders/1DpWUMSkjLWlbW1dMNJcoDGd-YkjSEyX1)
- [Pacote completo ZIP: código testado, notebook Colab, 600 pontos, referências Area1, XLSX e PDF](https://drive.google.com/file/d/1PkeQgJgoRCEALzVMRdwpKDIfg50j2xR6/view)
- [PDF — diagnóstico de execução](https://drive.google.com/file/d/14Jc1gCtHPGxA12rniuOWR2d66UPcO9K2/view)
- [Planilha de preparação](https://docs.google.com/spreadsheets/d/11qOfsWiptVv2dDFwnpmDHK_qY79rw3RK/edit)

O arquivo `validacao_CHMv2_quatro_regioes_colab.ipynb` dentro do pacote permite baixar os dois mosaicos publicamente disponíveis e calcular as tabelas quando o ambiente possuir acesso à rede. Preservadas a branch `main`, a área Centro histórica, os raster mapas e o PR #6 (rascunho).
