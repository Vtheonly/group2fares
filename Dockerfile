FROM python:3.11-slim

# Install system dependencies (OpenGL for Trimesh, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY factory_architect /app/factory_architect
COPY factory_builder /app/factory_builder

# Setup Directories
RUN mkdir -p /app/data/output /app/factory_builder/input /app/factory_builder/output /app/factory_builder/cache

# Environment Variables
ENV PYTHONPATH=/app:/app/factory_architect:/app/factory_builder
ENV PYTHONUNBUFFERED=1
ENV INPUT_FILE=/app/data/input.json
ENV OUTPUT_DIR=/app/data/output

# Builder Config Overrides (for integrated mode)
ENV INPUT_DIR=/app/factory_builder/input
ENV OUTPUT_DIR=/app/factory_builder/output
ENV TARGET_MACHINE_SIZE=3000.0
ENV MAX_WORKERS=1
ENV API_TIMEOUT=1200

# Entrypoint: Run Architect's Orchestrator
# This will invoke Scraping -> DXF -> 3D (via builder import) -> Scene Merge
CMD ["python", "-m", "factory_architect.src.main", "--orchestrate"]
