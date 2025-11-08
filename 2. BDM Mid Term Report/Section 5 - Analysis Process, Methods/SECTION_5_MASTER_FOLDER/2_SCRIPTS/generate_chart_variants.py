import os
from pathlib import Path
from PIL import Image

"""
Generate responsive image variants for charts used in Section 4.

Sources:
- 0.2. Pure'O Naturals Data/charts
- 2. BDM Mid Term Report/ADA Visuals

Outputs:
- preview/assets/charts/<basename>@{width}w.<ext>
- preview/assets/ada_visuals/<basename>@{width}w.<ext>

Variant widths: 480, 768, 1200
"""

SIZES = [480, 768, 1200]
ROOT = Path(__file__).resolve().parents[1]

SOURCES = [
    ROOT / "0.2. Pure'O Naturals Data" / "charts",
    ROOT / "2. BDM Mid Term Report" / "ADA Visuals",
]

DESTS = {
    "charts": ROOT / "preview" / "assets" / "charts",
    "ada_visuals": ROOT / "preview" / "assets" / "ada_visuals",
}


def ensure_dirs():
    for d in DESTS.values():
        d.mkdir(parents=True, exist_ok=True)


def process_image(src_path: Path, dest_dir: Path):
    try:
        with Image.open(src_path) as im:
            im.load()
            fmt = (src_path.suffix or ".png").lower().lstrip(".")
            w, h = im.size
            for size in SIZES:
                if size >= w:
                    # Avoid upscaling; use original size as the largest variant
                    target_w = w
                else:
                    target_w = size
                target_h = int(h * (target_w / w))
                resized = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
                out_name = f"{src_path.stem}@{target_w}w{src_path.suffix}"
                out_path = dest_dir / out_name
                params = {}
                if fmt in ("jpg", "jpeg"):
                    params.update(dict(quality=90, optimize=True))
                elif fmt == "png":
                    params.update(dict(optimize=True))
                resized.save(out_path, **params)
                print(f"Generated: {out_path}")
    except Exception as e:
        print(f"Skip {src_path}: {e}")


def main():
    ensure_dirs()
    for src_dir in SOURCES:
        if not src_dir.exists():
            print(f"Source not found: {src_dir}")
            continue
        if "ADA Visuals" in str(src_dir):
            dest_dir = DESTS["ada_visuals"]
        else:
            dest_dir = DESTS["charts"]
        for p in src_dir.iterdir():
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                process_image(p, dest_dir)


if __name__ == "__main__":
    main()