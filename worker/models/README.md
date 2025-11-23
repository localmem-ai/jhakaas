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

**Existing Styles:**
- **Anime**: ntc-ai/SDXL-LoRA-slider.anime
- **Cartoon**: ntc-ai/SDXL-LoRA-slider.cartoon
- **Pixar**: ntc-ai/SDXL-LoRA-slider.pixar-style

**Viral Effects (College Edition):**
- **Clay**: alvdansen/clay-style-lora (Claymation/Wallace & Gromit style)
- **PS2**: artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl (PS2 game graphics)
- **Pixel**: nerijs/pixel-art-xl (Pixel art style)
- **Aesthetic**: ntc-ai/SDXL-LoRA-slider.aesthetic (Instagram/TikTok trending)

## GPU Best Practices

Following [Google Cloud Run GPU best practices](https://cloud.google.com/run/docs/configuring/jobs/gpu-best-practices):

1. **Pre-download models at build time** - All models are downloaded to GCS using Cloud Build
2. **Incremental downloads** - Script checks GCS before downloading, skipping existing models
3. **Load from GCS mount** - Worker loads models from `/gcs/models/` mount (faster than downloading)
4. **Powerful build machine** - Use E2_HIGHCPU_32 with 500GB disk for model downloads
5. **Optimized base image** - Use PyTorch official CUDA runtime image

## How It Works

The download script intelligently checks GCS before downloading:

1. **Checks GCS first** - For each model directory (sdxl-base/, vae-fp16/, instantid/, etc.), checks if files already exist
2. **Skips existing models** - If model directory exists in GCS, skips HuggingFace download entirely
3. **Downloads only new models** - Only downloads from HuggingFace if model is missing
4. **Uploads to GCS** - New downloads are uploaded to GCS for future use
5. **Incremental LoRA downloads** - Each LoRA is checked individually, allowing partial updates

This approach makes builds **much faster** when models are already cached in GCS.

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
