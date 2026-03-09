# MCAT AI Tutor — Design Note

**Author:** MCAT AI Tutor Prototype  
**Version:** 0.1.0  
**Stack:** Python · LangChain · ChromaDB · OpenAI / Qwen3-Embedding-4B · Streamlit

---

## 1. How I Chunked the Documents

### Strategy: Recursive Character Splitter with Section-Aware Headers

**Chunk size:** 500 tokens (~2 000 characters), **overlap:** 50 tokens.

**Why 500 tokens?**  
MCAT passages explaining one concept (e.g., Bernoulli's principle) run ~150–300 words. At 500 tokens, a single chunk can hold one complete concept, its derivation, and a worked example without spilling into adjacent material. Smaller chunks (≤ 200 tokens) fragment equations from their surrounding explanation; larger chunks (≥ 800) dilute the retrieval signal.

**Why overlap?**  
50-token overlap ensures that sentences spanning a chunk boundary are not lost. For example, "…therefore pressure decreases [CHUNK 1 END]. This is the key MCAT trap [CHUNK 2 START]…" — without overlap, the causal link is severed.

**Split hierarchy (ordered by preference):**  
`\n\n` → `\n` → `. ` → `, ` → ` ` → `""`  
Paragraph boundaries are preferred, falling back to sentences, then words. Equations are kept intact because they rarely contain `\n\n`.

**Math preservation:**  
PyMuPDF extracts text character-by-character, which can fragment equations. Before chunking:
- Unicode superscripts/subscripts → ASCII (e.g., `r²` → `r^2`, `P₁` → `P1`)  
- Greek letters → named form (`ρ` → `rho`, `η` → `eta`)  
- Math operators → ASCII equivalents (`×` → `*`, `≥` → `>=`)  
- Soft hyphens + zero-width spaces removed  
- Hyphenated line-breaks rejoined (`Bern-\noulli` → `Bernoulli`)

**Section anchoring:**  
Each chunk carries the detected section heading from its source page prepended to the first chunk of that page. This allows the LLM to understand context (e.g., "BERNOULLI'S EQUATION section") even when the heading itself isn't in the retrieved text.

---

## 2. How Retrieval Works

### Vector Store: ChromaDB (cosine similarity, sqlite3 persistence)

ChromaDB replaced FAISS for three reasons:
1. **Automatic persistence** — no explicit `save()` step; the collection is written to `data/vector_store/chroma.sqlite3` during `build_from_chunks()`.
2. **Cosine similarity by default** — scores are 0.0–1.0 (higher = more similar), which is more intuitive than FAISS L2 distances.
3. **Metadata filtering** — ChromaDB's `where` clause allows future filtering by source, page, or difficulty without re-building the index.

### Embedding Backends (three options)

| Backend | Model | Dim | Notes |
|---|---|---|---|
| `openai` | text-embedding-3-small | 1 536 | Default; fast, requires API key |
| `local` | all-MiniLM-L6-v2 | 384 | sentence-transformers; CPU-friendly |
| `qwen3` | Qwen3-Embedding-4B | 2 560 | Highest quality; instruction-aware; ~8 GB VRAM |

**Qwen3-Embedding-4B** uses last-token pooling with cosine normalization. Queries are prefixed with a task instruction (`"Instruct: Given a question about MCAT Fluid Dynamics, retrieve the most relevant passage that answers it.\nQuery: "`) so the model understands retrieval intent. Passages are encoded without a prefix. This instruction-following design consistently improves retrieval quality on domain-specific corpora compared to sentence-transformers.

### Query Flow

```
Student question
    → embed_query()                          # backend-dependent (API or local)
    → ChromaDB similarity_search_with_relevance_scores(k=4)
    → top-4 chunks with cosine similarity scores (0–1)
    → formatted into context block
    → injected into LLM system prompt
```

**Persistence:** `data/vector_store/chroma.sqlite3` is written on first ingest and re-opened on subsequent runs. Re-ingestion is only needed when the document corpus or embedding model changes.

**top-K = 4:** 4 chunks (~2 000 tokens of context) provide sufficient retrieval coverage while staying well within GPT-4o-mini's context window and keeping prompt costs low.

---

## 3. How Explanation Style Is Controlled

### Structured Prompt Engineering

The system prompt hard-codes a **5-section template**:

| Section | Purpose |
|---|---|
| **Toolkit** | List the 3–5 equations/concepts needed |
| **Think It Through** | Step-by-step logic, tutor voice |
| **Analogy** | One concrete everyday analogy |
| **MCAT Trap** | The single most common student mistake |
| **Memory Rule** | ≤15-word recall hook |

The LLM is instructed to use these as exact headings so they can be reliably parsed and rendered in the UI.

### Mode System

Five explanation modes, injected as additional instructions after the base system prompt:

| Mode | Trigger phrases | Modification |
|---|---|---|
| `standard` | (default) | No modification |
| `simpler` | "simpler", "easier", "eli5" | Shorter sentences, heavier analogy, jargon-free |
| `tighter` | "tight", "brief", "concise" | Max 2–3 sentences per section |
| `another_way` | "another way", "different way" | Reframe from a different starting point |
| `analogy` | "analogy", "another analogy" | Lead with rich analogy, downplay equations |

Modes are auto-detected from natural language (regex keyword matching) or can be explicitly selected in the UI dropdown.

### Temperature

- Explanations: `temperature=0.4` — creative enough for varied analogies, grounded enough to stay factually accurate.  
- Question generation: `temperature=0.6` — more diversity in question stems and distractors.

### LLM-as-Judge

The evaluation suite uses **`gpt-5-nano`** as the judge model for the `--use-llm-judge` evaluation path. This model scores generated answers against reference answers on a 0–4 scale (normalized to 0.0–1.0). `gpt-5-nano` was chosen for its combination of low cost and sufficient reasoning ability for structured scoring tasks.

---

## 4. What I Would Improve With More Time

### Retrieval Quality
- **Hybrid search:** Combine dense (ChromaDB cosine) retrieval with BM25 sparse retrieval. Many students ask exact equation names ("Poiseuille's law") which sparse search handles better than dense embeddings.
- **Cross-encoder reranking:** Add a small cross-encoder (e.g., `ms-marco-MiniLM-L-6-v2`) to rerank the top-20 candidates before passing top-4 to the LLM. This typically improves Hit@4 by 5–15%.
- **ChromaDB metadata filtering:** Leverage ChromaDB's `where` clause to filter by source (Princeton vs. ExamKrackers) when the user specifies it, or by page range for targeted retrieval.
- **Qwen3 at higher precision:** Running `Qwen3-Embedding-4B` at fp32 on multi-GPU would unlock its full embedding quality while keeping retrieval latency acceptable.

### Document Parsing
- **Table and figure extraction:** PyMuPDF's `get_text("text")` misses equations in image-based figures. Adding OCR (Tesseract or AWS Textract) for math-heavy pages would recover ~10–15% of MCAT-critical content.
- **PDF-to-markdown:** Tools like `marker` (PDF → Markdown with LaTeX) preserve equation structure far better than raw text extraction.

### Generation Quality
- **Conversation memory:** Currently, each question is stateless. Adding a short conversation buffer (last 2–3 turns) would allow follow-up questions ("Now explain that more simply") without re-stating context.
- **Citation grounding:** Force the LLM to cite which retrieved chunk each claim comes from, reducing hallucination risk.
- **MCAT-specific fine-tuning:** Even light fine-tuning (20–30 examples) on the desired tutor voice would improve style consistency significantly.

### Evaluation
- **Human preference evaluation:** Ground-truth Q&A pairs are hand-crafted from curriculum knowledge. Ideally, 3–5 MCAT tutors would rate responses on a Likert scale to produce human-preference labels.
- **RAGAS integration:** Use RAGAS (`faithfulness`, `answer_relevancy`, `context_precision`) for automated end-to-end RAG evaluation.
- **Regression tests in CI/CD:** Any prompt or chunking change should be automatically validated against the eval suite before deployment.

### Infrastructure
- **Async generation:** Stream LLM responses token-by-token in Streamlit using `stream=True` for a much better UX (no waiting spinner).
- **Caching:** Cache (question, mode) → answer pairs with a TTL to avoid repeated API calls for identical queries.
- **Hosted vector store:** For production scale, migrate from ChromaDB sqlite to a hosted Chroma server, Qdrant, or Pinecone for concurrent access and horizontal scaling.
