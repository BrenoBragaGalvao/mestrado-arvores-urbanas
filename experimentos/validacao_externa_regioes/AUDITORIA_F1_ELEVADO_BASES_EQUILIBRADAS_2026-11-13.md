# Auditoria dos F1-macro elevados nas bases equilibradas — 13/11/2026

## Motivação e escopo

Verificar se F1-macro entre 0,94 e 0,99 obtidos na **validação espacial interna de cada região** podem ser explicados por vazamento treino-teste ou por overfitting. Não confundir com **validação geográfica externa** do modelo treinado na Area1.

**Dados auditados diretamente:** os cinco pacotes `01_area1_caxias_250_por_classe.zip` a `05_cristo_rei_sao_leopoldo_250_por_classe.zip`, na [pasta de 250 árvores + 250 gramíneas por imagem](https://drive.google.com/drive/folders/19U64ztJ_mxLAWkY6MFz-g1Z9AkOqbjPa). Foram extraídos e decodificados, sem alterar a origem, `Manifesto_amostragem.json`, `Amostras_treino.csv`, `Divisoes_espaciais.json` e `Metricas_por_divisao.csv`. A integridade dos quatro membros foi verificada por **CRC-32** em cada pacote.

## Checagens efetivamente realizadas

Nas quatro regiões externas, cada base contém 500 linhas, 250 árvores e 250 gramíneas, sem IDs de segmento duplicados. Para **cada uma das 10 divisões** (cinco em 250 m e cinco em 500 m), conferiram-se programaticamente:
1. interseção de IDs de segmento dos conjuntos de treino e teste: **0 nas 40 divisões**;
2. interseção dos valores `mancha_id` de treino e teste: **0 nas 40 divisões**;
3. distância euclidiana mínima entre os **pontos x/y** de treino e teste: todos os 40 mínimos excederam 25 m.

| Região | N amostras | N divisões | IDs repetidos treino-teste | Manchas repetidas treino-teste | Menor distância entre pontos |
|---|---:|---:|---:|---:|---:|
| Sagrada Família | 500 | 10 | 0 | 0 | 33,59 m |
| Centro de Novo Hamburgo | 500 | 10 | 0 | 0 | 79,71 m |
| Lomba Grande | 500 | 10 | 0 | 0 | 78,58 m |
| Cristo Rei | 500 | 10 | 0 | 0 | 34,73 m |

**Limite da auditoria espacial:** os CSVs fornecem pontos `x/y`; os mínimos acima são **distâncias entre pontos**, não distância geométrica entre os polígonos completos dos segmentos. Ainda é necessário reabrir os GeoPackages de segmentos e conferir também as **geometrias** e, se exigido pelo protocolo, grupos espaciais de bloco explicitamente persistidos. Portanto a auditoria encontrou ausência de vazamento por ID/mancha nos splits registrados, mas **não constitui certificado universal de ausência de vazamento**.

Na **Area1**, a base equilibrada contém 498 referências originais e apenas dois exemplos adicionais preliminares. Uma sobreposição aparente no campo `mancha_id` entre treino e teste representa valor genérico/ausente nos registros históricos, não uma mancha identificada compartilhada; não deve ser interpretada como vazamento. Seus mínimos entre pontos também superaram 25 m (menor 32,14 m). A base histórica de 505 segmentos permanece separada.

## Seleção das amostras e principal ameaça à validade

Todos os 2.000 segmentos locais das quatro regiões externas têm `classe_verificada` **vazia**. Os 200 pontos de validação geográfica cega reservados em cada região (800 ao todo) também constam como **não anotados** nos manifestos.

As referências locais foram **sugeridas por interpretação visual RGB assistida por IA**, selecionando segmentos Quickshift com **pelo menos 90% dos pixels na mancha rotulada** e ao menos 12 pixels por segmento.

| Região | Fração mínima no interior da mancha | Mediana da fração | Rótulos humanos confirmados |
|---|---:|---:|---:|
| Sagrada Família | 0,9030 | 0,9900 | 0 |
| Centro | 0,9027 | 0,9908 | 0 |
| Lomba Grande | 0,9042 | 0,9947 | 0 |
| Cristo Rei | 0,9004 | 0,9928 | 0 |

**Interpretação:** o protocolo interno mede desempenho na distinção de segmentos **visualmente homogêneos e selecionados**, não a classificação de toda a cena urbana. É plausível que esta seleção aumente o F1 por remover alvos ambíguos, bordas, sombras, gramíneas secas e coberturas não vegetais. Isso é uma ameaça de **viés de seleção / avaliação fácil**, independente do conceito clássico de sobreajuste a treino. Não afirmar que há vazamento de treino/teste só porque F1 é alto.

## Comparação de F1 da seleção interna e do teste espacial interno

Os arquivos de métricas guardam `f1_cv_interna` (seleção de parâmetros dentro do treino externo) e `f1_macro` no teste espacial externo ao ajuste. Estes campos **não são** o F1 calculado nos próprios pontos de treinamento. Exemplos SVM RBF / NDVI + HSV + Canny, médias de cinco divisões:

| Região | CV interna 250 m | Teste espacial 250 m | CV interna 500 m | Teste espacial 500 m |
|---|---:|---:|---:|---:|
| Area1 (500 segmentos) | 0,8792 | 0,8659 | 0,8566 | 0,8652 |
| Sagrada Família | 0,9659 | 0,9556 | 0,9632 | 0,9649 |
| Centro | 0,9715 | 0,9454 | 0,9655 | 0,9779 |
| Lomba Grande | 0,9636 | 0,9752 | 0,9749 | 0,9799 |
| Cristo Rei | 0,9907 | 0,9928 | 0,9872 | 0,9912 |

As médias internas e de teste **não evidenciam discrepância maciça e sistemática** no SVM local, mas **não permitem estimar a diferença F1 de treino − F1 de teste**. Para diagnosticá-la, registrar por fold `f1_treino` do estimador ajustado e `f1_teste`, sem jamais treinar com o teste. Mesmo uma diferença pequena não demonstraria generalização para pixels não selecionados ou para outra cidade.

## Divergência já observada na transferência da Area1

- Centro de Novo Hamburgo: o SVM **treinado com a Area1** marcou **100% dos pixels válidos como árvores**; com **treino local equilibrado**, o relatório registrou **18,0%**. O F1 local de 0,9779 em blocos de 500 m **não é o F1 do modelo transferido da Area1**.
- Sagrada Família contém a Area1 em grande extensão; avaliação externa deve excluir o polígono, 25 m de buffer e segmentos interceptantes, e usar referências independentes.
- Modelos binários aplicados a asfalto, telhados e solo exposto atribuem mesmo assim uma das duas classes. Hectares previstos não são cobertura vegetal verificada.

## Diagnóstico e próximos testes

**Diagnóstico atual:** os registros encontrados favorecem a conclusão de que os altos F1 locais resultam, pelo menos em parte, de **segmentos escolhidos em manchas fáceis** e referências **ainda não verificadas por humanos**. Não foi encontrado vazamento direto por ID ou mancha nas 40 divisões externas; a distância entre os pontos dos splits também respeita 25 m. Não existe ainda evidência suficiente para atribuir os F1 altos a overfitting convencional, afirmar ausência absoluta de vazamento, ou chamar esses valores de acurácia de transferência.

Para resolver cientificamente:
1. Auditar geometria poligonal completa e associações aos blocos, não só pontos; conferir se `mancha_id` não foi inferido de forma circular a partir das próprias previsões.
2. Reproduzir cada divisão com **F1 treino, CV interna, teste espacial, desvio-padrão e matriz de confusão**; comparar regularização moderada e forte apenas dentro do treino.
3. Testar sensibilidade espacial com buffer maior (por exemplo 50–100 m) e blocos mais amplos em **experimento novo**, sem substituir a bateria histórica, separando a hipótese sobre autocorrelação espacial.
4. Concluir **rotulação humana cega e independente** dos 200 pontos reservados por região; anotar também `outra cobertura` e `incerto`; documentar quantos pontos de árvores/gramíneas realmente forem avaliáveis.
5. Avaliar **nos mesmos pontos externos** os oito modelos congelados da Area1 e os modelos treinados localmente. O F1 externo das duas estratégias só pode ser calculado após os rótulos independentes, distinguindo teste binário condicional à vegetação de mapeamento integral urbano.

**Segurança:** esta auditoria é documental e computacional sobre artefatos existentes; não reexecutou o Google Colab, não alterou modelos, pontos, mapas, métricas históricas nem `main`. O PR deve permanecer em rascunho.
