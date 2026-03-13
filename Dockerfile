# MCAT AI Tutor — Dockerfile
# Multi-stage build for optimized image size

# ---------------------------------------------------------------------------
# Stage 1: Base Python image with system dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 2: Dependencies installation
# ---------------------------------------------------------------------------
FROM base as dependencies

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 3: Application
# ---------------------------------------------------------------------------
FROM dependencies as application

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/vector_store data/eval_results

# Expose Streamlit port (Render will set PORT env var)
EXPOSE 8501

# Render uses PORT env var; default to 8501 for local dev
ENV PORT=8501

# Run Streamlit with dynamic port from environment
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
