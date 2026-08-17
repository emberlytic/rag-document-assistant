import core.retriever as retriever


def test_tokenize_lowercases_and_strips_punctuation():
    assert retriever._tokenize("Hello, World! 2024") == ["hello", "world", "2024"]


def test_retrieve_returns_empty_list_when_no_chunks(monkeypatch):
    monkeypatch.setattr(retriever, "get_all", lambda name: [])
    result = retriever.retrieve("legal", "any question")
    assert result == []


def test_retrieve_ranks_relevant_chunk_first(monkeypatch):
    chunks = [
        {"text": "osha requires safety training for all employees", "source": "a.pdf", "page": 1},
        {"text": "unrelated content about the office lunch menu", "source": "b.pdf", "page": 1},
    ]
    monkeypatch.setattr(retriever, "get_all", lambda name: chunks)
    monkeypatch.setattr(retriever, "vs_query", lambda name, query_text, n_results: [chunks[0]])

    results = retriever.retrieve("legal", "osha safety training requirements", top_k=2)

    assert results[0]["source"] == "a.pdf"
    assert "score" in results[0]
    assert len(results) == 2
