FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for trimesh/ezdxf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package
COPY factory_builder/ ./factory_builder/
COPY main.py .

# Create data directories
RUN mkdir -p input output cache/images cache/models

# Set entrypoint
ENTRYPOINT ["python", "main.py"]
