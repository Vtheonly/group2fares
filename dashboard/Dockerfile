FROM python:3.11-slim-bookworm

WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python Libs
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Setup Directory Structure
# Note: Needs factory_builder/data to serve assets
RUN mkdir -p /app/shared_data /app/factory_builder/data

# Set Python Path
ENV PYTHONPATH=/app/dashboard:/app

# Expose Port
EXPOSE 8501

# Default Command
CMD ["streamlit", "run", "dashboard/src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]