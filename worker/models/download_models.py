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

# Cache the storage client and bucket
_storage_client = None
_bucket = None

def get_gcs_bucket():
    """Get cached GCS bucket instance"""
    global _storage_client, _bucket
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
        _bucket = _storage_client.bucket(BUCKET_NAME)
    return _bucket

def check_gcs_exists(gcs_path):
    """Check if a file exists in GCS"""
    bucket = get_gcs_bucket()
    blob = bucket.blob(gcs_path)
    exists = blob.exists()
    if exists:
        print(f"✓ Already in GCS: {gcs_path}")
    return exists

def check_gcs_directory_exists(gcs_prefix):
    """Check if any files exist in GCS with the given prefix"""
    bucket = get_gcs_bucket()
    blobs = list(bucket.list_blobs(prefix=gcs_prefix, max_results=1))
    exists = len(blobs) > 0
    if exists:
        print(f"✓ Directory already in GCS: {gcs_prefix}")
    return exists

def upload_to_gcs(local_path, gcs_path):
    """Upload a file to GCS (only if it doesn't exist)"""
    if check_gcs_exists(gcs_path):
        print(f"⏭️  Skipping upload (already exists): {gcs_path}")
        return

    bucket = get_gcs_bucket()
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
    print("📥 Checking InstantID Models")
    print("="*60)

    # Check if InstantID directory already exists in GCS
    if check_gcs_directory_exists("instantid/"):
        print("✓ InstantID models already in GCS, skipping download")
        return True

    print("📥 Downloading InstantID Models from HuggingFace...")

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
    print("📥 Checking AntelopeV2 Face Model")
    print("="*60)

    # Check if AntelopeV2 directory already exists in GCS
    if check_gcs_directory_exists("antelopev2/"):
        print("✓ AntelopeV2 model already in GCS, skipping download")
        return True

    print("📥 Downloading AntelopeV2 from HuggingFace...")

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
    """Download SDXL base model (complete directory structure)"""
    print("\n" + "="*60)
    print("📥 Checking SDXL Base Model")
    print("="*60)

    # Check if SDXL base directory already exists in GCS
    if check_gcs_directory_exists("sdxl-base/"):
        print("✓ SDXL base model already in GCS, skipping download")
        return True

    print("📥 Downloading SDXL Base from HuggingFace...")

    try:
        print("📥 Downloading stabilityai/stable-diffusion-xl-base-1.0...")
        # Download complete model (no filters - we need all config files)
        local_dir = snapshot_download(
            repo_id="stabilityai/stable-diffusion-xl-base-1.0",
            cache_dir="./cache",
            ignore_patterns=["*.ckpt", "*.bin"]  # Only skip old checkpoint formats
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
    print("📥 Checking VAE FP16 Fix")
    print("="*60)

    # Check if VAE FP16 directory already exists in GCS
    if check_gcs_directory_exists("vae-fp16/"):
        print("✓ VAE FP16 fix already in GCS, skipping download")
        return True

    print("📥 Downloading VAE FP16 from HuggingFace...")

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
    """Download community style LoRAs (existing + viral effects)"""
    print("\n" + "="*60)
    print("📥 Checking Style LoRAs")
    print("="*60)

    # Existing LoRAs + New Viral Effect LoRAs
    loras = [
        # EXISTING (Already working)
        ("ntc-ai/SDXL-LoRA-slider.anime", "anime"),
        ("ntc-ai/SDXL-LoRA-slider.cartoon", "cartoon"),
        ("ntc-ai/SDXL-LoRA-slider.pixar-style", "pixar"),

        # NEW VIRAL EFFECTS (College Edition)
        ("artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl", "ps2"),  # PS2 Graphics
        ("nerijs/pixel-art-xl", "pixel"),  # Pixel Art

        # AESTHETIC STYLES (Instagram/TikTok trending)
        ("ntc-ai/SDXL-LoRA-slider.aesthetic", "aesthetic"),  # General aesthetic

        # OPTIONAL: Add these if repos exist on HuggingFace
        # ("artificialguybr/BollywoodStyle", "bollywood"),  # Bollywood poster
        # ("ntc-ai/SDXL-LoRA-slider.korean-aesthetic", "kpop"),  # K-Pop/K-Drama
        # ("Joeythemonster/mermaid-ariel-lora-for-sdxl", "mermaid"),  # Mermaid
    ]

    downloaded_count = 0
    failed_count = 0
    skipped_count = 0

    for repo_id, style_name in loras:
        # Check if this LoRA already exists in GCS
        if check_gcs_directory_exists(f"style_loras/{style_name}/"):
            print(f"✓ {style_name} LoRA already in GCS, skipping")
            skipped_count += 1
            continue

        print(f"\n📥 Downloading {style_name} LoRA from {repo_id}...")
        try:
            # Download entire repo (LoRAs may have multiple files)
            local_dir = snapshot_download(
                repo_id=repo_id,
                cache_dir="./cache",
                allow_patterns=["*.safetensors", "*.json", "*.txt"]  # Only download necessary files
            )

            # Upload all .safetensors files
            uploaded = False
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    if file.endswith('.safetensors'):
                        file_path = os.path.join(root, file)
                        gcs_path = f"style_loras/{style_name}/{file}"
                        upload_to_gcs(file_path, gcs_path)
                        uploaded = True

            if uploaded:
                print(f"✓ {style_name} LoRA downloaded successfully")
                downloaded_count += 1
            else:
                print(f"⚠️  No .safetensors files found for {style_name}")
                failed_count += 1

        except Exception as e:
            print(f"⚠️  Failed to download {style_name} LoRA: {e}")
            failed_count += 1
            # Continue with other LoRAs

    print(f"\n📊 LoRA Download Summary:")
    print(f"   ✓ Downloaded: {downloaded_count}")
    print(f"   ⏭️  Skipped (already in GCS): {skipped_count}")
    print(f"   ⚠️  Failed: {failed_count}")
    print(f"   📦 Total: {len(loras)}")

    return True  # Don't fail build if some LoRAs fail

def download_ip_adapter_models():
    """Download IP-Adapter models for commercial-safe stack"""
    print("\n" + "="*60)
    print("📥 Checking IP-Adapter Models (Commercial Safe)")
    print("="*60)
    
    # 1. IP-Adapter for SDXL (Standard + Plus)
    # We download both to test which one is better
    repo_id = "h94/IP-Adapter"
    print(f"Downloading IP-Adapter weights from {repo_id}...")
    try:
        # Download specific files
        files_to_download = [
            "sdxl_models/ip-adapter_sdxl.safetensors",       # Standard
            "sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors", # Plus (Better quality)
        ]
        
        local_dir = snapshot_download(
            repo_id=repo_id,
            cache_dir="./cache",
            allow_patterns=files_to_download
        )
        
        # Upload to GCS
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if file.endswith('.safetensors'):
                    file_path = os.path.join(root, file)
                    # Keep structure: ip-adapter/sdxl_models/...
                    relative_path = os.path.relpath(file_path, local_dir)
                    gcs_path = f"ip-adapter/{relative_path}"
                    upload_to_gcs(file_path, gcs_path)
                    
        print("✓ IP-Adapter models downloaded")
    except Exception as e:
        print(f"⚠️  Failed to download IP-Adapter: {e}")
        return False

    # 2. ControlNet Canny for SDXL (Structure preservation)
    # This replaces InstantID's ControlNet for keeping face shape
    canny_repo = "diffusers/controlnet-canny-sdxl-1.0"
    print(f"\nDownloading ControlNet Canny from {canny_repo}...")
    try:
        local_dir = snapshot_download(
            repo_id=canny_repo,
            cache_dir="./cache",
            allow_patterns=["*.fp16.safetensors", "*.json"]
        )
        
        # Upload to GCS
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                if file.endswith('.safetensors') or file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    gcs_path = f"controlnet-canny/{file}"
                    upload_to_gcs(file_path, gcs_path)
                    
        print("✓ ControlNet Canny downloaded")
        return True
    except Exception as e:
        print(f"⚠️  Failed to download ControlNet Canny: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 Model Cache Builder")
    print("="*60)
    print(f"Target: gs://{BUCKET_NAME}/")
    print("="*60)

    success = True

    # 1. SDXL Base
    if not download_sdxl_base():
        success = False
        print("\n❌ Failed to download SDXL base model")

    # 2. VAE FP16
    if not download_vae_fp16():
        success = False
        print("\n❌ Failed to download VAE FP16 fix")

    # 3. InstantID (Existing Engine - Keep for now)
    # NOTE: download_instantid() is assumed to exist elsewhere or be a placeholder.
    # If it's not defined, this will cause a NameError.
    if not download_instantid(): # Assuming this function exists
        success = False
        print("\n❌ Failed to download InstantID models")

    # 4. Face Analysis (InsightFace - Required for InstantID only)
    if not download_antelopev2():
        success = False
        print("\n❌ Failed to download AntelopeV2 model")
        
    # 5. IP-Adapter (New Commercial Engine)
    if not download_ip_adapter_models():
        success = False
        print("\n❌ Failed to download IP-Adapter models")

    # 6. Style LoRAs (Viral Effects)
    if not download_style_loras():
        # LoRAs are optional, so we don't set success = False for this
        print("\n⚠️  Some Style LoRAs failed to download, but continuing.")

    print("\n" + "="*60)
    if success:
        print("✅ Model cache build complete!")
        print(f"Models available at: gs://{BUCKET_NAME}/")
    else:
        print("❌ Model cache build failed!")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
