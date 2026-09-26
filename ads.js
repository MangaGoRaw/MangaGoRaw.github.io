(function(){
'use strict';
var ROOT='/data/ads-config.json',mounted={};
function log(){try{console.debug.apply(console,['[MangaGoRaw ads]'].concat([].slice.call(arguments)))}catch(e){}}
function load(){return fetch(ROOT+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error();return r.json()}).catch(function(){return {sections:[]}})}
function slot(section,where){
 var key=section.id+'|'+where;if(mounted[key])return null;mounted[key]=1;
 var wrap=document.createElement('div');
 wrap.className='mgraw-ad-slot';
 wrap.setAttribute('data-ad-id',section.id);
 wrap.setAttribute('data-ad-placement',where);
 wrap.id='mgraw-ad-'+String(section.id).replace(/[^a-zA-Z0-9_-]/g,'-')+'-'+String(where).replace(/[^a-zA-Z0-9_-]/g,'-');
 wrap.style.cssText='display:flex;justify-content:center;align-items:center;width:100%;min-height:90px;margin:18px auto;overflow:visible;clear:both;';
 return wrap;
}
function runCode(host,code){
 var box=document.createElement('div');
 box.style.cssText='width:100%;display:flex;justify-content:center;align-items:center;overflow:visible;';
 host.appendChild(box);
 var html=String(code||'');
 var parser=document.createElement('div');
 parser.innerHTML=html;
 Array.prototype.slice.call(parser.childNodes).forEach(function(node){
   if(node.nodeType===1&&node.tagName.toLowerCase()==='script'){
     var s=document.createElement('script');
     Array.prototype.slice.call(node.attributes).forEach(function(a){s.setAttribute(a.name,a.value)});
     s.text=node.textContent||'';
     box.appendChild(s);
   }else{
     box.appendChild(node.cloneNode(true));
   }
 });
 return box;
}
function mount(cfg){
 var sections=Array.isArray(cfg.sections)?cfg.sections.filter(function(s){return s&&s.enabled&&String(s.code||'').trim()}):[];
 if(!sections.length){log('no enabled sections');return;}
 var chapter=location.pathname.indexOf('/chapter.html')===0;
 sections.forEach(function(s){
   var p=String(s.placement||'start'),n=Math.max(1,Number(s.between)||1);
   if(!chapter&&p==='between')return;
   var reader=document.querySelector('.reader');
   if(chapter&&!reader)return;
   if(chapter&&p==='between'){
     var pages=document.querySelector('.pages'),imgs=pages&&pages.querySelectorAll('img.page');
     if(!imgs||imgs.length<n)return;
     var el=slot(s,'between-'+n);
     if(el){imgs[n-1].insertAdjacentElement('afterend',el);try{runCode(el,el.__mangagorawAdCode||s.code)}catch(e){console.warn('MangaGoRaw ad failed',s.id,e)}}
   }else if(chapter&&(p==='start'||p==='end')){
     if(!reader)return;
     var el=slot(s,p);
     if(el){p==='start'?reader.insertBefore(el,reader.firstChild):reader.appendChild(el);try{runCode(el,s.code)}catch(e){console.warn('MangaGoRaw ad failed',s.id,e)}}
   }else{
     var target=document.querySelector('main')||document.body,el=slot(s,p);
     if(el){p==='start'?target.insertBefore(el,target.firstChild):target.appendChild(el);try{runCode(el,s.code)}catch(e){console.warn('MangaGoRaw ad failed',s.id,e)}}
   }
 });
}
function boot(){
 log('boot',location.pathname);
 load().then(function(cfg){
   var tries=0,timer=setInterval(function(){
     mount(cfg);tries++;
     var chapter=location.pathname.indexOf('/chapter.html')===0;
     var need=chapter&&!document.querySelector('.pages');
     if(!need||tries>=80)clearInterval(timer);
   },250);
 });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();