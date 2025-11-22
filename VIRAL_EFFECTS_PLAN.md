# Viral Effects Implementation Plan

Build order for proven viral effects using the current InstantID stack.

---

## Phase 1: Extend Current Test Suite (Week 1)

### Already Have ✅
1. **Anime/Manga** - 155.3M videos on TikTok
2. **Pixar/Disney** - Consistently trending

### Add Immediately 🚀
3. **AI Clay/Claymation** - Top 10 trending 2025
4. **PS2 Graphics** - Nostalgia viral effect
5. **Pixel Art** - Retro gaming aesthetic
6. **AI Mermaid** - Trending since May 2025

---

## Technical Implementation

### 1. AI Clay/Claymation Filter

**LoRA Model:**
```python
# HuggingFace: https://huggingface.co/alvdansen/clay-style-lora
lora_path = "alvdansen/clay-style-lora"
```

**Prompt Template:**
```python
{
    "style": "clay",
    "prompt": "claymation style portrait, clay figurine, soft lighting, handcrafted appearance",
    "lora_weight": 0.9,  # Strong clay effect
    "controlnet_scale": 0.8
}
```

**Expected Result:**
- Wallace & Gromit / Shaun the Sheep aesthetic
- Soft, matte textures
- Rounded features
- Stop-motion animation look

---

### 2. PS2 Graphics Filter

**LoRA Model:**
```python
# HuggingFace: https://huggingface.co/artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl
lora_path = "artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl"
# Or use PS2-specific LoRA if available
```

**Prompt Template:**
```python
{
    "style": "ps2",
    "prompt": "ps2 graphics, playstation 2 game character, low poly, early 2000s video game graphics",
    "lora_weight": 0.85,
    "controlnet_scale": 0.7,  # Lower to allow more stylization
    "negative_prompt": "high resolution, modern graphics, photorealistic"
}
```

**Post-Processing:**
```python
def ps2_post_process(image):
    # Reduce color depth (PS2 had limited color palette)
    image = reduce_colors(image, colors=256)

    # Add CRT scanlines effect
    image = add_scanlines(image, opacity=0.1)

    # Slight pixelation
    image = pixelate_subtle(image, factor=0.95)

    # Add chromatic aberration (CRT TVs)
    image = chromatic_aberration(image, strength=2)

    return image
```

---

### 3. Pixel Art Filter

**Approach 1: LoRA-based**
```python
# HuggingFace: https://huggingface.co/nerijs/pixel-art-xl
lora_path = "nerijs/pixel-art-xl"
```

**Approach 2: Programmatic (Faster)**
```python
def create_pixel_art(image, pixel_size=8):
    # Downscale
    h, w = image.size
    small = image.resize((w // pixel_size, h // pixel_size), Image.NEAREST)

    # Reduce colors (NES/SNES style)
    small = small.quantize(colors=16, method=2)

    # Upscale back (no antialiasing)
    pixelated = small.resize((w, h), Image.NEAREST)

    # Add pixel grid overlay (optional)
    pixelated = add_pixel_grid(pixelated, pixel_size)

    return pixelated
```

**Hybrid Approach (Best Results):**
```python
{
    "style": "pixel",
    "prompt": "16-bit pixel art portrait, retro game sprite, dithered shading",
    "lora_weight": 0.7,
    "post_process": create_pixel_art  # Apply programmatic pixelation after
}
```

---

### 4. AI Mermaid Effect

**LoRA Models:**
```python
# Option 1: Fantasy/Mermaid LoRA
lora_path = "Joeythemonster/mermaid-ariel-lora-for-sdxl"

# Option 2: Underwater + scales texture
lora_paths = [
    "fantasy-creatures-lora",
    "underwater-scene-lora"
]
```

**Prompt Template:**
```python
{
    "style": "mermaid",
    "prompt": "mermaid portrait, shimmering fish scales, iridescent skin, underwater glow, flowing hair, ethereal beauty, ocean depths",
    "lora_weight": 0.8,
    "controlnet_scale": 0.85,  # Preserve face structure
    "negative_prompt": "human legs, dry skin, land background"
}
```

**Post-Processing (Add Shimmer):**
```python
def add_mermaid_effects(image):
    # Add iridescent shimmer to skin/scales
    shimmer_mask = detect_skin_regions(image)
    image = add_shimmer_particles(image, mask=shimmer_mask)

    # Blue/green underwater color grade
    image = underwater_color_grade(image)

    # Add bubbles
    image = add_floating_bubbles(image, count=random(5, 15))

    return image
```

---

## Code Implementation

### Update `test_styles.py`

```python
STYLE_TESTS = [
    # ... existing styles ...

    # NEW VIRAL STYLES
    {
        "style": "clay",
        "prompt": "claymation style portrait",
        "description": "AI Clay/Claymation - Wallace & Gromit style",
        "lora": "alvdansen/clay-style-lora",
        "lora_weight": 0.9
    },
    {
        "style": "ps2",
        "prompt": "ps2 game character",
        "description": "PlayStation 2 Graphics - Early 2000s gaming",
        "lora": "artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl",
        "lora_weight": 0.85,
        "post_process": "ps2_effects"
    },
    {
        "style": "pixel",
        "prompt": "16-bit pixel art portrait",
        "description": "Pixel Art - Retro game sprite",
        "lora": "nerijs/pixel-art-xl",
        "lora_weight": 0.7,
        "post_process": "pixelate"
    },
    {
        "style": "mermaid",
        "prompt": "mermaid portrait with shimmering scales",
        "description": "AI Mermaid - Fantasy transformation",
        "lora": "Joeythemonster/mermaid-ariel-lora-for-sdxl",
        "lora_weight": 0.8,
        "post_process": "underwater_shimmer"
    }
]
```

### Update `model_manager.py`

Add LoRA loading capability:

```python
def load_style_lora(self, style_name, lora_path, weight=0.8):
    """Load a style LoRA from HuggingFace or GCS"""

    if style_name in self.style_loras:
        print(f"✓ LoRA '{style_name}' already loaded")
        return

    try:
        # Check GCS first
        gcs_lora_path = f"/gcs/models/loras/{style_name}"

        if os.path.exists(gcs_lora_path):
            print(f"Loading {style_name} LoRA from GCS...")
            self.pipe.load_lora_weights(gcs_lora_path)
        else:
            print(f"Downloading {style_name} LoRA from HuggingFace...")
            self.pipe.load_lora_weights(lora_path)

        # Store the loaded LoRA info
        self.style_loras[style_name] = {
            "path": lora_path,
            "weight": weight,
            "loaded": True
        }

        print(f"✓ LoRA '{style_name}' loaded successfully")

    except Exception as e:
        print(f"❌ Failed to load LoRA '{style_name}': {e}")
        # Fallback: use prompt engineering only
        self.style_loras[style_name] = {
            "loaded": False,
            "fallback": True
        }

def apply_style(self, style_name, weight=None):
    """Apply a loaded LoRA style to the pipeline"""

    if style_name not in self.style_loras:
        print(f"⚠️  Style '{style_name}' not loaded")
        return False

    lora_info = self.style_loras[style_name]

    if not lora_info.get("loaded"):
        print(f"Using prompt-only fallback for '{style_name}'")
        return True

    # Set LoRA scale
    lora_weight = weight if weight else lora_info["weight"]
    self.pipe.set_adapters([style_name], adapter_weights=[lora_weight])

    return True
```

### Add Post-Processing Pipeline

```python
# worker/post_process.py

from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import cv2

def ps2_effects(image):
    """Apply PS2-era graphics effects"""
    img_array = np.array(image)

    # 1. Reduce color depth
    img_array = (img_array // 32) * 32

    # 2. Add CRT scanlines
    h, w = img_array.shape[:2]
    for i in range(0, h, 2):
        img_array[i, :] = img_array[i, :] * 0.9

    # 3. Slight blur (CRT softness)
    img_array = cv2.GaussianBlur(img_array, (3, 3), 0.5)

    return Image.fromarray(img_array.astype('uint8'))

def pixelate(image, pixel_size=8):
    """Create pixel art effect"""
    w, h = image.size

    # Downscale
    small = image.resize(
        (w // pixel_size, h // pixel_size),
        Image.NEAREST
    )

    # Reduce colors
    small = small.quantize(colors=16)

    # Upscale
    return small.resize((w, h), Image.NEAREST)

def underwater_shimmer(image):
    """Add mermaid underwater effects"""
    img_array = np.array(image)

    # 1. Underwater color grade (blue-green tint)
    img_array[:, :, 0] = img_array[:, :, 0] * 0.8  # Reduce red
    img_array[:, :, 2] = img_array[:, :, 2] * 1.1  # Boost blue

    # 2. Add shimmer (random bright spots)
    shimmer = np.random.rand(*img_array.shape[:2]) > 0.98
    shimmer_color = np.array([200, 220, 255])
    img_array[shimmer] = shimmer_color

    # 3. Soft glow
    img = Image.fromarray(img_array.astype('uint8'))
    glow = img.filter(ImageFilter.GaussianBlur(radius=2))

    return Image.blend(img, glow, alpha=0.3)

# Export functions
POST_PROCESSORS = {
    "ps2_effects": ps2_effects,
    "pixelate": pixelate,
    "underwater_shimmer": underwater_shimmer
}
```

---

## LoRA Model Cache Strategy

### Download LoRAs to GCS (One-time)

Create `download_loras.py`:

```python
#!/usr/bin/env python3
"""
Download viral effect LoRAs to GCS model cache
Run once to cache all LoRAs
"""

from huggingface_hub import snapshot_download
from google.cloud import storage
import os

LORAS_TO_CACHE = {
    "clay": "alvdansen/clay-style-lora",
    "ps2": "artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl",
    "pixel": "nerijs/pixel-art-xl",
    "mermaid": "Joeythemonster/mermaid-ariel-lora-for-sdxl",
}

def download_and_upload_lora(style_name, repo_id):
    print(f"\n📥 Downloading {style_name} LoRA: {repo_id}")

    # Download to temp
    local_path = snapshot_download(
        repo_id=repo_id,
        cache_dir="/tmp/lora_cache"
    )

    # Upload to GCS
    bucket = storage.Client().bucket("jhakaas-models-jhakaas-dev")
    gcs_prefix = f"loras/{style_name}/"

    for root, dirs, files in os.walk(local_path):
        for file in files:
            local_file = os.path.join(root, file)
            gcs_path = gcs_prefix + file

            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(local_file)
            print(f"  ✓ Uploaded {file}")

    print(f"✅ {style_name} LoRA cached to GCS")

if __name__ == "__main__":
    for style, repo in LORAS_TO_CACHE.items():
        download_and_upload_lora(style, repo)

    print("\n🎉 All LoRAs cached successfully!")
```

Run via Cloud Build:
```bash
cd model_cache
# Update cloudbuild.yaml to include LoRA downloads
gcloud builds submit --config cloudbuild-loras.yaml
```

---

## Testing Strategy

### 1. Quick Test (Local/Fast)
```bash
# Test with just one style
python3 test_styles.py --style clay --quick
```

### 2. Full Viral Suite
```python
# Update test_styles.py to include all viral effects
VIRAL_STYLES = ["anime", "clay", "ps2", "pixel", "pixar", "mermaid"]

python3 test_styles.py --styles viral
```

### 3. A/B Testing (Production)
```python
# Track which effects get the most:
# - Generations
# - Shares
# - Processing time
# - User ratings

viral_metrics = {
    "anime": {"views": 0, "shares": 0, "avg_time": 0},
    "clay": {"views": 0, "shares": 0, "avg_time": 0},
    # ...
}
```

---

## Rollout Plan

### Day 1-2: Setup
- [ ] Download LoRAs to GCS cache
- [ ] Update model_manager.py with LoRA loading
- [ ] Add post-processing functions
- [ ] Test each effect individually

### Day 3-4: Integration
- [ ] Update test_styles.py with new effects
- [ ] Run full test suite
- [ ] Generate HTML comparison reports
- [ ] Verify quality of all effects

### Day 5-7: Launch
- [ ] Deploy to production
- [ ] Update API to expose new styles
- [ ] Create marketing materials (example images)
- [ ] Soft launch to test users

### Week 2: Optimize
- [ ] A/B test which effects are most viral
- [ ] Optimize prompts based on results
- [ ] Fine-tune LoRA weights
- [ ] Add more variations (e.g., different pixel sizes)

---

## Expected Performance

### Processing Time (with L4 GPU)
- **Anime/Manga**: ~8-12 seconds
- **Clay**: ~8-12 seconds
- **PS2 Graphics**: ~10-14 seconds (includes post-process)
- **Pixel Art**: ~6-8 seconds (lighter post-process)
- **Pixar**: ~8-12 seconds
- **Mermaid**: ~10-14 seconds (includes shimmer effects)

### Quality Targets
- **Face Preservation**: >85% similarity (InstantID)
- **Style Accuracy**: Recognizable as intended style
- **Artifact Rate**: <5% (weird/broken generations)
- **User Satisfaction**: >4.0/5.0 stars

---

## Monetization Ideas

### Freemium Model
- **Free**: 3 styles (Anime, Pixar, one seasonal)
- **Premium**: All 6+ styles, unlimited generations
- **Pro**: Priority processing, HD exports, API access

### Pricing Tiers
- **Free**: 10 generations/month
- **Basic ($4.99/mo)**: 100 generations/month, all styles
- **Pro ($14.99/mo)**: Unlimited, 4K exports, no watermark
- **API ($0.10/image)**: For developers/businesses

---

## Marketing Hooks

### Social Media Copy
1. **"Turn yourself into a PS2 game character!"** (Nostalgia)
2. **"Mermaid transformation in 10 seconds"** (Fantasy)
3. **"Become an anime character with AI"** (Identity)
4. **"Claymation yourself - Wallace & Gromit style!"** (Unique)
5. **"8-bit pixel art profile pic generator"** (Gaming)

### Viral Mechanics
- Before/After reveals
- "Which style suits you best?" quiz
- Friend comparison challenges
- Seasonal themes (Mermaid for summer, etc.)

---

**Status**: Ready to implement
**Next Step**: Download LoRAs and update model_manager.py
**Timeline**: 1 week to full launch
