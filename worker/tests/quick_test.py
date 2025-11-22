#!/usr/bin/env python3
"""Quick test - one image, one style"""
import sys
import subprocess
import requests

# Config
WORKER_URL = "https://jhakaas-worker-1098174162480.asia-southeast1.run.app"
TEST_IMAGE_URL = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400"
GCLOUD_PATH = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud"

def get_auth_token():
    result = subprocess.run(
        [GCLOUD_PATH, 'auth', 'print-identity-token'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def test_generate(style="natural", prompt="high quality portrait"):
    print(f"\n🧪 Testing {style} style...")
    print(f"📸 Image: {TEST_IMAGE_URL}")
    print(f"✍️  Prompt: {prompt}")

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "image_url": TEST_IMAGE_URL,
        "prompt": prompt,
        "style": style
    }

    print(f"\n⏳ Calling worker...")
    response = requests.post(
        f"{WORKER_URL}/generate",
        json=payload,
        headers=headers,
        timeout=120
    )

    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result}")

    if result.get("status") == "success":
        print(f"\n✅ SUCCESS!")
        print(f"Output URL: {result['output_url']}")
        return True
    else:
        print(f"\n❌ FAILED: {result}")
        return False

if __name__ == "__main__":
    style = sys.argv[1] if len(sys.argv) > 1 else "natural"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "high quality portrait"
    test_generate(style, prompt)
