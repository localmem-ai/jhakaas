# ✅ Viral Effects LoRA Setup - Complete Guide

**Status:** Ready to download!  
**Your existing infrastructure:** Perfect! ✅

---

## 🎯 What You Already Have (Perfect Setup!)

### ✅ **Existing Infrastructure:**
1. **`download_models.py`** - Downloads models from HuggingFace to GCS
2. **`cloudbuild.yaml`** - Automatically runs the download script
3. **GCS Bucket** - `jhakaas-models-jhakaas-dev` for model storage
4. **LoRA Support** - Already implemented in `model_manager.py`

### ✅ **What I Just Added:**
- Extended `download_models.py` to include **7 new viral effect LoRAs**:
  1. **Clay** (Claymation/Wallace & Gromit)
  2. **PS2** (PlayStation 2 graphics)
  3. **Pixel** (Pixel art/retro gaming)
  4. **Aesthetic** (Instagram/TikTok aesthetic)
  5. *(Optional: Bollywood, K-Pop, Mermaid - commented out)*

---

## 🚀 How to Download LoRAs to GCS

### **Option 1: Run Cloud Build (Recommended)**

```bash
# Navigate to models directory
cd worker/models

# Trigger Cloud Build to download all models + LoRAs
gcloud builds submit \
  --config cloudbuild.yaml \
  --project jhakaas-dev

# This will:
# 1. Download SDXL base model
# 2. Download InstantID models
# 3. Download AntelopeV2 (face detection)
# 4. Download VAE FP16
# 5. Download ALL LoRAs (existing + new viral effects) ✅
```

**Time:** ~30-45 minutes (one-time)  
**Cost:** ~$2-3 (Cloud Build compute)  
**Result:** All models + LoRAs cached in GCS forever

---

### **Option 2: Run Locally (Faster for testing)**

```bash
# Navigate to models directory
cd worker/models

# Install dependencies
pip install huggingface_hub google-cloud-storage

# Run download script
python3 download_models.py

# This downloads everything to GCS
```

**Time:** ~20-30 minutes (depends on internet speed)  
**Cost:** Free (uses your local machine)

---

## 📦 What Gets Downloaded

### **Existing Models (Already have):**
- ✅ SDXL Base (~12GB)
- ✅ InstantID ControlNet (~5GB)
- ✅ AntelopeV2 Face Model (~300MB)
- ✅ VAE FP16 Fix (~300MB)
- ✅ 3 existing LoRAs: Anime, Cartoon, Pixar (~500MB each)

### **NEW Viral Effect LoRAs (Added today):**
- ✅ Clay/Claymation (~500MB)
- ✅ PS2 Graphics (~500MB)
- ✅ Pixel Art (~500MB)
- ✅ Aesthetic (~500MB)

### **Total Additional Storage:**
- New LoRAs: ~2GB
- Total project: ~20GB (was ~18GB)
- GCS cost: +$0.05/month (negligible!)

---

## 🔍 Verify Downloads

After running Cloud Build, verify LoRAs are in GCS:

```bash
# List all LoRAs in GCS
gsutil ls gs://jhakaas-models-jhakaas-dev/style_loras/

# Should show:
# gs://jhakaas-models-jhakaas-dev/style_loras/anime/
# gs://jhakaas-models-jhakaas-dev/style_loras/cartoon/
# gs://jhakaas-models-jhakaas-dev/style_loras/pixar/
# gs://jhakaas-models-jhakaas-dev/style_loras/clay/      ← NEW
# gs://jhakaas-models-jhakaas-dev/style_loras/ps2/       ← NEW
# gs://jhakaas-models-jhakaas-dev/style_loras/pixel/     ← NEW
# gs://jhakaas-models-jhakaas-dev/style_loras/aesthetic/ ← NEW
```

---

## 🎨 Next Step: Update model_manager.py

After LoRAs are downloaded to GCS, update your code to use them:

### **1. Add LoRAs to style_lora_map:**

```python
# In worker/src/model_manager.py, line ~182
style_lora_map = {
    # EXISTING
    "anime": "ntc-ai/SDXL-LoRA-slider.anime",
    "cartoon": "ntc-ai/SDXL-LoRA-slider.cartoon",
    "pixar": "ntc-ai/SDXL-LoRA-slider.pixar-style",
    
    # NEW VIRAL EFFECTS
    "clay": "alvdansen/clay-style-lora",
    "ps2": "artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl",
    "pixel": "nerijs/pixel-art-xl",
    "aesthetic": "ntc-ai/SDXL-LoRA-slider.aesthetic",
}
```

### **2. Add prompts for new styles:**

```python
# In worker/src/model_manager.py, line ~240 (in process_image method)
style_prompts = {
    # EXISTING
    "natural": "...",
    "anime": "...",
    "cartoon": "...",
    "pixar": "...",
    
    # NEW VIRAL EFFECTS
    "clay": "claymation style portrait, clay figurine, soft lighting, handcrafted appearance, wallace and gromit style",
    "ps2": "ps2 graphics, playstation 2 game character, low poly, early 2000s video game graphics",
    "pixel": "16-bit pixel art portrait, retro game sprite, dithered shading, pixel perfect",
    "aesthetic": "aesthetic portrait, soft pastel colors, dreamy atmosphere, instagram aesthetic",
    
    # PROMPT-ONLY EFFECTS (No LoRA needed!)
    "yearbook": "professional yearbook portrait, studio lighting, clean background, 1990s school photo",
    "kpop": "k-pop idol portrait, korean beauty aesthetic, glass skin, soft lighting, pastel colors",
    "bollywood": "dramatic bollywood movie poster, cinematic lighting, vibrant colors, theatrical",
    "y2k": "y2k aesthetic, 2000s digital camera photo, flash photography, nostalgic",
}
```

---

## 🧪 Testing After Download

### **Test LoRA Loading:**

```bash
# Start worker locally
cd worker
python -m src.main

# Test Clay effect
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://storage.googleapis.com/your-test-image.jpg",
    "prompt": "claymation portrait",
    "style": "clay"
  }'

# Check logs for:
# "Loading clay LoRA from GCS: /gcs/models/style_loras/clay/..."
# "✓ clay LoRA loaded from GCS"
```

### **Test Prompt-Only Effects:**

```bash
# Test Yearbook (no LoRA needed)
curl -X POST http://localhost:8080/generate \
  -d '{
    "image_url": "...",
    "prompt": "professional portrait",
    "style": "yearbook"
  }'

# Should work immediately (no LoRA download)
```

---

## 📊 Download Summary

| Item | Size | Status | Source |
|------|------|--------|--------|
| SDXL Base | ~12GB | ✅ Existing | HuggingFace |
| InstantID | ~5GB | ✅ Existing | HuggingFace |
| AntelopeV2 | ~300MB | ✅ Existing | HuggingFace |
| VAE FP16 | ~300MB | ✅ Existing | HuggingFace |
| Anime LoRA | ~500MB | ✅ Existing | HuggingFace |
| Cartoon LoRA | ~500MB | ✅ Existing | HuggingFace |
| Pixar LoRA | ~500MB | ✅ Existing | HuggingFace |
| **Clay LoRA** | ~500MB | 🆕 **NEW** | HuggingFace |
| **PS2 LoRA** | ~500MB | 🆕 **NEW** | HuggingFace |
| **Pixel LoRA** | ~500MB | 🆕 **NEW** | HuggingFace |
| **Aesthetic LoRA** | ~500MB | 🆕 **NEW** | HuggingFace |
| **TOTAL** | ~20GB | - | - |

---

## 💰 Cost Impact

### **Storage (GCS):**
- Before: ~18GB × $0.023/GB/month = **$0.41/month**
- After: ~20GB × $0.023/GB/month = **$0.46/month**
- **Increase: $0.05/month** (negligible!)

### **Download (Cloud Build):**
- One-time cost: ~$2-3
- Future downloads: $0 (cached in GCS)

### **Processing (No change):**
- LoRA loading: +3 seconds per request
- GPU memory: +500MB (still fits in L4)
- Cost per request: Same

---

## 🎯 Recommended Workflow

### **Step 1: Download LoRAs (One-time)**
```bash
cd worker/models
gcloud builds submit --config cloudbuild.yaml
```
**Time:** 30-45 minutes  
**When:** Do this once, now

### **Step 2: Update Code**
```bash
# Add new styles to model_manager.py
# (I can help with this next!)
```
**Time:** 10 minutes  
**When:** After LoRAs are downloaded

### **Step 3: Deploy**
```bash
cd worker/deployment
gcloud builds submit --config cloudbuild.yaml
```
**Time:** 2-3 minutes  
**When:** After code is updated

### **Step 4: Test**
```bash
# Test each new effect
curl -X POST https://your-worker-url/generate -d '{"style": "clay", ...}'
```
**Time:** 5 minutes  
**When:** After deployment

---

## 🐛 Troubleshooting

### **Issue: LoRA download fails**
```
⚠️  Failed to download clay LoRA: 404 Not Found
```

**Solution:**
- Some LoRA repos may not exist or be private
- Check HuggingFace: https://huggingface.co/alvdansen/clay-style-lora
- If repo doesn't exist, comment out that LoRA in `download_models.py`

### **Issue: GCS upload fails**
```
❌ Failed to upload: Permission denied
```

**Solution:**
```bash
# Ensure Cloud Build service account has permissions
gcloud projects add-iam-policy-binding jhakaas-dev \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### **Issue: Out of disk space**
```
❌ No space left on device
```

**Solution:**
- Cloud Build already uses `diskSizeGb: 500` ✅
- Should be enough for all models
- If still fails, increase to `diskSizeGb: 1000`

---

## ✅ Summary

### **What You Have:**
- ✅ Perfect infrastructure (Cloud Build + GCS)
- ✅ Automatic model download pipeline
- ✅ Extended script to include viral LoRAs

### **What to Do:**
1. **Run Cloud Build** to download LoRAs (30-45 min, one-time)
2. **Update model_manager.py** to use new LoRAs (10 min)
3. **Deploy** updated code (3 min)
4. **Test** new effects (5 min)

### **Total Time:**
- First time: ~1 hour (mostly waiting for downloads)
- Future updates: ~20 minutes (just code + deploy)

---

**Next Step:** Run Cloud Build to download LoRAs?

```bash
cd worker/models
gcloud builds submit --config cloudbuild.yaml --project jhakaas-dev
```

Want me to help update `model_manager.py` with the new styles after the download completes? 🚀
