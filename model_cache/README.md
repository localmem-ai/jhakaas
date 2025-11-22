# Model Cache Builder

This folder contains a Cloud Build pipeline that downloads AI models from Hugging Face and caches them in GCS.

## What it does

1. Downloads InstantID models (ControlNet + IP-Adapter)
2. Downloads AntelopeV2 face analysis model
3. Downloads style LoRAs (anime, cartoon, pixar)
4. Uploads everything to `gs://jhakaas-models-jhakaas-dev/`

## Why separate from Docker?

- **Faster**: No Docker build overhead
- **Simpler**: Direct Python execution in Cloud Build
- **One-time operation**: Models only need to be downloaded once
- **No container bloat**: Worker Docker image stays smaller

## Usage

Run the Cloud Build pipeline:

```bash
gcloud builds submit --config cloudbuild.yaml --project jhakaas-dev .
```

## Models Downloaded

### InstantID
- `instantid/ControlNetModel/config.json`
- `instantid/ControlNetModel/diffusion_pytorch_model.safetensors`
- `instantid/ip-adapter.bin`

### AntelopeV2 (Face Analysis)
- `antelopev2/*` (complete face detection model)

### Style LoRAs
- `style_loras/anime/*.safetensors`
- `style_loras/cartoon/*.safetensors`
- `style_loras/pixar/*.safetensors`

## After Running

The worker container will load models from GCS on startup instead of downloading from Hugging Face each time.
