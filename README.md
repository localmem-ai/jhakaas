# Jhakaas

AI-powered photo enhancement service with viral style effects.

## Overview

Jhakaas is a production-ready GPU-accelerated service that transforms face photos into styled images using state-of-the-art AI models. Built on Cloud Run with dual-engine support for research and commercial use cases.

**Key Features:**
- 🎨 **19 Styles** - From anime & cartoon to viral effects like PS2 graphics and K-Pop aesthetics
- ⚡ **Dual Engines** - InstantID (research-grade) and IP-Adapter (commercial-safe)
- 🚀 **Production Ready** - FastAPI service on Cloud Run with GPU acceleration
- 📦 **Smart Caching** - GCS-backed model storage with incremental downloads
- 🔄 **Lazy Loading** - Automatic engine switching with VRAM management

## Quick Start

### Deploy Worker

```bash
# Trigger Cloud Build deployment
gcloud builds submit \
  --config worker/deployment/cloudbuild.yaml \
  --project jhakaas-dev

# Check deployment status
gcloud builds list --limit=5 --project jhakaas-dev

# Verify service health
curl https://jhakaas-worker-jv4qpcriga-as.a.run.app/health
```

### Generate Styled Image

```bash
# Get auth token
TOKEN=$(gcloud auth print-identity-token)

# Generate image
curl -X POST https://jhakaas-worker-jv4qpcriga-as.a.run.app/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://storage.googleapis.com/bucket/photo.jpg",
    "prompt": "portrait",
    "style": "anime",
    "engine": "instantid"
  }'
```

### Run Tests

```bash
cd worker/tests

# Add test images
cp your_photo.jpg test-images/

# Test all styles (19 × 2 engines = 38 generations)
python test_styles.py

# Test viral effects only (9 × 2 engines = 18 generations)
python test_viral_effects.py

# View HTML report
open results/html/test_report_*.html
```

## Documentation

### 📚 [Complete Worker Architecture Guide](docs/worker_architecture.md)

Comprehensive documentation covering:
- **System Architecture** - Dual-engine design, components, directory structure
- **Request Flow** - End-to-end journey from API call to styled image
- **Processing Pipeline** - Engine switching, LoRA loading, image generation
- **Dual Engine System** - InstantID vs IP-Adapter comparison
- **Styles Catalog** - All 19 styles with implementation details
- **Models Inventory** - Complete list of AI models and storage strategy
- **Deployment** - Cloud Run configuration, build process, health checks
- **Testing** - Test structure, running tests, HTML reports

### 📖 [Product Vision](docs/product_vision.md)

Product roadmap and feature planning.

## Project Structure

```
jhakaas/
├── README.md                    # This file
├── docs/
│   ├── worker_architecture.md   # Complete technical guide
│   └── product_vision.md        # Product roadmap
└── worker/
    ├── src/                     # FastAPI application
    │   ├── main.py              # API endpoints
    │   ├── model_manager.py     # Model loading & processing
    │   ├── config.py            # Settings
    │   ├── logger.py            # Structured logging
    │   └── utils.py             # Helpers
    ├── models/
    │   └── download_models.py   # Model download script
    ├── deployment/
    │   ├── Dockerfile           # Worker container
    │   ├── cloudbuild.yaml      # Build config
    │   └── base/
    │       ├── Dockerfile       # Base image with AI deps
    │       └── requirements.txt # PyTorch, diffusers, etc.
    └── tests/
        ├── test_styles.py       # E2E style tests
        ├── test_viral_effects.py # Viral effects tests
        └── utils/
            └── generate_html_report.py # Test reports
```

## Available Styles

### Classic Styles (10)
`natural`, `anime`, `cartoon`, `pixar`, `bollywood`, `cinematic`, `vintage`, `glamour`, `corporate`, `artistic`

### Viral Effects - LoRA (3)
- `ps2` - PlayStation 2 retro gaming graphics
- `pixel` - 16-bit retro pixel art
- `aesthetic` - Instagram/TikTok pastel aesthetic

### Viral Effects - Prompt-Only (6)
`yearbook`, `kpop`, `bollywood_poster`, `y2k`, `couple_aesthetic`, `mermaid`, `sigma`, `thug_life`

## Technology Stack

- **Framework:** FastAPI (async Python)
- **AI Models:** PyTorch, Diffusers, Stable Diffusion XL
- **Face Engines:** InstantID, IP-Adapter
- **Infrastructure:** Google Cloud Run (GPU), GCS FUSE
- **Monitoring:** Structured JSON logging

## License

Proprietary - All rights reserved

## Support

For technical documentation and architecture details, see [docs/worker_architecture.md](docs/worker_architecture.md).
