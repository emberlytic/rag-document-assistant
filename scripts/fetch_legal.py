"""
Fetch public legal and HR documents for the demo knowledge base.

Sources (all public domain / US government / Creative Commons):
- OSHA small-business handbook (osha.gov)
- EEOC employer EEO obligations guide (eeoc.gov)
- DOL FLSA overtime / employee classification fact sheets (dol.gov)
- FTC non-compete guidance (ftc.gov)
- SBA model NDA and independent contractor guides (sba.gov via public PDFs)
"""

import os
import sys
import time
from pathlib import Path

import httpx

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "legal"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DOCS = [
    # OSHA — Employer Responsibilities handbook
    {
        "url": "https://www.osha.gov/sites/default/files/publications/osha3021.pdf",
        "filename": "osha_employer_responsibilities_handbook.pdf",
        "desc": "OSHA Employer Responsibilities (3021)",
    },
    # OSHA — Worker Rights and Protections
    {
        "url": "https://www.osha.gov/sites/default/files/publications/osha3096.pdf",
        "filename": "osha_worker_rights.pdf",
        "desc": "OSHA Worker Rights (3096)",
    },
    # OSHA — Hazard Communication Standard (GHS/SDS)
    {
        "url": "https://www.osha.gov/sites/default/files/publications/OSHA3514.pdf",
        "filename": "osha_hazard_communication.pdf",
        "desc": "OSHA Hazard Communication (3514)",
    },
    # OSHA — Job Hazard Analysis guide
    {
        "url": "https://www.osha.gov/sites/default/files/publications/osha3153.pdf",
        "filename": "osha_job_hazard_analysis.pdf",
        "desc": "OSHA Job Hazard Analysis (3153)",
    },
    # OSHA — Ergonomics solutions for small businesses
    {
        "url": "https://www.osha.gov/sites/default/files/publications/osha3088.pdf",
        "filename": "osha_ergonomics.pdf",
        "desc": "OSHA Ergonomics for Small Businesses (3088)",
    },
    # DOL — FLSA minimum wage and pay requirements
    {
        "url": "https://www.dol.gov/sites/dolgov/files/WHD/legacy/files/minwagep.pdf",
        "filename": "dol_flsa_minimum_wage_poster.pdf",
        "desc": "DOL FLSA Minimum Wage Requirements",
    },
]


def fetch(doc: dict) -> bool:
    dest = OUTPUT_DIR / doc["filename"]
    if dest.exists():
        print(f"  [skip] {doc['filename']} already exists")
        return True

    print(f"  [fetch] {doc['desc']} ...", end=" ", flush=True)
    try:
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            r = client.get(doc["url"])
            r.raise_for_status()
            dest.write_bytes(r.content)
        print(f"OK ({len(r.content)//1024} KB)")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def main():
    print(f"Fetching {len(DOCS)} legal/HR documents → {OUTPUT_DIR}\n")
    ok = 0
    for doc in DOCS:
        if fetch(doc):
            ok += 1
        time.sleep(0.5)   # be polite to gov servers
    print(f"\nDone: {ok}/{len(DOCS)} documents ready in {OUTPUT_DIR}")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
