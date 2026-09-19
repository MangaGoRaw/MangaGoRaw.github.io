(function(){
'use strict';
var ROOT='/data/ads-config.json', mounted={};
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'})[c]})}
function load(){return fetch(ROOT+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('Ads config unavailable');return r.json()}).catch(function(){return {sections:[]}})}
function execCode(host,code){
  var box=document.createElement('div'); box.className='mgraw-ad-content';
  var tpl=document.createElement('template'); tpl.innerHTML=String(code||'');
  var nodes=Array.prototype.slice.call(tpl.content.childNodes);
  nodes.forEach(function(n){
    if(n.nodeType===1 && n.tagName.toLowerCase()==='script'){
      var s=document.createElement('script');
      for(var i=0;i<n.attributes.length;i++){var a=n.attributes[i];s.setAttribute(a.name,a.value)}
      if(n.src)s.src=n.src;else s.text=n.textContent||'';
      host.appendChild(s);
    }else host.appendChild(n.cloneNode(true));
  });
}
function slot(section,where){
  var key=section.id+'|'+where;
  if(mounted[key])return null;
  mounted[key]=1;
  var wrap=document.createElement('div');
  wrap.className='mgraw-ad-slot mgraw-ad-'+esc(section.id);
  wrap.setAttribute('data-ad-id',section.id);
  wrap.setAttribute('data-ad-placement',where);
  wrap.style.cssText='display:flex;justify-content:center;align-items:center;width:100%;min-height:0;margin:18px auto;overflow:visible;clear:both;';
  try{execCode(wrap,section.code)}catch(e){console.warn('MangaGoRaw ad failed',section.id,e)}
  return wrap;
}
function mount(){
  load().then(function(cfg){
    var sections=Array.isArray(cfg.sections)?cfg.sections.filter(function(s){return s&&s.enabled&&String(s.code||'').trim()}):[];
    if(!sections.length)return;
    var path=location.pathname, chapter=path.indexOf('/chapter.html')===0;
    sections.forEach(function(s){
      var p=String(s.placement||'start'), n=Math.max(1,Number(s.between)||1);
      if(p==='start'){
        var target=chapter?document.querySelector('.reader'):document.querySelector('main')||document.body;
        var el=slot(s,'start'); if(target&&el)target.insertBefore(el,target.firstChild);
      }else if(p==='end'){
        var target=chapter?document.querySelector('.reader'):document.querySelector('main')||document.body;
        var el=slot(s,'end'); if(target&&el)target.appendChild(el);
      }else if(p==='between'&&chapter){
        var pages=document.querySelector('.pages');
        if(!pages)return;
        var imgs=pages.querySelectorAll('img.page');
        if(imgs.length>=n){
          var el=slot(s,'between-'+n);
          if(el)imgs[n-1].insertAdjacentElement('afterend',el);
        }
      }
    });
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();