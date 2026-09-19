(function(){
'use strict';
var ROOT='/data/ads-config.json', mounted={};
function log(){try{console.debug.apply(console,['[MangaGoRaw ads]'].concat([].slice.call(arguments)))}catch(e){}}
function load(){return fetch(ROOT+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error();return r.json()}).catch(function(){return {sections:[]}})}
function execCode(host,code){
  var tpl=document.createElement('template'); tpl.innerHTML=String(code||'');
  Array.prototype.slice.call(tpl.content.childNodes).forEach(function(n){
    if(n.nodeType===1&&n.tagName.toLowerCase()==='script'){
      var s=document.createElement('script');
      for(var i=0;i<n.attributes.length;i++)s.setAttribute(n.attributes[i].name,n.attributes[i].value);
      if(n.src)s.src=n.src;else s.text=n.textContent||'';
      host.appendChild(s);
    }else host.appendChild(n.cloneNode(true));
  });
}
function slot(section,where){
  var key=section.id+'|'+where;if(mounted[key])return null;mounted[key]=1;
  var wrap=document.createElement('div');wrap.className='mgraw-ad-slot';wrap.setAttribute('data-ad-id',section.id);
  wrap.setAttribute('data-ad-placement',where);
  wrap.style.cssText='display:flex;justify-content:center;align-items:center;width:100%;min-height:0;margin:18px auto;overflow:visible;clear:both;';
  try{if(location.pathname==='/'||location.pathname==='/index.html'){var frame=document.createElement('iframe');frame.title='Advertisement';frame.setAttribute('aria-label','Advertisement');frame.setAttribute('scrolling','no');frame.style.cssText='display:block;border:0;width:100%;max-width:100%;height:280px;margin:0 auto;overflow:hidden;background:transparent;';frame.srcdoc='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;padding:0;background:transparent;overflow:hidden}body{display:flex;justify-content:center;align-items:flex-start;min-height:90px}</style></head><body>'+String(section.code||'')+'</body></html>';wrap.appendChild(frame)}else execCode(wrap,section.code)}catch(e){console.warn('MangaGoRaw ad failed',section.id,e)}
  return wrap;
}
function mount(cfg){
  var sections=Array.isArray(cfg.sections)?cfg.sections.filter(function(s){return s&&s.enabled&&String(s.code||'').trim()}):[];
  if(!sections.length){log('no enabled sections');return;}
  log('enabled sections',sections.length);
  var chapter=location.pathname.indexOf('/chapter.html')===0;
  sections.forEach(function(s){
    var p=String(s.placement||'start'),n=Math.max(1,Number(s.between)||1);
    if(!chapter&&(p==='between'))return;
    var reader=document.querySelector('.reader');
    if(chapter&&!reader)return;
    if(chapter&&p==='between'){
      var pages=document.querySelector('.pages'),imgs=pages&&pages.querySelectorAll('img.page');
      if(!imgs||imgs.length<n)return;
      var el=slot(s,'between-'+n);if(el)imgs[n-1].insertAdjacentElement('afterend',el);
    }else if(chapter&&(p==='start'||p==='end')){
      if(!reader)return;
      var el=slot(s,p);if(el)(p==='start'?reader.insertBefore(el,reader.firstChild):reader.appendChild(el));
    }else{
      var target=document.querySelector('main')||document.body,el=slot(s,p);
      if(el)(p==='start'?target.insertBefore(el,target.firstChild):target.appendChild(el));
    }
  });
}
function boot(){
 log('boot',location.pathname);
 load().then(function(cfg){
   var tries=0, timer=setInterval(function(){
     mount(cfg);tries++;
     var chapter=location.pathname.indexOf('/chapter.html')===0;
     var need=chapter&&!document.querySelector('.pages');
     if(!need||tries>=80)clearInterval(timer);
   },250);
 });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();