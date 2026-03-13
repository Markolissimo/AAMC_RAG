# Deployment Guide

## Prerequisites

Before deploying to Render, you must convert the base PDFs to markdown files locally:

```bash
# 1. Ensure you have LLAMA_CLOUD_API_KEY in your .env file
# 2. Run the conversion script
python scripts/convert_base_pdfs.py
```

This will create:
- `docs/Source-EK Fluid Dynamics.md`
- `docs/Source-Princeton Fluid Dynamics.md`

These markdown files will be included in the Docker image and serve as the base knowledge base.

## Deploy to Render

### Option 1: Deploy via Render Dashboard

1. **Connect your GitHub repository** to Render
2. **Create a new Web Service**
3. **Select "Docker" as the environment**
4. **Set environment variables** in the Render dashboard:
   - `OPENAI_API_KEY` (required)
   - `LLAMA_CLOUD_API_KEY` (required for PDF uploads)
5. **Deploy** — Render will automatically use `render.yaml` configuration

### Option 2: Deploy via render.yaml (Blueprint)

1. Push your code to GitHub (ensure base `.md` files are committed)
2. In Render dashboard, click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will read `render.yaml` and create the service
5. Set the secret environment variables:
   - `OPENAI_API_KEY`
   - `LLAMA_CLOUD_API_KEY`

### Render Configuration Details

- **Plan**: Starter ($7/month) — sufficient for demo/testing
- **Region**: Oregon (us-west)
- **Persistent Disk**: 1GB mounted at `/app/data` for vector store
- **Health Check**: `/_stcore/health` (Streamlit built-in)
- **Auto-deploy**: Enabled on push to `main` branch

## Local Development with Docker

### Using Docker Compose

```bash
# 1. Create .env file with your API keys
cp .env.example .env
# Edit .env and add your keys

# 2. Build and run
docker-compose up --build

# 3. Access the app
open http://localhost:8501
```

### Using Docker directly

```bash
# Build
docker build -t mcat-tutor .

# Run
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  -e LLAMA_CLOUD_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  mcat-tutor
```

## Environment Variables

### Required
- `OPENAI_API_KEY` — OpenAI API key for LLM and embeddings
- `LLAMA_CLOUD_API_KEY` — LlamaCloud API key for PDF OCR

### Optional (with defaults)
- `LLM_MODEL` (default: `gpt-4o-mini`)
- `EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- `CHUNK_SIZE` (default: `500`)
- `CHUNK_OVERLAP` (default: `50`)
- `TOP_K_RETRIEVAL` (default: `4`)

## Troubleshooting

### Base documents not showing up
- Ensure you ran `python scripts/convert_base_pdfs.py` before building
- Check that `docs/Source-*.md` files exist and are committed to git
- Verify `.dockerignore` is not excluding them

### Vector store not persisting
- On Render: check that the disk is properly mounted at `/app/data`
- Locally: ensure the volume is mounted in docker-compose.yml

### Out of memory errors
- Increase memory limits in `render.yaml` or upgrade Render plan
- Reduce `TOP_K_RETRIEVAL` or `CHUNK_SIZE` to lower memory usage

### Reranking not working
- FlashRank model (~22MB) downloads on first use to `~/.cache/flashrank`
- Ensure sufficient disk space on Render (1GB disk should be enough)
