# MCAT AI Tutor — Design Note

**Author:** MCAT AI Tutor Prototype  
**Version:** 0.1.0  
**Stack:** Python · LangChain · ChromaDB · OpenAI · LlamaCloud · Streamlit

---

## 1. How I Chunked the Documents

### OCR: LlamaCloud Agentic Tier

PDF ingestion uses **LlamaCloud** (`llama-cloud` SDK, agentic tier) instead of PyMuPDF. The agentic tier:
- Handles scanned, image-based, and complex-layout PDFs reliably
- Returns full-document markdown (`markdown_full`) and per-page markdown (`pages[]`)
- Saves the full markdown to `docs/<stem>.md` for persistence and inspection

Each ingested PDF is registered in two JSON tables (`data/documents.json`, `data/pages.json`) with unique UUIDs:
- **Document record**: `{doc_id, filename, created_at, md_path, page_count}`
- **Page records**: `{page_id, doc_id, page_number, text_preview}`

### Strategy: Recursive Character Splitter on Markdown

**Chunk size:** 500 tokens (~2 000 characters), **overlap:** 50 tokens.

**Why 500 tokens?**  
MCAT passages explaining one concept (e.g., Bernoulli's principle) run ~150–300 words. At 500 tokens, a single chunk can hold one complete concept, its derivation, and a worked example without spilling into adjacent material.

**Why overlap?**  
50-token overlap ensures that sentences spanning a chunk boundary are not lost.

**Split hierarchy (ordered by preference):**  
`\n\n` → `\n` → `. ` → `, ` → ` ` → `""`  
Markdown paragraph boundaries are preferred, falling back to sentences, then words.

**Chunk metadata:**  
Each chunk carries `doc_id` and `page_id` UUIDs from the registry, enabling traceability from any retrieved chunk back to its source document and page.

**Section anchoring:**  
The first detected heading-like line from each page is prepended to the first chunk of that page, preserving section context in retrieval.

---

## 2. How Retrieval Works

### Vector Store: ChromaDB (cosine similarity, sqlite3 persistence)

ChromaDB replaced FAISS for three reasons:
1. **Automatic persistence** — no explicit `save()` step; the collection is written to `data/vector_store/chroma.sqlite3` during `build_from_chunks()`.
2. **Cosine similarity by default** — scores are 0.0–1.0 (higher = more similar), which is more intuitive than FAISS L2 distances.
3. **Metadata filtering** — ChromaDB's `where` clause allows future filtering by source, page, or difficulty without re-building the index.

### Embedding Backend

Only the OpenAI backend is used:

| Backend | Model | Dim | Notes |
|---|---|---|---|
| `openai` | text-embedding-3-small | 1 536 | Fast, high quality, requires API key |

This simplifies the dependency footprint significantly — `sentence-transformers`, `torch`, and `transformers` are no longer required.

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

### Sovereign Teaching Voice

The system prompt enforces an **analogy-first, equation-last** teaching structure. The student must understand the concept intuitively before seeing the math. This is the "Sovereign tutor" voice requested by the client: equations appear only as confirmation, never as the opening move.

The system prompt hard-codes a **6-section template**:

| Section | Purpose |
|---|---|
| *(opening — no heading)* | Short analogy or intuition, no equations, first thing the student reads |
| **Core idea** | Core concept in plain language, no equations |
| **Simple picture** | 2–3 line visual using arrows/bullets showing the relationship |
| **MCAT concept** | Equation introduced here — as confirmation of prior intuition |
| **Another analogy** | Second everyday analogy reinforcing from a different angle |
| **The Hook** | Scaffolding tease in quotes inviting the student to go deeper |

The LLM is explicitly forbidden from opening with an equation or a textbook definition.

### Simpler Mode — Gold Standard Flow

When the student says "simpler", the output uses a stripped-down 3-part structure (no standard sections):

1. One short intuitive sentence (no heading, no equation)
2. **Simple analogy** — ≤3 bullet points, plain language only
3. **The Hook** — scaffolding tease

### Mode System

Five explanation modes, injected as additional instructions after the base system prompt:

| Mode | Trigger phrases | Modification |
|---|---|---|
| `standard` | (default) | No modification |
| `simpler` | "simpler", "easier", "eli5" | Stripped to 3 parts: intuition → Simple analogy → The Hook |
| `tighter` | "tight", "brief", "concise" | 1–2 sentences per section, same 6-section order |
| `another_way` | "another way", "different way" | Reframe opening analogy and Core idea from a different angle |
| `analogy` | "analogy", "another analogy" | Lead with rich new analogy; expand Another analogy; end with The Hook |

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
- **Alternative embeddings:** Swapping `text-embedding-3-small` for `text-embedding-3-large` (3072-dim) would improve retrieval at higher cost.

### Document Parsing
- **LlamaCloud tier upgrade:** Switching from `agentic` to `agentic_plus` tier may improve accuracy on heavily mathematical or hand-written pages.
- **Per-page chunking:** Currently the chunker splits per page and then recursively. Future work could preserve markdown heading structure for semantic splits.

### Generation Quality
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
