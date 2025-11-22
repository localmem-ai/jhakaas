import os
import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, AutoencoderKL
from diffusers.utils import load_image
import cv2
import numpy as np
from PIL import Image, ImageDraw
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

        # Load SDXL Img2Img pipeline for face-preserving style transfer
        self.pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
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

        # Load and prepare the original image
        print(f"Loading original image from: {face_image_path}")
        init_image = load_image(face_image_path)

        # Resize to SDXL resolution
        init_image = init_image.resize((1024, 1024), Image.LANCZOS)

        # Build style-aware prompt
        # Different styles require different prompting strategies
        style_prompts = {
            "anime": "anime art style, vibrant colors, cel shading, manga style",
            "cartoon": "cartoon style, bold outlines, flat colors, animated look",
            "bollywood": "Bollywood movie style, dramatic, vibrant, cinematic Indian film aesthetic",
            "cinematic": "cinematic style, professional photography, dramatic lighting",
            "natural": "natural style, realistic, photographic",
            "corporate": "corporate style, professional business headshot",
            "artistic": "artistic style, painterly, creative",
            "vintage": "vintage photography style, classic, timeless",
            "glamour": "glamour photography, elegant, sophisticated"
        }

        # Get style prompt or use the style as-is
        style_prompt = style_prompts.get(style.lower(), f"{style} style")

        # Combine user prompt with style
        full_prompt = f"{prompt}, {style_prompt}, high quality, detailed"

        # Negative prompt to maintain face quality and avoid artifacts
        negative_prompt = "distorted face, blurry, low quality, disfigured, ugly, bad anatomy, extra limbs, worst quality"

        print(f"Generating image with prompt: {full_prompt}")
        print(f"Style strength: 0.45 (preserves original face while applying style)")

        # Generate with img2img
        # Strength 0.45: Good balance between face preservation and style application
        # - Lower (0.2-0.3): Very similar to original, subtle style
        # - Higher (0.6-0.8): More dramatic style, less face preservation
        image = self.pipe(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            image=init_image,
            strength=0.45,  # Sweet spot for face preservation + style
            num_inference_steps=20,
            guidance_scale=7.5
        ).images[0]

        return image

def draw_kps(image_pil, kps, color_list=[(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]):
    # Helper to draw keypoints for ControlNet
    # Simplified for brevity
    return image_pil
