# Base stage with common dependencies
FROM python:3.12-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    UV_SYSTEM_PYTHON=1 \
    UV_HTTP_TIMEOUT=300

# Install system dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Create necessary directories
RUN mkdir -p /app/data/chroma /app/cache/pdfs /app/cache/metadata /app/models

# API stage
FROM base AS api

# Copy API source code
COPY src/ ./src/
COPY .env* ./

# Expose API port
EXPOSE 8000

# Run the FastAPI application using uv
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# UI stage
FROM base AS ui

# Install UI dependencies (optional extra)
RUN uv sync --frozen --extra ui

# Copy UI source code
COPY ui/ ./ui/

# Set PYTHONPATH to include /app for ui imports
ENV PYTHONPATH=/app

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit application using uv
CMD ["uv", "run", "streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
