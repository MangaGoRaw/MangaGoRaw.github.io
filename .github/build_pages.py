from pathlib import Path
from zipfile import ZipFile
import json
import shutil

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
        if name.startswith("Mangareader/chapter-images/") or name.startswith("Mangareader/manga-covers/"): continue
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
    for a,b in [("MangaReader","MangaGoRaw"),("MangaAtlas","MangaGoRaw"),("Mangareader","MangaGoRaw"),("mangareader","mangagoraw"),("mangaatlas.github.io","mangagoraw.github.io"),("manga-atlas.vercel.app","mangagoraw.github.io")]: text=text.replace(a,b)
    text=text.replace("raw.githubusercontent.com/MangaAtlas/MangaAtlas.github.io/main/","raw.githubusercontent.com/MangaGoRaw/MangaGoRaw.github.io/main/")
    if path.suffix.lower() in {".html",".htm"}:
        for tag in ('<script src="ads.js"></script>','<script src="ads-system.js"></script>','<script src="./ads.js"></script>','<script src="./ads-system.js"></script>','<script src="/ads-system.js?v=3"></script>'): text=text.replace(tag,"")
    path.write_text(text,encoding="utf-8")

# Repository data edited by the admin must override the archived ZIP copies.
for name in ["data/content.json","data/manual-chapters.json","data/extra-chapters.json","data/chapter-dates.json","data/upcoming-chapters.json"]:
    source=ROOT/name
    if source.exists():
        target=DIST/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)

# Keep the complete ad configuration for later activation, but force every
# public section OFF for this production build.
ads_path=DIST/"data"/"ads-config.json"
if ads_path.exists():
    cfg=json.loads(ads_path.read_text(encoding="utf-8"))
    for section in cfg.get("sections",[]):
        if isinstance(section,dict): section["enabled"]=False
    ads_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

OVERRIDES=["index.html","chapter.html","manga.html","latest-chapters.html","robots.txt","sitemap.xml","analytics.js","admin/index.html"]
for name in OVERRIDES:
    source=ROOT/name
    if source.exists():
        target=DIST/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
for item in BUILD.iterdir():
    target=DIST/item.name
    if item.is_dir(): shutil.copytree(item,target,dirs_exist_ok=True)
    else: shutil.copy2(item,target)
for name in OVERRIDES:
    source=ROOT/name
    if source.exists(): shutil.copy2(source,DIST/name)
(DIST/".nojekyll").touch()
print(f"Built {DIST} successfully; scan/covers excluded, admin data preserved, ads disabled.")
