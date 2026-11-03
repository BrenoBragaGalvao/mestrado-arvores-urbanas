# Reexecução E4b — ablação NDVI, HSV e Canny (03/11/2026)

## Objetivo e compatibilidade

Reexecutamos **a comparação entre HSV + Canny e NDVI + HSV + Canny** para os mesmos 505 segmentos rotulados de E2 (812 quadrantes), com **exatamente os mesmos 10 splits externos** da seção 3.6.1 (cinco blocos de 250 m, cinco de 500 m; embargo de 25 m entre geometrias), mesmos algoritmos e mesma política de seleção de regularização.

Para cada classificador e cada combinação de atributos, usamos separadamente as **mesmas três divisões espaciais internas do treinamento** para escolher entre as receitas *forte* e *moderada*, sem consultar os exemplos de teste externo. Em caso de empate, a receita forte é escolhida. Para o Dummy, há uma única receita. Os modelos SVM, KNN e regressão logística usam `Pipeline` com padronização somente no treino.

**900 avaliações de validação interna; 160 avaliações externas; 16 linhas agregadas** (dois grupos espaciais × oito classificadores). O teste externo foi previamente utilizado na pesquisa; não é novo conjunto independente.

## Consistência com a seção 3.6.1

Reproduzimos de forma **exata** os 16 resultados do conjunto **NDVI + HSV + Canny** que aparecem na seção 3.6.1: maior diferença numérica encontrada **0,0**. Assim as tabelas das seções 3.5 e 3.6.1 agora descrevem o mesmo protocolo supervisionado.

## Resultados, médias de cinco divisões

| Blocos | Classificador | HSV + Canny | NDVI + HSV + Canny | Ganho com NDVI |
|---|---|---:|---:|---:|
| 250 m | KNN | 0.7474 | 0.8931 | +0.1457 |
| 250 m | SVM RBF | 0.7464 | 0.8908 | +0.1444 |
| 250 m | Regressão logística | 0.7557 | 0.8879 | +0.1323 |
| 250 m | HistGradientBoosting | 0.7608 | 0.8325 | +0.0717 |
| 250 m | Extra Trees | 0.7369 | 0.8266 | +0.0897 |
| 250 m | Random Forest | 0.7522 | 0.8220 | +0.0699 |
| 250 m | Gaussian Naive Bayes | 0.7122 | 0.7986 | +0.0864 |
| 250 m | Dummy | 0.2980 | 0.2980 | +0.0000 |
| 500 m | Regressão logística | 0.7909 | 0.8666 | +0.0758 |
| 500 m | SVM RBF | 0.7900 | 0.8619 | +0.0719 |
| 500 m | KNN | 0.7835 | 0.8481 | +0.0646 |
| 500 m | Extra Trees | 0.7822 | 0.8335 | +0.0514 |
| 500 m | HistGradientBoosting | 0.7805 | 0.8246 | +0.0441 |
| 500 m | Random Forest | 0.7743 | 0.8240 | +0.0498 |
| 500 m | Gaussian Naive Bayes | 0.7256 | 0.7400 | +0.0144 |
| 500 m | Dummy | 0.2799 | 0.2799 | +0.0000 |

## Interpretação e limites

O F1-macro médio foi maior ao acrescentar NDVI em **todos os sete classificadores além do Dummy**, em ambas as escalas. O Dummy permaneceu inalterado. A diferença reflete o contraste entre **pipelines avaliados sob a mesma regra de tuning**; como cada braço pode escolher sua receita independentemente, não isola o efeito puro do NDVI com parâmetros de modelo idênticos.

É uma **validação espacial interna na mesma imagem Area1**, sem prova de ausência completa de overfitting ou de capacidade de generalização para outra região. Os resultados são médias de partições que compartilham exemplos e já haviam sido examinadas em estudos anteriores. Não houve nova segmentação Quickshift: reutilizamos as características já extraídas e rotuladas.

## Como reproduzir

No notebook `Segmentacao_area_completa_v2_experimentos.ipynb`, execute a célula *E4b — reexecução da comparação de atributos* depois que os dados E2 estiverem disponíveis. O script `experimentos/reexecutar_ablacao_atributos_aninhada_v2.py` tem dois modos:

- `--modo evidencias`: utiliza `E3c_base_rotulada_812.csv`, `E3c_geometrias_rotuladas_812.gpkg`, `amostras_comuns.csv` e `particoes_auditadas.csv` do pacote derivado de 03/11/2026. **Este modo reproduz os valores acima e a seção 3.6.1.**
- `--modo v2`: lê saídas progressivas atuais da V2 e faz embargo E2 por centroides, podendo produzir resultados diferentes. Também exige o diretório E9 por compatibilidade com o carregamento de dados existente.

O script gera `tabelas_readme_secao_3_5.csv`, `avaliacoes_externas_e4b.csv`, `avaliacoes_internas_e4b.csv`, `receitas_selecionadas_e4b.csv`, `auditoria_particoes_e4b.csv` e `manifesto.json`. Nenhum resultado anterior é apagado.