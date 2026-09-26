(function(){'use strict';
var ID='G-JZNNQSP90L';
if(window.__mangaGoRawGA)return;
window.__mangaGoRawGA=true;
window.dataLayer=window.dataLayer||[];
window.gtag=window.gtag||function(){window.dataLayer.push(arguments)};
window.gtag('js',new Date());
var isChapter=/\/chapter\.html$/i.test(location.pathname);
window.gtag('config',ID,{send_page_view:!isChapter});
var s=document.createElement('script');
s.async=true;
s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(ID);
document.head.appendChild(s);
window.mangaGoRawAnalytics={
 pageView:function(p){
  p=p||{};
  if(!isChapter)return;
  var title=String(p.page_title||document.title||'Manga Chapter Raw');
  var locationUrl=String(p.page_location||location.href);
  var chapterKey=String(p.chapter_key||'');
  var chapterSlug=String(p.chapter_slug||'');
  var chapterNumber=String(p.chapter_number==null?'':p.chapter_number);
  var mangaId=String(p.manga_id||'');
  var mangaTitle=String(p.manga_title||'');
  window.gtag('config',ID,{
   page_title:title,
   page_location:locationUrl,
   page_path:location.pathname+location.search,
   send_page_view:true
  });
  window.gtag('event','chapter_view',{
   chapter_key:chapterKey,
   chapter_slug:chapterSlug,
   chapter_number:chapterNumber,
   manga_id:mangaId,
   manga_title:mangaTitle,
   content_type:'manga_chapter'
  });
 },
 event:function(n,p){window.gtag('event',n,p||{})}
};
})();