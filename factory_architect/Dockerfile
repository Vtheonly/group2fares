FROM python:3.11-slim-bookworm

WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python Libs
COPY factory_architect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Setup Directory Structure (Mount points)
RUN mkdir -p /app/factory_architect/data /app/shared_data

# Set Python Path to root so imports work like 'src.main'
ENV PYTHONPATH=/app/factory_architect:/app

# No default command (handled by Compose)