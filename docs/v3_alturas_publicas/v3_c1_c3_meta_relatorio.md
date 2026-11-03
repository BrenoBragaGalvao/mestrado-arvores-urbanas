# V3 — Comparacao exploratoria de C1-C3 e modelos de Chatziathanasiou et al. (2024)

**Atencao:** o artigo apresenta CW=f(H) por especie em cidades gregas.
**Os coeficientes C1-C3 do codigo original NAO sao desse artigo.**
As estimativas Meta/WRI sao alturas MODELADAS de dossel, nao alturas de campo.
As diferencas numericas abaixo nao comprovam precisao real de altura.
Nao foi feito ajuste de coeficientes com a Meta.

## 1. Configuracoes empiricas originais (A = area do SUPERPIXEL)

| Config. | a | b | Potencial | Linear |
|---|---:|---:|---|---|
| C1 | 0.5 | 0.7 | 0.5 x A^0.7 | 0.5 + 0.7 x A |
| C2 | 0.6 | 0.8 | 0.6 x A^0.8 | 0.6 + 0.8 x A |
| C3 | 2.5 | 0.4 | 2.5 x A^0.4 | 2.5 + 0.4 x A |

## 2. Proximidade numerica da Meta nos mesmos 257 pontos

Comparacao principal: valor do pixel da Meta, incluindo zeros.
Sensibilidade: maximo Meta em raio de 5 m, excluindo valores zero.
Os indices originais NAO estao calibrados em metros: diferencas
devem ser descritas apenas como divergencia numerica, nao MAE
de altura real. O raio de 5 m pode incluir outra copa.

| Modelo | n pixel | Divergencia media pixel | n Meta raio 5m >0 | Divergencia media raio 5m >0 | Pearson raio 5m >0 |
|---|---:|---:|---:|---:|---:|
| C1_potencial | 257 | 11.553 | 215 | 8.711 | 0.036 |
| C3_potencial | 257 | 13.067 | 215 | 9.846 | 0.027 |
| C2_potencial | 257 | 25.395 | 215 | 21.869 | 0.038 |
| C3_linear | 257 | 52.173 | 215 | 48.433 | 0.044 |
| C1_linear | 257 | 90.796 | 215 | 86.908 | 0.044 |
| C2_linear | 257 | 104.454 | 215 | 100.534 | 0.044 |

## 3. Equacoes publicadas testadas por inversao algebrica

O artigo mede CW (largura real de copa) e H (altura real)
em Magnolia grandiflora e Acer negundo. Como a Area1 nao mede
CW, foi testada somente a hipotese de largura circular equivalente
CW=sqrt(4A/pi) a partir de area de SUPERPIXEL. Essa suposicao
nao demonstra largura real; especie de cada individuo e desconhecida.
Apenas alturas hipoteticas dentro do intervalo observado da especie
no artigo foram registradas; demais pontos sao ausentes.

| Modelo/especie | Equacao H invertida | n/257 validos sem extrapolacao | Diverg. pixel | Diverg. raio5 >0 |
|---|---|---:|---:|---:|
| Magnolia_Xanthi_inverse / Magnolia grandiflora | H=16.672/(7.280-CW) | 5 | 6.558 | 3.853 |
| Magnolia_Komotini_inverse / Magnolia grandiflora | H=14.882/(7.394-CW) | 7 | 7.042 | 5.015 |
| Magnolia_Orestiada_log / Magnolia grandiflora | H=exp((CW+1.440)/3.375) | 19 | 7.768 | 5.901 |
| Magnolia_Kavala_log / Magnolia grandiflora | H=exp((CW+1.906)/3.691) | 22 | 8.000 | 5.919 |
| Acer_total_compound / Acer negundo | H=ln(CW/0.676)/ln(1.123) | 0 | - | - |

A menor divergencia contra a Meta NAO indica o modelo
mais correto biologicamente; a Meta nao e verdade de campo.
A comparacao com o artigo e somente ensaio matematico de
transferibilidade e nao validacao ou calibracao regional.

## 4. Fonte e dados reprodutiveis

- Artigo: https://doi.org/10.3390/land13101579 (Tabelas 1, 3, 4, 5, 6, 8 e 9).
- Meta/WRI CHMv2: https://registry.opendata.aws/dataforgood-fb-forestsv2/
- CSV origem: v3_comparacao_c3_meta_257.csv (257 pontos).
- Saidas: v3_c1_c3_meta_257_pontos.csv; v3_c1_c3_meta_resumo_comparativo.csv;
  v3_modelos_artigo_testados.csv; v3_c1_c3_meta_comparacao.png.
- Necessario para validacao de altura: copa realmente delimitada,
  especie e medicao independente de altura dos mesmos individuos.
