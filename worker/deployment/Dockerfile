# Optimized Dockerfile using base image
# Build time: ~30 seconds (vs 10 minutes before base image approach)
# Base image contains all AI dependencies (PyTorch, diffusers, transformers, etc.)
# This Dockerfile only copies application code for fast builds

FROM asia-southeast1-docker.pkg.dev/jhakaas-dev/jhakaas-repo/worker-base:latest

WORKDIR /app

# Install missing dependencies (temporary fix until base image is rebuilt)
RUN pip install --no-cache-dir pydantic==2.5.0 pydantic-settings==2.1.0 tenacity==8.2.3

# Copy only application code (fast!)
COPY --chown=65534:65534 src ./src

# Switch to non-root user for security
USER 65534

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
