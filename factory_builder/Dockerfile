FROM python:3.11-slim-bookworm

WORKDIR /app

# System Dependencies: Blender, FFmpeg, OpenGL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    blender \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python Libs
COPY factory_builder/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Setup Directory Structure
RUN mkdir -p /app/factory_builder/data /app/shared_data

# Set Python Path
ENV PYTHONPATH=/app/factory_builder:/app

# No default command (handled by Compose)