#!/usr/bin/env python3
"""
Clean test plugin for Cloud Run worker style transfer

Reads images from test-images/, uploads to GCS, tests all styles,
and generates HTML comparison reports.
"""
import os
import sys
import time
import subprocess
import uuid
from pathlib import Path
from datetime import datetime

import requests
from PIL import Image
from io import BytesIO

# Import config
import config

# Create output directories
os.makedirs(config.HTML_DIR, exist_ok=True)
os.makedirs(config.IMAGES_DIR, exist_ok=True)


class WorkerAPIClient:
    """Client for interacting with worker API"""

    def __init__(self, worker_url=config.WORKER_URL):
        self.worker_url = worker_url
        self._token = None

    def _get_auth_token(self):
        """Get GCloud identity token"""
        if not self._token:
            result = subprocess.run(
                [config.GCLOUD_PATH, 'auth', 'print-identity-token'],
                capture_output=True,
                text=True
            )
            self._token = result.stdout.strip()
        return self._token

    def health_check(self):
        """Check worker health"""
        try:
            headers = {"Authorization": f"Bearer {self._get_auth_token()}"}
            response = requests.get(f"{self.worker_url}/health", headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def generate(self, image_url, prompt, style, engine="instantid"):
        """Generate styled image"""
        payload = {
            "image_url": image_url,
            "prompt": prompt,
            "style": style,
            "engine": engine
        }

        headers = {"Authorization": f"Bearer {self._get_auth_token()}"}
        response = requests.post(
            f"{self.worker_url}/generate",
            json=payload,
            headers=headers,
            timeout=120
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API returned {response.status_code}: {response.text}")


def upload_to_gcs(image_path):
    """Upload image to GCS and return public URL"""
    filename = Path(image_path).name
    gcs_path = f"gs://{config.TEST_BUCKET}/test-uploads/{filename}"

    result = subprocess.run(
        [config.GCLOUD_PATH, 'storage', 'cp', image_path, gcs_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Failed to upload to GCS: {result.stderr}")

    # Worker will download using authenticated GCS client, so no need to make public
    return f"https://storage.googleapis.com/{config.TEST_BUCKET}/test-uploads/{filename}"


def download_image(url):
    """Download image from URL (supports http/https and gs://)"""
    if url.startswith("gs://"):
        # Download from GCS using gcloud
        filename = f"/tmp/{uuid.uuid4()}.jpg"
        result = subprocess.run(
            [config.GCLOUD_PATH, 'storage', 'cp', url, filename],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"Failed to download from GCS: {result.stderr}")
        
        img = Image.open(filename)
        # Load into memory so we can delete the file
        img.load()
        os.remove(filename)
        return img
    else:
        # Download from HTTP
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))


def test_image_with_styles(image_path, client):
    """Test single image with all styles on both engines"""
    image_name = Path(image_path).stem
    print(f"\n{'='*70}")
    print(f"Testing: {image_name}")
    print(f"{'='*70}")

    # Upload test image
    print(f"Uploading to GCS...")
    image_url = upload_to_gcs(image_path)

    results = []
    engines = ["instantid", "ip_adapter"]
    
    for idx, style_config in enumerate(config.STYLES, 1):
        print(f"\n[{idx}/{len(config.STYLES)}] Testing {style_config['name']}...")
        
        style_result = {
            "style": style_config,
            "engines": {}
        }

        for engine in engines:
            print(f"   ⚙️  Engine: {engine}...", end="", flush=True)
            try:
                start_time = time.time()
                result = client.generate(
                    image_url=image_url,
                    prompt=style_config['prompt'],
                    style=style_config['style'],
                    engine=engine
                )
                elapsed = time.time() - start_time

                if result.get("status") == "success":
                    generated_img = download_image(result['output_url'])

                    # Save result
                    output_filename = f"{image_name}_{style_config['style']}_{engine}.jpg"
                    output_path = os.path.join(config.IMAGES_DIR, output_filename)
                    generated_img.save(output_path, quality=95)

                    print(f" ✅ ({elapsed:.1f}s)")

                    style_result["engines"][engine] = {
                        "image_path": output_path,
                        "time": elapsed,
                        "success": True
                    }
                else:
                    print(f" ❌ Failed: {result}")
                    style_result["engines"][engine] = {"success": False, "error": str(result)}

            except Exception as e:
                print(f" ❌ Error: {e}")
                style_result["engines"][engine] = {"success": False, "error": str(e)}
        
        results.append(style_result)

    return results


def generate_html_report(all_results):
    """Generate HTML comparison report"""
    from utils.generate_html_report import create_comparison_html

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(config.HTML_DIR, f"test_report_{timestamp}.html")

    create_comparison_html(all_results, report_file)
    return report_file


def main():
    """Run all tests"""
    print("="*70)
    print("Jhakaas Worker - Cloud Run Style Transfer Tests")
    print("="*70)

    # Initialize client
    client = WorkerAPIClient()

    # Health check
    print("\nChecking worker health...")
    health = client.health_check()
    print(f"Status: {health}")

    if not health.get("models_loaded"):
        print("\n⚠️  Warning: Models not loaded!")
        proceed = input("Continue? (y/n): ")
        if proceed.lower() != 'y':
            return

    # Find test images
    test_images = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        test_images.extend(Path(config.TEST_IMAGES_DIR).glob(ext))

    if not test_images:
        print(f"\n❌ No images found in {config.TEST_IMAGES_DIR}")
        print("Add test images and try again")
        return

    print(f"\nFound {len(test_images)} test image(s)")

    # Test each image
    all_results = {}
    for image_path in test_images:
        results = test_image_with_styles(str(image_path), client)
        all_results[image_path.name] = results

    # Generate report
    report_file = generate_html_report(all_results)

    print(f"\n{'='*70}")
    print(f"✅ Complete!")
    print(f"📊 Report: {report_file}")
    print(f"🖼️  Images: {config.IMAGES_DIR}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
