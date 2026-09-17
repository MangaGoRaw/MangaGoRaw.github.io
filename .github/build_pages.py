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

# Rebuild the supplied static site while intentionally excluding scan/covers
# from the public Pages artifact. The owner can add authorized media later.
with ZipFile(ARCHIVE) as z:
    for info in z.infolist():
        name = info.filename.replace("\\", "/")
        if not name.startswith("Mangareader/"):
            continue
        if name.startswith("Mangareader/chapter-images/"):
            continue
        if name.startswith("Mangareader/manga-covers/"):
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

# The current MangaGoRaw entry points take precedence over archived versions.
OVERRIDES = ["index.html", "chapter.html", "manga.html", "latest-chapters.html", "robots.txt", "sitemap.xml", "analytics.js"]
for name in OVERRIDES:
    source = ROOT / name
    if source.exists():
        target = DIST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

for item in BUILD.iterdir():
    target = DIST / item.name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)

# Re-apply overrides after copying archived content.
for name in OVERRIDES:
    source = ROOT / name
    if source.exists():
        shutil.copy2(source, DIST / name)

(DIST / ".nojekyll").touch()
print(f"Built {DIST} successfully without scan/covers.")
