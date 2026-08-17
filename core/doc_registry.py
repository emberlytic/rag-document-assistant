import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import os

_DB_PATH = os.getenv("REGISTRY_DB_PATH", "./db/registry.db")


def _connect() -> sqlite3.Connection:
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                filename TEXT NOT NULL,
                source_url TEXT,
                content_hash TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'current',
                UNIQUE(collection, filename)
            )
        """)
        conn.commit()


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_doc(collection: str, filename: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE collection=? AND filename=?",
            (collection, filename),
        ).fetchone()
        return dict(row) if row else None


def upsert_doc(collection: str, filename: str, content_hash: str, source_url: str = None) -> int:
    """Insert or update a document record. Returns the new version number."""
    now = datetime.now(timezone.utc).isoformat()
    existing = get_doc(collection, filename)
    if existing is None:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO documents (collection, filename, source_url, content_hash, ingested_at, version, status)
                   VALUES (?, ?, ?, ?, ?, 1, 'current')""",
                (collection, filename, source_url, content_hash, now),
            )
            conn.commit()
        return 1
    else:
        new_version = existing["version"] + 1
        with _connect() as conn:
            conn.execute(
                """UPDATE documents SET content_hash=?, ingested_at=?, version=?, status='current', source_url=COALESCE(?, source_url)
                   WHERE collection=? AND filename=?""",
                (content_hash, now, new_version, source_url, collection, filename),
            )
            conn.commit()
        return new_version


def is_changed(collection: str, filename: str, content_hash: str) -> bool:
    """Returns True if the document is new or its hash has changed."""
    doc = get_doc(collection, filename)
    return doc is None or doc["content_hash"] != content_hash


def list_docs(collection: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE collection=? ORDER BY filename",
            (collection,),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_stale(collection: str, filename: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE documents SET status='stale' WHERE collection=? AND filename=?",
            (collection, filename),
        )
        conn.commit()


init_db()
