from pathlib import Path
from zipfile import ZipFile
import shutil

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "Mangareader-final.zip"
BUILD = ROOT / ".build" / "Mangareader"
DIST = ROOT / "dist"

if DIST.exists():
    shutil.rmtree(DIST)
if BUILD.parent.exists():
    shutil.rmtree(BUILD.parent)
BUILD.mkdir(parents=True)
DIST.mkdir(parents=True)

if not ARCHIVE.exists():
    raise SystemExit("Mangareader-final.zip not found")

with ZipFile(ARCHIVE) as z:
    for info in z.infolist():
        name = info.filename.replace("\\", "/")
        if not name.startswith("Mangareader/"):
            continue
        if (
            name.startswith("Mangareader/chapter-images/")
            or name.startswith("Mangareader/manga-covers/")
            or name.startswith("Mangareader/supabase/")
            or name.startswith("Mangareader/.github/")
            or name.startswith("Mangareader/scripts/")
            or name == "Mangareader/README.md"
            or name == "Mangareader/vercel.json"
            or name in {"Mangareader/country.html","Mangareader/japan-blog.html","Mangareader/france-blog.html"}
        ):
            continue
        target = ROOT / ".build" / name
        if name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)

TEXT_EXTENSIONS = {".html", ".htm", ".js", ".css", ".json", ".xml", ".txt", ".md", ".mjs"}
for path in BUILD.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    text = text.replace("https://mangaatlas.github.io", "https://mangagoraw.github.io")
    text = text.replace("MangaAtlas.github.io", "MangaGoRaw.github.io")
    text = text.replace("MangaAtlas", "MangaGoRaw")
    text = text.replace("mangaatlas", "mangagoraw")
    text = text.replace("MANGAATLAS", "MANGAGORAW")
    text = text.replace("manga-atlas.vercel.app", "mangagoraw.github.io")
    text = text.replace("</span>Atlas", "</span>GoRaw")
    text = text.replace("MangaGoRaw/mangagoraw.github.io", "MangaGoRaw/MangaGoRaw.github.io")
    text = text.replace("cover:'https://placehold.co/300x400'", "cover:''")
    if path.name == "analytics.js":
        text = """(function(){'use strict';function load(src,id){if(document.querySelector('script[data-mangagoraw-'+id+']'))return;var s=document.createElement('script');s.src=src;s.async=false;s.setAttribute('data-mangagoraw-'+id,'true');document.head.appendChild(s)}function boot(){load('/seo-system.js?v=2','seo');if(location.pathname==='/chapter.html'||location.pathname==='/chapter')load('/chapter-navigation.js?v=2','navigation');if(location.pathname.indexOf('/admin')!==0)load('/ads-system.js?v=11','ads')}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();window.mangaGoRawAnalytics={pageView:function(){},event:function(){}}})();\n"""
    if path.name == "chapter-enhancements.js":
        start = text.find("function count(){")
        end = text.find("function boot()", start)
        if start >= 0 and end > start:
            text = text[:start] + "function count(){}\n" + text[end:]
        text = text.replace("if(current)nav(all,current,mangas);count()", "if(current)nav(all,current,mangas)")
    if path.name == "view-count.js":
        text = "/* View counters are disabled in the GitHub-only static build. */\n"
    path.write_text(text, encoding="utf-8")

for item in BUILD.iterdir():
    target = DIST / item.name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)

OVERRIDES = ["data/content.json","data/manual-chapters.json","data/extra-chapters.json","data/upcoming-chapters.json","data/ads-config.json"]
for name in OVERRIDES:
    source = ROOT / name
    if not source.exists():
        continue
    target = DIST / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

import json
from xml.sax.saxutils import escape
content = json.loads((DIST / "data/content.json").read_text(encoding="utf-8"))
manual = json.loads((DIST / "data/manual-chapters.json").read_text(encoding="utf-8"))
mangas = content.get("mangas", [])
chapters = [c for c in manual.get("chapters", []) if c.get("slug")]
urls = [("https://mangagoraw.github.io/", ""),("https://mangagoraw.github.io/latest-chapters.html", "2026-09-17")]
for m in mangas:
    slug = m.get("slug") or m.get("id")
    if slug: urls.append(("https://mangagoraw.github.io/manga.html?slug=" + slug, str(m.get("updated_at") or "")[:10]))
for c in chapters:
    if c.get("pages"):
        urls.append(("https://mangagoraw.github.io/chapter.html?slug=" + str(c["slug"]), str(c.get("updatedAt") or c.get("updated_at") or "")[:10]))
seen=set(); lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url,date in urls:
    if url in seen: continue
    seen.add(url); lines.append("  <url><loc>"+escape(url)+"</loc>"+(("<lastmod>"+date+"</lastmod>") if date else "")+"</url>")
lines.append("</urlset>")
(DIST / "sitemap.xml").write_text("\n".join(lines)+"\n",encoding="utf-8")
(DIST / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: https://mangagoraw.github.io/sitemap.xml\n",encoding="utf-8")

country='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow"><title>Manga by Country | MangaGoRaw</title><style>body{margin:0;background:#08090d;color:#f5f5f7;font-family:Inter,system-ui,sans-serif}.wrap{max-width:1380px;margin:auto;padding:45px 5%}.links{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.links a,.card{color:#fff;text-decoration:none}.links a{padding:8px 12px;border:1px solid #303340;border-radius:999px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.card{background:#101118;border:1px solid #242732;border-radius:14px;padding:12px}.card img{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:9px}.card h2{font-size:17px}.empty{padding:25px;color:#9296a5}@media(max-width:700px){.grid{grid-template-columns:repeat(2,1fr)}}</style><script src="/analytics.js"></script></head><body><main class="wrap"><a href="/">← MangaGoRaw</a><h1 id="title">Manga</h1><div class="links"><a href="?country=JP">🇯🇵 Japan</a><a href="?country=US">🇺🇸 United States</a><a href="?country=FR">🇫🇷 France</a><a href="?country=BR">🇧🇷 Brazil</a></div><p id="intro"></p><div id="grid" class="grid"></div></main><script>const code=(new URLSearchParams(location.search).get('country')||'').toUpperCase(),map={JP:['🇯🇵 Japanese Manga RAW','Japanese manga titles in the current static catalog.'],US:['🇺🇸 United States Manga','United States manga titles in the current static catalog.'],FR:['🇫🇷 France Manga','France manga titles in the current static catalog.'],BR:['🇧🇷 Brazil Manga','Brazil manga titles in the current static catalog.']};async function init(){const i=map[code],g=document.getElementById('grid');if(!i){g.innerHTML='<div class="empty">Country not found.</div>';return}document.getElementById('title').textContent=i[0];document.getElementById('intro').textContent=i[1];document.title=i[0]+' | MangaGoRaw';const d=await fetch('/data/content.json?v='+Date.now()).then(r=>r.json());const rows=(d.mangas||[]).filter(m=>String(m.country||'').toUpperCase()===code);g.innerHTML=rows.length?rows.map(m=>'<a class="card" href="/manga.html?slug='+encodeURIComponent(m.slug||m.id)+'">'+(m.cover?'<img src="'+m.cover+'" alt="'+m.title+' cover">':'')+'<h2>'+m.title+'</h2></a>').join(''):'<div class="empty">No manga published for this country yet.</div>'}init().catch(e=>{console.error(e);document.getElementById('grid').innerHTML='<div class="empty">Unable to load the catalog.</div>'});</script></body></html>'''
(DIST / "country.html").write_text(country,encoding="utf-8")
for fn,lang,title,market in [("japan-blog.html","ja","🇯🇵 日本マンガ最新チャプター","JP"),("france-blog.html","fr","🇫🇷 Blog Manga France","FR")]:
    html=f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow"><title>{title} | MangaGoRaw</title><style>body{{margin:0;background:#08090d;color:#f5f5f7;font-family:Inter,system-ui,sans-serif}}a{{color:inherit;text-decoration:none}}.wrap{{max-width:1050px;margin:auto;padding:45px 5%}}.post{{padding:20px 0;border-bottom:1px solid #242732}}.btn{{display:inline-block;padding:9px 13px;border:1px solid #34415a;border-radius:8px}}.empty{{color:#9296a5}}</style><script src="/analytics.js"></script></head><body><main class="wrap"><a href="/">MangaGoRaw</a><h1>{title}</h1><section id="posts"><p class="empty">Loading...</p></section></main><script>async function init(){{const [d,m]=await Promise.all([fetch('/data/content.json').then(r=>r.json()),fetch('/data/manual-chapters.json').then(r=>r.json())]);const a=[...(d.chapters||[]),...(m.chapters||[])].filter(c=>String(c.country||'').toUpperCase()==='{market}');a.sort((x,y)=>Date.parse(y.updatedAt||y.updated_at||'')-Date.parse(x.updatedAt||x.updated_at||''));document.getElementById('posts').innerHTML=a.length?a.map(c=>'<article class="post"><h2>'+String(c.title||('Chapter '+c.number)).replace(/[&<>]/g,'')+'</h2><a class="btn" href="/chapter.html?slug='+encodeURIComponent(c.slug)+'">Read chapter →</a></article>').join(''):'<p class="empty">No chapters available.</p>'}}init().catch(e=>{{console.error(e);document.getElementById('posts').innerHTML='<p class="empty">Unable to load chapters.</p>'}});</script></body></html>'''
    (DIST / fn).write_text(html,encoding="utf-8")

(DIST / ".nojekyll").touch()
print(f"Built {DIST} successfully.")
