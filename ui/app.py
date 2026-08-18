import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import html
import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Platform",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & globals ── */
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }
.stApp { background: #F7F7F6 !important; }

/* ── Preserve Material Icons — must NOT inherit Inter or ligatures render as text ── */
.material-icons,
[class*="material-icons"] {
    font-family: 'Material Icons' !important;
    font-size: 20px !important;
    font-style: normal !important;
    font-weight: normal !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    -webkit-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stToolbar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton              { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Main content area ── */
.main .block-container {
    padding: 1.5rem 2.5rem 2rem !important;
    max-width: 900px !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid #21262D !important;
}
section[data-testid="stSidebar"] > div:first-child {
    background: #0D1117 !important;
    padding-top: 0 !important;
}

/* Sidebar text */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label { color: #8B949E !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #E6EDF3 !important; }
section[data-testid="stSidebar"] .stMarkdown p { font-size: 12px !important; }

/* Sidebar selectbox */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    color: #C9D1D9 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] svg { color: #8B949E !important; }

/* Sidebar slider */
section[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {
    background: #7C3AED !important;
    border-color: #7C3AED !important;
}
section[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stTickBar"] + div > div {
    background: #7C3AED !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #C9D1D9 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 6px 12px !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #21262D !important;
    border-color: #7C3AED !important;
    color: #E6EDF3 !important;
}

/* ── Main area buttons (example questions) — light card style ── */
.main .stButton > button,
[data-testid="stMain"] .stButton > button {
    background: #FFFFFF !important;
    border: 1.5px solid #E9E8F0 !important;
    color: #374151 !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    text-align: left !important;
    white-space: normal !important;
    padding: 10px 14px !important;
    line-height: 1.45 !important;
    height: auto !important;
    min-height: 52px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: all 0.15s ease !important;
}
.main .stButton > button:hover,
[data-testid="stMain"] .stButton > button:hover {
    border-color: #7C3AED !important;
    color: #6D28D9 !important;
    background: #F5F3FF !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.08) !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border: 1px solid #EBEBEA !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
[data-testid="stChatMessage"] p { font-size: 14px !important; line-height: 1.65 !important; color: #1A1A1A !important; }

/* ── Chat input — nuke every layer of the dark container ── */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div,
[data-testid="stBottom"] > div > div > div,
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInputContainer"],
[data-testid="stChatInputContainer"] > div {
    background: #F7F7F6 !important;
    background-color: #F7F7F6 !important;
    box-shadow: none !important;
    border: none !important;
    border-radius: 0 !important;
}
[data-testid="stBottom"] {
    border-top: 1px solid #E5E5E4 !important;
    padding: 16px 0 20px !important;
}
[data-testid="stChatInputTextArea"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #DDD9E3 !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    color: #1A1A1A !important;
    padding: 14px 16px !important;
    min-height: 52px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInputTextArea"]:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
    outline: none !important;
}
[data-testid="stChatInputSubmitButton"] > button {
    background: #7C3AED !important;
    border-radius: 10px !important;
    border: none !important;
}

/* ── Expanders (sources panel) ── */
[data-testid="stExpander"] {
    border: 1px solid #EEEEED !important;
    border-radius: 10px !important;
    background: #FAFAF9 !important;
}
[data-testid="stExpander"] summary { font-size: 12px !important; color: #6B7280 !important; font-weight: 500 !important; }
[data-testid="stExpander"] summary:hover { color: #7C3AED !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    padding: 8px 16px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #7C3AED !important;
    border-bottom-color: #7C3AED !important;
}

/* ── Metrics (doc status) ── */
[data-testid="stMetric"] { background: #161B22; border-radius: 8px; padding: 8px 12px; }
[data-testid="stMetric"] label { color: #8B949E !important; font-size: 11px !important; }
[data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 18px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    return html.escape(str(text))

def _provider_badge(provider: str, model: str) -> str:
    icons = {"claude": "◆", "openai": "◇", "gemini": "◈", "ollama": "◉"}
    icon = icons.get(provider, "◈")
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:#F5F3FF;color:#6D28D9;border:1px solid #DDD6FE;'
        f'border-radius:20px;padding:2px 10px;font-size:11px;font-weight:500;">'
        f'{icon} {_esc(model)}</span>'
    )

def _source_card(src: dict, index: int) -> str:
    fname = _esc(src["source"])
    score_pct = int(src["score"] * 100)
    excerpt = _esc(src["text"][:280]) + ("…" if len(src["text"]) > 280 else "")
    return f"""
<div style="
    background:#FAFAFF;
    border:1px solid #EDE9FE;
    border-left:3px solid #7C3AED;
    border-radius:8px;
    padding:10px 14px;
    margin:6px 0;
">
  <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">
    <span style="width:18px;height:18px;background:#7C3AED;color:#fff;border-radius:50%;
                 display:inline-flex;align-items:center;justify-content:center;
                 font-size:10px;font-weight:700;flex-shrink:0;">{index}</span>
    <code style="background:#EDE9FE;color:#5B21B6;border-radius:4px;
                 padding:1px 6px;font-size:11px;max-width:260px;
                 overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{fname}</code>
    <span style="background:#7C3AED;color:#fff;border-radius:20px;
                 padding:1px 8px;font-size:10px;font-weight:600;">p.{src['page']}</span>
    <span style="background:#DCFCE7;color:#166534;border-radius:20px;
                 padding:1px 8px;font-size:10px;font-weight:500;">v{src['version']}</span>
    <span style="margin-left:auto;font-size:10px;color:#9CA3AF;">{score_pct}% match</span>
  </div>
  <p style="font-size:12px;color:#4B5563;line-height:1.55;margin:0;
            font-style:italic;border-top:1px solid #EDE9FE;padding-top:6px;">{excerpt}</p>
</div>"""


def _sidebar_label(text: str) -> None:
    st.sidebar.markdown(
        f'<p style="font-size:10px;font-weight:600;letter-spacing:.08em;'
        f'color:#4B5563;text-transform:uppercase;margin:16px 0 6px;">{text}</p>',
        unsafe_allow_html=True,
    )


# ── Sidebar ────────────────────────────────────────────────────────────────────

# Logo
st.sidebar.markdown("""
<div style="padding:20px 4px 16px;border-bottom:1px solid #21262D;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:32px;height:32px;background:linear-gradient(135deg,#7C3AED,#4F46E5);
                border-radius:8px;display:flex;align-items:center;justify-content:center;
                font-size:16px;color:#fff;flex-shrink:0;">◈</div>
    <div>
      <div style="font-size:14px;font-weight:700;color:#E6EDF3;line-height:1.2;">RAG Platform</div>
      <div style="font-size:11px;color:#4B5563;">Document Intelligence</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Provider selection
_sidebar_label("AI Provider")
try:
    from core.generator import available_providers
    providers = available_providers()
except Exception:
    providers = [{"id": "claude", "label": "Claude (default)", "model": "claude-sonnet-4-6"}]

provider_labels = [p["label"] for p in providers]
if "provider_idx" not in st.session_state:
    st.session_state.provider_idx = 0

selected_idx = st.sidebar.selectbox(
    "provider",
    options=range(len(providers)),
    format_func=lambda i: providers[i]["label"],
    index=st.session_state.provider_idx,
    label_visibility="collapsed",
)
st.session_state.provider_idx = selected_idx
selected_provider = providers[selected_idx]

# Sources slider
_sidebar_label("Retrieval")
top_k = st.sidebar.slider("Sources to fetch", min_value=3, max_value=12, value=5, label_visibility="visible")

# Knowledge base controls
st.sidebar.markdown('<div style="border-top:1px solid #21262D;margin:16px 0 8px;"></div>', unsafe_allow_html=True)
_sidebar_label("Knowledge Base")

col1, col2 = st.sidebar.columns(2)
with col1:
    ingest_clicked = st.button("⬇ Ingest", help="Load documents into vector store")
with col2:
    sync_clicked = st.button("↺ Sync", help="Re-fetch source data and detect updates")

if ingest_clicked:
    with st.sidebar:
        with st.spinner("Ingesting…"):
            try:
                r = httpx.post(f"{API_BASE}/ingest", json={"demo": "legal"}, timeout=300)
                r.raise_for_status()
                data = r.json()
                n_in = sum(1 for x in data["results"] if x["status"] == "ingested")
                n_sk = sum(1 for x in data["results"] if x["status"] == "skipped")
                st.success(f"{n_in} ingested · {n_sk} unchanged")
            except Exception as e:
                st.error(str(e))

if sync_clicked:
    with st.sidebar:
        with st.spinner("Syncing…"):
            try:
                r = httpx.post(f"{API_BASE}/sync", json={"demo": "legal"}, timeout=600)
                r.raise_for_status()
                data = r.json()
                n_in = sum(1 for x in data["results"] if x["status"] == "ingested")
                n_sk = sum(1 for x in data["results"] if x["status"] == "skipped")
                st.success(f"{n_in} updated · {n_sk} unchanged")
            except Exception as e:
                st.error(str(e))

# Document list
st.sidebar.markdown('<div style="border-top:1px solid #21262D;margin:16px 0 8px;"></div>', unsafe_allow_html=True)
_sidebar_label("Documents")
try:
    r = httpx.get(f"{API_BASE}/documents/legal", timeout=5)
    docs = r.json() if r.status_code == 200 else []
except Exception:
    docs = []

if docs:
    for doc in docs:
        status_dot = "🟢" if doc["status"] == "current" else "🟡"
        fname_short = doc["filename"][:28] + "…" if len(doc["filename"]) > 28 else doc["filename"]
        st.sidebar.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:4px 2px;">'
            f'<span style="font-size:11px;color:#8B949E;overflow:hidden;text-overflow:ellipsis;'
            f'white-space:nowrap;max-width:160px;" title="{_esc(doc["filename"])}">'
            f'{status_dot} {_esc(fname_short)}</span>'
            f'<span style="font-size:10px;color:#4B5563;flex-shrink:0;margin-left:4px;">v{doc["version"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.sidebar.markdown(
        '<p style="font-size:11px;color:#4B5563;padding:4px 2px;">No documents ingested yet.</p>',
        unsafe_allow_html=True,
    )


# ── Main area ──────────────────────────────────────────────────────────────────

# Header
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding-bottom:16px;border-bottom:1px solid #E5E5E4;margin-bottom:20px;">
  <div>
    <h2 style="font-size:18px;font-weight:700;color:#111;margin:0;line-height:1.3;">
      Legal &amp; HR Document Assistant
    </h2>
    <p style="font-size:12px;color:#9CA3AF;margin:2px 0 0;">
      OSHA · DOL · FMLA · FLSA · exact citations · {len(docs)} documents loaded
    </p>
  </div>
  <div style="display:flex;align-items:center;gap:8px;">
    {_provider_badge(selected_provider["id"], selected_provider["model"])}
  </div>
</div>
""", unsafe_allow_html=True)

# Chat input must be called at top level (no container context) so Streamlit
# pins it to the viewport bottom. Reading question here makes it available
# inside with tab_chat below without re-opening the context manager.
prefill = st.session_state.pop("pending_query", None)
question = st.chat_input("Ask a question about your documents…") or prefill

# Tabs
tab_chat, tab_docs = st.tabs(["💬  Chat", "📄  Documents"])


# ── Chat tab ──────────────────────────────────────────────────────────────────
with tab_chat:

    # Session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_provider" not in st.session_state:
        st.session_state.last_provider = selected_provider["id"]

    # Example queries (shown when chat is empty)
    if not st.session_state.messages:
        st.markdown("""
<div style="text-align:center;padding:40px 20px 24px;">
  <div style="font-size:32px;margin-bottom:12px;">◈</div>
  <p style="font-size:15px;font-weight:600;color:#374151;margin-bottom:4px;">
    Ask anything about your documents
  </p>
  <p style="font-size:13px;color:#9CA3AF;margin-bottom:24px;">
    Every answer cites the exact source, page, and version
  </p>
</div>""", unsafe_allow_html=True)

        cols = st.columns(2)
        try:
            from demos.registry import get_demo as _get_demo
            example_qs = _get_demo("legal").example_queries[:4]
        except Exception:
            example_qs = []
        for i, q in enumerate(example_qs):
            with cols[i % 2]:
                if st.button(q, key=f"ex_{i}", use_container_width=True):
                    st.session_state.pending_query = q
                    st.rerun()

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                label = f"📚 {len(msg['sources'])} sources · {msg.get('provider_label', '')}"
                with st.expander(label, expanded=False):
                    cards_html = "".join(
                        _source_card(s, i + 1)
                        for i, s in enumerate(msg["sources"])
                    )
                    st.markdown(cards_html, unsafe_allow_html=True)

    # Handle new question (question set at top level before st.tabs())
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating answer…"):
                try:
                    r = httpx.post(
                        f"{API_BASE}/query",
                        json={
                            "demo": "legal",
                            "question": question,
                            "top_k": top_k,
                            "provider": selected_provider["id"],
                        },
                        timeout=120,
                    )
                    r.raise_for_status()
                    data = r.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    attempts = data.get("attempts", [])

                    st.markdown(answer)

                    provider_label = selected_provider["label"]
                    fell_back = len(attempts) > 1
                    if fell_back:
                        st.caption(
                            f"⚠ {selected_provider['id']} was unavailable, answered by "
                            f"**{data['provider']}** instead ({' → '.join(attempts)})"
                        )
                    label = f"📚 {len(sources)} sources · {provider_label}"
                    with st.expander(label, expanded=True):
                        cards_html = "".join(
                            _source_card(s, i + 1) for i, s in enumerate(sources)
                        )
                        st.markdown(cards_html, unsafe_allow_html=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "provider_label": provider_label,
                    })
                except httpx.HTTPStatusError as e:
                    detail = e.response.json().get("detail", str(e))
                    st.error(f"API error: {detail}")
                except Exception as e:
                    st.error(f"Could not reach API. Is it running? ({e})")


# ── Documents tab ─────────────────────────────────────────────────────────────
with tab_docs:
    if not docs:
        st.markdown("""
<div style="text-align:center;padding:60px 20px;">
  <p style="font-size:15px;font-weight:600;color:#374151;margin-bottom:4px;">No documents ingested</p>
  <p style="font-size:13px;color:#9CA3AF;">Use the ⬇ Ingest button in the sidebar to load documents.</p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<p style="font-size:12px;color:#9CA3AF;margin-bottom:16px;">'
            f'{len(docs)} document{"s" if len(docs) != 1 else ""} in the knowledge base</p>',
            unsafe_allow_html=True,
        )
        for doc in docs:
            status_color = "#059669" if doc["status"] == "current" else "#D97706"
            status_label = doc["status"].capitalize()
            with st.expander(f"{doc['filename']}  ·  v{doc['version']}", expanded=False):
                c1, c2, c3 = st.columns(3)
                c1.markdown(
                    f'<div style="text-align:center;">'
                    f'<div style="font-size:22px;font-weight:700;color:#7C3AED;">v{doc["version"]}</div>'
                    f'<div style="font-size:11px;color:#9CA3AF;">Version</div></div>',
                    unsafe_allow_html=True,
                )
                c2.markdown(
                    f'<div style="text-align:center;">'
                    f'<div style="font-size:14px;font-weight:600;color:{status_color};">{status_label}</div>'
                    f'<div style="font-size:11px;color:#9CA3AF;">Status</div></div>',
                    unsafe_allow_html=True,
                )
                c3.markdown(
                    f'<div style="text-align:center;">'
                    f'<div style="font-size:14px;font-weight:600;color:#374151;">{doc["ingested_at"][:10]}</div>'
                    f'<div style="font-size:11px;color:#9CA3AF;">Last Ingested</div></div>',
                    unsafe_allow_html=True,
                )
