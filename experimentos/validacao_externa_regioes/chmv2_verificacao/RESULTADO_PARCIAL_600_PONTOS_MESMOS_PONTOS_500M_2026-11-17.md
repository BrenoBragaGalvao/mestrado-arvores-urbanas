# Experimento C — mesma avaliação cega de 600 pontos; F1-macro em blocos de 500 m

**Data da auditoria:** 17/11/2026. **Origem:** ZIP entregue pelo pesquisador, `resultado_final_600_pontos_500m-20261117T200128Z-1-001.zip`; há um segundo ZIP `validacao_externa_regioes-20261117T200130Z-1-001.zip` **vazio**, contendo apenas uma entrada de diretório.

**Avaliação de transferência:** somente Regressão Logística, com o modelo A treinado na Area1 inteira e o modelo C retreinado em **371 segmentos originais Area1 selecionados por concordância com CHMv2**. As 600 referências externas são **pseudo-rótulos automáticos CHMv2, não rótulos humanos**. O tamanho de bloco de 500 m organiza a dependência espacial; o F1 é calculado sobre as amostras elegíveis agregadas.

## Resultados reais extraídos e conferidos

| Região | Total planejado | Pontos com CHMv2 elegíveis | Blocos 500 m representados | F1 A | F1 C | Variação C-A | Controle de identidade A |
|---|---:|---:|---:|---:|---:|---:|---|
| Sagrada Família | 200 | 179 | 78 | 0,7597465 | **0,8260338** | **+0,0662873** | **0 divergências em 200** |
| Lomba Grande | 200 | 183 | 140 | **0,7785040** | 0,7469336 | −0,0315704 | **0 divergências em 200** |
| Cristo Rei | 200 | — | — | 0,8042 (prévio) | **não calculado** | — | RAR bloqueou extração |

## Matrizes de confusão

Ordem: linhas **referência CHMv2 árvore / grama** e colunas **previsto árvore / grama**.

- Sagrada A: `[[69,9],[34,67]]`; C: `[[68,10],[21,80]]`.
- Lomba A: `[[61,4],[36,82]]`; C: `[[61,4],[42,76]]`.

As previsões mudaram em **14 pontos elegíveis** de cada região. Em Sagrada, **13 mudanças foram concordantes** com a referência automática e **1 discordante**. Em Lomba, **4 concordantes** e **10 discordantes**.

## Incerteza

Bootstrap pareado por grupos de **500 m**, 10.000 reamostragens (semente 20261117), diferença F1 C-A:
- Sagrada Família: IC percentil 95% **[+0,0296, +0,1034]**.
- Lomba Grande: IC percentil 95% **[−0,0753, +0,0100]**.

Esses intervalos refletem reamostragem espacial dos **pseudo-rótulos disponíveis**. Não eliminam vieses/erros próprios do CHMv2 nem produzem validação de campo.

## Causa exata da incompletude

O arquivo de log `cristo_rei_sao_leopoldo_execucao_completa.log` registra que o Colab abriu o RAR válido de **1.563.064.317 bytes**, mas o `7z e` devolveu `No files to process` porque o padrão de extração original não encontrou o `_ORTHO_4BANDAS.tif` em pasta interna. **Não há F1 C para Cristo Rei**.

**Correção no código:** o script agora lista os membros com `7z l -slt`, identifica o nome real do TIFF multiespectral e extrai recursivamente. O notebook atualizado detecta os relatórios já finalizados de Sagrada e Lomba, **preserva os resultados deles**, processa apenas Cristo Rei e consolida os três valores.

Notebook corrigido:
https://colab.research.google.com/github/BrenoBragaGalvao/mestrado-arvores-urbanas/blob/feature/validacao-geografica-externa/experimentos/validacao_externa_regioes/chmv2_verificacao/Proposta1_F1_500m_Mesmos_600_Pontos_Colab.ipynb

**Conclusão provisória:** houve aumento do F1 de concordância em Sagrada e redução em Lomba; não há demonstração de melhoria generalizada. Falta executar Cristo Rei. Não misturar este conjunto de teste com os 1.500 candidatos locais homogêneos ou usá-lo para ajuste a posteriori.
