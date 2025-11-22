#!/usr/bin/env python3
"""
Test script for Jhakaas Cloud Run GPU Worker
Performs health check and full end-to-end image generation test
"""
import requests
import time
import sys
import os
import subprocess
from PIL import Image
from io import BytesIO

# Cloud Run URL (will be set after deployment)
WORKER_URL = "https://jhakaas-worker-1098174162480.asia-southeast1.run.app"

def get_auth_token():
    """Get identity token for authentication"""
    result = subprocess.run(
        ['/opt/homebrew/share/google-cloud-sdk/bin/gcloud', 'auth', 'print-identity-token'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# Test scenarios with different prompts and images
TEST_SCENARIOS = [
    {
        "name": "Professional Headshot",
        "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "prompt": "professional headshot, studio lighting, sharp focus, cinematic",
        "style": "cinematic"
    },
    {
        "name": "Portrait Enhancement",
        "image_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
        "prompt": "beautiful portrait, natural lighting, high quality, professional photography",
        "style": "natural"
    },
    {
        "name": "Business Professional",
        "image_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
        "prompt": "corporate headshot, professional attire, office background, high resolution",
        "style": "corporate"
    }
]

# Output directory for results
OUTPUT_DIR = "test_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_image(url):
    """Download image from URL and return PIL Image"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def create_comparison(original_img, generated_img, scenario_name, output_path):
    """Create side-by-side comparison of original and generated images"""
    try:
        # Resize images to same height for comparison
        height = 400
        original_aspect = original_img.width / original_img.height
        generated_aspect = generated_img.width / generated_img.height

        original_resized = original_img.resize(
            (int(height * original_aspect), height),
            Image.Resampling.LANCZOS
        )
        generated_resized = generated_img.resize(
            (int(height * generated_aspect), height),
            Image.Resampling.LANCZOS
        )

        # Create comparison image
        total_width = original_resized.width + generated_resized.width + 20
        comparison = Image.new('RGB', (total_width, height + 60), 'white')

        # Paste images
        comparison.paste(original_resized, (10, 40))
        comparison.paste(generated_resized, (original_resized.width + 20, 40))

        # Save comparison
        comparison.save(output_path)
        print(f"   Comparison saved to: {output_path}")

        # Open in default viewer
        os.system(f'open "{output_path}"')

        return True
    except Exception as e:
        print(f"Error creating comparison: {e}")
        return False

def test_health():
    """Test 1: Health Check - Verify service is up and GPU is available"""
    print("\n" + "="*60)
    print("TEST 1: HEALTH CHECK")
    print("="*60)

    if not WORKER_URL:
        print("❌ ERROR: WORKER_URL not set. Please update this script with your Cloud Run URL.")
        sys.exit(1)

    try:
        print(f"Calling: {WORKER_URL}/health")
        headers = {"Authorization": f"Bearer {get_auth_token()}"}
        response = requests.get(f"{WORKER_URL}/health", headers=headers, timeout=30)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            # Check critical fields
            if data.get("status") == "healthy":
                print("✅ Service is healthy")
            else:
                print("⚠️  Service status is not healthy")

            if data.get("gpu_available"):
                print("✅ GPU is available")
            else:
                print("❌ GPU not available!")

            if data.get("models_loaded"):
                print("✅ Models loaded successfully")
            else:
                print("⚠️  Models not loaded yet")

            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (service may be cold starting)")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_generate_scenario(scenario, scenario_num, total_scenarios):
    """Test image generation for a specific scenario"""
    print("\n" + "="*60)
    print(f"TEST {scenario_num}/{total_scenarios}: {scenario['name'].upper()}")
    print("="*60)

    try:
        # Download original image first
        print(f"\n📥 Downloading original image...")
        original_img = download_image(scenario['image_url'])
        if not original_img:
            print("❌ Failed to download original image")
            return False

        # Prepare payload
        payload = {
            "image_url": scenario['image_url'],
            "prompt": scenario['prompt'],
            "style": scenario['style']
        }

        print(f"\nCalling: {WORKER_URL}/generate")
        print(f"Image URL: {scenario['image_url']}")
        print(f"Prompt: {scenario['prompt']}")
        print(f"Style: {scenario['style']}")
        print("\n⏳ Processing (this may take 30-60 seconds)...")

        start_time = time.time()
        headers = {"Authorization": f"Bearer {get_auth_token()}"}
        response = requests.post(
            f"{WORKER_URL}/generate",
            json=payload,
            headers=headers,
            timeout=120  # 2 minute timeout for AI processing
        )
        elapsed = time.time() - start_time

        print(f"\nStatus Code: {response.status_code}")
        print(f"Processing Time: {elapsed:.1f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse:")
            print(f"  Status: {data.get('status')}")
            print(f"  Output URL: {data.get('output_url')}")
            print(f"  Parameters: {data.get('params')}")

            if data.get("status") == "success":
                print("\n✅ Image generation successful!")

                # Download generated image
                print(f"\n📥 Downloading generated image...")
                generated_img = download_image(data.get('output_url'))

                if generated_img:
                    # Create comparison
                    output_filename = f"{scenario['name'].lower().replace(' ', '_')}_comparison.jpg"
                    output_path = os.path.join(OUTPUT_DIR, output_filename)

                    print(f"\n🖼️  Creating side-by-side comparison...")
                    if create_comparison(original_img, generated_img, scenario['name'], output_path):
                        print(f"✅ Comparison created and opened!")
                    else:
                        print(f"⚠️  Could not create comparison")

                return True
            elif data.get("mock_mode"):
                print("\n⚠️  Service is in mock mode (models not loaded)")
                return False
            else:
                print(f"\n❌ Generation failed: {data}")
                return False
        else:
            print(f"❌ Generation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (GPU processing may be too slow)")
        return False
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        return False

def test_generate():
    """Test 2: Full Generation - Test all scenarios"""
    print("\n" + "="*60)
    print(f"IMAGE GENERATION TESTS - {len(TEST_SCENARIOS)} SCENARIOS")
    print("="*60)

    results = []
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        success = test_generate_scenario(scenario, i, len(TEST_SCENARIOS))
        results.append({
            "name": scenario["name"],
            "success": success
        })
        if i < len(TEST_SCENARIOS):
            print("\n⏸️  Pausing 2 seconds before next test...")
            time.sleep(2)

    # Print summary
    print("\n" + "="*60)
    print("GENERATION TEST SUMMARY")
    print("="*60)
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{result['name']}: {status}")

    all_passed = all(r["success"] for r in results)
    return all_passed

def main():
    """Run both tests"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║   JHAKAAS CLOUD RUN GPU WORKER - TEST SUITE          ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # Test 1: Health Check
    health_passed = test_health()

    if not health_passed:
        print("\n❌ Health check failed. Skipping generation test.")
        sys.exit(1)

    # Test 2: Full Generation (only if health passed)
    print("\n🚀 Health check passed! Proceeding to full generation test...")
    time.sleep(2)  # Brief pause

    generation_passed = test_generate()

    # Final Summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Health Check:      {'✅ PASS' if health_passed else '❌ FAIL'}")
    print(f"Image Generation:  {'✅ PASS' if generation_passed else '❌ FAIL'}")

    if health_passed and generation_passed:
        print("\n🎉 All tests passed! Worker is fully functional.")
        print(f"\n📁 Results saved in: {OUTPUT_DIR}/")
        print("   Check the comparison images to see before/after results!")
        sys.exit(0)
    elif health_passed:
        print("\n⚠️  Health check passed but generation failed.")
        print("   Check Cloud Run logs for details.")
        sys.exit(1)
    else:
        print("\n❌ Tests failed. Check Cloud Run deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
