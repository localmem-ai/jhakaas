# Worker Source Code

Core implementation of the Jhakaas AI worker service.

## Files

- **main.py** - FastAPI application entry point with /transform and /health endpoints
- **model_manager.py** - AI model management, InstantID pipeline, and LoRA handling
- **utils.py** - Image processing utilities and helper functions

## Key Components

### ModelManager
Manages the InstantID pipeline, face analysis, and style LoRA loading. Handles:
- Model initialization and caching
- Face detection and embedding
- ControlNet processing
- LoRA adapter loading/unloading
- Style transfer execution

### FastAPI Endpoints
- `POST /transform` - Apply style transfer to images
- `GET /health` - Service health check with model status

## Dependencies

Requires base image with torch, diffusers, transformers, xformers, and other AI dependencies.
See [../deployment/base/requirements.txt](../deployment/base/requirements.txt) for full list.
