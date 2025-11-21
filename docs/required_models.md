# Required AI Models for Jhakaas Worker

This document lists the AI models required for the "Jhakaas" photo enhancement worker. These files must be downloaded and uploaded to the GCS bucket (e.g., `gs://jhakaas-models/`).

## 1. Foundation Model (The Brain)
*   **Model**: Stable Diffusion XL Base 1.0
*   **Source**: HuggingFace
*   **File**: `sd_xl_base_1.0.safetensors` (~6.94 GB)
*   **URL**: `https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors`̌

## 2. Identity Adapter (The Face cloner)
*   **Model**: InstantID
*   **Source**: HuggingFace
*   **Files**:
    *   `ip-adapter.bin` (~1.2 GB): `https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin`
    *   `ControlNetModel/config.json`: `https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/config.json`
    *   `ControlNetModel/diffusion_pytorch_model.safetensors` (~2.5 GB): `https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/diffusion_pytorch_model.safetensors`

## 3. Face Restoration (The Fixer)
*   **Model**: GFPGAN v1.4
*   **Source**: GitHub Releases
*   **File**: `GFPGANv1.4.pth` (~348 MB)
*   **URL**: `https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth`

## 4. Styles (LoRAs) - Examples
*   **Bollywood Style**: (Need to find specific CivitAI link or train one)
*   **Cyberpunk**: `https://civitai.com/api/download/models/12345` (Placeholder)

## Total Storage Required
~12 GB of models.

## Action Plan
1.  Create GCS Bucket: `gs://jhakaas-models`
2.  Run a script to download these URLs directly to the bucket (using Cloud Shell or local).
