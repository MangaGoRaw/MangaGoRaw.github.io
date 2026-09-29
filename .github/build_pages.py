from pathlib import Path
from zipfile import ZipFile
import shutil, json, html, re, hashlib
from urllib.parse import quote
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "Mangareader-final.zip"
BUILD = ROOT / ".build" / "Mangareader"
DIST = ROOT / "dist"

if DIST.exists(): shutil.rmtree(DIST)
if BUILD.parent.exists(): shutil.rmtree(BUILD.parent)
BUILD.mkdir(parents=True); DIST.mkdir(parents=True)
if not ARCHIVE.exists(): raise SystemExit("Mangareader-final.zip not found")

with ZipFile(ARCHIVE) as z:
    for info in z.infolist():
        name = info.filename.replace("\\", "/")
        if not name.startswith("Mangareader/"): continue
        if (name.startswith("Mangareader/chapter-images/") or name.startswith("Mangareader/manga-covers/") or
            name.startswith("Mangareader/supabase/") or name.startswith("Mangareader/.github/") or
            name.startswith("Mangareader/scripts/") or name == "Mangareader/README.md" or name == "Mangareader/vercel.json" or
            name in {"Mangareader/country.html","Mangareader/japan-blog.html","Mangareader/france-blog.html"}): continue
        target = ROOT / ".build" / name
        if name.endswith("/"): target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, target.open("wb") as dst: shutil.copyfileobj(src, dst)

TEXT_EXTENSIONS={".html",".htm",".js",".css",".json",".xml",".txt",".md",".mjs"}
for path in BUILD.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS: continue
    try: text=path.read_text(encoding="utf-8")
    except UnicodeDecodeError: continue
    for a,b in [("https://mangaatlas.github.io","https://mangagoraw.github.io"),("MangaAtlas.github.io","MangaGoRaw.github.io"),("MangaAtlas","MangaGoRaw"),("mangaatlas","mangagoraw"),("MANGAATLAS","MANGAGORAW"),("manga-atlas.vercel.app","mangagoraw.github.io"),("</span>Atlas","</span>GoRaw"),("MangaGoRaw/mangagoraw.github.io","MangaGoRaw/MangaGoRaw.github.io")]: text=text.replace(a,b)
    if path.name == "analytics.js":
        text="""(function(){
'use strict';
var GA_ID='G-HC32QHLNXB';
window.dataLayer=window.dataLayer||[];
window.gtag=window.gtag||function(){window.dataLayer.push(arguments);};
window.gtag('js',new Date());
window.gtag('config',GA_ID,{send_page_view:false});
var script=document.createElement('script');
script.async=true;
script.src='https://www.googletagmanager.com/gtag/js?id='+GA_ID;
document.head.appendChild(script);
window.mangaGoRawAnalytics={
  pageView:function(data){
    data=data||{};
    window.gtag('event','page_view',{
      page_title:data.page_title||document.title,
      page_location:data.page_location||location.href,
      page_referrer:data.page_referrer||document.referrer
    });
    if(data.chapter_number!=null){
      window.gtag('event','chapter_view',{
        chapter_number:String(data.chapter_number),
        chapter_slug:String(data.chapter_slug||''),
        manga_id:String(data.manga_id||''),
        manga_title:String(data.manga_title||''),
        content_type:'manga_chapter'
      });
    }
  },
  event:function(name,data){window.gtag('event',name,data||{});}
};
window.addEventListener('load',function(){
  if(!window.__mgrawChapterPage && window.mangaGoRawAnalytics)
    window.mangaGoRawAnalytics.pageView({
      page_title:document.title,
      page_location:location.href,
      page_referrer:document.referrer
    });
});
})();"""
    if path.name == "chapter-enhancements.js":
        start=text.find("function count(){"); end=text.find("function boot()",start)
        if start>=0 and end>start: text=text[:start]+"function count(){}\n"+text[end:]
        text=text.replace("if(current)nav(all,current,mangas);count()","if(current)nav(all,current,mangas)")
    if path.name == "view-count.js": text="/* View counters are disabled in the GitHub-only static build. */\n"
    path.write_text(text,encoding="utf-8")

for item in BUILD.iterdir():
    target=DIST/item.name
    if item.is_dir(): shutil.copytree(item,target,dirs_exist_ok=True)
    else: shutil.copy2(item,target)

# Keep uploaded chapter image URLs on raw.githubusercontent.com. This avoids relying on
# Pages artifact serving for hidden upload directories and still works with the static reader.
chapter_reader = DIST / "chapter.html"
if chapter_reader.exists():
    t = chapter_reader.read_text(encoding="utf-8")
    t = t.replace("if(x.startsWith(raw))return pagesBase+x.slice(raw.length);", "if(x.startsWith(raw))return x;")
    t = t.replace("if(!/^https?:\\/\\//i.test(x))return pagesBase+x.replace(/^\\//,'');", "if(!/^https?:\\/\\//i.test(x))return raw+x.replace(/^\\//,'');")
    t = t.replace('<link id="canonical" rel="canonical" href="https://mangagoraw.github.io/chapter.html">', "")
    t = t.replace("document.getElementById('canonical').href=canonical;", "var canonicalEl=document.getElementById('canonical');if(!canonicalEl){canonicalEl=document.createElement('link');canonicalEl.id='canonical';canonicalEl.rel='canonical';document.head.appendChild(canonicalEl)}canonicalEl.href=canonical;")
    t = t.replace("window.mangaAtlasAnalytics.pageView(", "window.mangaGoRawAnalytics.pageView(")
    t = t.replace("<script>const slug=", "<script>window.__mgrawChapterPage=true;const slug=")
    t = t.replace("if(window.gtag)window.gtag('event','page_view',{page_title:document.title,page_location:location.href});", "")
    # Strengthen the shared chapter template for search engines: dynamic metadata is
    # populated from the matched chapter record, with a visible H1 and richer JSON-LD.
    t = re.sub(r"function setSeo\(c\)\{.*?\}function render", r'''function setSeo(c){const baseTitle=String(c.title||'Manga Chapter Raw').trim();const title=String(c.seoTitle||baseTitle+' | MangaGoRaw').trim();const mangaTitle=String(c.mangaTitle||c.manga||c.mangaId||'Manga').trim();const number=c.number!=null?String(c.number):'';const canonicalSlug=slug==='one-piece-raw-1194'?'one-piece-raw-jp-1194':slug;const canonical='https://mangagoraw.github.io/chapter.html?slug='+encodeURIComponent(canonicalSlug);const description=String(c.description||('Read '+mangaTitle+' chapter '+number+' raw on MangaGoRaw. View the latest Japanese manga chapter online.')).trim();document.title=title;document.getElementById('desc').content=description;document.getElementById('title').textContent=title;var canonicalEl=document.getElementById('canonical');if(!canonicalEl){canonicalEl=document.createElement('link');canonicalEl.id='canonical';canonicalEl.rel='canonical';document.head.appendChild(canonicalEl)}canonicalEl.href=canonical;const image=normalizePages(c.pages||[])[0]||'';document.getElementById('ogtitle').content=title;document.getElementById('ogdesc').content=description;document.getElementById('twtitle').content=title;document.getElementById('twdesc').content=description;document.querySelector('meta[property="og:url"]')?.setAttribute('content',canonical);document.querySelector('meta[property="og:image"]')?.setAttribute('content',image);document.querySelector('meta[name="twitter:image"]')?.setAttribute('content',image);const modified=c.updatedAt||c.updated_at||c.createdAt||c.created_at||undefined;const mangaSlug=c.mangaSlug||c.mangaId||c.manga_id||'';const ld={"@context":"https://schema.org","@graph":[{"@type":"Article","headline":title,"description":description,"mainEntityOfPage":{"@type":"WebPage","@id":canonical},"url":canonical,"image":image?[image]:undefined,"inLanguage":"ja","datePublished":c.createdAt||c.created_at||undefined,"dateModified":modified,"publisher":{"@type":"Organization","name":"MangaGoRaw","url":"https://mangagoraw.github.io/"},"isPartOf":{"@type":"WebSite","name":"MangaGoRaw","url":"https://mangagoraw.github.io/"},"about":{"@type":"Thing","name":mangaTitle},"keywords":[mangaTitle,'chapter '+number,'raw manga','Japanese manga']},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"MangaGoRaw","item":"https://mangagoraw.github.io/"},{"@type":"ListItem","position":2,"name":mangaTitle,"item":"https://mangagoraw.github.io/manga.html?slug="+encodeURIComponent(mangaSlug)},{"@type":"ListItem","position":3,"name":"Chapter "+number,"item":canonical}]}]};document.getElementById('chapter-jsonld').textContent=JSON.stringify(ld)}function render''', t, count=1, flags=re.S)
    t = re.sub(r"function render\(c\)\{.*?\}function unwrap", r'''function render(c){setSeo(c);const r=document.getElementById('reader');const pages=normalizePages(c.pages);const mangaTitle=String(c.mangaTitle||c.manga||c.mangaId||'Manga').trim();const number=c.number!=null?String(c.number):'';if(!pages.length){r.innerHTML='<article class="coming"><h1>'+esc(c.title)+'</h1><p>Read '+esc(mangaTitle)+' chapter '+esc(number)+' raw on MangaGoRaw.</p><p>Chapter images are not attached yet.</p></article>';return}const tags=relatedKeywords(c).map(k=>'<span class="keyword">'+esc(k)+'</span>').join('');const intro='<div class="chapter-intro"><h1>'+esc(c.title)+'</h1><p>Read '+esc(mangaTitle)+' chapter '+esc(number)+' raw online on MangaGoRaw.</p></div>';r.innerHTML=intro+'<div class="pages">'+pages.map((u,i)=>'<img class="page" src="'+esc(u)+'" alt="'+esc(c.title)+' - page '+(i+1)+'" loading="'+(i<2?'eager':'lazy')+'" decoding="async">').join('')+'</div><section class="related" aria-label="Related chapter searches"><h2>Related manga searches</h2><div class="keywords">'+tags+'</div></section>';if(window.mangaGoRawAnalytics)window.mangaGoRawAnalytics.pageView({chapter_key:(c.mangaId||c.manga_id||c.manga||c.mangaTitle||'Manga')+' #'+String(c.number||''),chapter_slug:slug,chapter_number:c.number,manga_id:c.mangaId||c.manga_id||'',manga_title:mangaTitle,page_title:document.title,page_location:location.href})}function unwrap''', t, count=1, flags=re.S)
    t = t.replace("const merged={...matches.reduce((acc,x)=>({...acc,...x}),{}),...c,pages:[...new Set(matches.flatMap(x=>normalizePages(x.pages))) ]};if(!merged.pages.length)merged.pages=Array.isArray(c.pages)?c.pages:[];render(merged);return", "const merged={...matches.reduce((acc,x)=>({...acc,...x}),{}),...c,pages:[...new Set(matches.flatMap(x=>normalizePages(x.pages))) ]};if(!merged.pages.length)merged.pages=Array.isArray(c.pages)?c.pages:[];const mangas=Array.isArray(sources[0].mangas)?sources[0].mangas:[];const manga=mangas.find(m=>String(m.id||m.slug||'').toLowerCase()===String(merged.mangaId||merged.manga_id||'').toLowerCase());if(manga){merged.mangaTitle=manga.title||manga.native_title||merged.mangaTitle||merged.manga||merged.mangaId;merged.mangaSlug=manga.slug||manga.id||merged.mangaId}render(merged);return")
    t = t.replace(".reader{max-width:1000px;margin:auto}.pages", ".reader{max-width:1000px;margin:auto}.chapter-intro{padding:28px 20px 18px}.chapter-intro h1{margin:0 0 8px;font-size:clamp(24px,4vw,36px);line-height:1.2}.chapter-intro p{margin:0;color:#aeb6c4;line-height:1.7}.pages")
    chapter_reader.write_text(t, encoding="utf-8")

# Load the static ads renderer on public pages. The renderer reads data/ads-config.json at runtime.
# Use the repository's current ads renderer; the source ZIP may contain an older copy.
ads_source=ROOT / "ads.js"
ads_target=DIST / "ads.js"
if ads_source.exists(): shutil.copy2(ads_source, ads_target)
ads_version = hashlib.sha256(ads_target.read_bytes()).hexdigest()[:12] if ads_target.exists() else 'missing'

GA_TAG='<script async src="https://www.googletagmanager.com/gtag/js?id=G-HC32QHLNXB"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag(\'js\',new Date());gtag(\'config\',\'G-HC32QHLNXB\');</script>'

for public_name in ["index.html","latest-chapters.html","manga.html","chapter.html"]:
    public_path=DIST/public_name
    if public_path.exists():
        page=public_path.read_text(encoding="utf-8")
        page=re.sub(r'src="/ads\.js\?v=[^"]*"', 'src="/ads.js?v=11676e70"', page, flags=re.I)
        if 'src="/ads.js' not in page:
            page=page.replace("</body>", '<script src="/ads.js?v=11676e70"></script></body>', 1)
        if 'src="/ads.js?v=11676e70"' not in page:
            raise SystemExit(f"Ads cache-bust injection failed in {public_name}")
        public_path.write_text(page, encoding="utf-8")

# Keep the GitHub-backed admin UI available on the Pages artifact.
admin_source=ROOT / "admin"
admin_target=DIST / "admin"
if admin_source.exists():
    shutil.copytree(admin_source, admin_target, dirs_exist_ok=True)
    # Pages-safe fallback route for the chapter admin UI.
    chapter_admin = admin_source / "chapters.html"
    chapter_route = admin_target / "chapters" / "index.html"
    if chapter_admin.exists():
        chapter_route.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(chapter_admin, chapter_route)

for live_dir in ["chapter-images", "manga-covers"]:
    source = ROOT / live_dir
    target = DIST / live_dir
    if source.exists(): shutil.copytree(source, target, dirs_exist_ok=True)


for name in ["data/content.json","data/manual-chapters.json","data/extra-chapters.json","data/upcoming-chapters.json","data/ads-config.json"]:
    source=ROOT/name
    if source.exists():
        target=DIST/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)

# Rewrite generated chapter image references from hidden repository folders to
# public Pages paths, copying each exact source file into the Pages artifact.
_RAW_PREFIX = "https://raw.githubusercontent.com/MangaGoRaw/MangaGoRaw.github.io/main/"
_PAGES_PREFIX = "https://mangagoraw.github.io/"

def _publish_chapter_value(value):
    if not isinstance(value, str):
        return value
    rel = value
    if rel.startswith(_RAW_PREFIX):
        rel = rel[len(_RAW_PREFIX):]
    elif rel.startswith(_PAGES_PREFIX):
        rel = rel[len(_PAGES_PREFIX):]
    rel = rel.lstrip("/")
    if "/.upload-" in rel:
        public_rel = rel.replace("/.upload-", "/upload-", 1)
        source_path = ROOT / rel
        target_path = DIST / public_rel
        if source_path.is_file():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            return _PAGES_PREFIX + public_rel
    if rel.startswith("chapter-images/") and (DIST / rel).is_file():
        return _PAGES_PREFIX + rel
    return value

def _publish_chapter_data(value):
    if isinstance(value, dict):
        return {k: _publish_chapter_data(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_publish_chapter_data(v) for v in value]
    return _publish_chapter_value(value)

for _data_name in ["data/content.json","data/manual-chapters.json","data/extra-chapters.json","data/upcoming-chapters.json"]:
    _data_path = DIST / _data_name
    if not _data_path.exists(): continue
    _data_obj = json.loads(_data_path.read_text(encoding="utf-8"))
    _data_obj = _publish_chapter_data(_data_obj)
    _data_path.write_text(json.dumps(_data_obj, ensure_ascii=False, indent=2), encoding="utf-8")

# Generate isolated ad documents so providers that depend on document.write/currentScript work normally.
ads_cfg_path=DIST/"data/ads-config.json"
ads_dir=DIST/"ads"
if ads_dir.exists(): shutil.rmtree(ads_dir)
ads_dir.mkdir(parents=True,exist_ok=True)
if ads_cfg_path.exists():
    ads_cfg=json.loads(ads_cfg_path.read_text(encoding="utf-8"))
    for _section in ads_cfg.get("sections",[]):
        if not _section.get("enabled") or not str(_section.get("code") or "").strip(): continue
        _sid=str(_section.get("id") or "").strip()
        if not _sid: continue
        _code=str(_section.get("code") or "")
        _doc='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;padding:0;background:transparent;overflow:hidden;width:100%;min-height:100px}body{display:flex;justify-content:center;align-items:flex-start}</style></head><body>'+_code+'</body></html>'
        (ads_dir/(_sid+'.html')).write_text(_doc,encoding="utf-8")

content=json.loads((DIST/"data/content.json").read_text(encoding="utf-8"))
manual=json.loads((DIST/"data/manual-chapters.json").read_text(encoding="utf-8"))
mangas=content.get("mangas",[])

# Merge chapter records from every supported source by slug. Some chapters are
# stored in content.json while an older/manual copy exists in manual-chapters.json.
# Prefer the record that has actual image pages, and union pages from duplicates.
chapter_map={}
for source in [content.get("chapters",[]), manual.get("chapters",[])]:
    for raw_chapter in source:
        if not isinstance(raw_chapter,dict) or not raw_chapter.get("slug"):
            continue
        slug=str(raw_chapter.get("slug")).strip()
        existing=chapter_map.get(slug)
        if existing is None:
            chapter_map[slug]=dict(raw_chapter)
            continue
        existing_pages=existing.get("pages") if isinstance(existing.get("pages"),list) else []
        new_pages=raw_chapter.get("pages") if isinstance(raw_chapter.get("pages"),list) else []
        merged=dict(existing)
        merged.update(raw_chapter)
        merged["pages"]=list(dict.fromkeys([*existing_pages,*new_pages]))
        if existing_pages and not new_pages:
            for key in ("createdAt","created_at","updatedAt","updated_at","title","number","mangaId","manga_id","country"):
                if key in existing:
                    merged[key]=existing[key]
        chapter_map[slug]=merged

chapters=list(chapter_map.values())
manga_map={str(m.get("id") or m.get("slug") or "").lower():m for m in mangas}

# Existing repository cover files. Use these when the data record has no explicit cover.
cover_files={
    "one-piece":"1789667418337-______raw___One_piece_raw__.webp",
    "days":"1789667403096-_______.jpg",
    "the-fragrant-flowers-bloom-dignifiedly":"1789667371729-img_kv2.jpg",
    "boku-to-roboko":"1789667349988-71X9QX_xG5L._UF1000_1000_QL80_.jpg",
}

def chapter_time(c): return str(c.get("updatedAt") or c.get("updated_at") or c.get("createdAt") or c.get("created_at") or "")
def manga_for(c): return manga_map.get(str(c.get("mangaId") or c.get("manga_id") or "").lower(),{})
def cover_for(m):
    cover=str(m.get("cover") or "").strip()
    mid=str(m.get("id") or m.get("slug") or "").lower()
    if cover:
        if cover.startswith("http"):
            return cover
        return "/"+cover.lstrip("/")
    filename=cover_files.get(mid)
    if filename:
        return "/manga-covers/"+quote(mid,safe="")+"/"+quote(filename,safe="")
    return ""
chapters.sort(key=chapter_time, reverse=True)

def chapter_has_local_image(c):
    pages=c.get("pages") if isinstance(c.get("pages"),list) else []
    raw_prefix="https://raw.githubusercontent.com/MangaGoRaw/MangaGoRaw.github.io/main/"
    pages_prefix="https://mangagoraw.github.io/"
    for page in pages:
        value=page if isinstance(page,str) else (page.get("path") or page.get("url") or page.get("src") or "")
        value=str(value)
        if value.startswith(raw_prefix): value=value[len(raw_prefix):]
        elif value.startswith(pages_prefix): value=value[len(pages_prefix):]
        value=value.lstrip("/")
        if value and (DIST/value).is_file(): return True
    return False

published_chapters=[c for c in chapters if chapter_has_local_image(c)]

index=DIST/"index.html"
if index.exists() and chapters:
    text=index.read_text(encoding="utf-8")
    cards=[]; items=[]
    for i,c in enumerate(published_chapters[:10]):
        m=manga_for(c); name=m.get("title") or c.get("mangaId") or "Manga"; number=c.get("number","")
        slug=str(c.get("slug") or ""); href="/chapter.html?slug="+quote(slug,safe="")
        label=html.escape(str(name)); num=html.escape(str(number)); cls=" featured" if i==0 else ""
        cover=cover_for(m)
        if cover:
            visual='<img src="'+html.escape(cover,quote=True)+'" alt="'+label+' cover" loading="lazy" decoding="async">'
        else:
            visual='<div class="ma-home-cover-fallback" aria-hidden="true">M</div>'
        cards.append('<a class="home-card'+cls+'" href="'+href+'">'+visual+'<div class="home-overlay"><small>Latest release</small><strong>'+label+'</strong><b>Chapter '+num+'</b></div></a>')
        items.append('<a href="'+href+'"><div><strong>'+label+'</strong><span>Chapter '+num+'</span></div><b>Read →</b></a>')
    static='<section class="home-static"><div class="home-head"><div><span>LATEST RELEASES</span><h2>Latest Chapters</h2><p>Newest posted or updated chapters.</p></div><a href="/latest-chapters.html">View all →</a></div><div class="home-grid">'+''.join(cards)+'</div><div class="home-list">'+''.join(items)+'</div></section>'
    text=re.sub(r'<main id="app" class="section">.*?</main>', '<main id="app" class="section">'+static+'</main>', text, count=1, flags=re.S)
    text=re.sub(r'<script[^>]+src=["\']/homepage-system\.js[^>]*></script>','',text,flags=re.I)
    index.write_text(text,encoding="utf-8")

# Final public-page safeguards: use one generated analytics.js tag and the current ads renderer.
for _public_name in ["index.html","latest-chapters.html","manga.html","chapter.html"]:
    _public_path=DIST/_public_name
    if not _public_path.exists(): continue
    _page=_public_path.read_text(encoding="utf-8")
    _page=re.sub(r'<script[^>]+googletagmanager\\.com/gtag/js[^>]*></script>', '', _page, flags=re.I)
    _page=re.sub(r'<script[^>]*>.*?window\\.dataLayer.*?gtag.*?</script>', '', _page, flags=re.I|re.S)
    _page=re.sub(r'src="/ads\\.js\\?v=[^"]*"', f'src="/ads.js?v={ads_version}"', _page, flags=re.I)
    if 'src="/ads.js' not in _page:
        _page=_page.replace("</body>",f'<script src="/ads.js?v={ads_version}"></script></body>',1)
    _public_path.write_text(_page,encoding="utf-8")

# Build the sitemap from the same merged chapter sources used by the site,
# re-reading every chapter source here so a late/manual upload can never be
# omitted just because another build step has a stale chapter list.
sitemap_chapter_map={}
for source_name in ["data/content.json","data/manual-chapters.json","data/extra-chapters.json","data/upcoming-chapters.json"]:
    source_path=DIST/source_name
    if not source_path.exists(): continue
    source_data=json.loads(source_path.read_text(encoding="utf-8"))
    for raw_chapter in source_data.get("chapters",[]):
        if not isinstance(raw_chapter,dict): continue
        slug=str(raw_chapter.get("slug") or "").strip()
        if not slug: continue
        pages=raw_chapter.get("pages") if isinstance(raw_chapter.get("pages"),list) else []
        existing=sitemap_chapter_map.get(slug)
        if existing is None:
            sitemap_chapter_map[slug]=dict(raw_chapter)
        else:
            merged=dict(existing)
            old_pages=existing.get("pages") if isinstance(existing.get("pages"),list) else []
            merged.update(raw_chapter)
            merged["pages"]=list(dict.fromkeys([*old_pages,*pages]))
            sitemap_chapter_map[slug]=merged

sitemap_chapters=list(sitemap_chapter_map.values())
latest_date=max([chapter_time(c) for c in published_chapters] or [""])[:10]
urls=[("https://mangagoraw.github.io/", latest_date),("https://mangagoraw.github.io/latest-chapters.html", latest_date),("https://mangagoraw.github.io/manga.html", latest_date)]
for m in mangas:
    slug=m.get("slug") or m.get("id")
    if slug: urls.append(("https://mangagoraw.github.io/manga.html?slug="+quote(str(slug),safe=""),str(m.get("updated_at") or "")[:10]))
canonical_aliases={"one-piece-raw-1194":"one-piece-raw-jp-1194"}
for c in [c for c in sitemap_chapter_map.values() if c.get("pages") and chapter_has_local_image(c)]:
    slug=str(c["slug"])
    if slug in canonical_aliases: continue
    urls.append(("https://mangagoraw.github.io/chapter.html?slug="+quote(slug,safe=""),str(c.get("updatedAt") or c.get("updated_at") or c.get("createdAt") or c.get("created_at") or "")[:10]))
seen=set(); lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url,date in urls:
    if url in seen: continue
    seen.add(url); lines.append("  <url><loc>"+escape(url)+"</loc>"+(("<lastmod>"+date+"</lastmod>") if date else "")+"</url>")
lines.append("</urlset>"); (DIST/"sitemap.xml").write_text("\n".join(lines)+"\n",encoding="utf-8")
(DIST/"robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: https://mangagoraw.github.io/sitemap.xml\n",encoding="utf-8")
(DIST/".nojekyll").touch()
print(f"Built {DIST} successfully with {len(published_chapters)} published image-backed chapters and cover-aware cards.")
