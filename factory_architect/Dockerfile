FROM python:3.11-slim-bookworm

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Libs
COPY requirements.txt .
# Filter requirements to only install architect specific ones if needed, 
# or install all since architect is light.
RUN pip install --no-cache-dir \
    google-generativeai \
    ezdxf \
    pydantic \
    pydantic-settings \
    loguru \
    python-dotenv \
    scipy \
    numpy

# Setup Paths
RUN mkdir -p /app/factory_architect/data /app/shared_data

# Copy Source
COPY factory_architect /app/factory_architect

# Add to path
ENV PYTHONPATH=/app