# Base Docker Image

Base container image with all AI/ML dependencies for the Jhakaas worker.

## Purpose

Separates heavy AI dependencies from application code for faster worker rebuilds. The base image is rebuilt only when dependencies change.

## Files

- **Dockerfile** - Base image definition with Python and system dependencies
- **requirements.txt** - Python packages (torch, diffusers, transformers, xformers, etc.)
- **cloudbuild.yaml** - Cloud Build configuration for base image

## Key Dependencies

- torch==2.1.2 - PyTorch deep learning framework
- diffusers==0.25.1 - Hugging Face diffusion models
- transformers==4.37.2 - Hugging Face transformers
- xformers==0.0.23.post1 - Memory-efficient attention for InstantID
- insightface - Face analysis and recognition
- onnxruntime-gpu - GPU-accelerated inference
- opencv-python - Image processing

## Building

```bash
gcloud builds submit --config worker/deployment/base/cloudbuild.yaml --project jhakaas-dev
```

Build time: ~5 minutes

## Image Location

`asia-southeast1-docker.pkg.dev/jhakaas-dev/jhakaas-repo/worker-base:latest`

## Updates

Only rebuild when adding/updating dependencies. Worker image automatically uses latest base.
