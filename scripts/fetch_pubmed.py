"""
Fetch open-access research papers from PubMed Central (PMC).
Uses the NCBI E-utilities API (free, no API key required for low volume).
Downloads up to MAX_PAPERS PDFs to data/pubmed/.
"""

import time
import sys
from pathlib import Path
import httpx

SEARCH_TERM = "sepsis diagnosis treatment"
MAX_PAPERS = 20  # Start small; increase once pipeline is validated
OUT_DIR = Path("data/pubmed")
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PMC_PDF_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
HEADERS = {"User-Agent": "NicheRAG-Demo/1.0 (research portfolio; contact: noreply@example.com)"}


def search_pmc(term: str, retmax: int) -> list[str]:
    """Search PMC for open-access articles. Returns list of PMC IDs."""
    params = {
        "db": "pmc",
        "term": f"{term}[Title/Abstract] AND open access[filter]",
        "retmax": retmax,
        "retmode": "json",
        "usehistory": "n",
    }
    r = httpx.get(ESEARCH_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    print(f"[fetch_pubmed] Found {len(ids)} PMC IDs for '{term}'")
    return ids


def fetch_pdf(pmcid: str, out_dir: Path) -> bool:
    """Download PDF for a PMC article. Returns True on success."""
    out_path = out_dir / f"PMC{pmcid}.pdf"
    if out_path.exists():
        print(f"[fetch_pubmed] PMC{pmcid}: already downloaded, skipping")
        return True
    url = PMC_PDF_URL.format(pmcid=f"PMC{pmcid}")
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=60)
        if r.status_code == 200 and b"%PDF" in r.content[:8]:
            out_path.write_bytes(r.content)
            print(f"[fetch_pubmed] PMC{pmcid}: downloaded ({len(r.content)//1024} KB)")
            return True
        else:
            print(f"[fetch_pubmed] PMC{pmcid}: PDF not available (status {r.status_code})")
            return False
    except Exception as e:
        print(f"[fetch_pubmed] PMC{pmcid}: error — {e}")
        return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pmc_ids = search_pmc(SEARCH_TERM, MAX_PAPERS * 3)  # fetch extra to account for unavailable PDFs
    downloaded = 0
    for pmcid in pmc_ids:
        if downloaded >= MAX_PAPERS:
            break
        success = fetch_pdf(pmcid, OUT_DIR)
        if success:
            downloaded += 1
        time.sleep(0.4)  # NCBI rate limit: max 3 requests/sec without API key
    print(f"\n[fetch_pubmed] Done. Downloaded {downloaded} PDFs to {OUT_DIR}/")


if __name__ == "__main__":
    main()
