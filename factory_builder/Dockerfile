FROM python:3.11-slim-bookworm

WORKDIR /app

# System deps (Heavy: Blender + Video Tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    blender \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Libs
COPY requirements.txt .
RUN pip install --no-cache-dir \
    trimesh[easy] \
    numpy \
    scipy \
    requests \
    beautifulsoup4 \
    tenacity \
    loguru \
    ezdxf \
    pydantic

# Setup Paths
RUN mkdir -p /app/factory_builder/data /app/shared_data

# Copy Source
COPY factory_builder /app/factory_builder

# Add to path
ENV PYTHONPATH=/app