# Case Study: Ashford HR Consulting

> Client names and identifying details are fictional.
> The problem structure, workflow logic, and solution approach are based on real-world patterns from actual engagements.

## Client

Ashford HR Consulting is a small firm advising SMB clients on employment law and workplace compliance -- OSHA safety obligations, wage and hour rules, hazard communication requirements, and related federal guidance. Their consultants field client questions by phone and email throughout the day.

## The Challenge

Answering a client question correctly means finding the right passage in the right federal handbook -- OSHA's employer responsibilities guide, DOL wage and hour fact sheets, EEOC guidance, hazard communication standards -- and citing it accurately. Consultants were doing this by searching PDFs manually or relying on memory, which was slow under time pressure and risky when the answer involved a specific number: a wage threshold, a regulation code, a deadline.

A generic chatbot doesn't solve this safely. Asked about an unusual or non-round compliance figure, general-purpose LLMs tend to "correct" it toward whatever value looks typical from training data rather than trusting the source document -- the opposite of what a compliance answer needs.

## What We Built

A retrieval-augmented generation pipeline over Ashford's document library (OSHA handbooks, DOL fact sheets, EEOC and FTC guidance, SBA guides -- all public federal documents). Documents are parsed, chunked, and embedded locally with sentence-transformers; retrieval combines BM25 keyword search with vector similarity via Reciprocal Rank Fusion, so both exact terms (like "29 CFR 1910.1200") and semantically related questions surface the right passages. The LLM answers strictly from retrieved chunks, with a system prompt that requires a citation -- filename, page, and document version -- on every factual claim, and explicitly instructs it to copy numbers verbatim rather than reconciling them against its own knowledge.

A SQLite registry tracks each document by content hash and version. Re-ingesting only processes files that actually changed, and the version number travels with every chunk into the citation, so an answer generated before a regulation update is traceable to the exact document version it came from.

Key decisions:

- Hybrid retrieval (BM25 + vector, not vector alone) because compliance questions often hinge on exact terms -- a regulation number, an act name, a specific dollar figure -- that pure semantic search can under-rank.
- The verbatim-number-copying rule in the system prompt exists specifically because early testing showed the opposite failure mode: the LLM "fixing" an unusual figure in the source text back to what it expected. We validated this directly by deliberately altering a stated dollar figure in a source PDF and confirming the system used the document's value rather than substituting its own -- the guardrail holds under an adversarial test, not just in the common case.
- Swappable providers (Claude, OpenAI, Gemini, or fully local Ollama) so the sensitivity of the document set can drive the privacy/cost tradeoff per query, rather than committing the whole system to one provider.
- No fine-tuning -- prompt engineering plus retrieval design on general-purpose LLMs was sufficient.

## Results

This is a working demo, not yet deployed to a live client, so there's no production accuracy or time-saved data to report -- only what direct testing against real OSHA/DOL/EEOC documents showed:

| Observation | Result |
|---|---|
| Citation accuracy across test queries | Every claim in every tested answer carried a correct filename + page citation matching the retrieved source |
| Verbatim-number test (deliberately altered source figure) | System used the document's stated value, not a "corrected" one, confirming the prompt guardrail holds |
| Document re-ingestion + versioning | Editing a source PDF and re-ingesting correctly bumped the citation from Version 1 to Version 2 on the next query, with no stale-version citations |
| Typical response time (Claude, hybrid retrieval + generation) | 9-20 seconds per query, depending on answer length |

> These are observations from direct testing against the demo's document set, not a production deployment. They're not a substitute for accuracy numbers from live client use, which we don't have yet.

## Stack

- Python 3.10+
- sentence-transformers (local embeddings) + ChromaDB (local vector store)
- rank-bm25 for hybrid retrieval
- pdfplumber for PDF parsing
- Claude API (used in this validation) -- also compatible with OpenAI, Gemini, or local Ollama

## Lessons

PDF text extraction on multi-column or poster-style layouts is unreliable in ways that are easy to miss -- `pdfplumber`'s raw output can merge text across columns in ways that look plausible but aren't. The ingestion pipeline includes cleanup logic for common cases, but any RAG system built on scanned or complex-layout PDFs needs this treated as an ongoing data-quality concern, not a one-time fix.

The verbatim-number-copying instruction in the generation prompt was the single highest-leverage line in the whole system for this use case -- it's the difference between a compliance assistant that's trustworthy on specific figures and one that quietly hallucinates "reasonable-sounding" ones. It's worth testing this behavior deliberately (not just trusting the prompt wording) before treating any RAG system as reliable for figures that matter.
