import re
from pathlib import Path
from typing import Optional

import pdfplumber

from core.doc_registry import hash_file, is_changed, upsert_doc, mark_stale
from core.vector_store import upsert_chunks, delete_by_source


def parse_pdf(path: str) -> list[dict]:
    """Returns list of {text, page} dicts, one per PDF page."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = _clean_pdf_text(text.strip())
            if text:
                pages.append({"text": text, "page": i})
    return pages


def _clean_pdf_text(text: str) -> str:
    """Fix common PDF extraction artifacts from multi-column layouts."""
    import re
    # Join words split across columns/lines without hyphen (e.g. "ti pped" → "tipped")
    # Pattern: 1-3 lowercase chars, space, then lowercase chars that together form a word
    # We detect this by checking if the combined token is longer than either part alone
    def rejoin_split_word(m):
        a, b = m.group(1), m.group(2)
        # Only rejoin if neither part looks like a real standalone word
        # Heuristic: short prefix (<=3 chars) + continuation starting with lowercase
        if len(a) <= 3 and b[0].islower():
            return a + b
        return m.group(0)
    text = re.sub(r'\b([a-z]{1,3}) ([a-z]+)', rejoin_split_word, text)
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    return text


def parse_text_file(path: str) -> list[dict]:
    """Parse a plain .txt file as a single 'page'."""
    text = Path(path).read_text(encoding="utf-8", errors="ignore").strip()
    return [{"text": text, "page": 1}] if text else []


def chunk_text(
    pages: list[dict],
    source: str,
    chunk_size: int = 100,
    overlap: int = 20,
) -> list[dict]:
    """Split pages into overlapping chunks, preserving page number and source."""
    chunks = []
    chunk_index = 0
    for page in pages:
        words = page["text"].split()
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            text = " ".join(chunk_words)
            chunk_id = _make_chunk_id(source, page["page"], chunk_index)
            chunks.append(
                {
                    "text": text,
                    "source": source,
                    "page": page["page"],
                    "chunk_id": chunk_id,
                }
            )
            chunk_index += 1
            start += chunk_size - overlap
    return chunks


def _make_chunk_id(source: str, page: int, index: int) -> str:
    safe = re.sub(r"[^\w\-]", "_", source)
    return f"{safe}__p{page}__c{index}"


def ingest_document(
    path: str,
    collection_name: str,
    source_url: Optional[str] = None,
    force: bool = False,
) -> dict:
    """
    Ingest a single document into ChromaDB.
    Skips unchanged documents unless force=True.
    Returns {filename, status, version}.
    """
    filename = Path(path).name
    content_hash = hash_file(path)

    if not force and not is_changed(collection_name, filename, content_hash):
        return {"filename": filename, "status": "skipped", "version": None}

    # Remove old chunks before re-ingesting
    delete_by_source(collection_name, filename)

    # Parse based on file type
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        pages = parse_pdf(path)
    else:
        pages = parse_text_file(path)

    if not pages:
        return {"filename": filename, "status": "empty", "version": None}

    chunks = chunk_text(pages, source=filename)
    version = upsert_doc(collection_name, filename, content_hash, source_url)

    # Attach version to each chunk
    for c in chunks:
        c["version"] = version

    upsert_chunks(collection_name, chunks)
    return {"filename": filename, "status": "ingested", "version": version}


def ingest_directory(
    data_dir: str,
    collection_name: str,
    extensions: tuple = (".pdf", ".txt"),
) -> list[dict]:
    """Ingest all matching files in a directory. Returns per-file status."""
    results = []
    data_path = Path(data_dir)
    files = [f for f in data_path.iterdir() if f.suffix.lower() in extensions]
    if not files:
        print(f"[ingest] No files found in {data_dir}")
        return results
    for f in sorted(files):
        result = ingest_document(str(f), collection_name)
        status = result["status"]
        version = result.get("version")
        print(f"[ingest] {f.name}: {status}" + (f" (v{version})" if version else ""))
        results.append(result)
    return results
