"""Test configuration"""
import os

# Worker API URL
WORKER_URL = os.getenv(
    "WORKER_URL",
    "https://jhakaas-worker-jv4qpcriga-as.a.run.app"
)

# GCloud path for auth
GCLOUD_PATH = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud"

# Test images directory
TEST_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "test-images")

# Results directory
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
HTML_DIR = os.path.join(RESULTS_DIR, "html")
IMAGES_DIR = os.path.join(RESULTS_DIR, "images")

# GCS bucket for uploading test images (they need to be accessible via URL)
TEST_BUCKET = os.getenv("TEST_BUCKET", "jhakaas-images-jhakaas-dev")

# Styles to test
STYLES = [
    # ============================================================================
    # EXISTING STYLES
    # ============================================================================
    {
        "name": "Natural",
        "style": "natural",
        "prompt": "high quality portrait, professional photography",
        "description": "Minimal changes, natural look"
    },
    {
        "name": "Anime",
        "style": "anime",
        "prompt": "portrait",
        "description": "Anime art with vibrant colors"
    },
    {
        "name": "Cartoon",
        "style": "cartoon",
        "prompt": "portrait",
        "description": "Cartoon with bold outlines"
    },
    {
        "name": "Pixar",
        "style": "pixar",
        "prompt": "portrait",
        "description": "Pixar 3D animation style"
    },
    {
        "name": "Bollywood",
        "style": "bollywood",
        "prompt": "dramatic portrait",
        "description": "Dramatic Bollywood aesthetic"
    },
    {
        "name": "Cinematic",
        "style": "cinematic",
        "prompt": "dramatic portrait, moody lighting",
        "description": "Cinematic film photography"
    },
    {
        "name": "Vintage",
        "style": "vintage",
        "prompt": "classic portrait",
        "description": "Classic vintage photography"
    },
    {
        "name": "Glamour",
        "style": "glamour",
        "prompt": "elegant portrait",
        "description": "Elegant glamour photography"
    },
    
    # ============================================================================
    # NEW VIRAL EFFECTS (LoRA-based)
    # ============================================================================
    {
        "name": "Clay/Claymation",
        "style": "clay",
        "prompt": "portrait",
        "description": "Wallace & Gromit style claymation"
    },
    {
        "name": "PS2 Graphics",
        "style": "ps2",
        "prompt": "game character",
        "description": "PlayStation 2 retro gaming graphics"
    },
    {
        "name": "Pixel Art",
        "style": "pixel",
        "prompt": "portrait",
        "description": "16-bit retro pixel art"
    },
    {
        "name": "Aesthetic",
        "style": "aesthetic",
        "prompt": "portrait",
        "description": "Instagram aesthetic with pastel colors"
    },
    
    # ============================================================================
    # NEW VIRAL EFFECTS (Prompt-only, no LoRA needed)
    # ============================================================================
    {
        "name": "Yearbook Photo",
        "style": "yearbook",
        "prompt": "professional portrait",
        "description": "90s school yearbook photo style"
    },
    {
        "name": "K-Pop Idol",
        "style": "kpop",
        "prompt": "portrait",
        "description": "K-Pop idol with glass skin aesthetic"
    },
    {
        "name": "Bollywood Poster",
        "style": "bollywood_poster",
        "prompt": "dramatic portrait",
        "description": "Dramatic Bollywood movie poster"
    },
    {
        "name": "Y2K/2000s",
        "style": "y2k",
        "prompt": "party photo",
        "description": "Early 2000s digital camera aesthetic"
    },
    {
        "name": "Couple Aesthetic",
        "style": "couple_aesthetic",
        "prompt": "romantic portrait",
        "description": "Instagram couple goals aesthetic"
    },
    {
        "name": "Mermaid",
        "style": "mermaid",
        "prompt": "fantasy portrait",
        "description": "Mermaid transformation with scales"
    },
    {
        "name": "Sigma/Chad",
        "style": "sigma",
        "prompt": "portrait",
        "description": "Dramatic sigma male aesthetic"
    },
    {
        "name": "Thug Life",
        "style": "thug_life",
        "prompt": "cool portrait",
        "description": "Urban street photography style"
    },
]

# Quick test subset (for fast iteration)
QUICK_TEST_STYLES = [
    "natural",
    "anime",
    "yearbook",  # NEW: Easy to test, no LoRA
    "kpop",      # NEW: Easy to test, no LoRA
    "clay",      # NEW: LoRA-based
]

# Viral effects only (for focused testing)
VIRAL_EFFECTS_ONLY = [
    "clay",
    "ps2",
    "pixel",
    "aesthetic",
    "yearbook",
    "kpop",
    "bollywood_poster",
    "y2k",
    "couple_aesthetic",
    "mermaid",
    "sigma",
    "thug_life",
]

