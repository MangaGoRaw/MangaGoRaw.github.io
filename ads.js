(function(){
'use strict';
var ROOT='/data/ads-config.json', mounted={};
function log(){try{console.debug.apply(console,['[MangaGoRaw ads]'].concat([].slice.call(arguments)))}catch(e){}}
function load(){return fetch(ROOT+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('Ads config HTTP '+r.status);return r.json()}).catch(function(e){console.warn('[MangaGoRaw ads] config unavailable',e);return {sections:[]}})}
function slotKey(section,where){return String(section.id||'')+'|'+String(where||'')}
function makeSlot(section,where){
  var key=slotKey(section,where);if(mounted[key])return null;mounted[key]=1;
  var wrap=document.createElement('div');
  wrap.className='mgraw-ad-slot';
  wrap.setAttribute('data-ad-id',String(section.id||''));
  wrap.setAttribute('data-ad-placement',String(where||''));
  wrap.style.cssText='display:flex;justify-content:center;align-items:center;width:100%;min-height:0;margin:18px auto;overflow:visible;clear:both;position:relative;z-index:1;';
  var frame=document.createElement('iframe');
  frame.className='mgraw-ad-frame';
  frame.title='Advertisement';
  frame.setAttribute('aria-label','Advertisement');
  frame.setAttribute('scrolling','no');
  frame.setAttribute('frameborder','0');
  frame.style.cssText='display:block;border:0;width:100%;max-width:100%;min-height:1px;overflow:hidden;background:transparent;';
  wrap.appendChild(frame);
  try{
    var code=String(section.code||'');
    var html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;padding:0;background:transparent;width:100%;overflow:hidden}body{display:flex;justify-content:center;align-items:flex-start}</style></head><body>'+code+'</body></html>';
    var resize=function(){
      try{
        var doc=frame.contentDocument||frame.contentWindow.document;
        var h=Math.max(doc.body?doc.body.scrollHeight:0,doc.documentElement?doc.documentElement.scrollHeight:0,1);
        frame.style.height=Math.min(Math.max(h,1),1200)+'px';
      }catch(e){}
    };
    frame.addEventListener('load',function(){resize();setTimeout(resize,300);setTimeout(resize,1200);});
    frame.setAttribute('data-ad-html',html);
    frame._mgrawActivate=function(){
      try{
        frame.srcdoc=frame.getAttribute('data-ad-html')||html;
        setTimeout(resize,700);
        setTimeout(resize,1800);
      }catch(e){console.warn('[MangaGoRaw ads] activation failed',section.id,e)}
    };
  }catch(e){console.warn('[MangaGoRaw ads] render failed',section.id,e)}
  return wrap;
}
function mount(cfg){
  var sections=Array.isArray(cfg.sections)?cfg.sections.filter(function(s){return s&&s.enabled&&String(s.code||'').trim()}):[];
  if(!sections.length){log('no enabled sections');return;}
  var chapter=location.pathname.indexOf('/chapter.html')===0;
  var reader=chapter?document.querySelector('.reader'):null;
  if(chapter&&!reader)return;
  sections.forEach(function(s){
    var p=String(s.placement||'start').toLowerCase(),n=Math.max(1,parseInt(s.between,10)||1),el;
    if(chapter&&p==='between'){
      var pages=document.querySelector('.pages'),imgs=pages&&pages.querySelectorAll('img.page');
      if(!imgs||imgs.length<n)return;
      el=makeSlot(s,'between-'+n);
      if(el){imgs[n-1].insertAdjacentElement('afterend',el);var fr=el.querySelector('.mgraw-ad-frame');if(fr&&fr._mgrawActivate)fr._mgrawActivate();}
      return;
    }
    if(chapter&&(p==='start'||p==='end')){
      el=makeSlot(s,p);if(el){p==='start'?reader.insertBefore(el,reader.firstChild):reader.appendChild(el);var fr=el.querySelector('.mgraw-ad-frame');if(fr&&fr._mgrawActivate)fr._mgrawActivate();}
      return;
    }
    if(!chapter&&(p==='between'))return;
    var target=document.querySelector('main')||document.body;
    el=makeSlot(s,p);
    if(el){p==='start'?target.insertBefore(el,target.firstChild):target.appendChild(el);var fr=el.querySelector('.mgraw-ad-frame');if(fr&&fr._mgrawActivate)fr._mgrawActivate();}
  });
}
function boot(){
  log('boot',location.pathname);
  load().then(function(cfg){
    var tries=0,timer=setInterval(function(){
      mount(cfg);tries++;
      var chapter=location.pathname.indexOf('/chapter.html')===0;
      var ready=!chapter||!!document.querySelector('.pages');
      if(ready||tries>=80)clearInterval(timer);
    },250);
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();