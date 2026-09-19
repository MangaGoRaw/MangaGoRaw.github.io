(function(){
'use strict';
var ROOT='/data/ads-config.json', mounted={};
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
  try{execCode(wrap,section.code)}catch(e){console.warn('MangaGoRaw ad failed',section.id,e)}
  return wrap;
}
function mount(cfg){
  var sections=Array.isArray(cfg.sections)?cfg.sections.filter(function(s){return s&&s.enabled&&String(s.code||'').trim()}):[];
  if(!sections.length)return;
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