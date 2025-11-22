# Optimized Dockerfile using base image
# Build time: ~30 seconds (vs 10 minutes before base image approach)
# Base image contains all AI dependencies (PyTorch, diffusers, transformers, etc.)
# This Dockerfile only copies application code for fast builds

FROM asia-southeast1-docker.pkg.dev/jhakaas-dev/jhakaas-repo/worker-base:latest

WORKDIR /app

# Copy only application code (fast!)
COPY src ./src

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
