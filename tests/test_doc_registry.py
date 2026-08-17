import core.doc_registry as doc_registry


def _fresh_registry(tmp_path, monkeypatch):
    db_path = str(tmp_path / "registry.db")
    monkeypatch.setattr(doc_registry, "_DB_PATH", db_path)
    doc_registry.init_db()


def test_new_document_gets_version_1(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    version = doc_registry.upsert_doc("legal", "handbook.pdf", "hash-a")
    assert version == 1


def test_reingesting_changed_content_bumps_version(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    doc_registry.upsert_doc("legal", "handbook.pdf", "hash-a")
    version = doc_registry.upsert_doc("legal", "handbook.pdf", "hash-b")
    assert version == 2


def test_is_changed_true_for_new_document(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    assert doc_registry.is_changed("legal", "handbook.pdf", "hash-a") is True


def test_is_changed_false_when_hash_matches(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    doc_registry.upsert_doc("legal", "handbook.pdf", "hash-a")
    assert doc_registry.is_changed("legal", "handbook.pdf", "hash-a") is False


def test_is_changed_true_when_hash_differs(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    doc_registry.upsert_doc("legal", "handbook.pdf", "hash-a")
    assert doc_registry.is_changed("legal", "handbook.pdf", "hash-b") is True


def test_list_docs_returns_only_matching_collection(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    doc_registry.upsert_doc("legal", "handbook.pdf", "hash-a")
    doc_registry.upsert_doc("medical", "paper.pdf", "hash-b")
    docs = doc_registry.list_docs("legal")
    assert len(docs) == 1
    assert docs[0]["filename"] == "handbook.pdf"


def test_mark_stale_updates_status(tmp_path, monkeypatch):
    _fresh_registry(tmp_path, monkeypatch)
    doc_registry.upsert_doc("legal", "handbook.pdf", "hash-a")
    doc_registry.mark_stale("legal", "handbook.pdf")
    doc = doc_registry.get_doc("legal", "handbook.pdf")
    assert doc["status"] == "stale"


def test_hash_file_is_deterministic(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("hello world")
    assert doc_registry.hash_file(str(f)) == doc_registry.hash_file(str(f))
