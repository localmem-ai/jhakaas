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

## Supported Features

### Style LoRAs (Model-based)
Existing styles:
- anime, cartoon, pixar

New viral effects (College Edition):
- **clay** - Claymation/Wallace & Gromit style
- **ps2** - PS2 game graphics retro style
- **pixel** - 16-bit pixel art
- **aesthetic** - Instagram/TikTok aesthetic

### Prompt-only Styles
No LoRA needed, prompt engineering only:
- yearbook, kpop, bollywood_poster, y2k, couple_aesthetic, mermaid, sigma, thug_life

## Notes

- Base image build time: ~5 minutes
- Worker image build time: ~4-5 minutes
- Deployment region: asia-southeast1
- Machine type: E2_HIGHCPU_8 for faster builds
