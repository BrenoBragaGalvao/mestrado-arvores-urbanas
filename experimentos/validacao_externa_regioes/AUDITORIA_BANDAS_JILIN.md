# Identificação das bandas Jilin-1 na Proposta 1

Os cinco GeoTIFFs multiespectrais originais têm a ordem física **azul, verde,
vermelho e infravermelho próximo**. O processamento científico lê as bandas
na sequência de índices **3, 2, 1, 4** para obter R, G, B, NIR. O indicador
ColorInterp dos três canais visíveis no TIFF multiespectral exportado não
reflete a ordem do produto de origem. O RGB de visualização permanece
separado do multiespectral.

## Rastreabilidade

Os quatro pacotes contêm produtos Jilin-1 MSS e PSH (pansharpened) e os seus
XMLs do fornecedor. Os seis XMLs PSH identificam a ordem pelo campo
`FUSMethod=B-G-R-NIR`. Três regiões usam KF01B, e o Centro de Novo Hamburgo
usa KF02B05. Foram cotejados os canais dos GeoTIFFs processados com os
seis PSH correspondentes. Pareamentos de feições locais SIFT na banda 1 e
homografias ajustadas com RANSAC aproximaram o registro para verificar a
identidade dos canais. Em todos os seis produtos, a atribuição [1,2,3,4]
maximizou a média das correlações de Spearman entre os quatro pares,
entre as 24 permutações. A correlação da banda 4 com a banda NIR de
origem variou de 0,7878 a 0,9468. A auditoria arquiva as matrizes completas.

Uma comparação adicional das tuplas digitais em 15 mil pixels de cada
ortoimagem encontrou 206, 213 e 611 coincidências exatas na ordem original,
respectivamente, em Sagrada Família, Cristo Rei e Lomba Grande. No Centro,
houve zero coincidências exatas para todas as permutações. A identificação
para o Centro se baseia nos dois XMLs PSH e no registro espacial, com
correlações de 0,7894 e 0,7878 para NIR.

Na Area1, os **46.961.301 pixels multiespectrais válidos** são idênticos nas
quatro bandas aos pixels correspondentes na mesma grade do multiespectral
de Sagrada Família. A auditoria espacial também confirma que os 510 pontos
originais estão dentro do RGB de Sagrada Família. A exclusão da Area1 e da
faixa de 25 m abrange pontos e segmentos que tocam a zona excluída.

O registro [bandas_verificadas_jilin.json](bandas_verificadas_jilin.json)
vincula cada ordem ao SHA-256 do TIFF multiespectral original. Inclui os
IDs dos produtos, o hash do XML e as matrizes de comparação. A
documentação do fornecedor está nas fichas do
[KF01B](https://www.jl1.cn/eweb/product_view.aspx?id=758) e da
[família KF02](https://www.jl1.cn/product_view.aspx?id=4253).
O [manual Catalyst do KF01](https://catalyst.earth/catalyst-system-files/professional-help/references/gdb_r/JL1KF01.html)
também explicita a numeração B1–B4 do produto.

## Consequências para a execução

O protocolo anterior usava a banda 1 como vermelho. O valor então
denominado NDVI comparava NIR e azul. A execução corrigida extrai os
atributos da Area1 com o vermelho identificado e o multiespectral
alinhado à grade RGB por interpolação bilinear. Os 505 segmentos
rotulados, suas classes e as divisões espaciais foram preservados. Os
oito modelos foram ajustados novamente na Area1. A reprodução no
[Colab](proposta1_cinco_areas_colab.ipynb) utiliza a ordem documentada
e uma pasta de saída separada dos experimentos anteriores.

O índice da classificação aplica a fórmula NDVI sobre valores digitais
dos produtos, sem conversão para reflectância de superfície. Identidade
das bandas e comparabilidade radiométrica são verificações distintas.
Os produtos KF01B trazem indicação de 12 bits e os dois KF02B05 do Centro
de Novo Hamburgo indicam 16 bits no XML. Mudanças de escala e distribuição
de brilho, bordas e índice devem ser examinadas ao interpretar a
transferência. Uma eventual calibração radiométrica constituiria outro
experimento, com treinamento e validação próprios.

A avaliação externa exige referências independentes de árvores e
gramíneas. Registros de ortoimagem, correlação de canais e contagens
de mapas são evidências de processamento, não medidas de acurácia.
