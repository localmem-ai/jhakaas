# Worker Tests

Clean test plugin system for Cloud Run worker style transfer.

## Structure

```
tests/
├── config.py                    # Test configuration (19 styles!)
├── test_styles.py               # Test ALL styles (full suite)
├── test_viral_effects.py        # Test ONLY viral effects (NEW!)
├── quick_test.py                # Quick single-style test
├── test-images/                 # Place test images here
├── results/                     # Test outputs (gitignored)
│   ├── html/                   # HTML reports
│   └── images/                 # Generated images
└── utils/
    └── generate_html_report.py  # Report generator
```

## Quick Start

1. **Add test images** to `test-images/` folder:
   ```bash
   cp ~/my-portrait.jpg worker/tests/test-images/
   ```

2. **Run tests:**
   ```bash
   cd worker/tests
   
   # Test all 19 styles (full suite)
   python test_styles.py
   
   # Test ONLY viral effects (12 new styles)
   python test_viral_effects.py
   
   # Quick test single style
   python quick_test.py yearbook "professional portrait"
   ```

3. **View results** in `results/html/test_report_*.html`

## Test Scripts

### **test_styles.py** - Full Test Suite
Tests all 19 styles (7 existing + 12 new viral effects)
- Takes ~30-40 minutes
- Generates comprehensive HTML report
- Best for full validation

### **test_viral_effects.py** - Viral Effects Only (NEW!)
Tests only the 12 new viral effects
- Takes ~15-20 minutes
- Focused on new features
- Best for validating viral effects

### **quick_test.py** - Single Style Test
Tests one style quickly
- Takes ~15 seconds
- Best for debugging
- Usage: `python quick_test.py <style> <prompt>`

## How It Works

1. Reads all images from `test-images/` (.jpg, .jpeg, .png)
2. Uploads them to GCS temporary bucket
3. Calls Cloud Run worker API for each style
4. Downloads generated images to `results/images/`
5. Creates HTML comparison report in `results/html/`

## Configuration

Edit [config.py](config.py) to customize:
- `WORKER_URL` - Cloud Run worker URL
- `TEST_BUCKET` - GCS bucket for uploading test images
- `STYLES` - List of styles to test (19 total)
- `QUICK_TEST_STYLES` - Subset for quick testing
- `VIRAL_EFFECTS_ONLY` - Just viral effects
- Output directories

## Requirements

- Python 3.8+ with `requests` and `Pillow`
- GCloud CLI authenticated (`gcloud auth login`)
- Access to Cloud Run worker service
- GCS bucket for temporary test image uploads

## Supported Styles (19 Total)

### **Existing Styles (8):**
- Natural, Anime, Cartoon, Pixar
- Bollywood, Cinematic, Vintage, Glamour

### **NEW Viral Effects - LoRA-based (4):**
- Clay/Claymation (Wallace & Gromit style)
- PS2 Graphics (retro gaming)
- Pixel Art (16-bit retro)
- Aesthetic (Instagram pastel)

### **NEW Viral Effects - Prompt-only (8):**
- Yearbook Photo (90s school photo)
- K-Pop Idol (Korean beauty aesthetic)
- Bollywood Poster (dramatic movie poster)
- Y2K/2000s (early 2000s digital camera)
- Couple Aesthetic (romantic goals)
- Mermaid (fantasy transformation)
- Sigma/Chad (dramatic portrait)
- Thug Life (urban street style)

**Note:** Prompt-only styles work immediately. LoRA-based styles require LoRAs to be downloaded to GCS first.

## Examples

```bash
# Test all styles
python test_styles.py

# Test only viral effects
python test_viral_effects.py

# Quick test yearbook effect
python quick_test.py yearbook "professional portrait"

# Quick test K-Pop effect
python quick_test.py kpop "portrait"

# Quick test clay effect (needs LoRA)
python quick_test.py clay "portrait"
```

Configure in [config.py](config.py)

