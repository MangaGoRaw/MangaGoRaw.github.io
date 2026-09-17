(function(){'use strict';
  var ID='G-HC32QHLNXB';
  if(!window.__mangaGoRawGA){
    window.__mangaGoRawGA=true;
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){dataLayer.push(arguments)};
    gtag('js',new Date());
    gtag('config',ID,{send_page_view:true});
    var s=document.createElement('script');
    s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(ID);
    document.head.appendChild(s);
  }
  window.mangaGoRawAnalytics={
    pageView:function(params){if(window.gtag)window.gtag('event','page_view',params||{});},
    event:function(name,params){if(window.gtag)window.gtag('event',name,params||{});}
  };
})();
