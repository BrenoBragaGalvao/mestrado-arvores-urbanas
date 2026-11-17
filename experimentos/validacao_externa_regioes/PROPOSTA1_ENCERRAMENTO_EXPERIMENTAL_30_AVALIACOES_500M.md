# Proposta 1 — Encerramento experimental: Regressão Logística original

**Data:** 17 de novembro de 2026. **Estado:** processamento e reprodução computacional **concluídos**; revisão visual independente das referências externas **pendente**.

## Decisão metodológica

Manter como único modelo principal a Regressão Logística original treinada exclusivamente com **510 pontos Area1** (257 árvores e 253 gramíneas), correspondentes a **505 segmentos únicos** (257 árvores, 248 gramíneas). Pipeline: Quickshift, intensidade HSV (brilho), bordas Canny e NDVI. Modelo: `StandardScaler + LogisticRegression(C=0.1, penalty='l2', max_iter=3000, random_state=42)`.

Os experimentos alternativos B/C/D não integram os valores centrais. O modelo original final permanece congelado; nenhuma variável ou regularização é escolhida com as referências CHMv2 externas.

## Resultados após 30 avaliações com blocos de 500 m

| Região | Média F1-macro | DP (n=30) | F1 original sem bootstrap | Protocolo |
|---|---:|---:|---:|---|
| Area1 / Caxias do Sul | **0,8421** | 0,0389 | 0,8542 (média das 5 primeiras divisões) | 30 separações espaciais com refit apenas na Area1; embargo geométrico 25 m |
| Sagrada Família / Caxias do Sul | **0,7584** | 0,0330 | 0,7597 | 30 reamostragens de blocos de 500 m com reposição |
| Lomba Grande / Novo Hamburgo | **0,7794** | 0,0337 | 0,7785 | 30 reamostragens de blocos de 500 m com reposição |
| Cristo Rei / São Leopoldo | **0,7961** | 0,0377 | 0,8042 | 30 reamostragens de blocos de 500 m com reposição |

**NOTA IMPORTANTE:** a Area1 foi re-treinada dentro de cada uma das 30 divisões; as 90 avaliações externas são *bootstrap espacial* dos mesmos pontos, mantendo o **mesmo classificador**. Portanto, não se trata de 120 treinamentos nem de 120 avaliações independentes, e os dois protocolos não são diretamente equiparáveis.

### Referências externas

- **Sagrada Família:** 179/200 pontos com referência CHMv2 elegível; F1 agregado 0,7597465431; matriz de confusão [69,9;34,67].
- **Lomba Grande:** 183/200; F1 agregado 0,7785039942; matriz [61,4;36,82].
- **Cristo Rei:** 181/200; F1 agregado 0,8042396712; matriz [83,13;22,63].

São **543 pontos elegíveis dos 600 selecionados**, após exclusão de 57 casos sem referência conservadora. As matrizes são de dados agregados não reamostrados, linhas CHMv2 (árvore,grama), colunas previsão (árvore,grama).

O Meta/WRI CHMv2 fornece **pseudo-rótulos automáticos** para comparação, não classes humanas validadas. Assim, os F1 externos são concordância com CHMv2, não prova definitiva de acurácia de campo. Os percentis de apenas 30 bootstraps não são intervalos de confiança formais.

## Auditoria de reprodutibilidade — concluída

Em 17/11/2026 foi executado novamente o script de 30 divisões e 90 reamostragens em diretório independente com o modelo e os dados-fonte congelados. O script conferiu o ajuste do modelo original e o afastamento espacial de 25 m. Os **quatro CSV** resultantes foram **idênticos byte a byte** aos de referência:

1. `area1_30_divisoes_500m.csv`
2. `externas_90_reamostragens_blocos_500m.csv`
3. `externas_f1_original_sem_reamostragem.csv`
4. `TABELA_FINAL_MEDIAS_30_AVALIACOES_500M.csv`

Foi organizado pacote portátil com código, dados derivados, geometrias, modelo original e manifestos SHA-256 para reproduzir esses cálculos. A reprodução desde os ortomosaicos RGB/NIR exigirá arquivos brutos que não integram o pacote portátil.

## Auditoria visual independente — preparada, não concluída

Foram selecionados **180 pontos cegos**: 60 por região externa, sendo um de cada bloco distinto de 500 m, amostragem aleatória com semente fixa sem uso da previsão do modelo ou do CHMv2 na escolha. Foram preparados recortes RGB, atlas e formulário com as classes humanas intencionalmente vazias. A anotação deve preceder qualquer consulta às previsões ou pseudo-rótulos. Não se declara uma validação humana concluída sem esse procedimento.

## Conclusão e escopo do fechamento

A **fase experimental computacional da Proposta 1** está fechada e reprodutível, com o modelo de Regressão Logística original e as quatro tabelas de F1. Permanece como **limitação aberta** a ausência de verificação visual independente dos rótulos externos; sem ela, evitar linguagem de validação de campo, acurácia geográfica definitiva ou equivalência entre valores internos e externos.

Documentação e arquivos originais de trabalho permanecem na branch `feature/validacao-geografica-externa`; **não houve alteração da branch `main`** por este encerramento.
