# RootAI v3.0 Dockerfile
# Multi-stage build for optimized deployment

FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Environment variable to control GPU usage (default: false for CPU)
ARG ROOTAI_USE_GPU=false
ENV ROOTAI_USE_GPU=${ROOTAI_USE_GPU}

# Install Python dependencies based on GPU usage
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    if [ "$ROOTAI_USE_GPU" = "true" ]; then \
        echo "Installing GPU dependencies..." && \
        pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu118 && \
        pip install --no-cache-dir faiss-gpu; \
    else \
        echo "Installing CPU dependencies..." && \
        pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
        pip install --no-cache-dir faiss-cpu; \
    fi && \
    pip install --no-cache-dir transformers camel-tools && \
    pip install --no-cache-dir fastapi uvicorn[standard] pydantic numpy scipy nltk sentencepiece datasets

# Production stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/
COPY api/ /app/api/
COPY data/ /app/data/
COPY pyproject.toml /app/

# Create data directory for models and cache
RUN mkdir -p /app/data /app/models /app/cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
# Default to CPU mode - set ROOTAI_USE_GPU=true for GPU
ARG ROOTAI_USE_GPU=false
ENV ROOTAI_USE_GPU=${ROOTAI_USE_GPU}

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8080"]
