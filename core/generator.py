import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

_BASE_SYSTEM = """You are a precise document retrieval assistant. Answer questions using ONLY the provided context documents.

Citation format: [Source: {source} | Page {page} | Version {version}]

Rules:
- Every factual claim must include a citation in the exact format above
- NUMBERS AND AMOUNTS: Copy every dollar amount, percentage, date, and numeric value VERBATIM from the context. If the context states $275.13, you write $275.13 — never $2.13 or any other value. Your training knowledge about typical values is IRRELEVANT and must be ignored. Do NOT add warnings, caveats, or notes suggesting a number from the document seems unusual, high, or low — the document is authoritative.
- Do not complete, paraphrase, or reconstruct sentences that appear cut off in the context — quote only what is fully present.
- Make direct inferences from dates and facts in the context (e.g. if someone completed a presidential term in March 1970, it is correct to state they served as president in 1969)
- Do not introduce any fact that cannot be derived from the context
- If the context genuinely contains no relevant information, say so explicitly
- Keep answers concise but complete"""

# Default models per provider
_MODELS = {
    "claude":  os.getenv("CLAUDE_MODEL",  "claude-sonnet-4-6"),
    "openai":  os.getenv("OPENAI_MODEL",  "gpt-4o-mini"),
    "gemini":  os.getenv("GEMINI_MODEL",  "gemini-1.5-flash"),
    "ollama":  os.getenv("OLLAMA_MODEL",  "gemma3:27b"),
}

_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@dataclass
class GenerationResult:
    answer: str
    provider: str
    model: str


def available_providers() -> list[dict]:
    """Return providers that have credentials configured."""
    providers = []
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append({"id": "claude",  "label": f"Claude · {_MODELS['claude']}",  "model": _MODELS["claude"]})
    if os.getenv("OPENAI_API_KEY"):
        providers.append({"id": "openai",  "label": f"OpenAI · {_MODELS['openai']}", "model": _MODELS["openai"]})
    if os.getenv("GOOGLE_API_KEY"):
        providers.append({"id": "gemini",  "label": f"Gemini · {_MODELS['gemini']}", "model": _MODELS["gemini"]})
    # Ollama needs no key — always listed
    providers.append({"id": "ollama", "label": f"Ollama · {_MODELS['ollama']} (local)", "model": _MODELS["ollama"]})
    return providers


def generate(query: str, chunks: list[dict], system_prompt: str = "", provider: str = "") -> str:
    return _dispatch(query, chunks, system_prompt, provider).answer


def generate_with_meta(query: str, chunks: list[dict], system_prompt: str = "", provider: str = "") -> GenerationResult:
    return _dispatch(query, chunks, system_prompt, provider)


def _dispatch(query: str, chunks: list[dict], system_prompt: str, provider: str) -> GenerationResult:
    p = (provider or os.getenv("LLM_BACKEND", "claude")).lower()
    user_msg = _build_user_message(query, chunks, system_prompt)
    if p == "openai":
        return _openai(user_msg)
    if p == "gemini":
        return _gemini(user_msg)
    if p == "ollama":
        return _ollama(user_msg)
    return _claude(user_msg)


def _build_user_message(query: str, chunks: list[dict], extra: str) -> str:
    parts = [
        f"[{i}] Source: {c['source']} | Page {c['page']} | Version {c['version']}\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    ]
    ctx = "\n\n".join(parts)
    prefix = f"{extra}\n\n" if extra else ""
    return f"{prefix}Context:\n{ctx}\n\nQuestion: {query}"


def _claude(user_msg: str) -> GenerationResult:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = _MODELS["claude"]
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[{"type": "text", "text": _BASE_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    return GenerationResult(answer=resp.content[0].text, provider="claude", model=model)


def _openai(user_msg: str) -> GenerationResult:
    from openai import OpenAI
    model = _MODELS["openai"]
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _BASE_SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
    )
    return GenerationResult(answer=resp.choices[0].message.content, provider="openai", model=model)


def _gemini(user_msg: str) -> GenerationResult:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = _MODELS["gemini"]
    m = genai.GenerativeModel(model_name=model, system_instruction=_BASE_SYSTEM)
    resp = m.generate_content(user_msg)
    return GenerationResult(answer=resp.text, provider="gemini", model=model)


def _ollama(user_msg: str) -> GenerationResult:
    import httpx
    model = _MODELS["ollama"]
    resp = httpx.post(
        f"{_OLLAMA_BASE_URL}/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": _BASE_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return GenerationResult(answer=resp.json()["message"]["content"], provider="ollama", model=model)
