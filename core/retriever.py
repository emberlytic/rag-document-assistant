import re
from rank_bm25 import BM25Okapi
from core.vector_store import query as vs_query, get_all

# Reciprocal Rank Fusion constant — 60 is standard
_RRF_K = 60

# How many candidates to pull from vector search before fusion
_VECTOR_CANDIDATES = 50


def _tokenize(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).split()


def retrieve(collection_name: str, query_text: str, top_k: int = 5) -> list[dict]:
    """
    Hybrid retrieval: BM25 + vector search combined with Reciprocal Rank Fusion.
    BM25 handles exact keyword/year matches; vector handles semantic similarity.
    """
    all_chunks = get_all(collection_name)
    if not all_chunks:
        return []

    n_candidates = min(_VECTOR_CANDIDATES, len(all_chunks))

    # --- Vector search ---
    vector_results = vs_query(collection_name, query_text, n_results=n_candidates)
    # Build lookup: chunk text -> vector rank
    vector_ranks: dict[str, int] = {c["text"]: i for i, c in enumerate(vector_results)}

    # --- BM25 search ---
    tokenized_corpus = [_tokenize(c["text"]) for c in all_chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(_tokenize(query_text))
    # Sort all_chunks by BM25 score descending
    bm25_ranked = sorted(
        range(len(all_chunks)), key=lambda i: bm25_scores[i], reverse=True
    )
    bm25_ranks: dict[str, int] = {all_chunks[i]["text"]: rank for rank, i in enumerate(bm25_ranked)}

    # --- Reciprocal Rank Fusion ---
    # Collect unique chunks from both result sets
    seen_texts: set[str] = set()
    candidate_chunks: list[dict] = []
    for c in vector_results:
        if c["text"] not in seen_texts:
            seen_texts.add(c["text"])
            candidate_chunks.append(c)
    for c in all_chunks:
        if c["text"] not in seen_texts:
            seen_texts.add(c["text"])
            candidate_chunks.append(c)

    def rrf_score(text: str) -> float:
        v_rank = vector_ranks.get(text, n_candidates)
        b_rank = bm25_ranks.get(text, len(all_chunks))
        return 1 / (_RRF_K + v_rank) + 1 / (_RRF_K + b_rank)

    candidate_chunks.sort(key=lambda c: rrf_score(c["text"]), reverse=True)
    top = candidate_chunks[:top_k]

    # Attach fused score (normalised 0-1 for display)
    max_score = rrf_score(top[0]["text"]) if top else 1
    return [
        {**c, "score": round(rrf_score(c["text"]) / max_score, 4)}
        for c in top
    ]
