/* Mermaid diagrams: show the research flowcharts, never raw source by default.
   Source is copied directly from the README and is preserved in a collapsible detail. */
(()=>{
  "use strict";
  const sourceUrl="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  let enginePromise=null;
  let rendering=false;
  let queued=false;
  function ensureEngine(){
    if(!enginePromise){
      enginePromise=import(sourceUrl).then(mod=>{
        const m=mod.default;
        m.initialize({
          startOnLoad:false,
          theme:"base",
          securityLevel:"loose",
          flowchart:{htmlLabels:true,useMaxWidth:true,nodeSpacing:46,rankSpacing:55,curve:"basis"},
          themeVariables:{
            background:"#ffffff",fontFamily:"Inter, Arial, sans-serif",fontSize:"15px",
            primaryColor:"#edf4fb",primaryTextColor:"#163e64",primaryBorderColor:"#94b6d5",
            secondaryColor:"#e7f3eb",tertiaryColor:"#fff6e7",
            lineColor:"#44719b",textColor:"#263f58",clusterBkg:"#f1f5fa",
            edgeLabelBackground:"#ffffff"
          }
        });
        return m;
      });
    }
    return enginePromise;
  }
  function markError(figure){
    figure.dataset.diagramStatus="error";
    const canvas=figure.querySelector(".diagram-surface");
    if(canvas)canvas.hidden=true;
    const msg=figure.querySelector(".diagram-message");
    if(msg){
      const section=figure.closest(".portal-view")?.dataset?.view||"topico-2";
      const id=section.replace(/^topico-/,"sec-");
      msg.innerHTML='O diagrama não pôde ser carregado neste navegador. '+
        '<a href="https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas/blob/main/README.md#'+id+'" target="_blank" rel="noopener noreferrer">Ver fluxograma renderizado no README ↗</a>';
    }
  }
  function enableExpand(figure){
    const button=figure.querySelector(".diagram-expand");
    if(!button)return;
    button.disabled=false;
    button.addEventListener("click",()=>{
      const expanded=figure.classList.toggle("diagram-expanded");
      document.body.classList.toggle("diagram-mode",expanded);
      button.setAttribute("aria-expanded",String(expanded));
      button.textContent=expanded?"Fechar visualização ×":"Ampliar ↗";
      if(expanded)figure.querySelector(".diagram-surface")?.scrollTo(0,0);
    });
  }
  async function renderVisible(){
    if(rendering){queued=true;return;}
    const figures=[...document.querySelectorAll('.portal-view:not([hidden]) .research-diagram[data-diagram-status="loading"]')];
    if(!figures.length)return;
    rendering=true;
    try{
      let m;
      try{m=await ensureEngine();}
      catch(error){
        console.warn("Biblioteca Mermaid indisponível:",error);
        figures.forEach(markError);
        return;
      }
      for(const figure of figures){
        if(figure.dataset.diagramStatus!=="loading")continue;
        const node=figure.querySelector("pre.mermaid");
        if(!node){markError(figure);continue;}
        try{
          await m.run({nodes:[node],suppressErrors:false});
          if(!node.querySelector("svg"))throw new Error("A biblioteca não gerou o SVG do fluxograma");
          figure.dataset.diagramStatus="ready";
          const message=figure.querySelector(".diagram-message");
          if(message)message.hidden=true;
          const svg=node.querySelector("svg");
          svg?.setAttribute("role","img");
          svg?.setAttribute("aria-label","Fluxograma de processamento e análise da pesquisa de mestrado");
          enableExpand(figure);
        }catch(e){
          console.warn("Erro ao renderizar fluxograma Mermaid:",e);
          markError(figure);
        }
      }
    }finally{
      rendering=false;
      if(queued){queued=false;void renderVisible();}
    }
  }
  function closeExpanded(){
    document.querySelectorAll(".research-diagram.diagram-expanded").forEach(fig=>{
      fig.classList.remove("diagram-expanded");
      const btn=fig.querySelector(".diagram-expand");
      if(btn){btn.textContent="Ampliar ↗";btn.setAttribute("aria-expanded","false");}
    });
    document.body.classList.remove("diagram-mode");
  }
  const init=()=>{
    window.addEventListener("atlas:page-change",()=>{closeExpanded();void renderVisible();});
    document.addEventListener("keydown",e=>{if(e.key==="Escape")closeExpanded();});
    void renderVisible();
  };
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});
  else init();
})();