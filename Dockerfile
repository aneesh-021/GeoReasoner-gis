# Dockerfile for GeoReasoner GIS Chatbot
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0

# Avoid interactive prompts during builds
ENV DEBIAN_FRONTEND=noninteractive

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    grass \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Create virtual environment and install Python packages
RUN python3 -m venv .venv \
    && . .venv/bin/activate \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose Ollama port (if using Ollama for LLM)
EXPOSE 11434

# Default command: Start Ollama in background + run your app
CMD . .venv/bin/activate && \
    ollama serve & \
    sleep 5 && \
    python main.py  # Replace 'main.py' with your entrypoint script