/* Atlas Urbano · painéis sem dependências externas.
   Dados classificatórios transcritos das tabelas auditadas do README.
   Dados alométricos carregados dos CSVs versionados no próprio repositório. */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const pt4 = (v) => Number(v).toLocaleString("pt-BR",{minimumFractionDigits:4,maximumFractionDigits:4});
  const pt3 = (v) => Number(v).toLocaleString("pt-BR",{minimumFractionDigits:3,maximumFractionDigits:3});
  const pt2 = (v) => Number(v).toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
  const safe = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const repository = "https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas";
  const tableCsv = "./v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv";
  const metricsCsv = "./v3_alturas_publicas/v3_11_familias_meta_resumo.csv";

  const models = [
    {name:"SVM RBF",             s512:{"250":0.9157,"500":0.8518},s256:{"250":0.9341,"500":0.8641}},
    {name:"Regressão logística", s512:{"250":0.9153,"500":0.8484},s256:{"250":0.9157,"500":0.8685}},
    {name:"Extra Trees",         s512:{"250":0.9064,"500":0.8747},s256:{"250":0.8968,"500":0.8545}},
    {name:"KNN (7)",             s512:{"250":0.8940,"500":0.8377},s256:{"250":0.9009,"500":0.8486}},
    {name:"Random Forest",       s512:{"250":0.8906,"500":0.8657},s256:{"250":0.8835,"500":0.8566}},
    {name:"Gaussian Naive Bayes",s512:{"250":0.8894,"500":0.8573},s256:{"250":0.8875,"500":0.8464}},
    {name:"HistGradientBoosting",s512:{"250":0.8738,"500":0.8390},s256:{"250":0.8714,"500":0.8411}},
    {name:"Dummy",               s512:{"250":0.2847,"500":0.2791},s256:{"250":0.2847,"500":0.2791}}
  ];

  const ablation = {
    "250":[
      {name:"SVM RBF",old:0.7523,all:0.8987,gain:0.1464},
      {name:"Regressão logística",old:0.7556,all:0.8928,gain:0.1372},
      {name:"KNN (7)",old:0.7445,all:0.8874,gain:0.1429},
      {name:"Extra Trees",old:0.7008,all:0.8790,gain:0.1782},
      {name:"Random Forest",old:0.6925,all:0.8656,gain:0.1731},
      {name:"HistGradientBoosting",old:0.7206,all:0.8556,gain:0.1349},
      {name:"Gaussian Naive Bayes",old:0.7409,all:0.8555,gain:0.1146},
      {name:"Dummy",old:0.2980,all:0.2980,gain:0}
    ],
    "500":[
      {name:"SVM RBF",old:0.7886,all:0.8668,gain:0.0781},
      {name:"Regressão logística",old:0.7992,all:0.8664,gain:0.0671},
      {name:"Extra Trees",old:0.7208,all:0.8629,gain:0.1421},
      {name:"Random Forest",old:0.7264,all:0.8530,gain:0.1266},
      {name:"HistGradientBoosting",old:0.7327,all:0.8524,gain:0.1197},
      {name:"KNN (7)",old:0.7678,all:0.8502,gain:0.0824},
      {name:"Gaussian Naive Bayes",old:0.7699,all:0.8398,gain:0.0700},
      {name:"Dummy",old:0.2799,all:0.2799,gain:0}
    ]
  };

  function renderClassifiers() {
    const size = $("classification-size").value;
    const block = $("classification-block").value;
    const seriesKey = size === "512" ? "s512" : "s256";
    const vals = models.map((x) => ({name:x.name,value:x[seriesKey][block]}))
      .sort((a,b)=>b.value-a.value);
    const best = vals[0].value;
    $("classification-chart").innerHTML = vals.map((x)=>(
      '<div class="bar-row '+(x.value===best?'top-model':'')+'">'+
      '<span class="bar-label">'+safe(x.name)+'</span>'+
      '<div class="bar-track" role="meter" aria-label="'+safe(x.name)+'" aria-valuemin="0" aria-valuemax="1" aria-valuenow="'+x.value+'"><div class="bar-fill" style="--bar-width:'+Math.max(0,x.value*100)+'%"></div></div>'+
      '<span class="bar-value">'+pt4(x.value)+'</span></div>'
    )).join("");
    $("classification-table").innerHTML = vals.map((x)=>'<tr><td>'+safe(x.name)+'</td><td>'+pt4(x.value)+'</td></tr>').join("");
    $("classification-note").textContent = "E9 · 119 recortes · "+size+" × "+size+" px · blocos "+block+" m · mesmas referências e divisões.";
  }

  function renderFeatures() {
    const block = $("feature-block").value;
    const list = ablation[block];
    $("feature-chart").innerHTML = list.map(x=>(
      '<div class="feature-bar-row"><span class="feature-bar-label">'+safe(x.name)+'</span>'+
      '<div class="feature-bars">'+
      '<div aria-label="'+safe(x.name)+': HSV e Canny, F1-macro '+pt4(x.old)+'"><i style="--bar-width:'+(x.old*100)+'%"></i></div>'+
      '<div aria-label="'+safe(x.name)+': NDVI, HSV e Canny, F1-macro '+pt4(x.all)+'"><i style="--bar-width:'+(x.all*100)+'%"></i></div>'+
      '</div><span class="feature-delta '+(!x.gain?'neutral':'')+'">'+(x.gain?'+':'')+pt4(x.gain)+'</span></div>'
    )).join("");
  }

  /* Parser CSV RFC-4180 simples, com aspas, escape de aspas, CRLF e BOM UTF-8. */
  function parseCSV(raw) {
    const text = String(raw).replace(/^\uFEFF/,"");
    const rows = []; let row = [], field = "", quoted = false;
    for(let i=0;i<text.length;i++){
      const c=text[i];
      if(quoted){
        if(c==='"' && text[i+1]==='"'){field+='"';i++;}
        else if(c==='"'){quoted=false;}
        else field+=c;
      } else if(c==='"'){quoted=true;}
      else if(c===','){row.push(field);field="";}
      else if(c==='\n'){
        row.push(field);if(row.some(v=>v!==''))rows.push(row);
        row=[];field="";
      } else if(c==='\r'){} else field+=c;
    }
    row.push(field); if(row.some(v=>v!==''))rows.push(row);
    if(!rows.length)return [];
    const headers=rows.shift();
    return rows.map(columns=>{
      const obj={};
      headers.forEach((header,i)=>{obj[header]=columns[i]??"";});
      return obj;
    });
  }

  async function loadCSV(url){
    const response=await fetch(url,{cache:"no-cache"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    return parseCSV(await response.text());
  }
  function errorMarkup(file){
    return '<div class="error-msg">Não foi possível carregar os dados CSV neste ambiente. Abra o site publicado no GitHub Pages para ativar os gráficos, ou consulte o <a href="'+safe(file)+'" target="_blank" rel="noopener noreferrer"><u>arquivo de origem no repositório</u></a>.</div>';
  }

  const prettyModels = {
    "Linear":"Linear","Logaritmico":"Logarítmica","Inverso":"Inversa",
    "Quadratico":"Quadrática","Cubico":"Cúbica","Potencial":"Potencial",
    "Composto":"Composta","Curva_S":"Curva-S","Logistico":"Logística",
    "Crescimento":"Crescimento","Exponencial":"Exponencial",
    "Controle_constante":"Controle constante","Selecao_aninhada":"Seleção aninhada"
  };
  let maeRows=[];
  function renderMAE(){
    const block=$("mae-block").value;
    const target=$("mae-target").value;
    if(!maeRows.length)return;
    const data=maeRows.filter(x=>String(x.bloco_m)===block && String(x.alvo)===target)
      .map(x=>({key:x.modelo,name:prettyModels[x.modelo]||x.modelo,mae:Number(x.mae_vs_meta_m)}))
      .filter(x=>Number.isFinite(x.mae)).sort((a,b)=>a.mae-b.mae);
    if(!data.length){
      $("mae-chart").innerHTML='<div class="error-msg">Nenhum dado disponível para a seleção.</div>';
      return;
    }
    const bestNoncontrol=data.filter(x=>x.key!=="Controle_constante"&&x.key!=="Selecao_aninhada")[0];
    const max=Math.max(...data.map(x=>x.mae))*1.04;
    $("mae-chart").innerHTML=data.map(x=>{
      const special=x.key==="Controle_constante"?"baseline":x.key===bestNoncontrol?.key?"best-family":"";
      return '<div class="mae-row '+special+'"><span class="mae-label">'+safe(x.name)+'</span>'+
        '<div class="mae-track" role="meter" aria-label="'+safe(x.name)+': MAE '+pt3(x.mae)+' metros" aria-valuemin="0" aria-valuemax="'+max+'" aria-valuenow="'+x.mae+'">'+
        '<div class="mae-fill" style="--bar-width:'+(x.mae/max*100)+'%"></div></div>'+
        '<span class="mae-value">'+pt3(x.mae)+' m</span></div>';
    }).join("")+
    '<p class="mae-note"><strong>Interpretação:</strong> entre as 11 famílias, o menor MAE nesta seleção é da '+safe(bestNoncontrol?.name||"—")+
    ' ('+pt3(bestNoncontrol?.mae||0)+' m). Os controles estão identificados separadamente; não se trata de erro contra alturas reais medidas.</p>';
    $("mae-caption").textContent=data.length+" séries exibidas · Meta/WRI · blocos "+block+" m · OOF espacial";
  }
  async function loadMAE(){
    try{
      maeRows=await loadCSV(metricsCsv);
      if(!maeRows.length)throw new Error("CSV sem registros");
      renderMAE();
    }catch(error){
      $("mae-chart").innerHTML=errorMarkup(repository+"/blob/main/docs/v3_alturas_publicas/v3_11_familias_meta_resumo.csv");
      console.warn("MAE:",error);
    }
  }

  let points=[],pointLimit=12;
  let pointModels=[];
  function buildPointModels(headers){
    const fromOOF=headers
      .map(header=>header.match(/^(.+) — pixel OOF 250m \(m\)$/))
      .filter(Boolean).map(match=>match[1]);
    const desired=["Linear","Logarítmico","Inverso","Quadrático","Cúbico","Potencial",
      "Composto","Curva-S","Logístico","Crescimento","Exponencial","Controle constante","Seleção aninhada"];
    const indices=headers.filter(h=>/^C[1-6] (potencial|linear) \(índice\)$/.test(h));
    pointModels=[...desired.filter(x=>fromOOF.includes(x)),...indices];
    const el=$("point-model");
    el.innerHTML=pointModels.map(x=>'<option value="'+safe(x)+'">'+safe(x)+'</option>').join("");
    el.value=pointModels.includes("Curva-S")?"Curva-S":(pointModels[0]||"");
  }
  function formatCell(value,isIndex){
    if(value==null||String(value).trim()==="" || !Number.isFinite(Number(value)))return '—';
    return pt2(Number(value)) + (isIndex?"":" m");
  }
  function renderPoints(){
    if(!points.length)return;
    const model=$("point-model").value;
    const block=$("point-block").value;
    const isIndex=/^C[1-6] (potencial|linear) \(índice\)$/.test(model);
    const keyPixel=isIndex?model:model+" — pixel OOF "+block+"m (m)";
    const key5=isIndex?null:model+" — 5m OOF "+block+"m (m)";
    $("point-col-head").textContent=isIndex?"Índice "+model:"Modelo · Meta pixel";
    $("point-col-head5").textContent=isIndex?"Índice sem referência 5 m":"Modelo · Meta 5 m";
    const query=$("point-query").value.trim();
    const filtered=points.filter(row=>!query||String(Number(row["Árvore"]))===query || String(row["Árvore"]).startsWith(query));
    const shown=filtered.slice(0,pointLimit);
    $("point-table").innerHTML=shown.length?shown.map(row=>{
      return "<tr><td>"+safe(row["Árvore"])+"</td>"+
        "<td>"+formatCell(row["Meta pixel (m)"],false)+"</td>"+
        "<td>"+formatCell(row["Meta 5 m (m)"],false)+"</td>"+
        "<td>"+formatCell(row[keyPixel],isIndex)+"</td>"+
        "<td>"+(key5?formatCell(row[key5],false):"—")+"</td></tr>";
    }).join(""):'<tr><td colspan="5">Nenhum ponto encontrado para esse filtro.</td></tr>';
    $("point-count").textContent="Exibindo "+shown.length+" de "+filtered.length+" pontos";
    $("point-more").hidden=shown.length>=filtered.length;
    $("point-block").disabled=isIndex;
    $("points-note").textContent=isIndex
      ? "C1–C6 são índices exploratórios e não alturas calibradas em metros. A referência Meta permanece em metros nas colunas 2 e 3."
      : "Previsões OOF (fora do treinamento), comparadas a alturas estimadas pela Meta/WRI; não são medições em campo.";
  }
  async function loadPoints(){
    try{
      points=await loadCSV(tableCsv);
      if(points.length!==257)console.warn("A quantidade de pontos encontrada difere dos 257 documentados:",points.length);
      if(!points.length)throw new Error("CSV sem registros");
      buildPointModels(Object.keys(points[0]));
      renderPoints();
    } catch(error){
      $("point-table").innerHTML='<tr><td colspan="5">'+errorMarkup(repository+"/blob/main/docs/v3_alturas_publicas/v3_todos_modelos_meta_257_completo.csv")+"</td></tr>";
      $("point-count").textContent="Dados completos disponíveis no repositório";
      $("point-more").hidden=true;
      console.warn("Pontos:",error);
    }
  }

  function setupMobileMenu(){
    const button=$("menu-button"),nav=$("main-nav");
    if(!button || !nav)return; // Menu atual controlado pelo portal lateral.
    button.addEventListener("click",()=>{
      const isOpen=nav.classList.toggle("open");
      button.setAttribute("aria-expanded",String(isOpen));
      button.setAttribute("aria-label",isOpen?"Fechar navegação":"Abrir navegação");
    });
    nav.querySelectorAll("a").forEach(link=>link.addEventListener("click",()=>{
      nav.classList.remove("open");
      button.setAttribute("aria-expanded","false");
      button.setAttribute("aria-label","Abrir navegação");
    }));
  }
  function setupActiveNav(){
    if(!$("main-nav") || !("IntersectionObserver" in window))return;
    const links=Array.from(document.querySelectorAll(".main-nav a"));
    const lookup=Object.fromEntries(links.map(link=>[link.getAttribute("href").slice(1),link]));
    const observer=new IntersectionObserver(entries=>{
      entries.filter(x=>x.isIntersecting).forEach(entry=>{
        links.forEach(link=>link.classList.remove("active"));
        const selected=lookup[entry.target.id];
        if(selected)selected.classList.add("active");
      });
    },{rootMargin:"-19% 0px -68% 0px"});
    Object.keys(lookup).map(id=>document.getElementById(id)).filter(Boolean).forEach(section=>observer.observe(section));
  }

  function init(){
    setupMobileMenu();
    setupActiveNav();
    $("classification-block").addEventListener("change",renderClassifiers);
    $("classification-size").addEventListener("change",renderClassifiers);
    $("feature-block").addEventListener("change",renderFeatures);
    $("mae-target").addEventListener("change",renderMAE);
    $("mae-block").addEventListener("change",renderMAE);
    $("point-model").addEventListener("change",()=>{pointLimit=12;renderPoints();});
    $("point-block").addEventListener("change",()=>{pointLimit=12;renderPoints();});
    $("point-query").addEventListener("input",()=>{pointLimit=12;renderPoints();});
    $("point-more").addEventListener("click",()=>{pointLimit+=18;renderPoints();});
    renderClassifiers();
    renderFeatures();
    void Promise.all([loadMAE(),loadPoints()]);
  }

  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});
  else init();
})();
