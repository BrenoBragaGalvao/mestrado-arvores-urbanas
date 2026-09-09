# Relação alométrica usada na estimativa empírica da altura

## Referência científica

A fundamentação para o uso de uma relação alométrica entre dimensões de copa e altura vem de:

> Chatziathanasiou, S.; Kitikidou, K.; Milios, E. **Crown Width–Tree Height Models for Magnolia grandiflora, Prunus cerasifera, and Acer negundo Growing in Cities in Northeastern Greece.** *Land*, 2024, 13, 1579. https://doi.org/10.3390/land13101579

O artigo avalia diferentes modelos de regressão entre **largura de copa (CW)** e **altura total da árvore (H)**. Entre os modelos testados está o modelo potencial:

$$
\widehat{CW}=b_0H^{b_1}
$$

## Adaptação realizada neste projeto

O projeto não aplica diretamente os coeficientes publicados no artigo. A segmentação produz polígonos georreferenciados e, para cada objeto classificado como árvore, é calculada a **área projetada da copa**.

A forma funcional potencial foi então usada como referência para uma relação empírica entre área da copa e uma estimativa de altura:

$$
\widehat{H}=aA^b
$$

em que:

- **A** = área projetada do objeto/copa;
- **\(\widehat{H}\)** = estimativa empírica da altura;
- **a** e **b** = coeficientes avaliados experimentalmente no notebook.

Portanto, **a forma funcional potencial é inspirada na literatura**, enquanto a substituição de largura de copa por área e os coeficientes usados neste projeto constituem uma **adaptação experimental**.

## Configurações exploradas no notebook

O notebook testa versões potencial e linear para diferentes pares de coeficientes:

| Configuração | a | b |
| --- | ---: | ---: |
| C1 | 0,5 | 0,7 |
| C2 | 0,6 | 0,8 |
| C3 | 2,5 | 0,4 |
| C4 | 4,0 | 0,5 |
| C5 | 0,4 | 0,9 |
| C6 | 1,35 | 0,72 |

Na configuração atualmente adotada no fluxo, utiliza-se **C3** na forma potencial:

$$
\widehat{H}=2{,}5A^{0{,}4}
$$

O notebook posteriormente aplica o filtro:

$$
\widehat{H}>7\,m
$$

para manter apenas os objetos que seguem para a análise de proximidade com a infraestrutura elétrica.

## Interpretação correta

A relação usada no projeto deve ser apresentada como **estimativa empírica de altura**, e não como altura medida em campo nem como equação diretamente publicada por Chatziathanasiou et al. (2024).

O artigo fornece a fundamentação para a relação alométrica CW–H e para a família funcional potencial. A transformação **área da copa → altura estimada** e os coeficientes **2,5** e **0,4** são específicos do experimento atual e ainda precisam de validação independente com alturas reais medidas em campo.

## Próxima validação recomendada

Quando houver alturas observadas de campo, comparar \(\widehat{H}\) com \(H\) por meio de métricas como:

- RMSE;
- MAE;
- coeficiente de determinação \(R^2\);
- análise gráfica entre altura observada e estimada.

Essa etapa permitirá verificar quantitativamente se a configuração C3 é de fato a mais adequada para os dados da área de estudo.
