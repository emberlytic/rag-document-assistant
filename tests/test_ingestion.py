from core.ingestion import _clean_pdf_text, _make_chunk_id, chunk_text


def test_chunk_text_splits_with_overlap():
    pages = [{"text": " ".join(f"word{i}" for i in range(25)), "page": 1}]
    chunks = chunk_text(pages, source="doc.pdf", chunk_size=10, overlap=2)
    # step size is chunk_size - overlap = 8; starts at 0, 8, 16, 24 -> 4 chunks
    assert len(chunks) == 4

    first_words = chunks[0]["text"].split()
    second_words = chunks[1]["text"].split()
    # last 2 words of chunk 1 should reappear as the first 2 of chunk 2
    assert first_words[-2:] == second_words[:2]


def test_chunk_text_preserves_source_and_page():
    pages = [{"text": "a b c", "page": 3}]
    chunks = chunk_text(pages, source="doc.pdf", chunk_size=10, overlap=2)
    assert chunks[0]["source"] == "doc.pdf"
    assert chunks[0]["page"] == 3


def test_make_chunk_id_sanitizes_source_name():
    chunk_id = _make_chunk_id("my report (final).pdf", 1, 0)
    assert " " not in chunk_id
    assert "(" not in chunk_id and ")" not in chunk_id
    assert chunk_id.endswith("__p1__c0")


def test_clean_pdf_text_rejoins_split_word_from_docstring_example():
    assert _clean_pdf_text("ti pped") == "tipped"


def test_clean_pdf_text_collapses_multiple_spaces():
    assert _clean_pdf_text("hello    world") == "hello world"


def test_clean_pdf_text_leaves_longer_words_alone():
    # "category" is longer than the 3-char prefix the rejoin heuristic looks
    # for, so this shouldn't trigger a merge.
    assert _clean_pdf_text("category exists") == "category exists"
