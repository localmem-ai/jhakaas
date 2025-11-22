# Model Management

Scripts and configurations for downloading and managing AI models.

## Files

- **download_models.py** - Downloads all required models to Cloud Storage
- **cloudbuild.yaml** - Cloud Build config for automated model downloads

## Models Downloaded

### Base Models (Required)
- **SDXL Base**: stabilityai/stable-diffusion-xl-base-1.0 (~7GB)
- **VAE FP16 Fix**: madebyollin/sdxl-vae-fp16-fix (~335MB)
- **InstantID ControlNet**: InstantX/InstantID/ControlNetModel (~2.5GB)
- **InstantID IP-Adapter**: InstantX/InstantID/ip-adapter.bin (~22MB)
- **AntelopeV2 Face Model**: DIAMONIK7777/antelopev2 (~260MB)

### Style LoRAs (Optional)
Downloaded from Hugging Face:
- **Anime**: ntc-ai/SDXL-LoRA-slider.anime
- **Cartoon**: ntc-ai/SDXL-LoRA-slider.cartoon
- **Pixar**: ntc-ai/SDXL-LoRA-slider.pixar-style

## GPU Best Practices

Following [Google Cloud Run GPU best practices](https://cloud.google.com/run/docs/configuring/jobs/gpu-best-practices):

1. **Pre-download models at build time** - All models are downloaded to GCS using Cloud Build
2. **Load from GCS mount** - Worker loads models from `/gcs/models/` mount (faster than downloading)
3. **Powerful build machine** - Use E2_HIGHCPU_32 with 500GB disk for model downloads
4. **Optimized base image** - Use PyTorch official CUDA runtime image

## Usage

Models are automatically downloaded to Cloud Storage and mounted to worker instances via Cloud Run volume mounts.

### Manual Download

```bash
python worker/models/download_models.py
```

### Automated Download via Cloud Build

```bash
gcloud builds submit --config worker/models/cloudbuild.yaml --project jhakaas-dev
```

## Storage Location

Models are stored in GCS bucket: `gs://jhakaas-models-{project}/`

Worker instances mount this bucket at `/models` for fast local access.
