import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from core.ingestion import ingest_directory
from core.retriever import retrieve
from core.generator import generate_with_meta
from core.doc_registry import list_docs
from core.observability import track_query, render_prometheus
from demos.registry import ALL_DEMOS, get_demo

app = FastAPI(
    title="Niche RAG API",
    description="Privacy-first niche RAG demo system. Supports Claude API and Ollama backends.",
    version="1.0.0",
)



# --- Request / Response models ---

class IngestRequest(BaseModel):
    demo: str  # "medical" | "legal" | "tech_support"


class IngestResult(BaseModel):
    demo: str
    files_processed: int
    results: list[dict]


class QueryRequest(BaseModel):
    demo: str
    question: str
    top_k: int = 5
    provider: str = ""


class Source(BaseModel):
    text: str
    source: str
    page: int
    version: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    provider: str
    attempts: list[str]
    sources: list[Source]


class DocumentInfo(BaseModel):
    filename: str
    version: int
    ingested_at: str
    status: str
    source_url: str | None = None


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok", "demos": list(ALL_DEMOS.keys())}


@app.post("/ingest", response_model=IngestResult)
def ingest(req: IngestRequest):
    demo = get_demo(req.demo)
    if not Path(demo.data_dir).exists():
        raise HTTPException(
            status_code=400,
            detail=f"Data directory '{demo.data_dir}' not found. Run the fetch script first: python {demo.fetch_script}",
        )
    results = ingest_directory(demo.data_dir, demo.collection)
    return IngestResult(demo=req.demo, files_processed=len(results), results=results)


@app.post("/sync", response_model=IngestResult)
def sync(req: IngestRequest):
    """Re-fetch source data then re-ingest. Detects and processes updated documents."""
    demo = get_demo(req.demo)
    script = demo.fetch_script
    if not script or not Path(script).exists():
        raise HTTPException(status_code=400, detail=f"No fetch script configured for demo '{req.demo}'")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Fetch script failed:\n{result.stderr}")
    results = ingest_directory(demo.data_dir, demo.collection)
    return IngestResult(demo=req.demo, files_processed=len(results), results=results)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    demo = get_demo(req.demo)
    with track_query(req.demo) as info:
        chunks = retrieve(demo.collection, req.question, top_k=req.top_k)
        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found. Make sure data has been ingested first.",
            )
        try:
            result = generate_with_meta(
                req.question, chunks, system_prompt=demo.system_prompt, provider=req.provider
            )
        except RuntimeError as exc:
            info["attempts"] = getattr(exc, "attempts", [])
            raise HTTPException(status_code=502, detail=str(exc))

        info["provider"] = result.provider
        info["attempts"] = result.attempts
        info["success"] = True

    sources = [
        Source(
            text=c["text"],
            source=c["source"],
            page=c["page"],
            version=c["version"],
            score=c["score"],
        )
        for c in chunks
    ]
    return QueryResponse(answer=result.answer, provider=result.provider, attempts=result.attempts, sources=sources)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_prometheus()


@app.get("/documents/{demo}", response_model=list[DocumentInfo])
def documents(demo: str):
    cfg = get_demo(demo)
    docs = list_docs(cfg.collection)
    return [
        DocumentInfo(
            filename=d["filename"],
            version=d["version"],
            ingested_at=d["ingested_at"],
            status=d["status"],
            source_url=d.get("source_url"),
        )
        for d in docs
    ]
