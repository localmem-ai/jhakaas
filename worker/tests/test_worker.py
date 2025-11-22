import requests
import json

WORKER_URL = "http://localhost:8080"

def test_health():
    print("Testing Health...")
    try:
        r = requests.get(f"{WORKER_URL}/health")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {e}")

def test_generate():
    print("\nTesting Generation...")
    payload = {
        "image_url": "https://example.com/selfie.jpg",
        "prompt": "bollywood movie poster, hero, dramatic lighting",
        "style": "bollywood"
    }
    try:
        r = requests.post(f"{WORKER_URL}/generate", json=payload)
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    test_health()
    test_generate()
