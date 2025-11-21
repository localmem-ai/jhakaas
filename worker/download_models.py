import os
import requests
import argparse
from google.cloud import storage

# Configuration
MODELS = {
    "sd_xl_base_1.0.safetensors": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
    "ip-adapter.bin": "https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin",
    "GFPGANv1.4.pth": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"
}

def download_file(url, filename):
    print(f"Downloading {filename} from {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {filename}")

def upload_to_gcs(filename, bucket_name):
    print(f"Uploading {filename} to gs://{bucket_name}...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)
    print(f"Uploaded {filename}")
    # Clean up local file
    os.remove(filename)

def main():
    parser = argparse.ArgumentParser(description='Download and upload models to GCS')
    parser.add_argument('project_id', help='GCP Project ID')
    args = parser.parse_args()

    bucket_name = f"jhakaas-models-{args.project_id}"
    print(f"Target Bucket: {bucket_name}")

    print("Starting model download and upload...")
    for filename, url in MODELS.items():
        try:
            download_file(url, filename)
            upload_to_gcs(filename, bucket_name)
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    main()
