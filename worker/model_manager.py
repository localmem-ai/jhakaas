import os
import torch
from diffusers import StableDiffusionXLPipeline, AutoencoderKL
from diffusers.utils import load_image
import cv2
import numpy as np
from PIL import Image
from insightface.app import FaceAnalysis

class ModelManager:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.app = None

        # Use /tmp for HuggingFace cache (models download ~12GB on first run)
        # In production, consider pre-downloading to GCS or baking into image
        self.cache_dir = "/tmp/hf_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        os.environ["HF_HOME"] = self.cache_dir
        os.environ["TRANSFORMERS_CACHE"] = self.cache_dir
        print(f"HuggingFace cache directory: {self.cache_dir}")

    def load_models(self):
        print(f"Loading models on {self.device}...")

        if self.device == "cpu":
            print("WARNING: Running on CPU. This will be slow.")
            return

        # Models are mounted from GCS at /gcs/models/
        gcs_models_path = "/gcs/models"

        # Check if GCS mount exists
        if not os.path.exists(gcs_models_path):
            print(f"WARNING: GCS models path not found: {gcs_models_path}")
            print("Proceeding with HuggingFace Hub downloads")

        # 1. Load Face Analysis (InsightFace) - Optional
        try:
            self.app = FaceAnalysis(name='antelopev2', root='./', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("✓ Face analysis model loaded")
        except Exception as e:
            print(f"Warning: Could not load face analysis: {e}")
            self.app = None

        # 2. Load SDXL Pipeline with 2025 Best Practices
        print("Loading SDXL pipeline with optimizations...")
        base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"

        # Load VAE FP16 fix to prevent numerical instabilities
        print("Loading VAE with FP16 fix...")
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch.float16
        )

        # Load SDXL pipeline
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            base_model_path,
            vae=vae,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16"
        ).to(self.device)

        # 2025 Optimization: Enable attention slicing for memory efficiency
        # Better than CPU offload when you have sufficient GPU memory
        self.pipe.enable_attention_slicing()
        print("✓ Attention slicing enabled")

        # 2025 Optimization: Enable xFormers or SDPA for faster attention
        # PyTorch >= 2.0 automatically uses SDPA (3x faster)
        try:
            self.pipe.enable_xformers_memory_efficient_attention()
            print("✓ xFormers memory efficient attention enabled")
        except Exception as e:
            print(f"xFormers not available (using PyTorch SDPA): {e}")

        # 2025 Optimization: torch.compile for UNet (DISABLED - too slow on first run)
        # First compilation takes 3-5 minutes, subsequent runs are faster
        # Enable this once we have persistent model caching
        # try:
        #     import torch._dynamo as dynamo
        #     dynamo.config.suppress_errors = True
        #     self.pipe.unet = torch.compile(self.pipe.unet, mode="reduce-overhead", fullgraph=True)
        #     print("✓ UNet compiled with torch.compile")
        # except Exception as e:
        #     print(f"torch.compile not available: {e}")

        print("✓ SDXL pipeline loaded with optimizations")
        print("Models loaded successfully!")

    def process_image(self, face_image_path, prompt, style):
        if not self.pipe:
            raise RuntimeError("Models not loaded")

        # For now, do simple text-to-image generation
        # Full InstantID implementation will be added later

        # Add style to prompt
        full_prompt = f"{prompt}, {style} style, high quality, detailed"

        print(f"Generating image with prompt: {full_prompt}")

        # Generate image with 2025 best practices:
        # - Reduced steps (20 vs 30) for 30% speed improvement with minimal quality loss
        # - Optimal guidance scale for SDXL
        image = self.pipe(
            prompt=full_prompt,
            num_inference_steps=20,
            guidance_scale=7.5,
            height=1024,
            width=1024
        ).images[0]

        return image

def draw_kps(image_pil, kps, color_list=[(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]):
    # Helper to draw keypoints for ControlNet
    # Simplified for brevity
    return image_pil
