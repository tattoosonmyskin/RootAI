# Use official Python slim image for a smaller security footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for neo4j and building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the spaCy model for the Prompt Analyzer
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the API with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
