FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Blender
RUN apt-get update && \
    apt-get install -y \
    blender \
    ffmpeg \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY render_video.py /app/render_video.py

ENTRYPOINT ["blender", "-b", "-P", "/app/render_video.py"]
