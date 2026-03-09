# MCAT AI Tutor — Fluid Dynamics RAG Prototype

A Retrieval-Augmented Generation (RAG) system that answers MCAT Fluid Dynamics questions and generates MCAT-style practice questions in a structured tutor voice.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Run the Streamlit app
```bash
streamlit run app.py
```

On first launch the system automatically ingests the two PDFs in `docs/`, embeds all chunks, and builds the ChromaDB vector store (~30–60s). Subsequent launches load from disk instantly.

---

## Docker Setup

### Prerequisites
- Docker Engine 20.10+ and Docker Compose v2.0+
- For GPU support (Qwen3 embeddings): NVIDIA Docker runtime

### Quick Start with Docker

**1. Create `.env` file with your API key:**
```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY=sk-...
```

**2. Build and run with docker-compose:**
```bash
docker-compose up -d
```

**3. Access the app:**
Open http://localhost:8501 in your browser.

**4. View logs:**
```bash
docker-compose logs -f mcat-tutor
```

**5. Stop the container:**
```bash
docker-compose down
```

### Configuration via Environment Variables

All configuration can be passed via `.env` file or `docker-compose.yml`:

```bash
# .env file
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EMBEDDING_BACKEND=openai          # or: local, qwen3
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=4
```

### Using Local Embeddings (No API Key for Embeddings)

Edit `docker-compose.yml` to use `local` backend:
```yaml
environment:
  - EMBEDDING_BACKEND=local
  - EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Then rebuild:
```bash
docker-compose up -d --build
```

### GPU Support for Qwen3 Embeddings

Uncomment the `mcat-tutor-gpu` service in `docker-compose.yml` and run:
```bash
docker-compose up mcat-tutor-gpu -d
```

Requires NVIDIA Docker runtime installed.

### Persistent Data

Vector store and evaluation results are persisted in Docker volumes:
- `vector_store` → `/app/data/vector_store`
- `eval_results` → `/app/data/eval_results`

To reset the vector store:
```bash
docker-compose down -v
docker-compose up -d
```

### Building the Image Manually

```bash
# Build
docker build -t mcat-ai-tutor .

# Run
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  -v $(pwd)/data/vector_store:/app/data/vector_store \
  mcat-ai-tutor
```

---

## Project Structure

```
AAMC_test_task/
├── docs/                              # Source PDFs (Princeton Review + ExamKrackers)
├── data/vector_store/                 # ChromaDB persistence (auto-created)
│   ├── chroma.sqlite3
│   └── <uuid>/
├── src/
│   ├── ingestion/
│   │   ├── pdf_parser.py              # PDF → text with math normalization (PyMuPDF)
│   │   └── chunker.py                 # 500-token recursive chunks with section anchoring
│   ├── retrieval/
│   │   ├── embeddings.py              # OpenAI / LocalEmbedder / Qwen3Embedder
│   │   └── vector_store.py            # ChromaDB wrapper (cosine similarity, auto-persist)
│   ├── generation/
│   │   ├── prompts.py                 # System prompts + 5 explanation modes
│   │   ├── explanation_engine.py      # Task 1: tutor-style explanation
│   │   └── question_generator.py      # Task 2: MCAT MCQ generation + parsing
│   └── rag_pipeline.py                # Top-level orchestrator
├── evaluation/
│   ├── qa_pairs.py                    # 10 explanation + 5 MCQ ground-truth pairs
│   ├── metrics.py                     # Retrieval (Hit@K, MRR) + generation metrics
│   └── evaluator.py                   # Full eval runner → CSV/JSON reports
├── tests/
│   ├── test_ingestion.py              # PDF parser + chunker unit tests
│   ├── test_retrieval.py              # ChromaDB store unit tests (mock embedder)
│   ├── test_generation.py             # Explanation engine + MCQ generator tests (mock LLM)
│   └── test_evaluation.py             # Metrics + Q&A dataset integrity tests
├── app.py                             # Streamlit UI (3 tabs)
├── design_note.md                     # Architecture decisions + improvement roadmap
├── requirements.txt
└── .env.example
```

---

## Running Tests

All tests run **without an API key** (mock embedder + mock LLM):

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_evaluation.py -v

# Run with coverage
pytest tests/ --cov=src --cov=evaluation --cov-report=term-missing
```

---

## Running the Evaluation Suite

```bash
# Heuristic metrics only (no API cost)
python -m evaluation.evaluator

# With LLM-as-judge (uses gpt-5-nano, ~$0.01 per run)
python -m evaluation.evaluator --use-llm-judge

# Single Q&A pair
python -m evaluation.evaluator --qa-id exp_001
```

Results are saved to `data/eval_results/` as JSON and CSV.

---

## Evaluation Metrics

### Retrieval
| Metric | Description |
|---|---|
| **Hit@K** | Does at least 1 of top-K chunks contain a relevant keyword? |
| **MRR** | Mean Reciprocal Rank of first relevant chunk |
| **Precision@K** | Fraction of top-K chunks that are relevant |
| **Keyword Coverage** | Fraction of expected keywords found in retrieved context |

### Generation (Explanation)
| Metric | Description |
|---|---|
| **Section Coverage** | Fraction of expected structural sections present (Toolkit, Analogy, etc.) |
| **Concept Coverage** | Fraction of expected key concepts/equations mentioned |
| **Style Score** | Average of section + concept coverage |
| **LLM Correctness** | LLM-as-judge score via `gpt-5-nano` (0–4 → 0.0–1.0) vs. reference answer |

### MCQ Generation
| Metric | Description |
|---|---|
| **Structure OK** | All 4 choices (A–D) present + correct answer is a valid letter |
| **Distractor Coverage** | Expected misconceptions represented in wrong answer choices |
| **Section Coverage** | Required sections (Question, Choices, Correct Answer, Explanation) present |

---

## Explanation Modes

| Mode | Trigger | Description |
|---|---|---|
| `standard` | Default | Full tutor voice, all 5 sections |
| `simpler` | "simpler", "easier", "eli5" | Shorter sentences, minimal jargon, heavy analogy |
| `tighter` | "tight", "brief", "concise" | ≤3 sentences per section |
| `another_way` | "another way", "reframe" | Different conceptual angle |
| `analogy` | "analogy", "another analogy" | Lead with vivid new analogy |

---

## Embedding Backends

Three backends are available, selected via `EMBEDDING_BACKEND` env var or the Streamlit sidebar:

| Backend | Model | Dim | Requires | Notes |
|---|---|---|---|---|
| `openai` | text-embedding-3-small | 1536 | API key | Default, fast, cost ~$0.0001/1K tokens |
| `local` | all-MiniLM-L6-v2 | 384 | None | Lightweight, CPU-friendly, sentence-transformers |
| `qwen3` | Qwen3-Embedding-4B | 2560 | ~8 GB VRAM | Highest quality, local, instruction-aware |

### Qwen3-Embedding-4B details
- Model ID: `Qwen/Qwen3-Embedding-4B` (HuggingFace)
- Last-token pooling with cosine normalization
- Queries prefixed with a retrieval instruction; passages encoded without prefix
- Requires `torch>=2.1.0` and `transformers>=4.51.0`
- First run downloads ~8 GB of model weights

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required for OpenAI embeddings + LLM |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model (`gpt-4o-mini` or `gpt-4o`) |
| `EMBEDDING_BACKEND` | `openai` | `openai`, `local`, or `qwen3` |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name (auto-set per backend) |
| `CHUNK_SIZE` | `500` | Chunk size in tokens |
| `CHUNK_OVERLAP` | `50` | Chunk overlap in tokens |
| `TOP_K_RETRIEVAL` | `4` | Number of chunks to retrieve |
| `VECTOR_STORE_PATH` | `./data/vector_store` | ChromaDB persistence directory |

---

## Fully Local Setup (No API Key)

```bash
# In .env — use local or Qwen3 embeddings
EMBEDDING_BACKEND=local          # or qwen3 for higher quality
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

The LLM (`ChatOpenAI`) still requires an OpenAI key. For a fully offline setup, replace `ChatOpenAI` in `src/generation/` with an Ollama-backed model.

---

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| **PDF parsing** | PyMuPDF (fitz) | Best math/equation text extraction; unicode normalization |
| **Chunking** | LangChain RecursiveCharacterTextSplitter | Respects paragraph/sentence boundaries |
| **Embeddings** | text-embedding-3-small / all-MiniLM-L6-v2 / Qwen3-Embedding-4B | Three backends for different cost/quality tradeoffs |
| **Vector store** | ChromaDB (cosine, sqlite3 persistence) | Auto-persists, metadata filtering, no manual save step |
| **LLM** | GPT-4o-mini (default) | Best cost/quality ratio for structured output |
| **LLM judge** | gpt-5-nano | Fastest/cheapest model for automated evaluation scoring |
| **Framework** | LangChain | Standard RAG orchestration |
| **UI** | Streamlit | Rapid prototype, supports markdown rendering |
| **Tests** | pytest | Mock-based, no API dependency required |
