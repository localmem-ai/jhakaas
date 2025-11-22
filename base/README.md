# Jhakaas Worker Base Image

This directory contains the base Docker image for the Jhakaas worker service. The base image includes all heavy dependencies (PyTorch, diffusers, transformers, etc.) and is built separately from the worker application code.

## Purpose

**Problem:** Every worker deployment rebuilds all dependencies (~10 minutes)
**Solution:** Pre-build dependencies in a base image, reuse it for all deployments (~30 seconds)

## Architecture

```
┌─────────────────────────────────┐
│  BASE IMAGE (this directory)    │
│  - PyTorch 2.1.2 + CUDA         │
│  - diffusers 0.30.0             │
│  - transformers 4.44.0          │
│  - All AI dependencies          │
│  Build: Once per dependency     │
│  change (~10 min)               │
└─────────────────────────────────┘
           ↓ FROM base
┌─────────────────────────────────┐
│  WORKER IMAGE (../worker/)      │
│  - Application code only        │
│  - main.py, model_manager.py    │
│  Build: Every code change       │
│  (~30 seconds!)                 │
└─────────────────────────────────┘
```

## When to Rebuild

Rebuild the base image when:
- ✅ Updating AI library versions (torch, diffusers, transformers)
- ✅ Adding new AI dependencies (e.g., new model libraries)
- ✅ Changing system dependencies (apt packages)

Don't rebuild for:
- ❌ Application code changes (main.py, model_manager.py)
- ❌ Configuration changes
- ❌ Bug fixes in application logic

## How to Build

### Manual Build

```bash
cd base
gcloud builds submit --config cloudbuild.yaml --project jhakaas-dev
```

### Expected Build Time
- **First build:** ~10-12 minutes (installs all dependencies)
- **Subsequent builds:** ~10-12 minutes (if dependencies change)
- **No-op rebuild:** ~2 minutes (cache hit, just pushes)

### Verify Build

After building, verify the image works:

```bash
# Pull the image
docker pull asia-southeast1-docker.pkg.dev/jhakaas-dev/jhakaas-repo/worker-base:latest

# Test it
docker run --rm asia-southeast1-docker.pkg.dev/jhakaas-dev/jhakaas-repo/worker-base:latest \
  python -c "import torch, diffusers, transformers; print('All imports successful!')"
```

## Image Tags

The base image is tagged with:
- `latest` - Always points to the most recent build
- `v1.0.0` - Semantic version (update manually when making breaking changes)
- `{commit-sha}` - Git commit that triggered the build (for rollbacks)

## Performance Impact

| Scenario | Before (monolithic) | After (base image) |
|----------|--------------------|--------------------|
| Dependency change | 10 min | 10 min (rebuild base) |
| Code change | 10 min | **30 sec** 🚀 |
| Typical deploy | 10 min | **30 sec** 🎉 |

**Time saved per deploy:** ~9.5 minutes
**With 5 deploys/day:** ~47.5 minutes saved daily

## Maintenance

1. **Quarterly review:** Check for updated versions of AI libraries
2. **Security updates:** Rebuild when PyTorch/CUDA updates released
3. **Dependency audit:** Review `requirements.txt` for unused packages

## Troubleshooting

**Image too large?**
- Current size: ~12-14 GB (mostly PyTorch + CUDA)
- Consider using `pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime` (no development tools)

**Build fails?**
- Check Cloud Build logs: `gcloud builds log <BUILD_ID>`
- Verify all dependencies in requirements.txt are compatible

**Worker can't find base image?**
- Ensure base image was pushed to Artifact Registry
- Check worker Dockerfile has correct FROM reference
