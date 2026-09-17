from pathlib import Path
from zipfile import ZipFile
import shutil

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "Mangareader-final.zip"
SRC = ROOT / ".build" / "Mangareader"
DIST = ROOT / "dist"

if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir(parents=True)

if ARCHIVE.exists():
    with ZipFile(ARCHIVE) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            # Do not publish third-party scan/image payloads from the source archive.
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
    SRC = ROOT / ".build" / "Mangareader"

if not SRC.exists():
    raise SystemExit("Mangareader source directory not found")

for item in SRC.iterdir():
    target = DIST / item.name
    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)

# Ensure GitHub Pages serves the static directory exactly as built.
(DIST / ".nojekyll").touch()
print(f"Built {DIST}")
