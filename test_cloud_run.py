#!/usr/bin/env python3
"""
Test script for Jhakaas Cloud Run GPU Worker
Performs health check and full end-to-end image generation test
"""
import requests
import time
import sys

# Cloud Run URL (will be set after deployment)
WORKER_URL = None  # Set this to your Cloud Run URL

# Test image URL (public image for testing)
TEST_IMAGE_URL = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400"

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
        response = requests.get(f"{WORKER_URL}/health", timeout=30)

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

def test_generate():
    """Test 2: Full Generation - Test AI image processing"""
    print("\n" + "="*60)
    print("TEST 2: IMAGE GENERATION")
    print("="*60)

    try:
        payload = {
            "image_url": TEST_IMAGE_URL,
            "prompt": "professional headshot, studio lighting, cinematic",
            "style": "cinematic"
        }

        print(f"\nCalling: {WORKER_URL}/generate")
        print(f"Image URL: {TEST_IMAGE_URL}")
        print(f"Prompt: {payload['prompt']}")
        print(f"Style: {payload['style']}")
        print("\n⏳ Processing (this may take 30-60 seconds)...")

        start_time = time.time()
        response = requests.post(
            f"{WORKER_URL}/generate",
            json=payload,
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
                print(f"✅ Output saved to: {data.get('output_url')}")
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
