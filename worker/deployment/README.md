# Worker Deployment

Deployment configurations and Docker images for the Jhakaas worker service.

## Files

- **Dockerfile** - Worker service container image definition
- **cloudbuild.yaml** - Cloud Build configuration for automated deployment
- **service.yaml** - Cloud Run service configuration
- **docker-compose.yml** - Local development setup (not used in production)

## Directory Structure

- **base/** - Base Docker image with AI dependencies (torch, diffusers, etc.)

## Deployment Process

1. Base image is built with all AI dependencies (infrequent updates)
2. Worker image builds on base, adding application code
3. Cloud Build automatically deploys to Cloud Run

### Trigger Deployment

```bash
gcloud builds submit --config worker/deployment/cloudbuild.yaml --project jhakaas-dev
```

### Check Build Status

```bash
gcloud builds list --limit=5 --project jhakaas-dev
```

## Environment Variables

Set in Cloud Run service configuration:
- `MODEL_CACHE_DIR` - Path to model cache
- `ENABLE_TORCH_COMPILE` - Enable/disable torch compilation
- Production settings configured via Terraform

## Notes

- Base image build time: ~5 minutes
- Worker image build time: ~4-5 minutes
- Deployment region: asia-southeast1
- Machine type: E2_HIGHCPU_8 for faster builds
