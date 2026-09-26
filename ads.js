(function(){
'use strict';
var ROOT='/data/ads-config.json', mounted={};
function log(){try{console.debug.apply(console,['[MangaGoRaw ads]'].concat([].slice.call(arguments)))}catch(e){}}
function load(){return fetch(ROOT+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error();return r.json()}).catch(function(){return {sections:[]}})}
function execCode(host,code){
  var html=String(code||'');
  /* Each ad gets an isolated document. Several existing provider snippets reuse
     the same container IDs and globals; isolation prevents one slot from
     stealing/overwriting another slot. */
  var frame=document.createElement('iframe');
  frame.title='Advertisement';
  frame.setAttribute('aria-label','Advertisement');
  frame.setAttribute('scrolling','no');
  frame.style.cssText='display:block;width:100%;max-width:100%;height:280px;border:0;margin:0 auto;overflow:hidden;background:transparent;';
  host.appendChild(frame);
  var doc=frame.contentDocument||frame.contentWindow.document;
  doc.open();
  doc.write('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:transparent;min-height:1px;text-align:center;overflow:hidden}body>*{max-width:100%;}</style></head><body>'+html+'</body></html>');
  doc.close();
  return frame;
}
function slot(section,where){
  var key=section.id+'|'+where;if(mounted[key])return null;mounted[key]=1;
  var wrap=document.createElement('div');wrap.className='mgraw-ad-slot';wrap.setAttribute('data-ad-id',section.id);
  wrap.setAttribute('data-ad-placement',where);wrap.id='mgraw-ad-'+String(section.id).replace(/[^a-zA-Z0-9_-]/g,'-')+'-'+String(where).replace(/[^a-zA-Z0-9_-]/g,'-');
  wrap.style.cssText='display:flex;justify-content:center;align-items:center;width:100%;min-height:0;margin:18px auto;overflow:visible;clear:both;';
  wrap.__mangagorawAdCode=String(section.code||'');
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
      var el=slot(s,'between-'+n);if(el){imgs[n-1].insertAdjacentElement('afterend',el);try{execCode(el,el.__mangagorawAdCode)}catch(e){console.warn('MangaGoRaw ad failed',s.id,e)}}
    }else if(chapter&&(p==='start'||p==='end')){
      if(!reader)return;
      var el=slot(s,p);if(el){p==='start'?reader.insertBefore(el,reader.firstChild):reader.appendChild(el);try{execCode(el,el.__mangagorawAdCode)}catch(e){console.warn('MangaGoRaw ad failed',s.id,e)}}
    }else{
      var target=document.querySelector('main')||document.body,el=slot(s,p);
      if(el){p==='start'?target.insertBefore(el,target.firstChild):target.appendChild(el);try{execCode(el,el.__mangagorawAdCode)}catch(e){console.warn('MangaGoRaw ad failed',s.id,e)}}
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