from pathlib import Path
from zipfile import ZipFile
import shutil, json, html, re
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
        text="""(function(){'use strict';var ID='G-HC32QHLNXB';if(!window.__mangaGoRawGA){window.__mangaGoRawGA=true;window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config',ID,{send_page_view:true});var g=document.createElement('script');g.async=true;g.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(ID);document.head.appendChild(g)}function load(src,id){if(document.querySelector('script[data-mangagoraw-'+id+']'))return;var s=document.createElement('script');s.src=src;s.async=false;s.setAttribute('data-mangagoraw-'+id,'true');document.head.appendChild(s)}function boot(){if(location.pathname==='/chapter.html'||location.pathname==='/chapter')load('/chapter-navigation.js?v=2','navigation')}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();window.mangaGoRawAnalytics={pageView:function(p){if(window.gtag)window.gtag('event','page_view',p||{})},event:function(n,p){if(window.gtag)window.gtag('event',n,p||{})}}})();\n"""
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

for live_dir in ["chapter-images", "manga-covers"]:
    source = ROOT / live_dir
    target = DIST / live_dir
    if source.exists(): shutil.copytree(source, target, dirs_exist_ok=True)

for name in ["data/content.json","data/manual-chapters.json","data/extra-chapters.json","data/upcoming-chapters.json","data/ads-config.json"]:
    source=ROOT/name
    if source.exists():
        target=DIST/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)

content=json.loads((DIST/"data/content.json").read_text(encoding="utf-8"))
manual=json.loads((DIST/"data/manual-chapters.json").read_text(encoding="utf-8"))
mangas=content.get("mangas",[])
chapters=[c for c in manual.get("chapters",[]) if c.get("slug")]
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

index=DIST/"index.html"
if index.exists() and chapters:
    text=index.read_text(encoding="utf-8")
    cards=[]; items=[]
    for i,c in enumerate(chapters[:10]):
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

urls=[("https://mangagoraw.github.io/", ""),("https://mangagoraw.github.io/latest-chapters.html", "2026-09-17"),("https://mangagoraw.github.io/manga.html", "")]
for m in mangas:
    slug=m.get("slug") or m.get("id")
    if slug: urls.append(("https://mangagoraw.github.io/manga.html?slug="+slug,str(m.get("updated_at") or "")[:10]))
for c in [c for c in chapters if c.get("pages")]: urls.append(("https://mangagoraw.github.io/chapter.html?slug="+quote(str(c["slug"]),safe=""),str(c.get("updatedAt") or c.get("updated_at") or c.get("createdAt") or c.get("created_at") or "")[:10]))
seen=set(); lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url,date in urls:
    if url in seen: continue
    seen.add(url); lines.append("  <url><loc>"+escape(url)+"</loc>"+(("<lastmod>"+date+"</lastmod>") if date else "")+"</url>")
lines.append("</urlset>"); (DIST/"sitemap.xml").write_text("\n".join(lines)+"\n",encoding="utf-8")
(DIST/"robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: https://mangagoraw.github.io/sitemap.xml\n",encoding="utf-8")
(DIST/".nojekyll").touch()
print(f"Built {DIST} successfully with {len(chapters)} homepage chapters and cover-aware cards.")
