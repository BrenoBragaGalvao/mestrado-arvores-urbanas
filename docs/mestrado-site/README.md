# Atlas Urbano — site público da pesquisa

Portal estático de divulgação científica do projeto de mestrado. Os arquivos deste site são independentes dos notebooks, experimentos e projetos da FGV.

## Organização

- `docs/index.html` — página principal, com sete seções de pesquisa;
- `docs/mestrado-site/styles.css` — interface responsiva acadêmico-institucional (design próprio);
- `docs/mestrado-site/app.js` — gráficos interativos e explorador dos 257 pontos;
- `docs/v3_alturas_publicas/v3_11_familias_meta_resumo.csv` — fonte do gráfico de MAE;
- `docs/v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv` — fonte da tabela interativa;
- imagens e relatórios em `docs/` já existentes no repositório.

Os dados de F1-macro da comparação E9 (recortes 512/256) e da ablação E4b estão representados no JavaScript conforme as tabelas do README, mantendo suas escalas espaciais e protocolos distintos. Quando esses experimentos forem atualizados, atualizar também os números transcritos em `app.js`.

## Publicar pelo GitHub Pages

**O Pages ainda precisa estar habilitado nas configurações do repositório**, pois criar os arquivos não publica automaticamente o site.

1. Abra o repositório `BrenoBragaGalvao/mestrado-arvores-urbanas` no GitHub.
2. Vá em **Settings → Pages**.
3. Em **Build and deployment**, selecione **Deploy from a branch**.
4. Defina **Branch: main** e **Folder: /docs**; clique em **Save**.
5. Depois que o GitHub confirmar a publicação, o endereço esperado será:
   `https://brenobragagalvao.github.io/mestrado-arvores-urbanas/`

O site não precisa de Node, Python, bundler nem biblioteca externa para funcionar. Gráficos de alometria e a tabela exigem acesso HTTP aos CSVs do próprio diretório; ao abrir o HTML via `file://`, o navegador pode bloquear essa leitura. Para um teste local, na raiz do repositório execute `python -m http.server 8000` e abra `http://localhost:8000/docs/`.

## Transparência científica

- As estimativas da Meta/WRI CHMv2 não substituem medições em campo.
- Os índices C1–C6 não são alturas individuais validadas.
- O experimento histórico e os novos protocolos não podem ser comparados diretamente por acurácia versus F1-macro.
- Proximidade bidimensional a postes não comprova risco elétrico.
- O projeto utiliza um visual original inspirado em portais acadêmicos; não utiliza marca, logotipo, arquivo, identidade visual oficial nem infraestrutura da Fundação Getulio Vargas.

## Manutenção

O README do repositório permanece a documentação científica principal. Este portal é um resumo navegável com acesso às fontes, métricas e notebooks. Nenhuma métrica é calculada sobre arquivos privados; os gráficos utilizam apenas os CSVs públicos versionados.
