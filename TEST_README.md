# Cloud Run Worker Testing Guide

## Enhanced Test Script

The `test_cloud_run.py` script now includes comprehensive testing with visual comparisons.

### Features

1. **Health Check**: Verifies service status and GPU availability
2. **Multi-Scenario Testing**: Tests 3 different AI generation scenarios
3. **Visual Comparisons**: Creates side-by-side images of original vs AI-generated
4. **Auto-Display**: Opens comparison images automatically

### Test Scenarios

1. **Professional Headshot**
   - Style: Cinematic
   - Prompt: "professional headshot, studio lighting, sharp focus, cinematic"

2. **Portrait Enhancement**
   - Style: Natural
   - Prompt: "beautiful portrait, natural lighting, high quality, professional photography"

3. **Business Professional**
   - Style: Corporate
   - Prompt: "corporate headshot, professional attire, office background, high resolution"

### Usage

```bash
# 1. Set your Cloud Run URL in the script
# Edit test_cloud_run.py and set WORKER_URL

# 2. Run the test
python3 test_cloud_run.py
```

### With IAM Authentication

```bash
# Option A: Using gcloud proxy
gcloud run services proxy jhakaas-worker --port=8080 --project=jhakaas-dev --region=asia-southeast1

# Then set WORKER_URL="http://localhost:8080" in script

# Option B: Using auth tokens
# Modify the script to include Authorization header with:
# TOKEN=$(gcloud auth print-identity-token)
```

### Output

Results are saved in `test_results/` directory:
- `professional_headshot_comparison.jpg`
- `portrait_enhancement_comparison.jpg`
- `business_professional_comparison.jpg`

Each comparison shows:
- Left: Original image
- Right: AI-generated image

### Quick Health Check

For a quick health check without full testing:

```bash
./test_health.sh <CLOUD_RUN_URL>
```
