# Auditoria executada — quatro regiões com rasters reais

**Data:** 12/11/2026  
**Fonte:** arquivos regionais do [Google Drive fornecido para a pesquisa](https://drive.google.com/drive/u/1/folders/1cUNFdo2w3V-ldPnxA9N_vnjmQtOrVHyd).  
**Evidência:** [GitHub Actions — Auditar rasters geográficos reais, execução 43292319271](https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/actions/runs/43292319271), quatro jobs **concluídos com sucesso**. Os runners baixaram os pacotes, extraíram apenas os dois TIFFs relevantes, leram metadados com Rasterio, alinhavam amostras por WarpedVRT e executaram Quickshift em janelas de 256 × 256 pixels. Os rasters não foram publicados em GitHub.

## 1. Dimensões, resolução e CRS observados

| Região | RGB (altura × largura) | 4 bandas (altura × largura) | Resolução | CRS |
|---|---:|---:|---|---|
| Centro — Novo Hamburgo | 10.554 × 10.502 | 14.587 × 14.256 | 0,5 m/pixel | EPSG:31982 |
| Lomba Grande — Novo Hamburgo | 16.409 × 17.423 | 20.074 × 18.349 | 0,5 m/pixel | EPSG:31982 |
| Cristo Rei — São Leopoldo | 10.530 × 10.410 | 14.602 × 14.460 | 0,5 m/pixel | EPSG:31982 |
| Sagrada Família — Caxias do Sul | 10.456 × 10.422 | 14.643 × 14.566 | 0,5 m/pixel | EPSG:31982 |

Os quatro pares **não estão alinhados na mesma grade**: imagens RGB e imagens de quatro bandas têm dimensões e limites distintos. Na auditoria, o multiespectral foi amostrado com **WarpedVRT**, utilizando a grade RGB e reamostragem bilinear. Este procedimento é uma harmonização explícita de georreferenciamento, não uma afirmação de que os pixels originais já coincidiam.

## 2. Quickshift realmente executado em amostras de 256 × 256 pixels

| Região | Janela 1 | Janela 2 | Janela 3 | Total nas janelas auditadas |
|---|---:|---:|---:|---:|
| Centro — Novo Hamburgo | 192 | 186 | 171 | 549 |
| Lomba Grande — Novo Hamburgo | 195 | 167 | Não amostrada (sem pixels válidos no ponto escolhido) | 362 |
| Cristo Rei — São Leopoldo | 180 | 180 | 227 | 587 |
| Sagrada Família — Caxias do Sul | 184 | 180 | 165 | 529 |

Valores são **quantidades de segmentos Quickshift apenas nas janelas auditadas**. Não representam contagem total de segmentos de cada região; não são rótulos, não indicam árvores reconhecidas e **não são métricas F1**.

Parâmetros reproduzidos dos quadrantes da Area1: `kernel_size=3`, `max_dist=5`, `ratio=0.04`, `rng=42`; três descritores calculados sobre janelas multi amostradas: média do brilho HSV, média de bordas Canny sobre canal 4/10000 e índice tipo NDVI com banda 4 e vermelho **sob hipótese ainda não confirmada de NIR na quarta banda**.

### Alerta de compatibilidade espectral

- Os quatro rasters multiespectrais possuem 4 bandas, porém **a quarta banda não está explicitamente descrita como NIR nos metadados lidos**. Portanto, não podemos ainda tratar o valor como NDVI cientificamente confirmado.
- As três bandas iniciais da ortoimagem multiespectral tiveram correlações positivas altas com as bandas RGB nas janelas amostradas (com exceções pontuais), o que favorece a compatibilidade de RGB, **mas não demonstra a interpretação da quarta banda**.
- As médias espectrais variaram significativamente entre janelas/regiões: por exemplo, as três janelas de Centro apresentaram valores candidatos de (NIR−R)/(NIR+R) negativos, enquanto as amostras de Cristo Rei e Sagrada Família apresentaram valores positivos. **Não se deve concluir diferença de vegetação ou qualidade do modelo sem confirmar as bandas e a radiometria.**

## 3. Comparação com a Area1 original

A Area1 anteriormente documentada utiliza raster de **6.942 × 7.294 pixels**. O pacote completo **Sagrada Família** contém RGB de **10.456 × 10.422 pixels**. Logo, **não são o mesmo TIFF com dimensões idênticas**; a Area1 pode ser um recorte do mesmo levantamento, mas a equivalência espacial precisa ser verificada por interseção dos limites, amostras e origem de dados. Não presumir que o ZIP Sagrada Família é exatamente o arquivo Area1.

Os arquivos originais `AOI_RGB_NEW.tif`, `AOI_NEW_MULTI.tif`, `Arvores.gpkg` e `Grama.gpkg` estão acessíveis ao ChatGPT via conexão de Drive, mas o Google informou que **não têm compartilhamento público**. O runner GitHub Actions, sem as credenciais do Drive, não conseguiu obter seus bytes. Por proteção de dados, **nenhum acesso privado foi divulgado nem compartilhamento foi alterado**.

## 4. Avaliação externa: situação real

| Etapa | Estado |
|---|---|
| Listar arquivos internos ZIP/RAR | Concluída nas quatro regiões |
| Baixar e ler os rasters RGB e 4 bandas | Concluída nas quatro regiões |
| Verificar CRS e resolução espacial | Concluída nas quatro regiões |
| Executar Quickshift em amostras reais | Concluída nas quatro regiões |
| Conferir posição espectral verdadeira de NIR | **Pendente da documentação da origem das bandas** |
| Aplicar Quickshift na cobertura integral de cada região | **Não executado** |
| Treinar oito classificadores na Area1 real | **Não executado** neste runner sem autenticação ao Drive privado |
| Gerar mapas classificados completos das novas regiões | **Não executado** |
| Calcular F1-macro externo | **Não calculado**: não há rótulos independentes nas pastas regionais examinadas |

**Próxima execução válida:** no Colab, após autorizar o Drive da Area1, reconstruir/carregar a base dos 505 segmentos, validar a correspondência espectral do canal 4, ajustar os modelos exclusivamente pela validação interna espacial e executar a inferência em cada região. Sem rótulos locais, gerar mapas e amostras para rotulação cega; calcular F1 somente após referências externas independentes.

Este documento é uma auditoria **de dados realmente processados**, não um relatório de classificação supervisionada concluída.
