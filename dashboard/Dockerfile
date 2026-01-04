FROM python:3.11-slim-bookworm

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Libs
COPY requirements.txt .
RUN pip install --no-cache-dir \
    streamlit \
    plotly \
    pandas \
    watchdog \
    loguru

# Setup Paths
RUN mkdir -p /app/shared_data /app/factory_builder/data

# Copy Source
COPY dashboard /app/dashboard

# Add to path
ENV PYTHONPATH=/app

# Expose Streamlit
EXPOSE 8501