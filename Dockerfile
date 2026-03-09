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

# Install system dependencies for PyMuPDF and potential OCR support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
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

# Expose Streamlit default port
EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set the entrypoint to run Streamlit
ENTRYPOINT ["streamlit", "run", "app.py"]

# Default Streamlit configuration
CMD ["--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
