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

if not ARCHIVE.exists():
    raise SystemExit("Mangareader-final.zip not found")

# Build from the supplied source archive while keeping copyrighted scan/covers
# out of the public Pages artifact until publication rights are established.
with ZipFile(ARCHIVE) as z:
    for info in z.infolist():
        name = info.filename.replace("\\", "/")
        if name.startswith("Mangareader/chapter-images/"):
            continue
        if name.startswith("Mangareader/manga-covers/"):
            continue
        if not name.startswith("Mangareader/"):
            continue
        target = ROOT / ".build" / name
        if name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)

if not BUILD.exists():
    raise SystemExit("Mangareader source directory not found")

TEXT_EXTENSIONS = {".html", ".htm", ".js", ".css", ".json", ".xml", ".txt", ".md", ".mjs"}

for path in BUILD.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue

    text = text.replace("MangaReader", "MangaGoRaw")
    text = text.replace("Mangareader", "MangaGoRaw")
    text = text.replace("mangareader", "mangagoraw")

    if path.suffix.lower() in {".html", ".htm"}:
        for tag in (
            '<script src="ads.js"></script>',
            '<script src="ads-system.js"></script>',
            '<script src="./ads.js"></script>',
            '<script src="./ads-system.js"></script>',
        ):
            text = text.replace(tag, "")

    path.write_text(text, encoding="utf-8")

# Keep the current clean repository entry points in control of the public shell.
for name in ["index.html", "chapter.html", "manga.html", "latest-chapters.html", "robots.txt", "sitemap.xml"]:
    source = ROOT / name
    if source.exists():
        shutil.copy2(source, DIST / name)

for item in BUILD.iterdir():
    target = DIST / item.name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)

# Re-apply repository entry points after copying the source archive.
for name in ["index.html", "chapter.html", "manga.html", "latest-chapters.html", "robots.txt", "sitemap.xml"]:
    source = ROOT / name
    if source.exists():
        shutil.copy2(source, DIST / name)

(DIST / ".nojekyll").touch()
print(f"Built {DIST} without scan/covers; rebranded source UI and disabled ad execution.")
