# Base image for Jhakaas worker
# Contains all heavy dependencies - build once, reuse many times
# Build time: ~10 minutes (one-time cost)
# Subsequent worker builds: ~30 seconds!

FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install system dependencies
# These are needed for OpenCV, InsightFace, and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
# This is the slowest part (~8-10 minutes) but we only do it once!
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify installations
RUN python -c "import torch; print(f'PyTorch {torch.__version__} installed')" && \
    python -c "import diffusers; print(f'Diffusers {diffusers.__version__} installed')" && \
    python -c "import transformers; print(f'Transformers {transformers.__version__} installed')" && \
    python -c "import insightface; print('InsightFace installed')"

# Set up HuggingFace cache directory
ENV HF_HOME=/tmp/hf_cache
ENV TRANSFORMERS_CACHE=/tmp/hf_cache

# Create non-root user for security
# Use nobody user (UID 65534) which is standard across systems
RUN groupadd -g 65534 appuser || true && \
    useradd -r -u 65534 -g 65534 appuser 2>/dev/null || true && \
    mkdir -p /tmp/hf_cache /tmp/insightface && \
    chown -R 65534:65534 /tmp /app

# Label for tracking
LABEL maintainer="jhakaas-dev"
LABEL description="Base image with AI dependencies for Jhakaas worker"
LABEL version="1.0.0"
