# Model Management

Scripts and configurations for downloading and managing AI models.

## Files

- **download_models.py** - Downloads all required models to Cloud Storage
- **cloudbuild.yaml** - Cloud Build config for automated model downloads

## Models Downloaded

### InstantID Models
- Face encoder: InstantX/InstantID (ip-adapter.bin)
- ControlNet: InstantX/InstantID (ControlNetModel)

### Base Models
- SDXL: stabilityai/stable-diffusion-xl-base-1.0
- Face analysis: buffalo_l (InsightFace)

### Style LoRAs
Downloaded from CivitAI:
- Pixar style
- Anime style
- Sketch style
- Oil painting
- Watercolor
- Clay animation
- Comic book
- Pop art

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
