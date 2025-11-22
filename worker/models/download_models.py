#!/usr/bin/env python3
"""
Download InstantID, HyperLoRA, and Style LoRA models from Hugging Face
and upload them to GCS bucket.

This script runs in Cloud Build (no Docker needed).
"""

import os
import sys
from huggingface_hub import hf_hub_download, snapshot_download
from google.cloud import storage

# Configuration
BUCKET_NAME = "jhakaas-models-jhakaas-dev"
PROJECT_ID = "jhakaas-dev"

def upload_to_gcs(local_path, gcs_path):
    """Upload a file to GCS"""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)

    # Get file size for progress
    file_size = os.path.getsize(local_path)
    file_size_mb = file_size / (1024 * 1024)

    print(f"📤 Uploading {os.path.basename(local_path)} ({file_size_mb:.1f}MB) to gs://{BUCKET_NAME}/{gcs_path}")
    blob.upload_from_filename(local_path)
    print(f"✓ Uploaded {gcs_path}")

def download_instantid():
    """Download InstantID ControlNet and IP-Adapter"""
    print("\n" + "="*60)
    print("📥 Downloading InstantID Models")
    print("="*60)

    files_to_download = [
        ("InstantX/InstantID", "ControlNetModel/config.json", "instantid/ControlNetModel/config.json"),
        ("InstantX/InstantID", "ControlNetModel/diffusion_pytorch_model.safetensors", "instantid/ControlNetModel/diffusion_pytorch_model.safetensors"),
        ("InstantX/InstantID", "ip-adapter.bin", "instantid/ip-adapter.bin"),
    ]

    for repo_id, filename, gcs_path in files_to_download:
        print(f"\n📥 Downloading {filename} from {repo_id}...")
        try:
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir="./cache"
            )
            upload_to_gcs(local_path, gcs_path)
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            return False

    return True

def download_antelopev2():
    """Download InsightFace AntelopeV2 face analysis model"""
    print("\n" + "="*60)
    print("📥 Downloading AntelopeV2 Face Model")
    print("="*60)

    try:
        print("📥 Downloading from DIAMONIK7777/antelopev2...")
        local_dir = snapshot_download(
            repo_id="DIAMONIK7777/antelopev2",
            cache_dir="./cache"
        )

        # Upload all files
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if file.startswith('.'):  # Skip hidden files
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_dir)
                gcs_path = f"antelopev2/{relative_path}"
                upload_to_gcs(file_path, gcs_path)

        return True
    except Exception as e:
        print(f"❌ Failed to download AntelopeV2: {e}")
        return False

def download_sdxl_base():
    """Download SDXL base model"""
    print("\n" + "="*60)
    print("📥 Downloading SDXL Base Model")
    print("="*60)

    try:
        print("📥 Downloading stabilityai/stable-diffusion-xl-base-1.0...")
        local_dir = snapshot_download(
            repo_id="stabilityai/stable-diffusion-xl-base-1.0",
            cache_dir="./cache",
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"],  # Download FP16 variant
        )

        # Upload all files to GCS
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if file.startswith('.'):  # Skip hidden files
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_dir)
                gcs_path = f"sdxl-base/{relative_path}"
                upload_to_gcs(file_path, gcs_path)

        print("✓ SDXL base model downloaded")
        return True
    except Exception as e:
        print(f"❌ Failed to download SDXL base: {e}")
        return False

def download_vae_fp16():
    """Download VAE FP16 fix"""
    print("\n" + "="*60)
    print("📥 Downloading VAE FP16 Fix")
    print("="*60)

    try:
        print("📥 Downloading madebyollin/sdxl-vae-fp16-fix...")
        local_dir = snapshot_download(
            repo_id="madebyollin/sdxl-vae-fp16-fix",
            cache_dir="./cache"
        )

        # Upload all files to GCS
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if file.startswith('.'):  # Skip hidden files
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_dir)
                gcs_path = f"vae-fp16/{relative_path}"
                upload_to_gcs(file_path, gcs_path)

        print("✓ VAE FP16 fix downloaded")
        return True
    except Exception as e:
        print(f"❌ Failed to download VAE: {e}")
        return False

def download_style_loras():
    """Download community style LoRAs"""
    print("\n" + "="*60)
    print("📥 Downloading Style LoRAs")
    print("="*60)

    # These are LoRA sliders from ntc-ai
    loras = [
        ("ntc-ai/SDXL-LoRA-slider.anime", "anime"),
        ("ntc-ai/SDXL-LoRA-slider.cartoon", "cartoon"),
        ("ntc-ai/SDXL-LoRA-slider.pixar-style", "pixar"),
    ]

    for repo_id, style_name in loras:
        print(f"\n📥 Downloading {style_name} LoRA from {repo_id}...")
        try:
            # Download entire repo (slider LoRAs have specific structure)
            local_dir = snapshot_download(
                repo_id=repo_id,
                cache_dir="./cache"
            )

            # Upload all .safetensors files
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    if file.endswith('.safetensors'):
                        file_path = os.path.join(root, file)
                        gcs_path = f"style_loras/{style_name}/{file}"
                        upload_to_gcs(file_path, gcs_path)
        except Exception as e:
            print(f"⚠️  Failed to download {style_name} LoRA: {e}")
            # Continue with other LoRAs

    return True

def main():
    print("\n" + "="*60)
    print("🚀 InstantID Model Cache Builder")
    print("="*60)
    print(f"Target: gs://{BUCKET_NAME}/")
    print("="*60)

    success = True

    # Download all model components
    if not download_sdxl_base():
        success = False
        print("\n❌ Failed to download SDXL base model")

    if not download_vae_fp16():
        success = False
        print("\n❌ Failed to download VAE FP16 fix")

    if not download_instantid():
        success = False
        print("\n❌ Failed to download InstantID models")

    if not download_antelopev2():
        success = False
        print("\n❌ Failed to download AntelopeV2 model")

    if not download_style_loras():
        # LoRAs are optional, don't fail the build
        print("\n⚠️  Some style LoRAs failed to download")

    print("\n" + "="*60)
    if success:
        print("✅ Model cache build complete!")
        print(f"Models available at: gs://{BUCKET_NAME}/")
    else:
        print("❌ Model cache build failed!")
        print("Some critical models could not be downloaded.")
    print("="*60)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
