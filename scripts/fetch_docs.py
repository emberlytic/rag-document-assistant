"""
Fetch public technical documentation for the tech support demo.
Scrapes the FastAPI public docs (MIT-licensed open source project).
Saves each page as a .txt file to data/tech_support/.
"""

import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

OUT_DIR = Path("data/tech_support")
BASE_URL = "https://fastapi.tiangolo.com"
HEADERS = {"User-Agent": "NicheRAG-Demo/1.0 research-portfolio"}
MAX_PAGES = 40


def get_doc_links(base_url: str) -> list[str]:
    """Crawl the docs index page and return all internal doc links."""
    r = httpx.get(base_url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        # Only keep pages on the same domain, ignore anchors and external links
        if parsed.netloc == urlparse(base_url).netloc and not parsed.fragment:
            links.add(full.rstrip("/") + "/")
    return sorted(links)


def scrape_page(url: str, out_dir: Path) -> bool:
    """Scrape a single doc page and save as .txt."""
    slug = urlparse(url).path.strip("/").replace("/", "_") or "index"
    out_path = out_dir / f"{slug}.txt"
    if out_path.exists():
        print(f"[fetch_docs] {slug}: already downloaded, skipping")
        return True
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Extract main content only — skip nav, footer, sidebar
        main = soup.find("article") or soup.find("main") or soup.find("body")
        if not main:
            return False
        # Remove script/style noise
        for tag in main(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = main.get_text(separator="\n", strip=True)
        if len(text) < 200:  # skip near-empty pages
            return False
        content = f"Source: {url}\n\n{text}"
        out_path.write_text(content, encoding="utf-8")
        print(f"[fetch_docs] {slug}: saved ({len(text)//1024} KB)")
        return True
    except Exception as e:
        print(f"[fetch_docs] {url}: error — {e}")
        return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[fetch_docs] Discovering links from {BASE_URL}...")
    links = get_doc_links(BASE_URL)
    print(f"[fetch_docs] Found {len(links)} links, scraping up to {MAX_PAGES}")
    saved = 0
    for url in links[:MAX_PAGES]:
        if scrape_page(url, OUT_DIR):
            saved += 1
        time.sleep(0.3)
    print(f"\n[fetch_docs] Done. Saved {saved} pages to {OUT_DIR}/")


if __name__ == "__main__":
    main()
