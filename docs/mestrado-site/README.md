# Atlas Urbano — portal acadêmico do mestrado

Site público: https://brenobragagalvao.github.io/mestrado-arvores-urbanas/

O site funciona como um **portal com menu lateral**, contendo uma página de **Início**, os **seis capítulos do README** e **18 subtópicos navegáveis**. Cada seleção abre seu conteúdo na área principal, sem exigir percorrer uma única página extensa.

## Estrutura atual

- `docs/index.html`: estrutura do portal, tela inicial, componentes de gráficos e explorador;
- `docs/mestrado-site/portal.css`: estrutura responsiva do portal e navegação por capítulos;
- `docs/mestrado-site/unb-theme.css`: tema visual azul e branco inspirado no painel de referência fornecido, sem alteração em qualquer projeto da FGV;
- `docs/mestrado-site/portal.js`: navegação por capítulos/subtópicos e renderização de tabelas, textos e figuras do README;
- `docs/mestrado-site/readme-content.js`: cópia estruturada das seis seções científicas do `README.md`, com os 18 subtópicos;
- `docs/mestrado-site/styles.css`: estilos de visualização para gráficos e tabelas;
- `docs/mestrado-site/app.js`: gráficos interativos e exploração dos 257 registros.

**Atualização dos textos:** quando o README científico for modificado, a cópia `readme-content.js` deve ser regenerada para refletir o novo conteúdo. Este arquivo não é atualizado automaticamente pelo GitHub Pages.

## Navegação e gráficos

- **Início:** objetivo da pesquisa, números e acesso a cada capítulo.
- **1 — Área de estudo:** dimensões, georreferenciamento e dados de referência.
- **2 — Método original:** classificação, proximidade a postes e pipeline.
- **3 — Evolução metodológica:** validação espacial, recortes, atributos, oito classificadores, F1-macro e memória.
- **4 — Alometria:** Meta/WRI, espécies locais, fórmulas, MAE e explorador de 257 pontos.
- **5 — Conclusões:** resultados e restrições de interpretação.
- **6 — Código e documentação:** notebooks e materiais reprodutíveis.

Os gráficos de MAE e a tabela de 257 pontos leem os CSVs versionados neste mesmo repositório. Os dados dos gráficos de F1-macro foram transcritos das tabelas científicas do README, preservando os protocolos correspondentes.

## Publicação

O GitHub Pages utiliza a branch `main` e a pasta `/docs`. Alterações de HTML, CSS e JavaScript nestes arquivos são publicadas pelo fluxo de implantação do Pages.

Para conferir ou alterar a configuração: **Settings → Pages** no repositório GitHub, fonte **Deploy from a branch**, branch **main**, pasta **/docs**.

## Observações científicas e institucionais

- O desempenho do método original (acurácia histórica) não pode ser comparado diretamente com o F1-macro das avaliações espaciais atuais.
- A Meta/WRI fornece estimativas de altura de dossel, não medições de campo.
- C1–C6 são índices exploratórios, não alturas reais validadas.
- Proximidade bidimensional com postes não demonstra risco elétrico.
- O portal é um projeto independente: **não pertence à FGV nem é um portal institucional da UnB**. Seu tema segue a referência visual fornecida pelo autor e não utiliza código ou infraestrutura da FGV.
- O cabeçalho utiliza a [logo azul e verde da UnB disponibilizada no Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Webysther_20160322_-_Logo_UnB.svg), indicada pelo autor do projeto. A imagem é carregada por URL externa, e a utilização de símbolo institucional não indica vínculo ou endosso da universidade; observe as regras de uso de marca aplicáveis.
