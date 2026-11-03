# V3 — Auditoria exploratória da alometria em Caxias do Sul

## Questão levantada na qualificação
As estimativas de porte da fórmula original são numericamente plausíveis diante das faixas de altura de árvores documentadas para Caxias do Sul?

A V3 é **independente** do notebook original e da V2. Usa apenas os arquivos **já existentes** em Area1: AOI_RGB_NEW.tif e Arvores.gpkg. Não solicita novos dados. A lista externa de espécies é bibliografia municipal, e não um novo rótulo para as árvores da imagem.

## Evidência municipal
O [Plano Diretor de Arborização Urbana de Caxias do Sul](https://caxias.rs.gov.br/servicos/meio-ambiente/plano-diretor-de-arborizacao-urbana-pdau) disponibiliza [Anexo 1 com o porte das espécies](https://gcpstorage.caxias.rs.gov.br/documents/2020/09/c2d2ec2b-dfb4-4646-aadd-01eced79a722.pdf).

| Espécie | Porte descrito | Observação |
|---|---|---|
| Pitangueira (*Eugenia uniflora*) | 6–12 m | Pode apresentar menor porte na arborização |
| Araucária (*Araucaria angustifolia*) | 20–50 m | Faixa de espécie, não medição de indivíduo |
| Quaresmeira (*Tibouchina sellowiana*) | 4–15 m | Na arborização local raramente passa de 8 m |
| Caroba (*Jacaranda micrantha*) | 10–25 m | Espécie presente na lista municipal |
| Jacarandá-mimoso (*Jacaranda mimosifolia*) | 12–15 m | Faixa de espécie |
| Tipuana (*Tipuana tipu*) | 12–16 m | Faixa de espécie |

As faixas vêm de espécies diferentes. **Não há identificação botânica ou medida de altura nos 257 pontos originais**; não atribuímos espécie a cada ponto nem interpretamos a faixa local como medição na Area1.

## Método
O [notebook V3](../Alometria_caxias_v3.ipynb) aciona [um script independente](../experimentos/v3_alometria_caxias.py). O script lê apenas as bandas RGB e os pontos de Arvores.gpkg, segmenta **em janelas de 256 pixels**, registra o superpixel que contém cada ponto e sua área em m², assinalando os que tocam a borda da janela. Reproduz as seis fórmulas experimentais C1–C6 (potencial e linear), com destaque para o índice C3 = 2,5 × A^0,4 e seu corte histórico maior que 7. Há opção de repetir com janelas de 512 pixels.

**Superpixel Quickshift não equivale a uma copa individual delimitada.** Os coeficientes C1–C6 não foram ajustados às alturas reais desta região e não são os coeficientes de artigos externos. O índice C3 não tem validação como altura em metros. A publicação [Chatziathanasiou et al. (2024)](https://doi.org/10.3390/land13101579) investiga relação largura de copa–altura em três espécies de cidades gregas, mas não calibra a fórmula original da Area1.

## Execução inicial com arquivos reais da Area1
Na execução exploratória de 256 px sobre os arquivos RGB e Arvores.gpkg já presentes no Drive, obtivemos:

| Indicador | Resultado |
|---|---:|
| Pontos originais de árvores | **257** |
| Pontos vinculados a superpixel | **257** |
| Janelas únicas processadas | **114** |
| Segmentos associados que tocam borda | **79 (30,7%)** |
| Área mediana do superpixel | **120,25 m²** |
| Mediana do índice C3, não altura | **16,98** |
| Amplitude do índice C3, não altura | **7,34–29,40** |
| Índice C3 maior que 7 | **257 de 257** |

Esses valores descrevem um **índice obtido de áreas de superpixels**, não alturas reais. Em especial, **não podemos afirmar que a altura mediana seja 16,98 m**, nem que 100% das árvores reais tenham altura superior a 7 m. Os 257 pontos também não equivalem ao conjunto histórico de candidatos do cluster 3.

A [tabela de referências regionais](v3_referencias_alturas_caxias.csv) registra as faixas bibliográficas, com fonte e número de página. O [resumo de execução](v3_resumo_exploratorio.json) guarda métricas agregadas e as restrições interpretativas.

## Reproduzir no Colab
Montar o Google Drive e executar, sem alterar os arquivos originais:

~~~bash
python experimentos/v3_alometria_caxias.py --area /content/drive/MyDrive/Area1 \
  --out /content/v3_resultados_alometria --tile 256
~~~

Se a pasta Area1 estiver em outro local do Drive, ajustar apenas --area. Rodar com --tile 512 é um teste adicional de sensibilidade da segmentação.

## Fonte externa exclusiva: Meta/WRI CHMv2 (257 pontos)

A V3 passa a utilizar **somente o produto Meta/WRI CHMv2** para estimar a **altura modelada do dossel** nos pontos de referência de árvores da Area1. Os 257 valores por ponto foram efetivamente extraídos do [GeoTIFF público `2103121330.tif`](https://dataforgood-fb-data.s3.us-east-1.amazonaws.com/forests/v2/global/dinov3_global_chm_v2_ml3/chm/2103121330.tif), sem autenticação, pelo [script reprodutível](../experimentos/v3_amostrar_altura_publica.py). A amostragem considera o valor do **pixel exato** e, separadamente, o **máximo dentro de 5 m**.

**Dados e metodologia:** [análise estatística dos 257 pontos](v3_alturas_publicas/v3_analise_comparativa.md), [CSV original com C3 e alturas Meta](v3_alturas_publicas/v3_comparacao_c3_meta_257.csv), [dados Meta brutos](v3_alturas_publicas/v3_meta_chmv2_estimativas_257_arvores.csv), [resumo JSON](v3_alturas_publicas/v3_meta_chmv2_resumo.json).

| Indicador | Resultado Meta/WRI na Area1 |
|---|---:|
| Pontos amostrados | **257/257** |
| Mediana da previsão no pixel exato | **2 m** |
| Mediana do máximo estimado em 5 m | **6 m** |
| Valores zero no pixel | **107 (41,6%)** |
| Valores zero em todo o raio de 5 m | **42 (16,3%)** |
| Correlação Pearson C3 × previsão Meta no pixel | **r = 0,019** |
| Correlação Pearson C3 × máximo Meta no raio de 5 m | **r = 0,014** |

A previsão Meta/WRI **não é uma medição direta de altura individual**. Zero no pixel não demonstra inexistência de árvore; o máximo em 5 m pode corresponder a outro indivíduo. **C3 continua um índice não calibrado**, calculado sobre superpixels, e não deve ser interpretado como altura real em metros.

### Execução e reprodução no notebook V3

Abra [`Alometria_caxias_v3.ipynb`](../Alometria_caxias_v3.ipynb). Execute os índices alométricos com os arquivos originais da Area1, então carregue o CSV Meta/WRI já incluído no repositório. O próprio notebook verifica os **257 IDs**, gera uma tabela consolidada com as previsões e os índices e calcula correlações e um gráfico de dispersão. A atualização da fonte externa por COG é **opcional** e fica desativada por padrão.

Referências externas: [Meta/WRI — AWS Open Data](https://registry.opendata.aws/dataforgood-fb-forestsv2/) · [Brandt et al. (2026), *Scientific Data*](https://doi.org/10.1038/s41597-026-07882-0). O artigo relata **MAE aproximado de 3,0 m** no protocolo de validação SatLidar v2; esse erro **não é uma estimativa de precisão local para a Area1**.

## Novos testes: C1, C2 e C3 (potencial e linear) versus Meta/WRI

Conferimos as **seis configurações C1–C6** presentes no [notebook original](../Segmentacao_area_completa.ipynb). O escopo desta bateria é deliberadamente **C1, C2 e C3, com duas formas cada**, sem reestimar seus coeficientes ou alterar o código original.

| Configuração | Parâmetros originais | Forma potencial | Forma linear |
|---|---|---|---|
| C1 | a=0,5; b=0,7 | 0,5 × A^0,7 | 0,5 + 0,7 × A |
| C2 | a=0,6; b=0,8 | 0,6 × A^0,8 | 0,6 + 0,8 × A |
| C3 | a=2,5; b=0,4 | 2,5 × A^0,4 | 2,5 + 0,4 × A |

**Proveniência:** esses coeficientes são escolhas exploratórias **do notebook original** e **não são os coeficientes publicados** em [Chatziathanasiou et al. (2024)](https://doi.org/10.3390/land13101579). O artigo modela **largura de copa CW=f(H)** com medições de **700 árvores de três espécies**, realizadas em cinco cidades da Grécia. A inversão de algumas equações para obter H a partir de CW **não torna a relação diretamente transferível para Caxias do Sul**.

A análise **foi executada com os 257 pontos e somente a Meta/WRI CHMv2 como referência externa**, tanto no pixel exato (257 valores) como na sensibilidade do máximo do raio de 5 m (215 valores positivos). A menor **divergência numérica** em ambos os recortes foi da **C1 potencial**, porém as correlações com Meta foram próximas de zero (por exemplo, r≈0,036 para C1 potencial e o máximo positivo no raio de 5 m). Não atribuímos validade biológica ou acurácia em metros a esse resultado: **índice empírico não é altura real**, e o mapa Meta também é previsão.

### Modelos efetivamente publicados: teste com inversões matemáticas

Selecionamos cinco equações com coeficientes publicados que permitem inversão matemática de CW=f(H): duas equações logarítmicas de *Magnolia grandiflora*, duas inversas da mesma espécie, e uma composta de *Acer negundo*. Para testar, assumimos **apenas como simulação**, sem suporte geométrico individual, que a largura de copa seria **CW = √(4A/π)**, com A a área do **superpixel**, não a área de uma copa delimitada. Sem dados de espécie de cada ponto, foram mantidos apenas valores dentro dos intervalos observados por espécie no artigo.

| Equação publicada invertida | Pontos sem extrapolação |
|---|---:|
| *Magnolia grandiflora*, Kavala (logarítmica) | 22/257 |
| *Magnolia grandiflora*, Orestiada (logarítmica) | 19/257 |
| *Magnolia grandiflora*, Xanthi (inversa) | 5/257 |
| *Magnolia grandiflora*, Komotini (inversa) | 7/257 |
| *Acer negundo*, conjunto de quatro cidades (composta) | 0/257 |

**Não se deve comparar essas divergências para eleger um melhor modelo de altura**: as quantidades válidas diferem entre fórmulas, as espécies são desconhecidas e os superpixels não são copas reais. O modelo de *Acer* teve **zero pontos elegíveis** dentro dos intervalos impostos; isso não significa que seja um modelo errado para *Acer negundo*.

**Materiais finais:** [notebook V3 atualizado](../Alometria_caxias_v3.ipynb) · [script reprodutível](../experimentos/v3_comparar_c1_c3_meta_e_artigo.py) · [CSV com os 257 registros e todos os índices](v3_alturas_publicas/v3_c1_c3_meta_257_pontos.csv) · [resumo das 11 alternativas](v3_alturas_publicas/v3_c1_c3_meta_resumo_comparativo.csv) · [gráfico](v3_alturas_publicas/v3_c1_c3_meta_comparacao.png) · [relatório com tabelas e limites](v3_alturas_publicas/v3_c1_c3_meta_relatorio.md).

## Calibração dos coeficientes a e b com as estimativas Meta/WRI — avaliação espacial

A V3 foi ampliada para que **os coeficientes das fórmulas de altura possam ser ajustados**, em vez de fixar permanentemente os valores C1–C3. O código histórico **não foi modificado**. No [script de calibração](../experimentos/v3_calibrar_altura_meta.py), testamos uma potência simples (a × A^b), potência com intercepto, raiz quadrada, logarítmica, linear, saturação e um controle constante.

A variável A continua sendo **área de superpixel Quickshift**; a resposta é o **valor de altura estimado pela Meta/WRI**. Foram utilizados somente os 257 pontos originais, em duas análises distintas: Meta no pixel exato e maior valor Meta a 5 m.

**Fórmulas potenciais ajustadas nos 257 pontos:**

| Alvo Meta/WRI | Fórmula recalibrada, com A em m² |
|---|---|
| Pixel exato | **H = 1,3684 × A^0,17089** |
| Maior valor em 5 m | **H = 4,9039 × A^0,04608** |

**Validação espacial:** cinco folds em blocos de **250 m e 500 m**, com exclusão de **25 m** entre treino e teste e seleção interna de modelos. As previsões de teste são feitas apenas em pontos não usados no respectivo ajuste. Abaixo, o MAE frente às **alturas modeladas Meta**, não frente a alturas medidas em campo:

| Modelo | MAE pixel (250 m) | MAE máx. 5 m (250 m) | MAE pixel (500 m) | MAE máx. 5 m (500 m) |
|---|---:|---:|---:|---:|
| **Controle constante** | **4,578** | **4,778** | **4,451** | **4,665** |
| Potência a × A^b | 4,593 | 4,810 | 4,510 | 4,734 |
| Potência com intercepto | 4,584 | 4,822 | 4,532 | 4,756 |
| Logarítmica | 4,581 | 4,808 | 4,504 | 4,733 |
| Linear | 4,589 | 4,819 | 4,519 | 4,739 |

**Resultado:** embora o ajuste de a e b reduza a divergência numérica em relação às fórmulas históricas não calibradas, **nenhuma família que utiliza A superou o controle constante na validação espacial em MAE**. A seleção interna escolheu o controle em todos os folds. A referência constante **não é um modelo de porte individual**; demonstra que os dados atuais não sustentam a predição individual baseada apenas na área do superpixel.

A [tabela completa de todos os sete modelos](v3_alturas_publicas/v3_meta_calibracao_validacao_espacial.csv), as [fórmulas ajustadas](v3_alturas_publicas/v3_meta_calibracao_parametros_e_limites.json), as [previsões de 257 pontos](v3_alturas_publicas/v3_meta_calibracao_257_pontos.csv) e os [detalhes de treinamento/teste](v3_alturas_publicas/v3_meta_calibracao_folds.csv) permitem auditar os resultados.

**Recomendação metodológica:** a estimativa de alturas reais deve considerar a **copa da árvore individualizada** (e não um superpixel genérico), outras variáveis relacionadas à vegetação e, para validação efetiva, observações reais de altura. Até então, o **Meta/WRI CHMv2 é uma previsão externa independente**, não verdade de campo. Copiar diretamente os valores da Meta para os 257 pontos seria reproduzir o produto, e não demonstrar uma nova equação alométrica.

## Escolha de estudo: fórmula logarítmica e comparação individual com a Meta/WRI

Por decisão metodológica, a V3 mantém a **fórmula logarítmica como candidata principal** para investigar a relação entre a área do superpixel e a altura do dossel **modelada pelo Meta/WRI CHMv2**, apesar de não superar um controle constante em testes espaciais.

Os dois experimentos **não são duas fontes**: são duas amostragens do mesmo produto Meta/WRI para cada um dos 257 pontos originais.

| Alvo Meta | Fórmula recalibrada nos 257 pontos |
|---|---|
| Pixel exato | **H = 1,02061062 + 0,43611553 × ln(1 + A)** |
| Máximo no raio de 5 m | **H = 4,83406389 + 0,26716928 × ln(1 + A)** |

A corresponde à **área do superpixel Quickshift** em m². Essas fórmulas foram ajustadas contra **previsões de altura Meta/WRI**, não contra alturas medidas em campo. A referência do raio de 5 m pode captar outra árvore, enquanto o pixel exato da Meta pode mostrar zero por diferenças geométricas ou temporais.

Para separar a demonstração de previsão individual da avaliação, geramos **três valores logarítmicos por ponto e por alvo**: (1) fórmula ajustada aos 257 pontos, apresentada somente para **ilustração da equação**; (2) previsão espacial **fora de treinamento** com blocos de 250 m; (3) previsão espacial **fora de treinamento** com blocos de 500 m. Os testes usam **25 m de embargo** entre treino e teste.

**Resultados dos testes espaciais:**

| Referência Meta | Bloco espacial | MAE da logarítmica frente à Meta | MAE do controle constante |
|---|---:|---:|---:|
| Pixel exato | 250 m | **4,581 m** | **4,578 m** |
| Pixel exato | 500 m | **4,504 m** | **4,451 m** |
| Máximo em 5 m | 250 m | **4,808 m** | **4,778 m** |
| Máximo em 5 m | 500 m | **4,733 m** | **4,665 m** |

A fórmula logarítmica **não superou a referência constante** em nenhum desses cenários. Os testes demonstram dificuldades para prever a variabilidade individual das alturas do produto Meta usando apenas a área de superpixel. **MAE contra o mapa Meta não equivale a MAE de altura verdadeira**, e o cálculo calibrado em todos os pontos não deve ser usado como estimativa independente de precisão.

**Dados rastreáveis:** [tabela das 257 alturas por fórmula e Meta/WRI](v3_alturas_publicas/v3_logaritmica_257_alturas_vs_meta.csv) · [análise com exemplos](v3_alturas_publicas/v3_logaritmica_comparacao_meta.md) · [resumo JSON](v3_alturas_publicas/v3_logaritmica_resumo.json) · [código reprodutível](../experimentos/v3_comparar_logaritmica_meta.py) · [V3 notebook](../Alometria_caxias_v3.ipynb).

## Conclusão permitida
A V3 examina **sensibilidade e plausibilidade numérica exploratória**, pesquisando faixas de porte locais. Sem **copas individualizadas, espécies identificadas e alturas de referência dos mesmos indivíduos**, **não é possível validar o acerto das alturas** (nem calcular MAE, RMSE, R²). Altura não foi medida. A análise de proximidade a postes continua horizontal e exploratória; não comprova risco elétrico.
