#!/usr/bin/env python3
"""
Test script for local Docker container (no authentication needed)
"""
import requests
import time
import sys

# Local Docker URL
WORKER_URL = "http://localhost:8080"

def test_health():
    """Test health check"""
    print("\n" + "="*60)
    print("TEST: HEALTH CHECK (Local)")
    print("="*60)

    try:
        print(f"Calling: {WORKER_URL}/health")
        response = requests.get(f"{WORKER_URL}/health", timeout=30)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            if data.get("status") == "healthy":
                print("✅ Service is healthy")
            if data.get("gpu_available"):
                print("✅ GPU is available")
            else:
                print("⚠️  Running on CPU (will be slow)")
            if data.get("models_loaded"):
                print("✅ Models loaded successfully")

            return True
        else:
            print(f"❌ Health check failed")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local container")
        print("\n💡 Did you start the container?")
        print("   Run: docker-compose up")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_generate():
    """Test simple generation"""
    print("\n" + "="*60)
    print("TEST: IMAGE GENERATION (Local)")
    print("="*60)

    try:
        payload = {
            "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
            "prompt": "professional headshot, studio lighting",
            "style": "cinematic"
        }

        print(f"\nCalling: {WORKER_URL}/generate")
        print(f"Prompt: {payload['prompt']}")
        print("\n⏳ Processing (CPU will take 5-10 minutes, GPU ~15 seconds)...")

        start_time = time.time()
        response = requests.post(
            f"{WORKER_URL}/generate",
            json=payload,
            timeout=600  # 10 minutes for CPU
        )
        elapsed = time.time() - start_time

        print(f"\nStatus Code: {response.status_code}")
        print(f"Processing Time: {elapsed:.1f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse: {data}")
            print("\n✅ Generation successful!")
            return True
        else:
            print(f"❌ Generation failed")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (try increasing timeout for CPU)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║   LOCAL DOCKER TEST (NO GPU)                         ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    health_passed = test_health()

    if not health_passed:
        sys.exit(1)

    print("\n🤔 Do you want to test image generation? (very slow on CPU)")
    response = input("   Press Enter to skip, or type 'yes' to continue: ")

    if response.lower() == 'yes':
        test_generate()
    else:
        print("\n⏭️  Skipping generation test")

    print("\n✅ Local test complete!")

if __name__ == "__main__":
    main()
