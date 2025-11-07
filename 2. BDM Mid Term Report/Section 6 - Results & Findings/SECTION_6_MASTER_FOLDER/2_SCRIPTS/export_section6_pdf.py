import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

from PyPDF2 import PdfReader, PdfWriter


BASE_DIR = Path(__file__).resolve().parent.parent
PREVIEW_HTML = BASE_DIR / "preview" / "section6" / "index.html"
OUTPUTS_DIR = BASE_DIR / "0.2. Pure'O Naturals Data" / "outputs"
PDF_PATH = OUTPUTS_DIR / "Section6_PureO_Naturals.pdf"


def find_browser():
    candidates = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def ensure_outputs_dir():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def print_to_pdf(browser_path: str, url: str, out_pdf: Path):
    cmd = [
        browser_path,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={str(out_pdf)}",
        url,
    ]
    subprocess.run(cmd, check=True)


def add_pdf_metadata_and_bookmarks(pdf_path: Path):
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Metadata
    writer.add_metadata({
        "/Title": "Section 6 — Results & Findings (Pure'O Naturals)",
        "/Author": "BDM Capstone — Pure'O Naturals Team",
        "/Subject": "Results & Findings",
        "/Keywords": "BDM Capstone, Pure'O Naturals, Section 6, Volatility, Margin, ABC, DSLS, Price Variance",
        "/Creator": "Trae IDE Exporter",
    })

    # Bookmarks: assumes each main section starts at a new page due to page-breaks
    toc = [
        ("6.1 Revenue Volatility (CV)", 0),
        ("6.2 Rolling Volatility by Month", 1),
        ("6.3 Margin Analysis", 2),
        ("6.4 ABC Classification (Pareto)", 3),
        ("6.5 Slow Movers (DSLS)", 4),
        ("6.6 Price Variance (Top 20)", 5),
        ("Quality Assurance & Traceability", 6),
        ("Synthesis & 90-Day Plan", 7),
        ("Submission Checklist", 8),
        ("Data References", 9),
    ]
    # Clamp to available pages
    max_pages = len(reader.pages)
    for title, page_index in toc:
        if page_index < max_pages:
            writer.add_outline_item(title, page_index)

    tmp_path = pdf_path.with_suffix(".tmp.pdf")
    with open(tmp_path, "wb") as f:
        writer.write(f)
    os.replace(tmp_path, pdf_path)


def main():
    if not PREVIEW_HTML.exists():
        print(f"HTML not found: {PREVIEW_HTML}")
        sys.exit(1)

    ensure_outputs_dir()
    browser = find_browser()
    if not browser:
        print("No Chromium-based browser found (Chrome/Edge). Install one to enable PDF export.")
        sys.exit(2)

    url = "http://localhost:8000/preview/section6/index.html"
    print(f"Printing to PDF via {browser} -> {PDF_PATH}")
    print_to_pdf(browser, url, PDF_PATH)

    add_pdf_metadata_and_bookmarks(PDF_PATH)
    print(f"PDF ready: {PDF_PATH}")


if __name__ == "__main__":
    main()