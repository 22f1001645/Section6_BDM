from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC = BASE_DIR / "preview" / "section6" / "index.html"
DEST = BASE_DIR / "preview" / "section6" / "embed_fragment.html"


def make_fragment(html: str) -> str:
    # Extract container contents only
    start = html.find('<div class="container">')
    end = html.find('</div>', start)
    fragment = html[start:end+6]
    # Remove external stylesheet link; keep inline styles if any
    fragment = fragment.replace('<link rel="stylesheet" href="/preview/shared/styles.css">', '')
    # Namespace top-level container to avoid CSS collisions in master doc
    fragment = fragment.replace('<div class="container">', '<div class="container section6-embed">')
    return fragment


def main():
    html = SRC.read_text(encoding='utf-8')
    frag = make_fragment(html)
    DEST.write_text(frag, encoding='utf-8')
    print(f"Embed fragment ready: {DEST}")


if __name__ == '__main__':
    main()