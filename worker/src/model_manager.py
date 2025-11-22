import os
import shutil
import torch
from diffusers import (
    DiffusionPipeline,
    AutoencoderKL,
    EulerDiscreteScheduler
)
from diffusers.utils import load_image
from diffusers.models import ControlNetModel
import cv2
import numpy as np
from PIL import Image
from insightface.app import FaceAnalysis
from google.cloud import storage
from src.pipelines import StableDiffusionXLInstantIDPipeline

class ModelManager:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.app = None
        self.style_loras = {}  # Cache for loaded style LoRAs
        self.current_lora = None  # Track currently active LoRA

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

        # 1. Load Face Analysis (InsightFace AntelopeV2)
        print("\n1️⃣ Loading Face Analysis Model (AntelopeV2)...")
        try:
            # InsightFace needs writable directory for cache
            # Use /tmp since GCS mount is read-only
            insightface_root = '/tmp/insightface'
            os.makedirs(insightface_root, exist_ok=True)

            # Check if we can copy from GCS to avoid download
            antelopev2_gcs = os.path.join(gcs_models_path, 'antelopev2')
            antelopev2_tmp = os.path.join(insightface_root, 'models', 'antelopev2')

            if os.path.exists(antelopev2_gcs) and not os.path.exists(antelopev2_tmp):
                print(f"Copying AntelopeV2 from GCS to /tmp...")
                os.makedirs(os.path.dirname(antelopev2_tmp), exist_ok=True)
                shutil.copytree(antelopev2_gcs, antelopev2_tmp)
                print("✓ Copied from GCS")
            elif os.path.exists(antelopev2_tmp):
                print("✓ Using cached AntelopeV2 from /tmp")
            else:
                print("Downloading AntelopeV2 to /tmp (first run only)...")

            self.app = FaceAnalysis(name='antelopev2', root=insightface_root, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("✓ Face analysis model loaded")
        except Exception as e:
            print(f"❌ Failed to load face analysis: {e}")
            raise RuntimeError("Face analysis is required for InstantID")

        # 2. Load InstantID ControlNet
        print("\n2️⃣ Loading InstantID ControlNet...")
        try:
            controlnet_path = os.path.join(gcs_models_path, 'instantid/ControlNetModel') if os.path.exists(gcs_models_path) else None

            if controlnet_path and os.path.exists(controlnet_path):
                print(f"Loading ControlNet from GCS: {controlnet_path}")
                controlnet = ControlNetModel.from_pretrained(
                    controlnet_path,
                    torch_dtype=torch.float16
                )
            else:
                print("Loading ControlNet from HuggingFace...")
                controlnet = ControlNetModel.from_pretrained(
                    "InstantX/InstantID",
                    subfolder="ControlNetModel",
                    torch_dtype=torch.float16
                )
            print("✓ ControlNet loaded")
        except Exception as e:
            print(f"❌ Failed to load ControlNet: {e}")
            raise

        # 3. Load SDXL Base Model with InstantID
        print("\n3️⃣ Loading SDXL InstantID Pipeline...")

        # Check for SDXL in GCS first (GPU best practice: pre-download models)
        sdxl_gcs_path = os.path.join(gcs_models_path, 'sdxl-base') if os.path.exists(gcs_models_path) else None
        if sdxl_gcs_path and os.path.exists(sdxl_gcs_path):
            print(f"Loading SDXL from GCS: {sdxl_gcs_path}")
            base_model_path = sdxl_gcs_path
        else:
            print("Loading SDXL from HuggingFace (first run only)...")
            base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"

        # Load VAE FP16 fix to prevent numerical instabilities
        print("Loading VAE with FP16 fix...")
        vae_gcs_path = os.path.join(gcs_models_path, 'vae-fp16') if os.path.exists(gcs_models_path) else None
        if vae_gcs_path and os.path.exists(vae_gcs_path):
            print(f"Loading VAE from GCS: {vae_gcs_path}")
            vae = AutoencoderKL.from_pretrained(
                vae_gcs_path,
                torch_dtype=torch.float16
            )
        else:
            print("Loading VAE from HuggingFace (first run only)...")
            vae = AutoencoderKL.from_pretrained(
                "madebyollin/sdxl-vae-fp16-fix",
                torch_dtype=torch.float16
            )

        # Load InstantID Pipeline (local bundled version - diffusers 0.27.2 compatible)
        self.pipe = StableDiffusionXLInstantIDPipeline.from_pretrained(
            base_model_path,
            controlnet=controlnet,
            vae=vae,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16"
        ).to(self.device)

        # Load IP-Adapter
        print("Loading IP-Adapter...")
        try:
            ip_adapter_path = os.path.join(gcs_models_path, 'instantid/ip-adapter.bin') if os.path.exists(gcs_models_path) else None

            if ip_adapter_path and os.path.exists(ip_adapter_path):
                print(f"Loading IP-Adapter from GCS: {ip_adapter_path}")
                self.pipe.load_ip_adapter_instantid(ip_adapter_path)
            else:
                print("Loading IP-Adapter from HuggingFace...")
                self.pipe.load_ip_adapter_instantid("InstantX/InstantID")

            # Set optimal IP-Adapter scale for face preservation
            self.pipe.set_ip_adapter_scale(0.8)
            print("✓ IP-Adapter loaded (scale: 0.8)")
        except Exception as e:
            print(f"❌ Failed to load IP-Adapter: {e}")
            raise

        # Use Euler scheduler for better results (recommended for InstantID)
        self.pipe.scheduler = EulerDiscreteScheduler.from_config(
            self.pipe.scheduler.config
        )
        print("✓ Euler scheduler configured")

        # 2025 Optimization: Enable attention slicing for memory efficiency
        self.pipe.enable_attention_slicing()
        print("✓ Attention slicing enabled")

        # 2025 Optimization: Enable xFormers or SDPA for faster attention
        try:
            self.pipe.enable_xformers_memory_efficient_attention()
            print("✓ xFormers memory efficient attention enabled")
        except Exception as e:
            print(f"xFormers not available (using PyTorch SDPA): {e}")

        print("✓ InstantID pipeline loaded successfully!")
        print("Models loaded successfully!")

    def load_style_lora(self, style):
        """Load style-specific LoRA from GCS or HuggingFace"""
        # Map styles to their LoRA repositories
        style_lora_map = {
            "anime": "ntc-ai/SDXL-LoRA-slider.anime",
            "cartoon": "ntc-ai/SDXL-LoRA-slider.cartoon",
            "pixar": "ntc-ai/SDXL-LoRA-slider.pixar-style",
        }

        style_lower = style.lower()
        if style_lower not in style_lora_map:
            print(f"No LoRA available for style: {style}")
            return False

        # Check if this LoRA is already active
        if self.current_lora == style_lower:
            print(f"✓ Style LoRA already active: {style}")
            return True

        # Unload previous LoRA if different style
        if self.current_lora is not None:
            print(f"Unloading previous LoRA: {self.current_lora}")
            try:
                self.pipe.unload_lora_weights()
                self.current_lora = None
            except Exception as e:
                print(f"⚠️  Failed to unload LoRA: {e}")

        try:
            repo_id = style_lora_map[style_lower]
            print(f"Loading {style} LoRA from {repo_id}...")

            # Try to load from GCS first
            gcs_lora_path = f"/gcs/models/style_loras/{style_lower}"
            if os.path.exists(gcs_lora_path):
                safetensors_files = [f for f in os.listdir(gcs_lora_path) if f.endswith('.safetensors')]
                if safetensors_files:
                    lora_path = os.path.join(gcs_lora_path, safetensors_files[0])
                    print(f"Loading LoRA from GCS: {lora_path}")
                    self.pipe.load_lora_weights(lora_path)
                    self.style_loras[style_lower] = lora_path
                    self.current_lora = style_lower
                    print(f"✓ {style} LoRA loaded from GCS")
                    return True

            # Fallback to HuggingFace
            print(f"Loading LoRA from HuggingFace: {repo_id}")
            self.pipe.load_lora_weights(repo_id)
            self.style_loras[style_lower] = repo_id
            self.current_lora = style_lower
            print(f"✓ {style} LoRA loaded from HuggingFace")
            return True

        except Exception as e:
            print(f"⚠️  Failed to load {style} LoRA: {e}")
            self.current_lora = None
            return False

    def process_image(self, face_image_path, prompt, style):
        """Process image using InstantID with style LoRAs"""
        if not self.pipe:
            raise RuntimeError("Models not loaded")

        if not self.app:
            raise RuntimeError("Face analysis model not loaded")

        # Load and prepare the face image
        print(f"\n📸 Loading face image from: {face_image_path}")
        face_image = load_image(face_image_path)

        # Resize to SDXL resolution (1024x1024)
        face_image = face_image.resize((1024, 1024), Image.LANCZOS)

        # 1. Extract face embeddings and keypoints using InsightFace
        print("🔍 Detecting face and extracting embeddings...")
        face_image_cv = cv2.cvtColor(np.array(face_image), cv2.COLOR_RGB2BGR)
        faces = self.app.get(face_image_cv)

        if not faces:
            raise ValueError("No face detected in the image. Please provide an image with a clear face.")

        # Use the first detected face
        face_info = faces[0]
        face_emb = face_info.embedding  # 512-dim face embedding
        face_kps = face_info.kps  # 5 facial keypoints

        print(f"✓ Face detected (confidence: {face_info.det_score:.2f})")
        print(f"✓ Face embedding shape: {face_emb.shape}")

        # 2. Load style LoRA if available
        lora_loaded = self.load_style_lora(style)
        if lora_loaded:
            lora_scale = 0.8  # Optimal weight from research: 0.75-0.85
            print(f"🎨 Style LoRA active with scale: {lora_scale}")
        else:
            lora_scale = 0.0
            print("🎨 No LoRA - using prompt-based styling")

        # 3. Build style-aware prompt
        style_prompts = {
            "anime": "anime art style, vibrant colors, cel shading, manga illustration, Japanese animation",
            "cartoon": "cartoon style, bold outlines, flat colors, animated character design, Western animation",
            "bollywood": "Bollywood movie star, dramatic Indian cinema style, vibrant colors, cinematic lighting",
            "cinematic": "cinematic photography, professional film still, dramatic lighting, depth of field",
            "natural": "natural photography, realistic, soft lighting, photorealistic",
            "corporate": "corporate headshot, professional business portrait, neutral background",
            "artistic": "artistic portrait, painterly style, creative interpretation",
            "vintage": "vintage photography, classic portrait, timeless aesthetic, film grain",
            "glamour": "glamour photography, elegant portrait, sophisticated lighting",
            "pixar": "Pixar animation style, 3D character, glossy rendering, animated feature film"
        }

        # Get style prompt or use the style as-is
        style_prompt = style_prompts.get(style.lower(), f"{style} style")

        # Combine user prompt with style
        # For InstantID, prompts should focus on style/environment, not face description
        full_prompt = f"{prompt}, {style_prompt}, high quality, detailed, professional"

        # Negative prompt to avoid artifacts while allowing style transformation
        negative_prompt = "monochrome, lowres, bad anatomy, worst quality, low quality, blurry, nsfw, nude"

        print(f"📝 Prompt: {full_prompt}")
        print(f"🎯 Style: {style}")

        # 4. Generate with InstantID
        # Optimal settings from research:
        # - CFG: 4-5 (lower = stronger face preservation, higher = more creative)
        # - Steps: 12-18 (sweet spot for quality/speed)
        # - ControlNet scale: 0.8 (face structure preservation)
        # - IP-Adapter scale: 0.8 (already set in load_models)
        print(f"\n🚀 Generating with InstantID...")
        print(f"   • Guidance scale: 5.0 (CFG)")
        print(f"   • Inference steps: 15")
        print(f"   • ControlNet scale: 0.8")
        print(f"   • LoRA scale: {lora_scale}")

        # Generate with optimal settings
        guidance = 5.0
        steps = 15
        conditioning_scale = 0.8  # Face structure preservation

        image = self.pipe(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            image_embeds=face_emb,  # Face identity embedding
            image=face_image,  # Reference face image for ControlNet
            controlnet_conditioning_scale=conditioning_scale,  # Face structure preservation
            num_inference_steps=steps,  # Optimal: 12-18
            guidance_scale=guidance,  # Optimal: 4-5 (lower than standard SDXL)
            cross_attention_kwargs={"scale": float(lora_scale)} if lora_loaded else None,
        ).images[0]

        print("✅ Image generated successfully!")
        return image
