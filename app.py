"""
MCAT AI Tutor — Streamlit Application

Modes:
  1. Chat-based Explanation Engine: tutor-style answers with in-memory conversation
  2. MCAT Question Generator: generate MCQ with tutor-style explanation
  3. Evaluation Dashboard

Run:
    streamlit run app.py
"""

from __future__ import annotations

import os
import re
import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MCAT AI Tutor — Fluid Dynamics",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages: list[dict] = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing: bool = False
if "pipeline" not in st.session_state:
    st.session_state.pipeline = None
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded: str | None = None
if "session_uploaded_docs" not in st.session_state:
    st.session_state.session_uploaded_docs: list[str] = []  # doc_ids uploaded this session
if "upload_statuses" not in st.session_state:
    st.session_state.upload_statuses: dict = {}  # {fname: {status, doc_id, error}}


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def _get_or_init_pipeline():
    """Return the pipeline from session state, initialising it on first call."""
    if st.session_state.pipeline is None:
        from src.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline()
        pipeline.ingest()
        st.session_state.pipeline = pipeline
    return st.session_state.pipeline


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0; }
    .subtitle   { font-size: 1rem; color: #555; margin-bottom: 1.5rem; }
    .hint-row   { font-size: 0.78rem; color: #888; margin-top: 4px; }
    .source-pill {
        display: inline-block;
        background: #e8f4f8; border: 1px solid #b3d9e8;
        border-radius: 12px; padding: 2px 10px;
        font-size: 0.78rem; color: #2c6e8a; margin: 2px;
    }
    .metric-badge { display: inline-block; padding: 3px 8px; border-radius: 4px;
                    font-size: 0.78rem; font-weight: 600; margin: 2px; }
    .badge-green  { background: #d4edda; color: #155724; }
    .badge-yellow { background: #fff3cd; color: #856404; }
    .badge-red    { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<p class="main-title">🧪 MCAT AI Tutor</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Fluid Dynamics — Powered by RAG + GPT-4o-mini</p>', unsafe_allow_html=True)
st.divider()


# ---------------------------------------------------------------------------
# Sidebar — settings + PDF upload
# ---------------------------------------------------------------------------
with st.sidebar:
    # ---- Health Check ----
    if st.button("🏥 Check Server Health", use_container_width=True):
        import requests
        try:
            response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Server is healthy and running!")
            else:
                st.warning(f"⚠️ Server responded with status {response.status_code}")
        except requests.exceptions.RequestException:
            st.error("❌ Server is not responding. If deployed on Render, the server may be sleeping. Please wait ~1 minute for it to wake up, then try again.")
    
    st.divider()
    st.header("⚙️ Settings")

    model_choice = st.selectbox(
        "LLM Model",
        ["gpt-4o-mini", "gpt-4o"],
        index=0 if os.getenv("LLM_MODEL", "gpt-4o-mini") == "gpt-4o-mini" else 1,
        help="gpt-4o-mini is faster and cheaper; gpt-4o gives higher quality.",
    )
    os.environ["LLM_MODEL"] = model_choice

    top_k = st.slider("Retrieved chunks (top-K)", min_value=2, max_value=8, value=4, step=1)
    os.environ["TOP_K_RETRIEVAL"] = str(top_k)

    st.caption(f"🔢 Embeddings: `text-embedding-3-small`")
    st.caption(f"🧠 LLM: `{model_choice}`")
    st.caption("v0.2.0 — MCAT Fluid Dynamics RAG Prototype")
    st.divider()

    # ---- Document Upload ----
    st.markdown("### 📤 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF or Markdown files",
        type=["pdf", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # Queue newly-selected files that haven't been seen yet
    if uploaded_files:
        for f in uploaded_files:
            if f.name not in st.session_state.upload_statuses:
                is_pdf = f.name.lower().endswith(".pdf")
                if is_pdf and not llama_key:
                    st.error(f"⚠️ LlamaCloud API key required for '{f.name}'.")
                else:
                    st.session_state.upload_statuses[f.name] = {
                        "status": "queued",
                        "doc_id": None,
                        "error": None,
                    }

    # Per-file status list
    for fname, finfo in list(st.session_state.upload_statuses.items()):
        col_icon, col_name, col_btn = st.columns([1, 5, 1])
        short = fname if len(fname) <= 22 else fname[:19] + "…"
        fstatus = finfo["status"]
        with col_icon:
            if fstatus == "queued":
                st.markdown("⏳")
            elif fstatus == "processing":
                st.markdown("🔄")
            elif fstatus == "done":
                st.markdown("✅")
            else:
                st.markdown("❌")
        with col_name:
            st.caption(short)
            if fstatus == "error" and finfo.get("error"):
                st.caption(f"↳ {finfo['error'][:45]}")
        with col_btn:
            if fstatus == "done" and finfo.get("doc_id"):
                if st.button("🗑️", key=f"del_file_{fname}", help=f"Remove from knowledge base"):
                    pipeline = _get_or_init_pipeline()
                    doc_id = finfo["doc_id"]
                    pipeline.remove_document(doc_id)
                    del st.session_state.upload_statuses[fname]
                    if doc_id in st.session_state.session_uploaded_docs:
                        st.session_state.session_uploaded_docs.remove(doc_id)
                    st.rerun()

    # Process next queued/stuck-processing file (one per rerun)
    queued_names = [
        fn for fn, s in st.session_state.upload_statuses.items()
        if s["status"] in ("queued", "processing")
    ]
    if queued_names and uploaded_files:
        next_fname = queued_names[0]
        file_obj = next((f for f in uploaded_files if f.name == next_fname), None)
        if file_obj:
            st.session_state.upload_statuses[next_fname]["status"] = "processing"
            is_pdf = next_fname.lower().endswith(".pdf")
            tmp_path = None
            try:
                suffix = ".pdf" if is_pdf else ".md"
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix,
                    prefix=Path(next_fname).stem + "_",
                ) as tmp:
                    tmp.write(file_obj.read())
                    tmp_path = tmp.name
                pipeline = _get_or_init_pipeline()
                ocr_result = pipeline.ingest_document(
                    tmp_path,
                    llama_api_key=llama_key if is_pdf else None,
                )
                st.session_state.upload_statuses[next_fname]["status"] = "done"
                st.session_state.upload_statuses[next_fname]["doc_id"] = ocr_result.doc_id
                st.session_state.session_uploaded_docs.append(ocr_result.doc_id)
            except Exception as exc:
                st.session_state.upload_statuses[next_fname]["status"] = "error"
                st.session_state.upload_statuses[next_fname]["error"] = str(exc)
            finally:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)
            st.rerun()

    # Sync is_processing with queue state
    st.session_state.is_processing = any(
        s["status"] in ("queued", "processing")
        for s in st.session_state.upload_statuses.values()
    )

    st.divider()

    # ---- Knowledge Base ----
    st.markdown("### 📚 Knowledge Base")
    _SESSION_RE = re.compile(r'_[a-z0-9]{8}\.md$', re.IGNORECASE)
    _docs_dir = Path("docs")
    base_files = [
        f for f in sorted(_docs_dir.glob("*.md"))
        if not _SESSION_RE.search(f.name)
    ] if _docs_dir.exists() else []
    for f in base_files:
        st.caption(f"📄 {f.stem}")

    session_done = [
        (fname, finfo) for fname, finfo in st.session_state.upload_statuses.items()
        if finfo["status"] == "done"
    ]
    if session_done:
        st.caption("**This session:**")
        for fname, _ in session_done:
            st.caption(f"📎 {Path(fname).stem}")

    # ---- End Session button ----
    if st.session_state.session_uploaded_docs:
        if st.button("🗑️ End Session (Remove Uploads)", use_container_width=True):
            pipeline = _get_or_init_pipeline()
            for doc_id in st.session_state.session_uploaded_docs:
                pipeline.remove_document(doc_id)
            st.session_state.session_uploaded_docs = []
            st.session_state.upload_statuses = {}
            st.session_state.messages = []
            st.rerun()


# ---------------------------------------------------------------------------
# Processing guard — shown in tabs during upload
# ---------------------------------------------------------------------------
def _processing_banner() -> bool:
    """Show a banner and return True if the pipeline is currently processing."""
    if st.session_state.is_processing:
        st.info("⏳ Processing a PDF upload — please wait before using this tab.")
        return True
    return False


def _pipeline_ready_guard() -> bool:
    """Return True if the pipeline is ready, else show an upload prompt."""
    pipeline = _get_or_init_pipeline()
    if not pipeline.is_ready():
        st.info("📤 Upload a PDF in the sidebar to build the knowledge base first.")
        return False
    return True


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_explain, tab_mcq, tab_eval = st.tabs([
    "💬 Chat",
    "❓ MCAT Question Generator",
    "📊 Evaluation",
])


# ===========================================================================
# TAB 1 — Chat (Explanation Engine with in-memory conversation)
# ===========================================================================
with tab_explain:
    if _processing_banner():
        pass
    else:
        # ---- Header row ----
        col_title, col_clear = st.columns([5, 1])
        with col_title:
            st.subheader("💬 Chat")
        with col_clear:
            if st.button("🗑️ Clear", help="Clear conversation history"):
                st.session_state.messages = []
                st.rerun()

        # ---- Conversation history ----
        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                st.markdown(
                    "<div style='color:#aaa; text-align:center; padding:2rem 0'>"
                    "Ask a question below to start the conversation.</div>",
                    unsafe_allow_html=True,
                )
            for msg in st.session_state.messages:
                # User messages on right, assistant on left
                avatar = "🧑" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])
                    if msg.get("sources"):
                        with st.expander(f"📚 Sources ({len(msg['sources'])} chunks)", expanded=False):
                            for i, src in enumerate(msg["sources"], 1):
                                meta = src["metadata"]
                                label = (
                                    f"{meta.get('source', '?')} · "
                                    f"p.{meta.get('page', '?')} · "
                                    f"score: {src['score']:.3f}"
                                )
                                st.markdown(f"**[{i}]** `{label}`")
                                st.text(src["text"][:300] + ("…" if len(src["text"]) > 300 else ""))

        # ---- Chat input ----
        user_input = st.chat_input("Ask about fluid dynamics…")

        # ---- Sample queries (small, below input) ----
        st.markdown(
            "<div class='hint-row'>💡 Try: "
            "<i>Why does blood flow faster through a narrow artery?</i> &nbsp;·&nbsp; "
            "<i>Simpler please</i> &nbsp;·&nbsp; "
            "<i>Explain buoyancy</i> &nbsp;·&nbsp; "
            "<i>Give another analogy for Pascal's principle</i>"
            "</div>",
            unsafe_allow_html=True,
        )

        # ---- Handle submission ----
        if user_input:
            if not _pipeline_ready_guard():
                pass
            else:
                pipeline = _get_or_init_pipeline()

                # Append user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input,
                })

                # Show thinking indicator on left side
                with st.chat_message("assistant", avatar="🤖"):
                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown("_Thinking..._")
                    
                    try:
                        t0 = time.perf_counter()

                        # Build history (exclude the message we just appended)
                        history = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages[:-1]
                        ]

                        # Always use auto-detect mode
                        result = pipeline.explain_auto(user_input, history=history)

                        elapsed = time.perf_counter() - t0
                        answer_with_meta = (
                            result.answer
                            + f"\n\n<sub>Mode: **{result.mode.value}** · "
                            f"{elapsed:.1f}s · {result.model}</sub>"
                        )

                        # Clear thinking indicator and show actual response
                        thinking_placeholder.empty()

                        # Append assistant message
                        st.session_state.messages.append({
                            "role":    "assistant",
                            "content": answer_with_meta,
                            "sources": result.sources,
                        })

                    except Exception as exc:
                        thinking_placeholder.empty()
                        st.session_state.messages.append({
                            "role":    "assistant",
                            "content": f"❌ Error: {exc}",
                            "sources": [],
                        })

                st.rerun()


# ===========================================================================
# TAB 2 — MCAT Question Generator
# ===========================================================================
with tab_mcq:
    if _processing_banner():
        pass
    else:
        st.subheader("❓ MCAT Question Generator")
        st.caption(
            "Enter a topic and the system will generate a full MCAT-style question "
            "with 4 answer choices, correct answer, and a tutor-style explanation."
        )

        mcq_col1, mcq_col2 = st.columns([3, 1])
        with mcq_col1:
            mcq_topic = st.text_input(
                "Topic",
                placeholder="e.g. buoyancy, Bernoulli's principle, Poiseuille's law…",
                label_visibility="collapsed",
                key="mcq_topic",
            )
        with mcq_col2:
            generate_btn = st.button("⚡ Generate", type="primary", use_container_width=True)

        # Quick topic buttons
        st.caption("💡 Quick topics:")
        topic_cols = st.columns(5)
        quick_topics = ["buoyancy", "Bernoulli", "Poiseuille's law", "Pascal's principle", "hydrostatic pressure"]
        for i, (col, topic) in enumerate(zip(topic_cols, quick_topics)):
            with col:
                if st.button(topic, key=f"topic_{i}", use_container_width=True):
                    mcq_topic = topic

        if generate_btn:
            if not mcq_topic.strip():
                st.warning("Please enter a topic first.")
            elif not _pipeline_ready_guard():
                pass
            else:
                pipeline = _get_or_init_pipeline()
                with st.spinner("⚡ Generating MCAT question…"):
                    try:
                        t0 = time.perf_counter()
                        mcq = pipeline.generate_question(mcq_topic)
                        elapsed = time.perf_counter() - t0

                        st.success(f"✅ Generated in {elapsed:.1f}s  |  Model: **{mcq.model}**")
                        st.divider()

                        st.markdown("### 📝 Question")
                        st.info(mcq.question_stem)

                        st.markdown("### 🔠 Answer Choices")
                        answer_cols = st.columns(2)
                        for idx, letter in enumerate(["A", "B", "C", "D"]):
                            choice_text = mcq.choices.get(letter, "—")
                            is_correct = letter == mcq.correct_answer.upper()
                            with answer_cols[idx % 2]:
                                if is_correct:
                                    st.success(f"**{letter})** {choice_text} ✓")
                                else:
                                    st.markdown(f"**{letter})** {choice_text}")

                        st.markdown("### ✅ Correct Answer")
                        st.success(f"**{mcq.correct_answer}** — {mcq.correct_rationale}")

                        st.markdown("### 🎓 Tutor Explanation")
                        st.markdown(mcq.explanation)

                        with st.expander(f"📚 Retrieved Sources ({len(mcq.sources)} chunks)"):
                            for i, src in enumerate(mcq.sources, 1):
                                meta = src["metadata"]
                                label = f"{meta.get('source', '?')} · p.{meta.get('page', '?')}"
                                st.markdown(f"**[{i}]** `{label}`")
                                st.text(src["text"][:300] + ("…" if len(src["text"]) > 300 else ""))

                    except Exception as exc:
                        st.error(f"❌ Error: {exc}")


# ===========================================================================
# TAB 3 — Evaluation Dashboard
# ===========================================================================
with tab_eval:
    if _processing_banner():
        pass
    else:
        st.subheader("📊 Evaluation Dashboard")
        st.caption(
            "Run the evaluation suite against the 10 explanation Q&A pairs and 5 MCQ "
            "generation pairs. Scores are computed without an LLM judge by default."
        )

        use_llm_judge = st.toggle(
            "Use LLM-as-judge for generation scoring (slower, costs API calls)",
            value=False,
        )

        eval_col1, eval_col2 = st.columns([2, 1])
        with eval_col1:
            run_eval_btn = st.button("▶️ Run Full Evaluation", type="primary")
        with eval_col2:
            qa_filter = st.text_input("Filter by Q&A id (optional)", placeholder="exp_001")

        if run_eval_btn:
            if not _pipeline_ready_guard():
                pass
            else:
                pipeline = _get_or_init_pipeline()
                with st.spinner("🔬 Running evaluation suite…"):
                    try:
                        from evaluation.evaluator import Evaluator
                        evaluator = Evaluator(pipeline, use_llm_judge=use_llm_judge)
                        results = evaluator.run_all(
                            qa_id=qa_filter.strip() or None,
                            save=True,
                        )

                        summary = results["summary"]
                        exp_res = results["explanation_results"]
                        mcq_res = results["mcq_results"]

                        st.markdown("#### 📘 Explanation Engine Summary")
                        e = summary["explanation"]
                        m_cols = st.columns(4)
                        m_cols[0].metric("Hit@K",       f"{e['hit_at_k']:.0%}"         if e['hit_at_k']          else "—")
                        m_cols[1].metric("Avg MRR",     f"{e['avg_mrr']:.3f}"           if e['avg_mrr']           else "—")
                        m_cols[2].metric("Style Score", f"{e['avg_style_score']:.3f}"   if e['avg_style_score']   else "—")
                        m_cols[3].metric("Overall",     f"{e['avg_overall_score']:.3f}" if e['avg_overall_score'] else "—")

                        st.markdown("#### ❓ MCQ Generator Summary")
                        m = summary["mcq_generation"]
                        m_cols2 = st.columns(4)
                        m_cols2[0].metric("Structure OK",     f"{m['structure_ok_rate']:.0%}"        if m['structure_ok_rate']       is not None else "—")
                        m_cols2[1].metric("Distractor Cov.",  f"{m['avg_distractor_coverage']:.3f}"  if m['avg_distractor_coverage'] else "—")
                        m_cols2[2].metric("Section Cov.",     f"{m['avg_section_coverage']:.3f}"     if m['avg_section_coverage']    else "—")
                        m_cols2[3].metric("Avg Latency",      f"{m['avg_latency_s']:.1f}s"           if m['avg_latency_s']           else "—")

                        if exp_res:
                            import pandas as pd
                            st.markdown("#### Per-sample Explanation Results")
                            display_keys = [
                                "id", "topic", "difficulty", "hit_at_k", "mrr",
                                "keyword_coverage", "section_coverage", "concept_coverage",
                                "style_score", "overall_score", "latency_s",
                            ]
                            df = pd.DataFrame([
                                {k: r.get(k) for k in display_keys}
                                for r in exp_res if "error" not in r
                            ])
                            st.dataframe(df, use_container_width=True)

                        if mcq_res:
                            import pandas as pd
                            st.markdown("#### Per-sample MCQ Generation Results")
                            mcq_keys = [
                                "id", "topic", "difficulty", "structure_ok",
                                "correct_answer_valid", "distractor_coverage",
                                "section_coverage", "latency_s",
                            ]
                            df_mcq = pd.DataFrame([
                                {k: r.get(k) for k in mcq_keys}
                                for r in mcq_res if "error" not in r
                            ])
                            st.dataframe(df_mcq, use_container_width=True)

                        st.info("Results saved to `data/eval_results/`")

                    except Exception as exc:
                        st.error(f"❌ Evaluation error: {exc}")

        results_dir = Path("data/eval_results")
        if results_dir.exists():
            json_files = sorted(results_dir.glob("eval_*.json"), reverse=True)
            if json_files:
                with st.expander(f"📂 Previous results ({len(json_files)} runs)"):
                    for f in json_files[:5]:
                        st.caption(f"• {f.name}")
