FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system libs for geometrical calculations if needed later
# RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Create data volume mount points
RUN mkdir -p /app/data/output

CMD ["python", "-m", "src.main"]
