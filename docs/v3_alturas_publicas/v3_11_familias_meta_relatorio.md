# V3 — Onze familias do artigo de CW–H adaptadas para H=f(D_eq), comparadas com a Meta/WRI

## ADVERTENCIA DE INTERPRETACAO

**As 11 familias de curvas foram testadas, mas NAO sao as 11 equacoes
originais com os coeficientes publicados.** O artigo de
[Chatziathanasiou et al. (2024)](https://doi.org/10.3390/land13101579)
ajusta **largura de copa medida CW=f(H) a partir de altura real medida**
em especies e cidades gregas. **Aqui adaptamos a mesma familia de curvas**
para **H_modelada_Meta=f(D_eq)**. A variavel D_eq=2sqrt(A_superpixel/pi)
e o **diametro circular equivalente de um SUPERPIXEL QUICKSHIFT**,
**nao a largura da copa individual observada no artigo**.

A [correcao de 2026](https://doi.org/10.3390/land15030473)
retificou formas de equacoes no artigo; este ensaio registra a correcao
e nao reutiliza coeficientes de especies da Grecia.
Os valores Meta/WRI CHMv2 sao **altura de dossel MODELADA**,
nao medidas de campo. O MAE avalia exclusivamente concordancia
com Meta/WRI, nunca precisao de altura real.

## Parametrizacao ensaiada

Definimos x=D_eq/10 m para estabilizar numericamente os ajustes
(sem mudar a familia funcional). Restricao de crescimento
nao decrescente e valores previstos entre 0 e 40 m. No modelo
logistico, u=40 m e fixo como hipotese de trabalho.

| Modelo artigo (familia) | Equacao ADAPTADA, H_modelada=f(x) |
|---|---|
| 1. Linear | H=b0+b1 x |
| 2. Logaritmico | H=b0+b1 ln(x) |
| 3. Inverso | H=b0-b1/x |
| 4. Quadratico | H=b0+b1 x+b2 x² |
| 5. Cubico | H=b0+b1 x+b2 x²+b3 x³ |
| 6. Potencial | H=b0 x^b1 |
| 7. Composto | H=b0 b1^x |
| 8. Curva-S | H=exp(b0-b1/x) |
| 9. Logistico | H=1/(1/40+b0 b1^x) |
| 10. Crescimento | H=exp(b0+b1 x) |
| 11. Exponencial | H=b0 exp(b1 x) |

**Atenção: modelos 7, 10 e 11 sao reparametrizacoes da MESMA
familia exponencial de dois parametros**, nao tres classes
funcionais independentes. A ordem entre elas nao deve ser
interpretada como superioridade de uma tecnica distinta.

## Resultados com validacao espacial de 5 divisões e embargo de 25 m

Todos os 257 pontos aparecem em teste fora do respectivo
ajuste em cada uma das escalas 250 m e 500 m.
A selecao da familia e feita somente em tres folds
internos, sem usar os alvos de teste externos.

### Pixel exato — blocos de 250 m

| Modelo | MAE vs. Meta (m) | RMSE vs. Meta (m) | MAE no subset Meta >0 (m) |
|---|---:|---:|---:|
| Controle_constante | 4.578 | 6.434 | 6.250 |
| Selecao_aninhada | 4.578 | 6.434 | 6.250 |
| Cubico | 4.584 | 6.032 | 5.560 |
| Curva_S | 4.587 | 6.051 | 5.582 |
| Logaritmico | 4.588 | 6.050 | 5.579 |
| Quadratico | 4.589 | 6.040 | 5.567 |
| Inverso | 4.589 | 6.051 | 5.587 |
| Linear | 4.591 | 6.047 | 5.574 |
| Potencial | 4.593 | 6.057 | 5.583 |
| Logistico | 4.597 | 6.056 | 5.585 |
| Exponencial | 4.598 | 6.057 | 5.586 |
| Crescimento | 4.598 | 6.057 | 5.586 |
| Composto | 4.598 | 6.057 | 5.586 |

**Melhor das 11 por MAE observado:** Cubico (4.584 m).
**Controle constante:** 4.578 m.
**Seleção aninhada:** 4.578 m.
**Famílias selecionadas internamente nos cinco folds:** {'Controle_constante': 5}.
A melhor família da tabela é uma escolha exploratória APÓS ver
os resultados de teste; para alegar desempenho de seleção
sem viés, usar a linha Seleção_aninhada e avaliação futura.

### Pixel exato — blocos de 500 m

| Modelo | MAE vs. Meta (m) | RMSE vs. Meta (m) | MAE no subset Meta >0 (m) |
|---|---:|---:|---:|
| Controle_constante | 4.451 | 6.342 | 6.307 |
| Selecao_aninhada | 4.451 | 6.342 | 6.307 |
| Curva_S | 4.505 | 5.940 | 5.484 |
| Logaritmico | 4.506 | 5.937 | 5.478 |
| Inverso | 4.506 | 5.944 | 5.495 |
| Linear | 4.509 | 5.932 | 5.467 |
| Potencial | 4.510 | 5.938 | 5.470 |
| Logistico | 4.519 | 5.938 | 5.471 |
| Composto | 4.520 | 5.939 | 5.473 |
| Exponencial | 4.520 | 5.939 | 5.473 |
| Crescimento | 4.520 | 5.939 | 5.473 |
| Quadratico | 4.522 | 5.939 | 5.476 |
| Cubico | 4.529 | 5.941 | 5.486 |

**Melhor das 11 por MAE observado:** Curva_S (4.505 m).
**Controle constante:** 4.451 m.
**Seleção aninhada:** 4.451 m.
**Famílias selecionadas internamente nos cinco folds:** {'Controle_constante': 5}.
A melhor família da tabela é uma escolha exploratória APÓS ver
os resultados de teste; para alegar desempenho de seleção
sem viés, usar a linha Seleção_aninhada e avaliação futura.

### Maximo 5 m — blocos de 250 m

| Modelo | MAE vs. Meta (m) | RMSE vs. Meta (m) | MAE no subset Meta >0 (m) |
|---|---:|---:|---:|
| Controle_constante | 4.778 | 6.077 | 4.488 |
| Selecao_aninhada | 4.778 | 6.077 | 4.488 |
| Inverso | 4.802 | 6.117 | 4.531 |
| Curva_S | 4.803 | 6.118 | 4.532 |
| Logaritmico | 4.808 | 6.124 | 4.535 |
| Potencial | 4.810 | 6.127 | 4.537 |
| Linear | 4.814 | 6.131 | 4.539 |
| Logistico | 4.817 | 6.135 | 4.542 |
| Composto | 4.818 | 6.136 | 4.543 |
| Exponencial | 4.818 | 6.136 | 4.543 |
| Crescimento | 4.818 | 6.136 | 4.543 |
| Quadratico | 4.819 | 6.136 | 4.542 |
| Cubico | 4.820 | 6.138 | 4.540 |

**Melhor das 11 por MAE observado:** Inverso (4.802 m).
**Controle constante:** 4.778 m.
**Seleção aninhada:** 4.778 m.
**Famílias selecionadas internamente nos cinco folds:** {'Controle_constante': 5}.
A melhor família da tabela é uma escolha exploratória APÓS ver
os resultados de teste; para alegar desempenho de seleção
sem viés, usar a linha Seleção_aninhada e avaliação futura.

### Maximo 5 m — blocos de 500 m

| Modelo | MAE vs. Meta (m) | RMSE vs. Meta (m) | MAE no subset Meta >0 (m) |
|---|---:|---:|---:|
| Controle_constante | 4.665 | 6.007 | 4.405 |
| Selecao_aninhada | 4.665 | 6.007 | 4.405 |
| Curva_S | 4.731 | 6.063 | 4.458 |
| Inverso | 4.731 | 6.065 | 4.459 |
| Logaritmico | 4.733 | 6.060 | 4.456 |
| Potencial | 4.734 | 6.061 | 4.456 |
| Linear | 4.735 | 6.060 | 4.452 |
| Logistico | 4.737 | 6.063 | 4.453 |
| Exponencial | 4.738 | 6.064 | 4.453 |
| Composto | 4.738 | 6.064 | 4.453 |
| Crescimento | 4.738 | 6.064 | 4.453 |
| Quadratico | 4.743 | 6.069 | 4.455 |
| Cubico | 4.751 | 6.077 | 4.458 |

**Melhor das 11 por MAE observado:** Curva_S (4.731 m).
**Controle constante:** 4.665 m.
**Seleção aninhada:** 4.665 m.
**Famílias selecionadas internamente nos cinco folds:** {'Controle_constante': 5}.
A melhor família da tabela é uma escolha exploratória APÓS ver
os resultados de teste; para alegar desempenho de seleção
sem viés, usar a linha Seleção_aninhada e avaliação futura.

## Reprodutibilidade

- [257 pontos, referência Meta e previsões OOF de todas as famílias](v3_11_familias_meta_257_previsoes.csv).
- [Resumo dos 11 modelos, controle e seleção aninhada](v3_11_familias_meta_resumo.csv).
- [Folds espaciais, embargo e escolha interna](v3_11_familias_meta_folds.csv).
- [Gráfico comparativo de MAE](v3_11_familias_meta_mae.png).
- [Script do experimento](../../experimentos/v3_testar_11_modelos_artigo_meta.py).

**Limitações:** D_eq calculado por área de SUPERPIXEL pode não
representar nenhuma copa real. O máximo Meta em 5 m pode
pertencer a outra árvore; zero no pixel Meta não implica
ausência da árvore. Nenhum modelo foi validado com altura medida
em campo. Estes resultados NÃO justificam substituir automaticamente
os coeficientes históricos C1–C6 do notebook original.
