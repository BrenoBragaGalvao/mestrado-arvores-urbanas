# Proposta 2 — Ficha de campo e validação HeightCzech (Candangolândia)

## Objetivo da próxima etapa

Avaliar, **após a visita**, a concordância de **CHMv2 (Meta/WRI)** e **ETH 2020** com a altura observada em **12 árvores intencionalmente selecionadas na Candangolândia (DF)**. Os cálculos só devem ocorrer quando as leituras reais estiverem preenchidas. A diferença entre produtos de satélite, isoladamente, **não é um erro de validação**.

A seleção atual preserva os **IDs originais dos 25 candidatos**: CAND-002, 004, 006, 007, 008, 012, 013, 015, 016, 019, 020 e 023. Os 25 registros originais não foram alterados. **Não renumerar** essas árvores para CAND-01…CAND-12: isto compromete o vínculo com a base original. O README agora usa os mesmos IDs completos.

## Arquivos

- [`pontos_12_coleta_heightczech.csv`](pontos_12_coleta_heightczech.csv): ficha sem nenhuma leitura de campo preenchida. Contém as 12 posições originais WGS84 e estimativas CHMv2 e ETH já documentadas.
- [`validar_heightczech_12_arvores.py`](validar_heightczech_12_arvores.py): validação e cálculo de diferenças pareadas, com mediana de três leituras por árvore.
- [`test_validar_heightczech.py`](test_validar_heightczech.py): testes **exclusivamente com dados sintéticos** que não são resultados científicos.

## Como coletar

Copie a ficha para um arquivo privado, **fora do Git**, por exemplo `medicoes_privadas.csv`. Para cada árvore:

1. Confirme em campo que o indivíduo observado corresponde ao ID e às coordenadas originais; se não houver correspondência inequívoca, marque `INCERTA` ou `NAO_LOCALIZADA`, sem mover o ponto para outra árvore.
2. Verifique o acesso público e a segurança da observação. Registre `SIM` apenas quando houver acesso de observação confirmado, sem entrar em propriedade privada nem se aproximar de condutores.
3. Com o **HeightCzech**, obtenha **três leituras independentes** da altura (reapontando para base e topo), registre a **distância horizontal medida**, a data, o modelo do smartphone e a versão do aplicativo. Se o topo/base não estiver visível, não invente leitura.
4. Para registros sem medição, deixe as três leituras e respectivos metadados vazios. **Não coloque os valores CHMv2 ou ETH nos campos HeightCzech.**
5. Guarde evidências fotográficas de forma privada, observando privacidade de pessoas/placas e locais de acesso restrito.

Valores permitidos de `identificacao`: `PENDENTE`, `CONFIRMADA`, `INCERTA`, `NAO_LOCALIZADA`. Em `acesso_publico`: `PENDENTE`, `SIM`, `NAO`.

Os campos `id_arvore`, `latitude`, `longitude`, `altura_chmv2_m` e `altura_eth2020_m` são **congelados**. O verificador recusa alterações, inclusões, exclusões, duplicações ou rearranjos de registros.

## Execução depois da coleta

```bash
python3 experimentos/proposta2_candangolandia/validar_heightczech_12_arvores.py \
  --entrada /CAMINHO_PRIVADO/medicoes_privadas.csv \
  --saida /CAMINHO_PRIVADO/resultado_validacao
```

Saídas: `comparacao_pareada_12_arvores.csv` (medianas e erros assinados individualizados, nunca inventados) e `resumo_validacao_campo.json` (número válido, MAE, RMSE e viés para **ambos** os modelos na **mesma amostra pareada**). Para cada árvore, o erro é **modelo menos mediana de campo**, em metros, e a amplitude é a maior leitura menos a menor.

**Regras científicas:**

- **Sem medições de campo:** `AGUARDA_CAMPO`, (n=0), métricas = `null`. É a condição atual.
- **Uma ou duas árvores válidas:** `MEDICOES_INSUFICIENTES`, sem MAE/RMSE agregados.
- **De três a onze:** `PARCIAL_EXPLORATORIO`, com métricas apenas descritivas e `n` explícito.
- **Doze:** `MEDICOES_COMPLETAS_REQUER_REVISAO` — exige revisão científica/visual antes de apresentar conclusão.

Somente registros com **três leituras**, data válida, distância horizontal, identificação confirmada, acesso confirmado e metadados do aparelho são incluídos. Amostras com identificação incerta, restrição de acesso ou medições faltantes não entram no cálculo; não são substituídas por árvores mais convenientes.

Mesmo com doze valores, trata-se de **amostra dirigida** e de alturas observadas por smartphone, sujeitas a incerteza. Um MAE menor significa apenas maior concordância **nessa amostra e nessas condições**. O estudo **não** mede fiação, distância vertical aos cabos ou risco de queda/interferência elétrica.

## Controle de reprodutibilidade

O GitHub Actions [`testar-proposta2-candangolandia.yml`](../../.github/workflows/testar-proposta2-candangolandia.yml) executa testes sintéticos e confirma que a **ficha original sem leituras** continua retornando `AGUARDA_CAMPO` e métricas nulas. Isso não equivale a medições de campo realizadas.

Fonte da amostra e metodologia: `AMOSTRA_12_PONTOS_METODOLOGIA_E_TABELA.md` (arquivos da pesquisa, 21/11/2026), lista dos 25 candidatos e seção 5.2 do README principal. Os valores ETH não foram extraídos novamente.
