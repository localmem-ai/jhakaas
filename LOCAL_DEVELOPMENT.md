# Running Jhakaas Worker Locally

## ⚠️ Important Limitations

### GPU Compatibility
- **Cloud Version**: NVIDIA L4 GPU with CUDA 12.1 (~12 seconds per image)
- **MacBook Air**: No NVIDIA GPU, runs on **CPU only** (~5-10 minutes per image)

Your MacBook Air cannot run CUDA containers natively. You have two options:

## Option 1: Run on CPU (Slow but Works)

### Prerequisites
- Docker Desktop installed
- At least 16GB RAM
- ~20GB free disk space for models

### Steps

1. **Build and start the container:**
```bash
cd /Users/VivekGupta/projects/jhakaas
docker-compose up --build
```

This will:
- Build the Docker image (~5-10 minutes first time)
- Download SDXL models (~12GB) on first run
- Start the service on `http://localhost:8080`

2. **Test the local container:**
```bash
# In a new terminal
python3 test_local.py
```

3. **Stop the container:**
```bash
# Press Ctrl+C in the docker-compose terminal
# Or run:
docker-compose down
```

### Expected Performance
- **Health check**: <1 second
- **Model loading**: ~2-3 minutes (first time)
- **Image generation**: **5-10 minutes per image** (CPU)

## Option 2: Use Cloud Run (Recommended)

Instead of running locally, just use the deployed Cloud Run service:

```bash
python3 test_cloud_run.py
```

**Advantages:**
- ✅ Fast (12 seconds per image with GPU)
- ✅ No local resources used
- ✅ Always up-to-date with latest code
- ✅ Production environment

**To point to Cloud Run:**
The test script already uses: `https://jhakaas-worker-1098174162480.asia-southeast1.run.app`

## Pointing Test Script to Local

If you want to test against your local container, edit `test_cloud_run.py`:

```python
# Change line 15 from:
WORKER_URL = "https://jhakaas-worker-1098174162480.asia-southeast1.run.app"

# To:
WORKER_URL = "http://localhost:8080"

# And comment out the get_auth_token() function calls (no auth needed locally)
```

Or just use the dedicated local test script:
```bash
python3 test_local.py
```

## Debugging

### Check if container is running:
```bash
docker ps
```

### View logs:
```bash
docker-compose logs -f
```

### Check health endpoint:
```bash
curl http://localhost:8080/health
```

### Rebuild after code changes:
```bash
docker-compose down
docker-compose up --build
```

## Why Cloud Run is Better for Development

| Feature | Local (CPU) | Cloud Run (GPU) |
|---------|-------------|-----------------|
| Speed | 5-10 min/image | 12 sec/image |
| Setup Time | 15-20 minutes | Already done |
| Model Downloads | 12GB locally | Cached in cloud |
| RAM Usage | 16GB+ | 0GB (cloud) |
| Cost | Free (local) | ~$0.50/hour when running |
| Updates | Manual rebuild | Automatic via CI/CD |

**Recommendation**: Use Cloud Run for development. Only run locally if:
- You're debugging container issues
- You're offline
- You want to modify the code and test immediately without deploying

## Apple Silicon (M1/M2/M3) Note

Your MacBook Air with Apple Silicon **cannot** run CUDA containers at native speed. Options:
1. **CPU mode** (very slow) - what we've set up above
2. **Use Cloud Run** (recommended)
3. **Build Mac-native version** with Metal/MPS support (requires rewriting the Dockerfile)

For production AI work, Cloud Run with GPU is the best choice.
