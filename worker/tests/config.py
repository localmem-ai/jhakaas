"""Test configuration"""
import os

# Worker API URL
WORKER_URL = os.getenv(
    "WORKER_URL",
    "https://jhakaas-worker-1098174162480.asia-southeast1.run.app"
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
TEST_BUCKET = os.getenv("TEST_BUCKET", "jhakaas-test-images-dev")

# Styles to test
STYLES = [
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
    }
]
