(function(){
'use strict';
var ROOT='/data/ads-config.json',mounted={};
function log(){try{console.debug.apply(console,['[MangaGoRaw ads]'].concat([].slice.call(arguments)))}catch(e){}}
function load(){return fetch(ROOT+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('Ads config HTTP '+r.status);return r.json()}).catch(function(e){console.warn('[MangaGoRaw ads] config unavailable',e);return {sections:[]}})}
function slot(section,where){
 var key=String(section.id||'')+'|'+where;if(mounted[key])return null;mounted[key]=1;
 var wrap=document.createElement('div');wrap.className='mgraw-ad-slot';wrap.setAttribute('data-ad-id',String(section.id||''));wrap.setAttribute('data-ad-placement',where);
 wrap.id='mgraw-ad-'+String(section.id||'').replace(/[^a-zA-Z0-9_-]/g,'-')+'-'+String(where).replace(/[^a-zA-Z0-9_-]/g,'-');
 wrap.style.cssText='display:flex;justify-content:center;align-items:center;width:100%;min-height:1px;margin:18px auto;overflow:visible;clear:both;position:relative;z-index:1;';
 return wrap;
}
function runScripts(host,code){
 var tpl=document.createElement('template');tpl.innerHTML=String(code||'');
 var nodes=Array.prototype.slice.call(tpl.content.childNodes);
 var chain=Promise.resolve();
 nodes.forEach(function(n){
  if(n.nodeType!==1){if(n.textContent&&n.textContent.trim())host.appendChild(n.cloneNode(true));return;}
  if(n.tagName.toLowerCase()!=='script'){host.appendChild(n.cloneNode(true));return;}
  chain=chain.then(function(){return new Promise(function(resolve){
   var s=document.createElement('script');
   for(var i=0;i<n.attributes.length;i++)s.setAttribute(n.attributes[i].name,n.attributes[i].value);
   if(n.src){
    s.async=false;
    s.onload=function(){resolve()};s.onerror=function(){console.warn('[MangaGoRaw ads] provider script failed',n.src);resolve()};
    host.appendChild(s);
   }else{s.text=n.textContent||'';host.appendChild(s);resolve()}
  })});
 });
 return chain;
}
function render(section,where,parent){
 var code=String(section.code||'').trim();if(!code)return;
 var el=slot(section,where);if(!el)return;
 parent(el);runScripts(el,code).catch(function(e){console.warn('[MangaGoRaw ads] render failed',section.id,e)});
}
function mount(cfg){
 var sections=Array.isArray(cfg.sections)?cfg.sections.filter(function(s){return s&&s.enabled&&String(s.code||'').trim()}):[];
 if(!sections.length){log('no enabled sections');return}log('enabled sections',sections.length);
 var chapter=location.pathname.indexOf('/chapter.html')===0;
 var reader=chapter?document.querySelector('.reader'):null;if(chapter&&!reader)return;
 sections.forEach(function(s){
  var p=String(s.placement||'start').toLowerCase(),n=Math.max(1,parseInt(s.between,10)||1);
  if(chapter&&p==='between'){
   var pages=document.querySelector('.pages'),imgs=pages&&pages.querySelectorAll('img.page');if(!imgs||imgs.length<n)return;
   render(s,'between-'+n,function(el){imgs[n-1].insertAdjacentElement('afterend',el)});return;
  }
  if(chapter&&(p==='start'||p==='end')){render(s,p,function(el){p==='start'?reader.insertBefore(el,reader.firstChild):reader.appendChild(el)});return}
  if(!chapter&&p==='between')return;
  var target=document.querySelector('main')||document.body;render(s,p,function(el){p==='start'?target.insertBefore(el,target.firstChild):target.appendChild(el)});
 });
}
function boot(){load().then(function(cfg){var tries=0,timer=setInterval(function(){mount(cfg);tries++;var chapter=location.pathname.indexOf('/chapter.html')===0;var ready=!chapter||!!document.querySelector('.pages');if(ready||tries>=80)clearInterval(timer)},250)})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();