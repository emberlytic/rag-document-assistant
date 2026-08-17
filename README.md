# Legal & HR Document Assistant (RAG)

> Answers legal and HR compliance questions from a library of source documents, with every claim tied to a citation (filename, page, version) -- and no number rewritten to "look right" if it disagrees with the LLM's training data.

## The Problem

Staff answering employment-law and compliance questions -- OSHA safety obligations, FLSA wage rules, EEOC guidance, workplace policy -- have to dig through hundreds of pages of federal handbooks and fact sheets to find the right answer with the right citation. Manual search is slow, and paraphrasing a compliance figure from memory risks getting it wrong. A generic chatbot has the opposite problem: asked about an unusual or non-round number, it will often "correct" the document's actual value back toward whatever looks typical from its training data -- exactly the kind of error that matters most in a compliance context.

## The Solution

A retrieval-augmented generation pipeline: source PDFs are parsed, chunked, embedded locally, and indexed. A query runs hybrid retrieval (BM25 keyword search + vector similarity, combined with Reciprocal Rank Fusion) so both exact terms (regulation numbers, dollar figures) and semantically related phrasing get surfaced. The LLM then answers strictly from the retrieved chunks, with a system prompt that requires a citation on every factual claim and explicitly instructs it to copy numbers verbatim from the context rather than reconciling them against its own knowledge.

A SQLite document registry tracks each source file by content hash, so re-ingesting only processes documents that actually changed, and every retrieved chunk carries a version number -- if a regulation gets updated, old citations don't silently keep pointing at superseded text.

## Data Handling

Embeddings and retrieval always run locally (sentence-transformers + ChromaDB on-disk) -- documents never leave the machine for the indexing step. The answer-generation step is different: retrieved passages ARE sent to whichever LLM provider is selected, if it's a hosted API (Claude, OpenAI, Gemini). Selecting the Ollama provider keeps the entire pipeline, including generation, fully local with no data leaving the machine. Choose the provider per query based on the sensitivity of the documents involved.

## Architecture

```mermaid
flowchart LR
    A[PDF / TXT Docs] --> B[Parse + Chunk]
    B --> C[SQLite Doc Registry<br/>hash + version tracking]
    B --> D[Local Embeddings<br/>all-MiniLM-L6-v2]
    D --> E[ChromaDB<br/>vector store]

    F[User Question] --> G[Hybrid Retrieval<br/>BM25 + Vector + RRF]
    E --> G
    G --> H[LLM API<br/>Claude / OpenAI / Gemini / Ollama]
    H --> I[Cited Answer]
```

## Stack

- Python 3.10+
- sentence-transformers (`all-MiniLM-L6-v2`) -- local embeddings
- ChromaDB -- local persistent vector store
- rank-bm25 -- keyword search half of hybrid retrieval
- pdfplumber -- PDF text extraction
- SQLite -- document registry (content hash, version, ingested_at)
- FastAPI + Streamlit -- API and demo UI
- Claude, OpenAI, Gemini, or Ollama -- swappable LLM backend for answer generation

## How to Run

**1. Clone and install**
```bash
git clone https://github.com/emberlytic/rag-document-assistant.git
cd rag-document-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure your API key**
```bash
cp .env.example .env
# Edit .env -- set at least one of ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY,
# or point OLLAMA_BASE_URL at a local Ollama instance for a fully local setup
```

**3. Fetch source documents**

Sample data isn't checked into the repo. Each demo has a fetch script that pulls public documents:
```bash
python scripts/fetch_legal.py   # OSHA / DOL / EEOC / FTC / SBA guidance (this demo)
python scripts/fetch_pubmed.py  # medical research demo
python scripts/fetch_docs.py    # FastAPI documentation demo
```

**4. Start the API and UI**
```bash
./start.sh
# API:  http://localhost:8000
# UI:   http://localhost:8501
```

**5. Ingest and query**

Via the Streamlit UI (http://localhost:8501), or directly against the API:
```bash
curl -X POST localhost:8000/ingest -H "Content-Type: application/json" -d '{"demo": "legal"}'

curl -X POST localhost:8000/query -H "Content-Type: application/json" \
  -d '{"demo": "legal", "question": "What are the OSHA hazard communication requirements for chemicals?"}'
```

**Sample response** (`provider` defaults to `LLM_BACKEND` in `.env`; pass `"provider": "claude"` etc. to override per query):
```json
{
  "answer": "## Employer Requirements for Chemical Hazard Communication\n\n**Chemical Inventory & Labeling:** Keep a current list of hazardous chemicals in the workplace and ensure containers are properly labeled with hazard warnings [Source: osha_employer_responsibilities_handbook.pdf | Page 11 | Version 1].\n\n**Safety Data Sheets:** Make Safety Data Sheets available to workers, readily accessible without leaving their work area [Source: osha_hazard_communication.pdf | Page 7 | Version 1].\n\n**Governing Standard:** These requirements fall under 29 CFR 1910.1200, aligned with the UN Globally Harmonized System (GHS) [Source: osha_hazard_communication.pdf | Page 7 | Version 1].",
  "sources": [
    {"text": "...", "source": "osha_hazard_communication.pdf", "page": 7, "version": 1, "score": 1.0}
  ]
}
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Lists configured demos |
| `/ingest` | POST | `{"demo": "legal"}` -- ingest all files in that demo's `data_dir`, skipping unchanged ones |
| `/sync` | POST | Re-runs the demo's fetch script, then ingests -- picks up updated source documents |
| `/query` | POST | `{"demo", "question", "top_k", "provider"}` -- returns a cited answer and its source chunks |
| `/documents/{demo}` | GET | Lists ingested documents with version and status |

## Included Demos

This repo ships three pre-configured demos, selectable by `demo` name (`demos/registry.py`):

- **`legal`** -- Legal & HR compliance assistant over OSHA/DOL/EEOC/FTC/SBA public guidance (this README's focus)
- **`medical`** -- Medical research literature assistant over PubMed papers, with contradiction flagging across sources and explicit no-clinical-advice guardrails
- **`tech_support`** -- Technical documentation assistant over FastAPI's public docs

Each demo is a `DemoConfig` (`demos/__init__.py`) pairing a system prompt, a data directory, and a fetch script. Adapting to a new document set means writing a new `DemoConfig` and fetch script -- the retrieval and generation pipeline is shared.

## Case Study

See [case-study.md](./case-study.md) for the full scenario walkthrough.

---

> Client names and identifying details in this case study are fictional.
> The problem structure, workflow logic, and solution approach are based on real-world patterns from actual engagements.
