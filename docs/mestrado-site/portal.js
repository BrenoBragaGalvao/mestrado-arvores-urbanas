/* Atlas Urbano — portal acadêmico de capítulos e subtópicos do README. */
(()=>{
 "use strict";
 const data=window.ATLAS_README;
 if(!data||!Array.isArray(data.chapters))return;
 const $=id=>document.getElementById(id);
 const repo="https://github.com/BrenoBragaGalvao/mestrado-arvores-urbanas";
 const labels={1:"Área de estudo",2:"Método original",3:"Evolução metodológica",4:"Alometria e Meta/WRI",5:"Conclusões",6:"Código e documentação"};
 const summaries={1:"Território, imagens, resolução e referências geográficas utilizadas na Area1.",2:"Quickshift global, K-Means, Random Forest e as duas propostas originais.",3:"Segmentação em recortes, atributos, validação espacial e classificadores.",4:"Alturas modeladas, índices C1–C6, onze famílias e dados dos 257 pontos.",5:"Resultados sustentados pelas evidências e limites científicos.",6:"Notebooks, scripts, relatórios e documentação reprodutível."};
 const children={
  "topico-1-1":"Dimensões e cobertura","topico-1-2":"Resolução e arquivos",
  "topico-2-1":"Árvores e gramíneas","topico-2-2":"Porte e postes","topico-2-3":"Pipeline original",
  "topico-3-1":"Memória RAM","topico-3-2":"Os 119 recortes","topico-3-3":"Quickshift e atributos","topico-3-4":"Treino e teste espaciais","topico-3-5":"NDVI, brilho e bordas","topico-3-6":"Resultados dos modelos","topico-3-7":"Consumo de RAM","topico-3-8":"Controle do sobreajuste",
  "topico-4-1":"Meta/WRI CHMv2","topico-4-2":"Inventário e espécies","topico-4-3":"Alturas nos 257 pontos","topico-4-4":"Equações alométricas","topico-4-5":"Comparação das 15 árvores","topico-4-6":"Fontes e limites"
 };
 const widgets={"topico-3-5":"widget-features","topico-3-6":"widget-classifiers","topico-4-4":"widget-mae","topico-4-5":"widget-points"};
 const symbols=["◈","◇","▤","∿","✓","▣"];
 const pages=new Map([["inicio",{id:"inicio",title:"Início",number:0}]]);
 for(const chapter of data.chapters){pages.set(chapter.id,{...chapter,kind:"chapter",chapter});for(const p of chapter.pages)pages.set(p.id,{...p,kind:"subtopic",chapter});}
 const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 function urlRewrite(raw){
  const val=String(raw).trim();
  if(val.startsWith("#sec-")){const m=val.match(/^#sec-([1-6])(?:-(\d+))?/);if(m){const key="topico-"+m[1]+(m[2]?"-"+m[2]:"");return "#"+(pages.has(key)?key:"topico-"+m[1]);}}
  if(val.startsWith("#"))return val;
  if(/^(?:https?:|mailto:|tel:)/i.test(val))return val;
  if(val.startsWith("docs/")){const name=val.slice(5);return /\.(?:png|jpg|jpeg|webp|svg|gif|csv|pdf)$/i.test(name)?"./"+name:repo+"/blob/main/docs/"+name;}
  if(val.startsWith("./"))return val;
  if(val.startsWith("../"))return repo+"/blob/main/"+val.replace(/^(?:\.\.\/)+/,"");
  if(val.startsWith("/"))return val;
  return repo+"/blob/main/"+val;
 }
 function attrLink(u){return 'href="'+esc(u)+'"'+(u.startsWith("#")||u.startsWith("./")?"":' target="_blank" rel="noopener noreferrer"');}
 function inline(text){
  let raw=String(text),tokens=[];
  const hold=html=>{const token="ZZTOKEN"+tokens.length+"ZZ";tokens.push(html);return token;};
  raw=raw.replace(/\x60([^\x60]+)\x60/g,(_,v)=>hold("<code>"+esc(v)+"</code>"));
  raw=raw.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g,(_,alt,path)=>hold('<img src="'+esc(urlRewrite(path))+'" alt="'+esc(alt)+'" loading="lazy">'));
  raw=raw.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g,(_,label,path)=>{const u=urlRewrite(path);return hold('<a '+attrLink(u)+'>'+esc(label)+'</a>');});
  raw=esc(raw).replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/(?<!\*)\*(?!\*)([^*]+)\*/g,"<em>$1</em>").replace(/~~(.+?)~~/g,"<del>$1</del>").replace(/&lt;br\s*\/?&gt;/gi,"<br>");
  return raw.replace(/ZZTOKEN(\d+)ZZ/g,(_,idx)=>tokens[Number(idx)]||"");
 }
 function splitRow(line){
  const s=line.trim().replace(/^\|/,"").replace(/\|$/,"");const cells=[];let buf="",tick=false,escape=false;
  for(const char of s){if(escape){buf+=char;escape=false;continue;}if(char==="\\"){escape=true;buf+=char;continue;}if(char==="\x60"){tick=!tick;buf+=char;continue;}if(char==="|"&&!tick){cells.push(buf.trim());buf="";continue;}buf+=char;}cells.push(buf.trim());return cells;
 }
 function divider(s){return /^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$/.test(s);}
 function rawHtml(s){return s.replace(/\b(src|href)=(["'])(.*?)\2/g,(_,key,q,value)=>key+"="+q+esc(urlRewrite(value))+q);}
 function md(markdown){
  const lines=String(markdown||"").replace(/\r/g,"").split("\n"),out=[];let para=[],list=null,code=false,codeLines=[],codeLanguage="";
  const flush=()=>{if(para.length){out.push("<p>"+inline(para.join(" ").trim())+"</p>");para=[];}};
  const stop=()=>{if(list){out.push("</"+list+">");list=null;}};
  for(let i=0;i<lines.length;i++){
   const line=lines[i],t=line.trim();
   if(/^\x60{3}/.test(t)){
    flush();stop();
    if(!code){
      code=true;codeLines=[];codeLanguage=t.slice(3).trim().split(/\s+/)[0].toLowerCase();
    } else {
      const raw=codeLines.join("\n");
      if(codeLanguage==="mermaid"){
        out.push('<figure class="research-diagram" data-diagram-status="loading">'+
          '<figcaption class="diagram-heading"><span class="diagram-heading-icon" aria-hidden="true">◇</span><span><strong>Fluxograma da metodologia</strong><small>Diagrama original da pesquisa · renderização vetorial</small></span>'+
          '<button type="button" class="diagram-expand" aria-label="Ampliar ou reduzir fluxograma" aria-expanded="false" disabled>Ampliar ↗</button></figcaption>'+
          '<div class="diagram-surface"><pre class="mermaid">'+esc(raw)+'</pre></div>'+
          '<div class="diagram-message" role="status">Preparando fluxograma interativo…</div>'+
          '<details class="diagram-source"><summary>Consultar o código Mermaid original</summary><pre><code>'+esc(raw)+'</code></pre></details></figure>');
      } else {
        const safeLang=/^[a-z0-9_+-]{1,32}$/.test(codeLanguage)?codeLanguage:"texto";
        out.push('<div class="source-code-block"><div class="source-code-caption">Código · '+esc(safeLang)+'</div><pre><code>'+esc(raw)+'</code></pre></div>');
      }
      code=false;codeLines=[];codeLanguage="";
    }
    continue;
   }
   if(code){codeLines.push(line);continue;}
   if(!t){flush();stop();continue;}
   if(/^<!--/.test(t)||/^<a\s+id=/.test(t))continue;
   if(/^<(?:\/?(?:p|div|figure|figcaption|details|summary|table|tr|td|th|thead|tbody|img|svg|picture|source|iframe)\b)/i.test(t)){flush();stop();out.push(rawHtml(line));continue;}
   if(/^\s*---+\s*$/.test(t)){flush();stop();out.push("<hr>");continue;}
   const head=t.match(/^(#{2,6})\s+(.*)$/);
   if(head){flush();stop();const n=Math.min(5,Math.max(2,head[1].length-1));out.push("<h"+n+">"+inline(head[2])+"</h"+n+">");continue;}
   if(/^\s*\|.*\|\s*$/.test(line)&&i+1<lines.length&&divider(lines[i+1])){
    flush();stop();const h=splitRow(line);i++;const rows=[];
    while(i+1<lines.length && /^\s*\|.*\|\s*$/.test(lines[i+1])&&!divider(lines[i+1]))rows.push(splitRow(lines[++i]));
    out.push('<div class="article-table-scroll"><table><thead><tr>'+h.map(x=>"<th>"+inline(x)+"</th>").join("")+"</tr></thead><tbody>");
    for(const row of rows)out.push("<tr>"+h.map((_,j)=>"<td>"+inline(row[j]||"")+"</td>").join("")+"</tr>");
    out.push("</tbody></table></div>");continue;
   }
   if(/^>\s?/.test(line)){flush();stop();const q=[line.replace(/^>\s?/,"")];while(i+1<lines.length&&/^>\s?/.test(lines[i+1]))q.push(lines[++i].replace(/^>\s?/,""));out.push("<blockquote>"+md(q.join("\n"))+"</blockquote>");continue;}
   const bullet=line.match(/^\s*[-*+]\s+(.*)$/),numbered=line.match(/^\s*\d+[.)]\s+(.*)$/);
   if(bullet||numbered){flush();const kind=bullet?"ul":"ol";if(list!==kind){stop();out.push("<"+kind+">");list=kind;}out.push("<li>"+inline((bullet||numbered)[1])+"</li>");continue;}
   if(/^\s*<\w+/.test(t)&&/<[^>]+>/.test(t)){flush();stop();out.push(rawHtml(line));continue;}
   para.push(t);
  }
  flush();stop();if(code)out.push('<div class="source-code-block"><pre><code>'+esc(codeLines.join("\n"))+'</code></pre></div>');
  return out.join("\n");
 }
 const ICONS={
  0:'<path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9M9 20v-7h6v7"/>',
  1:'<path d="M3 19V6l7-3 7 3v13"/><path d="m10 3 0 16M17 8l4-2v13M3 19h18"/>',
  2:'<path d="M12 22v-7"/><path d="M5 22h14M5 15l7-12 7 12H5Z"/><path d="M7 18h10"/>',
  3:'<path d="m3 17 6-6 4 3 8-9"/><path d="M15 5h6v6"/><path d="M3 21h18"/>',
  4:'<path d="M12 22v-7"/><path d="M12 15C6 15 4 12 4 7c6 0 8 3 8 8Z"/><path d="M12 15c0-5 2-8 8-8 0 5-2 8-8 8Z"/>',
  5:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  6:'<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m9 9-3 3 3 3m6-6 3 3-3 3"/>'
 };
 function icon(number){
  return '<svg class="nav-icon" viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(ICONS[number]||ICONS[0])+'</svg>';
 }
 function navigation(){
  const blocks=['<a class="sidebar-home-link portal-nav-link" href="#inicio" data-link="inicio"><span class="home-icon" aria-hidden="true">'+icon(0)+'</span><span>Início</span></a>'];
  const home=[];
  for(const [i,ch] of data.chapters.entries()){
   const id=ch.id,num=String(ch.number).padStart(2,"0");
   blocks.push('<div class="sidebar-group" data-group="'+num+'"><div class="sidebar-group-head"><a class="sidebar-chapter-link portal-nav-link" data-link="'+id+'" href="#'+id+'"><span class="chapter-index">'+icon(ch.number)+'</span><span class="chapter-label">'+esc(labels[ch.number])+'</span></a>'+(ch.pages.length?'<button type="button" class="chapter-toggle" aria-label="Mostrar subtópicos de '+esc(labels[ch.number])+'" aria-expanded="false">⌄</button>':'')+'</div>');
   if(ch.pages.length){blocks.push('<div class="sidebar-subtopics">');for(const p of ch.pages)blocks.push('<a href="#'+p.id+'" class="sidebar-subtopic-link portal-nav-link" data-link="'+p.id+'"><span>'+esc(p.number)+'</span><b>'+esc(children[p.id]||p.title)+'</b></a>');blocks.push("</div>");}
   blocks.push("</div>");
   home.push('<a class="home-chapter-card" href="#'+id+'"><div class="chapter-card-head"><span>'+num+' / CAPÍTULO</span><i aria-hidden="true">'+symbols[i]+'</i></div><h3>'+esc(labels[ch.number])+'</h3><p>'+esc(summaries[ch.number])+'</p><div class="chapter-card-foot"><span>'+(ch.pages.length?ch.pages.length+" subtópicos":"Abrir capítulo")+'</span><strong aria-hidden="true">→</strong></div></a>');
  }
  $("sidebar-nav").innerHTML=blocks.join("");$("home-chapters").innerHTML=home.join("");
  document.querySelectorAll(".chapter-toggle").forEach(b=>b.addEventListener("click",()=>{const g=b.closest(".sidebar-group");const open=!g.classList.contains("expanded");g.classList.toggle("expanded",open);b.setAttribute("aria-expanded",String(open));}));
 }
 function sections(){
  const result=[];
  for(const ch of data.chapters){
   const num=String(ch.number).padStart(2,"0");
   const overview=ch.markdown.trim()?md(ch.markdown):"<p>"+esc(summaries[ch.number])+"</p>";
   const tiles=ch.pages.length?'<div class="chapter-index-heading">EXPLORE OS SUBTÓPICOS</div><div class="chapter-index-grid">'+ch.pages.map(p=>'<a href="#'+p.id+'" class="chapter-subcard"><span>'+esc(p.number)+'</span><strong>'+esc(children[p.id]||p.title)+'</strong><em aria-hidden="true">↗</em></a>').join("")+"</div>":"";
   result.push('<section class="portal-view chapter-view" data-view="'+ch.id+'" id="page-'+ch.id+'" hidden><div class="chapter-topline"><span>CAPÍTULO '+num+' / 06</span><span>DOCUMENTAÇÃO DA PESQUISA</span></div><div class="chapter-title-block"><span class="chapter-eyebrow">TÓPICO '+num+'</span><h1>'+esc(labels[ch.number])+'</h1><p>'+esc(summaries[ch.number])+'</p></div><div class="chapter-source"><span>Conteúdo fundamentado no README do repositório</span><a href="'+repo+'/blob/main/README.md#sec-'+ch.number+'" target="_blank" rel="noopener noreferrer">Ler no GitHub ↗</a></div><article class="readme-article">'+overview+'</article>'+tiles+'</section>');
   for(const p of ch.pages){
    result.push('<section class="portal-view chapter-view subtopic-view" data-view="'+p.id+'" id="page-'+p.id+'" hidden><div class="chapter-topline"><span>CAPÍTULO '+num+' / 06</span><span>'+esc(labels[ch.number]).toUpperCase()+'</span></div><div class="chapter-title-block"><span class="chapter-eyebrow">SUBTÓPICO '+esc(p.number)+'</span><h1>'+esc(p.title)+'</h1></div><div class="chapter-source"><a href="#'+ch.id+'">← Todos os subtópicos de '+esc(labels[ch.number])+'</a><a href="'+repo+'/blob/main/README.md#sec-'+p.number.replace(".","-")+'" target="_blank" rel="noopener noreferrer">Consultar no README ↗</a></div><div class="subtopic-lead"><span>DOCUMENTAÇÃO DO TÓPICO '+esc(p.number)+'</span><p>'+esc(summaries[ch.number])+'</p></div><article class="readme-article">'+md(p.markdown)+'</article><div class="widget-mount" id="mount-'+p.id+'"></div><div class="end-nav"><a href="#'+ch.id+'">← Voltar para '+esc(labels[ch.number])+'</a></div></section>');
   }
  }
  $("chapter-pages").innerHTML=result.join("\n");
  for(const [page,widgetId] of Object.entries(widgets)){
   const widget=$(widgetId),mount=$("mount-"+page);
   if(widget&&mount){widget.removeAttribute("hidden");mount.appendChild(widget);}
  }
 }
 let active="inicio";
 function closeMenu(){$("sidebar").classList.remove("open");$("sidebar-scrim").hidden=true;$("sidebar-toggle").setAttribute("aria-expanded","false");document.body.classList.remove("menu-open");}
 function openMenu(){$("sidebar").classList.add("open");$("sidebar-scrim").hidden=false;$("sidebar-toggle").setAttribute("aria-expanded","true");document.body.classList.add("menu-open");$("sidebar-close").focus();}
 function activate(id){
  const next=pages.has(id)?id:"inicio",old=$("page-"+active),current=$("page-"+next);
  if(old)old.hidden=true;if(current)current.hidden=false;active=next;
  document.querySelectorAll("[data-link]").forEach(el=>{const selected=el.getAttribute("data-link")===next;el.classList.toggle("active",selected);if(selected)el.setAttribute("aria-current","page");else el.removeAttribute("aria-current");});
  const entry=pages.get(next),chapter=entry?.chapter;
  document.querySelectorAll(".sidebar-group").forEach(g=>{
   const same=chapter&&g.dataset.group===String(chapter.number).padStart(2,"0");
   if(same)g.classList.add("expanded");g.classList.toggle("active-group",!!same);
   const toggle=g.querySelector(".chapter-toggle");if(toggle)toggle.setAttribute("aria-expanded",String(g.classList.contains("expanded")));
  });
  const text=next==="inicio"?"Início":entry.kind==="chapter"?labels[entry.number]:entry.number+" · "+(children[next]||entry.title);
  $("breadcrumb-current").textContent=text;document.title=text+" | Atlas Urbano";
  window.scrollTo({top:0,behavior:"instant"});closeMenu();
  window.dispatchEvent(new CustomEvent("atlas:page-change",{detail:{id:next}}));
 }
 function route(){activate(decodeURIComponent(location.hash.replace(/^#/,"")).trim()||"inicio");}
 function init(){
  navigation();sections();
  $("sidebar-toggle").addEventListener("click",()=>{$("sidebar").classList.contains("open")?closeMenu():openMenu();});
  $("sidebar-close").addEventListener("click",closeMenu);
  $("sidebar-scrim").addEventListener("click",closeMenu);
  window.addEventListener("hashchange",route);
  document.addEventListener("keydown",e=>{if(e.key==="Escape")closeMenu();});
  route();
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
