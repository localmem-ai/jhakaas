# Jhakaas Worker Architecture

Complete guide to the Jhakaas AI Worker - a GPU-accelerated FastAPI service for AI-powered photo enhancement with style transfer.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Request Flow](#request-flow)
4. [Worker Processing Pipeline](#worker-processing-pipeline)
5. [Dual Engine System](#dual-engine-system)
6. [Styles Catalog](#styles-catalog)
7. [Models Inventory](#models-inventory)
8. [Deployment](#deployment)
9. [Testing](#testing)

---

## System Overview

Jhakaas Worker is a production-ready AI service that transforms face photos into styled images using state-of-the-art AI models. It supports 19 different styles ranging from anime and cartoon to viral effects like PS2 graphics and K-Pop idol aesthetics.

**Key Features:**
- **Dual Engine Architecture**: InstantID (research-grade) and IP-Adapter (commercial-safe)
- **19 Styles**: 10 classic styles + 9 viral effects
- **Lazy Loading**: Smart engine switching with automatic VRAM management
- **Production Ready**: Cloud Run deployment with health checks, structured logging, timeout handling
- **Smart Caching**: GCS-backed model cache with incremental downloads

**Tech Stack:**
- FastAPI (async Python web framework)
- PyTorch + Diffusers (AI models)
- Stable Diffusion XL (base model)
- InstantID / IP-Adapter (face engines)
- Google Cloud Run (serverless GPU hosting)
- GCS FUSE (model storage)

---

## Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Request                        │
│         POST /generate {image_url, prompt, style, engine}    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  - Request validation (Pydantic)                             │
│  - Auth middleware (GCloud Identity Token)                   │
│  - Structured logging (JSON)                                 │
│  - Timeout handling (120s default)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Model Manager                            │
│  ┌──────────────────┐        ┌──────────────────┐           │
│  │ InstantID Engine │   OR   │ IP-Adapter Engine│           │
│  │  (Research)      │        │  (Commercial)     │           │
│  │ - InstantID      │        │ - IP-Adapter     │           │
│  │ - FaceAnalysis   │        │ - Canny ControlNet│          │
│  │ - ControlNet     │        │ - Edge Detection  │          │
│  └──────────────────┘        └──────────────────┘           │
│                                                               │
│  Shared Components:                                          │
│  - SDXL Base Model (stabilityai/stable-diffusion-xl-base-1.0)│
│  - VAE FP16 (madebyollin/sdxl-vae-fp16-fix)                  │
│  - Style LoRAs (anime, cartoon, pixar, ps2, pixel, aesthetic)│
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    GCS Storage                               │
│  - Input images (jhakaas-images-jhakaas-dev/test-uploads/)   │
│  - Output images (jhakaas-images-jhakaas-dev/generated/)     │
│  - Models (jhakaas-models-jhakaas-dev/) mounted via FUSE     │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
worker/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── model_manager.py     # Model loading & image processing
│   ├── config.py            # Pydantic settings
│   ├── logger.py            # Structured logging
│   ├── utils.py             # Image download/upload helpers
│   └── pipelines/           # Bundled InstantID pipeline
├── models/
│   └── download_models.py   # Model download script with GCS checking
├── deployment/
│   ├── Dockerfile           # Worker container image
│   ├── cloudbuild.yaml      # Cloud Build config
│   └── base/
│       ├── Dockerfile       # Base image with AI dependencies
│       └── requirements.txt # PyTorch, diffusers, etc.
└── tests/
    ├── test_styles.py       # E2E tests for all styles
    ├── test_viral_effects.py # Focused tests for viral effects
    └── utils/
        └── generate_html_report.py # Dual-engine comparison reports
```

---

## Request Flow

### End-to-End Request Journey

```
1. Client Request
   │
   ├─▶ POST /generate
   │   {
   │     "image_url": "https://storage.googleapis.com/.../photo.jpg",
   │     "prompt": "portrait",
   │     "style": "anime",
   │     "engine": "instantid"
   │   }
   │
2. FastAPI Middleware
   │
   ├─▶ Generate request ID (UUID)
   ├─▶ Validate request (Pydantic)
   │   - image_url: Must be from allowed domains
   │   - prompt: 1-500 chars
   │   - style: Must be valid style literal
   │   - engine: "instantid" or "ip_adapter"
   │
3. Download Input Image
   │
   ├─▶ utils.download_image(image_url)
   │   - Supports https:// and gs:// URLs
   │   - Downloads to /tmp/{uuid}.jpg
   │
4. Model Manager Processing
   │
   ├─▶ Switch engine if needed (lazy loading)
   │   - Unload current engine
   │   - Load requested engine
   │   - Clear VRAM cache
   │
   ├─▶ Load style LoRA (if available)
   │   - Check GCS: /gcs/models/style_loras/{style}/
   │   - Fallback to HuggingFace
   │   - Unload previous LoRA if different
   │
   ├─▶ Build style-aware prompt
   │   - Combine user prompt + style prompts
   │   - Add negative prompts
   │
   ├─▶ Generate Image (Engine-Specific)
   │
   │   InstantID:
   │   - Extract face embeddings (InsightFace)
   │   - Apply ControlNet for face structure
   │   - Run SDXL pipeline with IP-Adapter
   │   - 20 inference steps, 5.0 guidance
   │
   │   IP-Adapter:
   │   - Extract Canny edges (ControlNet)
   │   - Use face as IP-Adapter reference
   │   - Run SDXL ControlNet pipeline
   │   - 20 inference steps, 5.0 guidance
   │
5. Upload Result
   │
   ├─▶ utils.upload_image(result_image)
   │   - Generate unique filename
   │   - Upload to GCS: jhakaas-images-jhakaas-dev/generated/
   │   - Make public & return URL
   │
6. Return Response
   │
   └─▶ {
       "status": "success",
       "output_url": "https://storage.googleapis.com/.../result.jpg",
       "request_id": "uuid",
       "processing_time_ms": 16234,
       "params": {...}
     }
```

### Error Handling

- **Validation Errors (422)**: Invalid image URL, prompt too long, unknown style
- **Service Unavailable (503)**: Models not loaded, GPU unavailable, low VRAM
- **Gateway Timeout (504)**: Processing exceeds 120s timeout
- **Internal Error (500)**: Unexpected runtime errors

All errors return structured JSON with `error`, `error_code`, `request_id`, and `timestamp`.

---

## Worker Processing Pipeline

### Image Processing Flow

```python
def process_image(face_image_path, prompt, style, engine="instantid"):
    """
    Main processing pipeline with dual engine support
    """

    # STEP 1: Engine Switching (Lazy Loading)
    if engine == "ip_adapter" and current_engine != "ip_adapter":
        unload_current_pipeline()
        load_ip_adapter_engine()
    elif engine == "instantid" and current_engine != "instantid":
        unload_current_pipeline()
        load_models()  # Loads InstantID by default

    # STEP 2: Image Preparation
    face_image = load_image(face_image_path)
    face_image = face_image.resize((1024, 1024), Image.LANCZOS)

    # STEP 3: Style LoRA Loading (if available)
    lora_loaded = load_style_lora(style)
    lora_scale = 0.8 if lora_loaded else 0.0

    # STEP 4: Prompt Engineering
    full_prompt = build_style_prompt(prompt, style)
    negative_prompt = get_negative_prompt(style)

    # STEP 5: Engine-Specific Generation
    if engine == "ip_adapter":
        return process_image_ip_adapter(
            face_image, full_prompt, negative_prompt, style, lora_scale
        )
    else:
        return process_image_instantid(
            face_image, full_prompt, negative_prompt, style, lora_scale
        )
```

### InstantID Processing

```python
def process_image_instantid(face_image, prompt, negative_prompt, style, lora_scale):
    # 1. Face Analysis (InsightFace AntelopeV2)
    faces = app.get(cv2.cvtColor(np.array(face_image), cv2.COLOR_RGB2BGR))
    faceid_embeds = torch.from_numpy(faces[0].normed_embedding)

    # 2. Generate with InstantID Pipeline
    images = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image_embeds=faceid_embeds,      # Face identity
        image=face_image,                # Face structure (ControlNet)
        controlnet_conditioning_scale=0.8,
        ip_adapter_scale=0.8,
        num_inference_steps=20,
        guidance_scale=5.0,
        cross_attention_kwargs={"scale": lora_scale}
    ).images

    return images[0]
```

### IP-Adapter Processing

```python
def process_image_ip_adapter(face_image, prompt, negative_prompt, style, lora_scale):
    # 1. Canny Edge Detection (for structure preservation)
    image_np = np.array(face_image)
    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    canny_image = cv2.Canny(image_cv, 100, 200)
    canny_image = Image.fromarray(
        np.stack([canny_image, canny_image, canny_image], axis=2)
    )

    # 2. Generate with IP-Adapter Pipeline
    images = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        ip_adapter_image=face_image,    # Face reference
        image=canny_image,              # Structure (ControlNet)
        controlnet_conditioning_scale=0.5,
        num_inference_steps=20,
        guidance_scale=5.0,
        cross_attention_kwargs={"scale": lora_scale}
    ).images

    return images[0]
```

### VRAM Management

- **Engine Switching**: Unload inactive engine to free VRAM (~8GB per engine)
- **LoRA Swapping**: Unload previous LoRA before loading new one (~200MB each)
- **Attention Slicing**: Reduce memory usage during inference
- **xFormers**: Memory-efficient attention implementation
- **Cache Clearing**: `torch.cuda.empty_cache()` on engine switch

---

## Dual Engine System

### Engine Comparison

| Feature | InstantID | IP-Adapter |
|---------|-----------|------------|
| **License** | Research (Non-Commercial) | Commercial-Safe |
| **Face Preservation** | ★★★★★ Excellent | ★★★★☆ Very Good |
| **Speed** | ~16-18s | ~16-18s |
| **VRAM** | ~8GB | ~8GB |
| **Face Analysis** | InsightFace AntelopeV2 | Canny Edge Detection |
| **ControlNet** | InstantID ControlNet | Canny ControlNet |
| **Best For** | High-fidelity portraits, research | Production apps, commercial use |

### When to Use Each Engine

**Use InstantID when:**
- Maximum face preservation is critical
- Research or non-commercial projects
- You need best-in-class face identity retention

**Use IP-Adapter when:**
- Building commercial applications
- Need permissive licensing
- Acceptable to trade slight quality for legal safety

### Technical Differences

**InstantID:**
- Uses face embeddings from InsightFace (512D vector)
- Custom ControlNet trained on face keypoints
- Dedicated IP-Adapter for InstantID
- Stronger face identity preservation

**IP-Adapter:**
- Uses Canny edge detection for structure
- Standard SDXL ControlNet (Canny)
- Generic IP-Adapter (h94/IP-Adapter)
- More flexible for commercial use

---

## Styles Catalog

### All Available Styles (19 Total)

#### Classic Styles (10)

| Style | Type | LoRA | Description |
|-------|------|------|-------------|
| `natural` | Prompt-only | ❌ | Minimal changes, professional photography |
| `anime` | LoRA | ✅ | Vibrant anime art with cel shading |
| `cartoon` | LoRA | ✅ | Western animation with bold outlines |
| `pixar` | LoRA | ✅ | 3D Pixar animation style |
| `bollywood` | Prompt-only | ❌ | Dramatic Bollywood aesthetic |
| `cinematic` | Prompt-only | ❌ | Moody film photography |
| `vintage` | Prompt-only | ❌ | Classic vintage photography |
| `glamour` | Prompt-only | ❌ | Elegant fashion photography |
| `corporate` | Prompt-only | ❌ | Professional headshots |
| `artistic` | Prompt-only | ❌ | Fine art portrait |

#### Viral Effects - LoRA-Based (3)

| Style | LoRA Repository | Description |
|-------|----------------|-------------|
| `ps2` | artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl | PlayStation 2 retro gaming graphics |
| `pixel` | nerijs/pixel-art-xl | 16-bit retro pixel art |
| `aesthetic` | ntc-ai/SDXL-LoRA-slider.aesthetic | Instagram/TikTok pastel aesthetic |

#### Viral Effects - Prompt-Only (6)

| Style | Description |
|-------|-------------|
| `yearbook` | 90s school yearbook photo style |
| `kpop` | K-Pop idol with glass skin aesthetic |
| `bollywood_poster` | Dramatic Bollywood movie poster |
| `y2k` | Early 2000s digital camera aesthetic |
| `couple_aesthetic` | Instagram couple goals aesthetic |
| `mermaid` | Mermaid transformation with scales |
| `sigma` | Dramatic sigma male aesthetic |
| `thug_life` | Urban street photography style |

### Style Implementation Details

**LoRA-Based Styles:**
- Model files: `~200-500MB` each
- Stored in GCS: `/gcs/models/style_loras/{style}/`
- Loaded on-demand, cached in memory
- LoRA scale: `0.8` (optimal for quality)
- Unloaded when switching styles

**Prompt-Only Styles:**
- No model download required
- Implemented via prompt engineering
- Instant switching (no loading time)
- Examples:
  ```python
  "yearbook": "1990s school yearbook portrait, neutral background,
               soft lighting, retro photography, film grain"

  "kpop": "K-pop idol, glass skin, dewy makeup, soft lighting,
           professional photography, Korean beauty standard"
  ```

---

## Models Inventory

### Base Models

| Model | Size | Source | Purpose |
|-------|------|--------|---------|
| **SDXL Base 1.0** | ~6.9GB | stabilityai/stable-diffusion-xl-base-1.0 | Foundation model for image generation |
| **VAE FP16** | ~335MB | madebyollin/sdxl-vae-fp16-fix | Prevents numerical instabilities in FP16 |

### InstantID Components

| Model | Size | Source | Purpose |
|-------|------|--------|---------|
| **AntelopeV2** | ~400MB | InsightFace buffalo_l | Face detection & embedding extraction |
| **InstantID ControlNet** | ~2.5GB | InstantX/InstantID | Face structure preservation |
| **IP-Adapter (InstantID)** | ~1.7GB | InstantX/InstantID | Face identity injection |

### IP-Adapter Components

| Model | Size | Source | Purpose |
|-------|------|--------|---------|
| **IP-Adapter SDXL** | ~1.8GB | h94/IP-Adapter | Face reference encoding |
| **ControlNet Canny** | ~2.5GB | diffusers/controlnet-canny-sdxl-1.0 | Edge-based structure control |

### Style LoRAs

| LoRA | Size | Repository | Status |
|------|------|-----------|--------|
| anime | ~200MB | ntc-ai/SDXL-LoRA-slider.anime | ✅ Active |
| cartoon | ~200MB | ntc-ai/SDXL-LoRA-slider.cartoon | ✅ Active |
| pixar | ~200MB | ntc-ai/SDXL-LoRA-slider.pixar-style | ✅ Active |
| ps2 | ~400MB | artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl | ✅ Active |
| pixel | ~300MB | nerijs/pixel-art-xl | ✅ Active |
| aesthetic | ~200MB | ntc-ai/SDXL-LoRA-slider.aesthetic | ✅ Active |

### Model Storage & Caching

**GCS Bucket:** `jhakaas-models-jhakaas-dev`

**Directory Structure:**
```
jhakaas-models-jhakaas-dev/
├── sdxl-base/              # SDXL Base 1.0
├── vae-fp16/               # VAE FP16 Fix
├── instantid/
│   ├── ControlNetModel/    # InstantID ControlNet
│   └── ip-adapter.bin      # InstantID IP-Adapter
├── ip-adapter/
│   └── sdxl_models/
│       └── ip-adapter_sdxl.safetensors
├── controlnet-canny/       # Canny ControlNet
├── antelopev2/             # InsightFace models
└── style_loras/
    ├── anime/
    ├── cartoon/
    ├── pixar/
    ├── ps2/
    ├── pixel/
    └── aesthetic/
```

**Download Strategy:**
- **Build Time**: `download_models.py` checks GCS before downloading
- **Runtime**: Models loaded from `/gcs/models/` (GCS FUSE mount)
- **Fallback**: Download from HuggingFace if GCS unavailable
- **Caching**: HuggingFace cache at `/tmp/hf_cache`

---

## Deployment

### Cloud Run Configuration

**Service:** `jhakaas-worker`
- **Region:** asia-southeast1
- **Machine:** CPU: 4, Memory: 16GB, GPU: NVIDIA T4 (16GB VRAM)
- **Concurrency:** 1 (GPU workload)
- **Timeout:** 300s
- **Min Instances:** 0 (scale to zero)
- **Max Instances:** 10

**Environment Variables:**
```yaml
MODEL_BUCKET: jhakaas-models-jhakaas-dev
IMAGES_BUCKET: jhakaas-images-jhakaas-dev
ENVIRONMENT: production
LOG_LEVEL: INFO
PROCESSING_TIMEOUT_SECONDS: 120
MAX_PROMPT_LENGTH: 500
```

**GCS FUSE Mount:**
```yaml
volumeMounts:
  - name: gcs-models
    mountPath: /gcs/models
volumes:
  - name: gcs-models
    csi:
      driver: gcsfuse.csi.storage.gke.io
      volumeAttributes:
        bucketName: jhakaas-models-jhakaas-dev
```

### Build Process

**Cloud Build Pipeline:**
```bash
# Trigger build
gcloud builds submit \
  --config worker/deployment/cloudbuild.yaml \
  --project jhakaas-dev

# Monitor build
gcloud builds list --limit=5 --project jhakaas-dev

# Check logs
gcloud builds log <BUILD_ID> --project jhakaas-dev
```

**Build Steps:**
1. Build base image (Python 3.11 + PyTorch + CUDA)
2. Build worker image (FastAPI + application code)
3. Push to Artifact Registry
4. Deploy to Cloud Run
5. Wait for health checks

**Build Time:**
- Base image: ~5 minutes (infrequent)
- Worker image: ~4-5 minutes
- Total deployment: ~8-10 minutes

### Health Checks

**Liveness Probe:** `/health/liveness`
- Simple alive check
- Used by Cloud Run to restart crashed containers

**Readiness Probe:** `/health/readiness`
- Checks models loaded
- Checks GPU available
- Checks VRAM > 1GB
- Used to route traffic only to ready instances

**Legacy Endpoint:** `/health` (backward compatibility)

---

## Testing

### Test Structure

**Test Files:**
- `test_styles.py`: Tests all 19 styles on both engines
- `test_viral_effects.py`: Focused test for 9 viral effects only

**Test Flow:**
1. Upload test images to GCS
2. Call `/generate` API for each style
3. Download & save results
4. Generate HTML comparison report

### Running Tests

```bash
# Setup
cd worker/tests
pip install -r requirements.txt

# Add test images
cp your_photo.jpg test-images/

# Run all styles (38 generations = 19 styles × 2 engines)
python test_styles.py

# Run viral effects only (18 generations = 9 styles × 2 engines)
python test_viral_effects.py

# View results
open results/html/test_report_TIMESTAMP.html
open results/html/viral_effects_report_TIMESTAMP.html
```

### Test Reports

**HTML Report Features:**
- Side-by-side comparison (InstantID vs IP-Adapter)
- Processing time for each generation
- Success/failure status
- Visual quality comparison
- Easy to share & review

**Example Report:**
```
┌─────────────────┬────────────────────┬────────────────────┐
│ Style           │ InstantID          │ IP-Adapter         │
├─────────────────┼────────────────────┼────────────────────┤
│ Anime           │ ✅ 16.2s           │ ✅ 17.1s           │
│ Yearbook        │ ✅ 15.8s           │ ✅ 16.4s           │
│ PS2             │ ✅ 18.3s           │ ✅ 18.9s           │
└─────────────────┴────────────────────┴────────────────────┘
```

### Configuration

**Test Config:** `tests/config.py`
```python
WORKER_URL = "https://jhakaas-worker-jv4qpcriga-as.a.run.app"
TEST_BUCKET = "jhakaas-images-jhakaas-dev"
TEST_IMAGES_DIR = "test-images/"
RESULTS_DIR = "results/"
```

---

## Troubleshooting

### Common Issues

**1. Models not loading**
- Check GCS FUSE mount: `ls /gcs/models/`
- Check logs for download errors
- Verify HuggingFace hub access

**2. CUDA out of memory**
- Check current VRAM: `nvidia-smi`
- Enable attention slicing (already enabled)
- Reduce batch size (already 1)
- Switch engine to free VRAM

**3. Slow generation**
- Expected: 16-20s per image
- Check GPU utilization: `nvidia-smi`
- Verify xFormers enabled
- Check for CPU fallback

**4. Build failures**
- Check Cloud Build logs
- Verify base image exists
- Check dependencies in requirements.txt
- Ensure model downloads complete

### Debugging

**Check worker logs:**
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=jhakaas-worker" \
  --limit 50 --format json
```

**Test locally:**
```bash
cd worker
export WORKER_URL=http://localhost:8080
python -m uvicorn src.main:app --reload --port 8080
```

---

## Performance Benchmarks

**Average Processing Times (NVIDIA T4):**
- InstantID: 16-18s
- IP-Adapter: 16-18s
- LoRA loading: ~2s (first time per style)
- Engine switching: ~8-10s

**VRAM Usage:**
- InstantID engine: ~7.5GB
- IP-Adapter engine: ~7.8GB
- Style LoRA: ~200-400MB additional

**Throughput:**
- Single GPU: ~3-4 images/minute
- With engine switching overhead: ~2-3 images/minute

---

## Future Improvements

**Planned Enhancements:**
- [ ] Engine pooling (pre-load both engines)
- [ ] Batch processing support
- [ ] Custom LoRA uploads
- [ ] Video style transfer
- [ ] Multi-face detection
- [ ] Advanced prompt templating
- [ ] A/B testing framework
- [ ] Metrics dashboard

---

## References

- **InstantID**: https://github.com/InstantID/InstantID
- **IP-Adapter**: https://github.com/tencent-ailab/IP-Adapter
- **SDXL**: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- **Diffusers**: https://github.com/huggingface/diffusers
- **Cloud Run**: https://cloud.google.com/run/docs

---

**Last Updated:** 2025-01-23
**Version:** 1.0.0
