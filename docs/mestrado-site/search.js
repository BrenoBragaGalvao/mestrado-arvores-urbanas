/* Busca local por capítulo e subtópico. Nenhum dado é enviado para servidor. */
(()=>{
 "use strict";
 const $=id=>document.getElementById(id);
 const normalize=text=>String(text||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase("pt-BR");
 const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 let matches=[], selected=0, wasFocused=null;
 const pages=[{id:"inicio",title:"Início",parent:"Apresentação geral da pesquisa"}];
 for(const chapter of (window.ATLAS_README?.chapters||[])){
   pages.push({id:chapter.id,title:chapter.title,parent:"Capítulo "+chapter.number});
   for(const sub of chapter.pages)pages.push({id:sub.id,title:sub.title,parent:"Subtópico "+sub.number+" · "+chapter.title});
 }
 function render(){
   const q=normalize($("command-input").value.trim());
   matches=pages.filter(x=>!q||normalize(x.title+" "+x.parent).includes(q)).slice(0,18);
   selected=Math.max(0,Math.min(selected,matches.length-1));
   $("command-results").innerHTML=matches.length?matches.map((item,i)=>
     '<a class="command-result'+(i===selected?' selected':'')+'" href="#'+esc(item.id)+'" data-index="'+i+'">'+
     '<span class="command-result-icon" aria-hidden="true">'+(item.id==="inicio"?"⌂":"▤")+'</span>'+
     '<span class="command-result-info"><strong>'+esc(item.title)+'</strong><small>'+esc(item.parent)+'</small></span>'+
     '<span class="command-result-arrow" aria-hidden="true">↵</span></a>'
   ).join(""):'<div class="command-no-result">Nenhum tópico encontrado para essa busca.</div>';
   $("command-results").querySelectorAll(".command-result").forEach(a=>a.addEventListener("click",close));
 }
 function open(){
   const dialog=$("command-search");if(!dialog||!dialog.hidden)return;
   wasFocused=document.activeElement;
   dialog.hidden=false;
   document.body.classList.add("command-open");
   $("command-input").value="";selected=0;render();
   $("command-input").focus();
 }
 function close(){
   const dialog=$("command-search");if(!dialog||dialog.hidden)return;
   dialog.hidden=true;
   document.body.classList.remove("command-open");
   if(wasFocused?.focus)wasFocused.focus();
 }
 function choose(){
   const item=matches[selected];if(!item)return;
   const target="#"+item.id;
   close();
   if(location.hash===target)window.scrollTo({top:0,behavior:"instant"});
   else location.hash=target;
 }
 function init(){
   const trigger=$("open-command-search"),dialog=$("command-search"),input=$("command-input");
   if(!trigger||!dialog||!input)return;
   trigger.addEventListener("click",open);
   $("close-command-search").addEventListener("click",close);
   dialog.addEventListener("click",ev=>{if(ev.target===dialog)close();});
   input.addEventListener("input",()=>{selected=0;render();});
   input.addEventListener("keydown",ev=>{
     if(ev.key==="ArrowDown"&&matches.length){ev.preventDefault();selected=(selected+1)%matches.length;render();}
     if(ev.key==="ArrowUp"&&matches.length){ev.preventDefault();selected=(selected+matches.length-1)%matches.length;render();}
     if(ev.key==="Enter"){ev.preventDefault();choose();}
   });
   document.addEventListener("keydown",ev=>{
     if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==="k"){ev.preventDefault();dialog.hidden?open():close();}
     else if(ev.key==="Escape"&&!dialog.hidden){ev.preventDefault();close();}
   });
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
