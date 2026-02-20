# Use a lightweight Python image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# --- CONFIGURATION ---
ENV UV_PROJECT_ENVIRONMENT="/usr/local"
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install base dependencies
RUN uv sync --no-install-project

RUN uv pip install --system \
    "langgraph==0.2.20" \
    "langchain-core>=0.2.39,<0.3.0" \
    "langchain-openai<0.2.0" \
    "langchain<0.3.0"

# Copy application code
COPY . .