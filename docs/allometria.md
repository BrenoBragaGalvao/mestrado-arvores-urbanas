# Estimativa experimental de altura por área da copa

## Fundamentação e ressalva científica

Referência bibliográfica discutida neste projeto:

> Chatziathanasiou, S.; Kitikidou, K.; Milios, E. *Crown Width–Tree Height Models for Magnolia grandiflora, Prunus cerasifera, and Acer negundo Growing in Cities in Northeastern Greece*. **Land**, 2024, 13, 1579. https://doi.org/10.3390/land13101579

O trabalho citado discute relações entre **largura de copa** e **altura**. O notebook **não utiliza diretamente coeficientes desse artigo**: adota uma relação experimental **área projetada do polígono → estimativa de altura**, com coeficientes escolhidos no âmbito do projeto:

```python
altura_estimada = a * area ** b
```

Assim, a relação é uma **hipótese/estimativa empírica**, ainda sem validação por alturas reais observadas em campo. Não deve ser apresentada como medida de altura obtida por sensoriamento remoto, nem como equação literalmente publicada pelos autores citados.

## Configurações presentes no notebook original

O notebook atual [`Segmentacao_area_completa.ipynb`](../Segmentacao_area_completa.ipynb) contém **as seis configurações C1–C6**, com **duas formas em cada uma**: potencial (`a * area ** b`) e linear (`a + area * b`).

| Configuração | a | b |
|---|---:|---:|
| C1 | 0,5 | 0,7 |
| C2 | 0,6 | 0,8 |
| C3 | 2,5 | 0,4 |
| C4 | 4,0 | 0,5 |
| C5 | 0,4 | 0,9 |
| C6 | 1,35 | 0,72 |

O notebook constrói os campos `Power_tree_size_C1` a `Power_tree_size_C6` e `Linear_tree_size_C1` a `Linear_tree_size_C6` e apresenta gráficos exploratórios. Para a seleção dos objetos usados na proximidade de postes, usa especificamente:

```python
tree_polys['Power_tree_size_C3'] = 2.5 * (tree_polys['area'] ** 0.4)
filter_tree = tree_polys[tree_polys['Power_tree_size_C3'] > 7]
```

**Cuidado:** o código original não exige que `predicted_classe == 'arvore'` ao criar `filter_tree`. A seleção combina os segmentos candidatos existentes com o limiar empírico de C3 e pode incluir segmentos classificados como gramíneas. A documentação registra esse comportamento; **não modifica o código**.

## Como validar cientificamente

Se forem obtidas medições reais de altura, comparar estimativas e observações por **MAE**, **RMSE**, análise de resíduos e, quando adequado, **R²**, além de avaliar o ajuste por espécies, classes de porte e área urbana.

Até essa validação, o valor `> 7` deve ser descrito como **limiar da estimativa empírica**, não como confirmação de árvores com altura real maior que 7 metros.

Também não se deve transformar proximidade geométrica de 1, 3 ou 5 metros a postes em afirmação de risco elétrico comprovado.
