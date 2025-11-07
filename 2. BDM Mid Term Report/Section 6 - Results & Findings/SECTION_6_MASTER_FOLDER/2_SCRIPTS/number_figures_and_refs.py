import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = BASE_DIR / "preview" / "section6" / "index.html"


def renumber_figures(html: str):
    # Standardize captions: Figure 6.x — ...
    fig_map = {
        "Figure 6.1.1": "Figure 6.1",
        "Figure 6.2.1": "Figure 6.2",
        "Figure 6.3.1": "Figure 6.3",
        "Figure 6.4.1": "Figure 6.4",
        "Figure 6.5.1": "Figure 6.5",
        "Figure 6.6.1": "Figure 6.6",
    }
    for old, new in fig_map.items():
        html = html.replace(old, new)

    # Fix references like Charts: Figure 6.x.1 -> Figure 6.x
    html = re.sub(r"Charts:\s*Figure\s6\.(\d)\.1", r"Charts: Figure 6.\1", html)

    # Ensure figure IDs exist (fig-6-1 .. fig-6-6)
    for i in range(1, 7):
        html = re.sub(
            rf"<figure(?![^>]*id=)[^>]*>",
            rf"<figure id=\"fig-6-{i}\">",
            html,
            count=1,
        )
    return html


def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    updated = renumber_figures(html)
    HTML_PATH.write_text(updated, encoding="utf-8")
    print("Figure numbering and references normalized.")


if __name__ == "__main__":
    main()