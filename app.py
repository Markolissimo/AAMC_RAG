"""
MCAT AI Tutor — Streamlit Application

Two modes:
  1. Explanation Engine (Task 1): answer + explain fluids questions in tutor style
  2. MCAT Question Generator (Task 2): generate full MCQ with tutor-style explanation

Run:
    streamlit run app.py
"""

from __future__ import annotations

import os
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
# Lazy pipeline import (avoids import errors before deps are installed)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="⚙️ Loading pipeline…")
def get_pipeline():
    from src.rag_pipeline import RAGPipeline
    pipeline = RAGPipeline()
    pipeline.ingest()
    return pipeline

def _show_runtime_error(error: Exception) -> None:
    message = str(error)

    if (
        "requires OCR" in message
        or "Tesseract" in message
        or "No chunks were produced for ingestion" in message
    ):
        st.error(
            "OCR required: your source PDFs appear to be scanned/image-based, so the app cannot ingest them yet."
        )
        st.markdown(
            """
**How to fix it**

- Install **Tesseract OCR** on Windows
- Make sure `tesseract` is available on your `PATH`
- Delete the existing `data/vector_store` folder if it was created during a failed ingest
- Restart the Streamlit app and try again
            """
        )
        with st.expander("Show technical details"):
            st.code(message)
        return

    st.error(f"Error: {message}")

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main title */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1rem;
        color: #555;
        margin-bottom: 1.5rem;
    }

    /* Source citation pill */
    .source-pill {
        display: inline-block;
        background: #e8f4f8;
        border: 1px solid #b3d9e8;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.78rem;
        color: #2c6e8a;
        margin: 2px;
    }

    /* Section cards */
    .section-card {
        background: #f8f9ff;
        border-left: 4px solid #4a6cf7;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    }
    .section-card.trap {
        border-left-color: #e74c3c;
        background: #fff5f5;
    }
    .section-card.memory {
        border-left-color: #27ae60;
        background: #f0fff4;
    }
    .section-card.analogy {
        border-left-color: #f39c12;
        background: #fffbf0;
    }

    /* MCQ choice buttons */
    .choice-row {
        background: #f5f5f5;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 4px 0;
        font-size: 0.95rem;
    }
    .choice-row.correct {
        background: #d4edda;
        border: 1px solid #28a745;
    }

    /* Metric badges */
    .metric-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }
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
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    openai_key = st.text_input(
        "OpenAI API Key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="sk-… key. Set OPENAI_API_KEY env var to avoid re-entering.",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    model_choice = st.selectbox(
        "LLM Model",
        ["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="gpt-4o-mini is faster and cheaper; gpt-4o gives higher quality.",
    )
    os.environ["LLM_MODEL"] = model_choice

    embedding_backend = st.selectbox(
        "Embedding Backend",
        ["openai", "local", "qwen3"],
        index=0,
        help=(
            "**openai** → text-embedding-3-small (API key required). "
            "**local** → all-MiniLM-L6-v2 (no key, fast, 384-dim). "
            "**qwen3** → Qwen3-Embedding-4B (no key, high quality, ~8 GB VRAM)."
        ),
    )
    if embedding_backend == "qwen3":
        st.caption("⚠️ Qwen3-Embedding-4B requires ~8 GB VRAM (GPU) or ~12 GB RAM (CPU). First load downloads ~8 GB.")
    os.environ["EMBEDDING_BACKEND"] = embedding_backend

    top_k = st.slider("Retrieved chunks (top-K)", min_value=2, max_value=8, value=4, step=1)
    os.environ["TOP_K_RETRIEVAL"] = str(top_k)

    st.divider()
    st.caption("📄 **Knowledge Base**")
    docs_path = Path("docs")
    if docs_path.exists():
        for pdf in docs_path.glob("*.pdf"):
            st.caption(f"• {pdf.name}")

    st.divider()
    _backend_labels = {"openai": "text-embedding-3-small", "local": "all-MiniLM-L6-v2", "qwen3": "Qwen3-Embedding-4B"}
    st.caption(f"🔢 Embeddings: `{_backend_labels.get(embedding_backend, embedding_backend)}`")
    st.caption(f"🧠 LLM: `{model_choice}`")
    st.caption("v0.1.0 — MCAT Fluid Dynamics RAG Prototype")


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_explain, tab_mcq, tab_eval = st.tabs([
    "💬 Explanation Engine",
    "❓ MCAT Question Generator",
    "📊 Evaluation",
])


# ===========================================================================
# TAB 1 — Explanation Engine
# ===========================================================================
with tab_explain:
    st.subheader("💬 Explanation Engine")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        user_question = st.text_input(
            "Your question",
            placeholder="e.g. Explain Bernoulli's principle in simpler terms.",
            label_visibility="collapsed",
        )

    with col_right:
        mode_override = st.selectbox(
            "Mode",
            ["Auto-detect", "Standard", "Simpler", "Tighter", "Another Way", "New Analogy"],
            label_visibility="collapsed",
        )

    # Quick example prompts
    st.caption("💡 Try:")
    example_cols = st.columns(4)
    examples = [
        "Explain Bernoulli's principle.",
        "Why does fluid move faster in a narrow pipe?",
        "Explain buoyancy in simpler terms.",
        "Give another analogy for Pascal's principle.",
    ]
    for i, (col, ex) in enumerate(zip(example_cols, examples)):
        with col:
            if st.button(ex, key=f"ex_{i}", use_container_width=True):
                user_question = ex

    explain_btn = st.button("🔍 Explain", type="primary", use_container_width=False)

    if explain_btn or (user_question and st.session_state.get("_explain_triggered")):
        if not openai_key and embedding_backend == "openai":
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        elif not user_question.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("🧠 Thinking…"):
                try:
                    pipeline = get_pipeline()

                    _mode_map = {
                        "Auto-detect": None,
                        "Standard":    "standard",
                        "Simpler":     "simpler",
                        "Tighter":     "tighter",
                        "Another Way": "another_way",
                        "New Analogy": "analogy",
                    }
                    t0 = time.perf_counter()

                    if mode_override == "Auto-detect":
                        result = pipeline.explain_auto(user_question)
                    else:
                        result = pipeline.explain(user_question, mode=_mode_map[mode_override])

                    elapsed = time.perf_counter() - t0

                    # ---- Display answer ----
                    st.success(f"✅ Generated in {elapsed:.1f}s  |  Mode: **{result.mode.value}**  |  Model: **{result.model}**")
                    st.divider()
                    st.markdown(result.answer)

                    # ---- Sources expander ----
                    with st.expander(f"📚 Retrieved Sources ({len(result.sources)} chunks)"):
                        for i, src in enumerate(result.sources, 1):
                            meta = src["metadata"]
                            source_label = f"{meta.get('source', '?')} · p.{meta.get('page', '?')} · score: {src['score']:.3f}"
                            st.markdown(f"**[{i}]** `{source_label}`")
                            st.text(src["text"][:400] + ("…" if len(src["text"]) > 400 else ""))
                            st.divider()

                except Exception as e:
                    _show_runtime_error(e)


# ===========================================================================
# TAB 2 — MCAT Question Generator
# ===========================================================================
with tab_mcq:
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
        generate_btn = st.button("⚡ Generate Question", type="primary", use_container_width=True)

    # Quick topic buttons
    st.caption("💡 Quick topics:")
    topic_cols = st.columns(5)
    quick_topics = ["buoyancy", "Bernoulli's principle", "Poiseuille's law", "Pascal's principle", "hydrostatic pressure"]
    for i, (col, topic) in enumerate(zip(topic_cols, quick_topics)):
        with col:
            if st.button(topic, key=f"topic_{i}", use_container_width=True):
                mcq_topic = topic

    if generate_btn or st.session_state.get("_mcq_triggered"):
        if not openai_key and embedding_backend == "openai":
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        elif not mcq_topic.strip():
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("⚡ Generating MCAT question…"):
                try:
                    pipeline = get_pipeline()
                    t0 = time.perf_counter()
                    mcq = pipeline.generate_question(mcq_topic)
                    elapsed = time.perf_counter() - t0

                    st.success(f"✅ Generated in {elapsed:.1f}s  |  Model: **{mcq.model}**")
                    st.divider()

                    # Question stem
                    st.markdown("### 📝 Question")
                    st.info(mcq.question_stem)

                    # Answer choices
                    st.markdown("### 🔠 Answer Choices")
                    answer_cols = st.columns(2)
                    letters = ["A", "B", "C", "D"]
                    for idx, letter in enumerate(letters):
                        choice_text = mcq.choices.get(letter, "—")
                        is_correct = letter == mcq.correct_answer.upper()
                        col = answer_cols[idx % 2]
                        with col:
                            if is_correct:
                                st.success(f"**{letter})** {choice_text} ✓")
                            else:
                                st.markdown(f"**{letter})** {choice_text}")

                    # Correct answer callout
                    st.markdown("### ✅ Correct Answer")
                    st.success(
                        f"**{mcq.correct_answer}** — {mcq.correct_rationale}"
                    )

                    # Full explanation
                    st.markdown("### 🎓 Tutor Explanation")
                    st.markdown(mcq.explanation)

                    # Sources
                    with st.expander(f"📚 Retrieved Sources ({len(mcq.sources)} chunks)"):
                        for i, src in enumerate(mcq.sources, 1):
                            meta = src["metadata"]
                            label = f"{meta.get('source', '?')} · p.{meta.get('page', '?')}"
                            st.markdown(f"**[{i}]** `{label}`")
                            st.text(src["text"][:300] + ("…" if len(src["text"]) > 300 else ""))

                except Exception as e:
                    _show_runtime_error(e)


# ===========================================================================
# TAB 3 — Evaluation Dashboard
# ===========================================================================
with tab_eval:
    st.subheader("📊 Evaluation Dashboard")
    st.caption(
        "Run the evaluation suite against the 10 explanation Q&A pairs and 5 MCQ "
        "generation pairs. Scores are computed without an LLM judge by default "
        "(pure heuristic metrics)."
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
        if not openai_key and embedding_backend == "openai":
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        else:
            with st.spinner("🔬 Running evaluation suite…"):
                try:
                    from evaluation.evaluator import Evaluator
                    pipeline = get_pipeline()
                    evaluator = Evaluator(pipeline, use_llm_judge=use_llm_judge)
                    results = evaluator.run_all(
                        qa_id=qa_filter.strip() or None,
                        save=True,
                    )

                    summary = results["summary"]
                    exp_res = results["explanation_results"]
                    mcq_res = results["mcq_results"]

                    # ---- Summary metrics ----
                    st.markdown("#### 📘 Explanation Engine Summary")
                    e = summary["explanation"]
                    m_cols = st.columns(4)
                    m_cols[0].metric("Hit@K", f"{e['hit_at_k']:.0%}" if e['hit_at_k'] else "—")
                    m_cols[1].metric("Avg MRR", f"{e['avg_mrr']:.3f}" if e['avg_mrr'] else "—")
                    m_cols[2].metric("Style Score", f"{e['avg_style_score']:.3f}" if e['avg_style_score'] else "—")
                    m_cols[3].metric("Overall", f"{e['avg_overall_score']:.3f}" if e['avg_overall_score'] else "—")

                    st.markdown("#### ❓ MCQ Generator Summary")
                    m = summary["mcq_generation"]
                    m_cols2 = st.columns(4)
                    m_cols2[0].metric("Structure OK", f"{m['structure_ok_rate']:.0%}" if m['structure_ok_rate'] is not None else "—")
                    m_cols2[1].metric("Distractor Cov.", f"{m['avg_distractor_coverage']:.3f}" if m['avg_distractor_coverage'] else "—")
                    m_cols2[2].metric("Section Cov.", f"{m['avg_section_coverage']:.3f}" if m['avg_section_coverage'] else "—")
                    m_cols2[3].metric("Avg Latency", f"{m['avg_latency_s']:.1f}s" if m['avg_latency_s'] else "—")

                    # ---- Per-sample table ----
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

                except Exception as e:
                    st.error(f"❌ Evaluation error: {e}")

    # Show last results if available
    results_dir = Path("data/eval_results")
    if results_dir.exists():
        json_files = sorted(results_dir.glob("eval_*.json"), reverse=True)
        if json_files:
            with st.expander(f"📂 Previous results ({len(json_files)} runs)"):
                for f in json_files[:5]:
                    st.caption(f"• {f.name}")
