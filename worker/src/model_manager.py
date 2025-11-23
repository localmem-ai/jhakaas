import os
import shutil
import torch
from diffusers import (
    DiffusionPipeline,
    StableDiffusionXLControlNetPipeline,
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
        self.pipe = None  # Current active pipeline
        self.current_engine = None # "instantid" or "ip_adapter"
        self.app = None # InsightFace app (InstantID only)
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
        self.current_engine = "instantid"
        print("Models loaded successfully!")

    def load_ip_adapter_engine(self):
        """Load the Commercial-Safe IP-Adapter Engine"""
        print(f"\n🚀 Loading IP-Adapter Engine (Commercial Safe)...")
        
        if self.current_engine == "ip_adapter" and self.pipe is not None:
            print("✓ IP-Adapter engine already loaded")
            return

        # Unload previous engine if exists to save VRAM
        if self.pipe is not None:
            print("Unloading previous engine...")
            del self.pipe
            torch.cuda.empty_cache()
            self.pipe = None

        gcs_models_path = "/gcs/models"
        
        # 1. Load SDXL Base
        print("Loading SDXL Base...")
        sdxl_path = os.path.join(gcs_models_path, 'sdxl-base') if os.path.exists(gcs_models_path) else "stabilityai/stable-diffusion-xl-base-1.0"
        
        # 2. Load ControlNet Canny (Structure)
        print("Loading ControlNet Canny...")
        canny_path = os.path.join(gcs_models_path, 'controlnet-canny') if os.path.exists(gcs_models_path) else "diffusers/controlnet-canny-sdxl-1.0"
        controlnet = ControlNetModel.from_pretrained(canny_path, torch_dtype=torch.float16)

        # 3. Load VAE
        print("Loading VAE...")
        vae_path = os.path.join(gcs_models_path, 'vae-fp16') if os.path.exists(gcs_models_path) else "madebyollin/sdxl-vae-fp16-fix"
        vae = AutoencoderKL.from_pretrained(vae_path, torch_dtype=torch.float16)

        # 4. Initialize Pipeline
        print("Initializing SDXL ControlNet Pipeline...")
        self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
            sdxl_path,
            controlnet=controlnet,
            vae=vae,
            torch_dtype=torch.float16,
            use_safetensors=True,
            variant="fp16"
        ).to(self.device)

        # 5. Load IP-Adapter
        print("Loading IP-Adapter weights...")
        ip_adapter_path = os.path.join(gcs_models_path, 'ip-adapter') if os.path.exists(gcs_models_path) else "h94/IP-Adapter"
        
        # Load Standard SDXL IP-Adapter
        self.pipe.load_ip_adapter(
            ip_adapter_path, 
            subfolder="sdxl_models", 
            weight_name="ip-adapter_sdxl.safetensors"
        )
        
        # Set scale (0.6-0.8 is good for likeness)
        self.pipe.set_ip_adapter_scale(0.7)

        # Optimize
        self.pipe.scheduler = EulerDiscreteScheduler.from_config(self.pipe.scheduler.config)
        self.pipe.enable_attention_slicing()
        try:
            self.pipe.enable_xformers_memory_efficient_attention()
        except:
            pass

        self.current_engine = "ip_adapter"
        print("✓ IP-Adapter Engine loaded successfully!")

    def load_style_lora(self, style):
        """Load style-specific LoRA from GCS or HuggingFace"""
        # Map styles to their LoRA repositories
        style_lora_map = {
            # EXISTING STYLES
            "anime": "ntc-ai/SDXL-LoRA-slider.anime",
            "cartoon": "ntc-ai/SDXL-LoRA-slider.cartoon",
            "pixar": "ntc-ai/SDXL-LoRA-slider.pixar-style",
            
            # NEW VIRAL EFFECTS (Downloaded via download_models.py)
            "ps2": "artificialguybr/ps1redmond-ps1-game-graphics-lora-for-sdxl",
            "pixel": "nerijs/pixel-art-xl",
            "aesthetic": "ntc-ai/SDXL-LoRA-slider.aesthetic",
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

            self.current_lora = None
            return False

    def process_image_ip_adapter(self, face_image, prompt, negative_prompt, style, lora_scale):
        """Process image using IP-Adapter Engine"""
        print(f"\n🚀 Generating with IP-Adapter Engine...")
        
        # 1. Prepare Control Image (Canny Edge)
        # This preserves the face structure/composition
        image_np = np.array(face_image)
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # Apply Canny edge detection
        low_threshold = 100
        high_threshold = 200
        canny_image = cv2.Canny(image_cv, low_threshold, high_threshold)
        canny_image = canny_image[:, :, None]
        canny_image = np.concatenate([canny_image, canny_image, canny_image], axis=2)
        canny_image = Image.fromarray(canny_image)
        
        print("✓ Canny control image created")

        # 2. Generate
        # IP-Adapter uses the face_image as the "ip_adapter_image" prompt
        # ControlNet uses canny_image to keep structure
        
        try:
            images = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                ip_adapter_image=face_image, # The face reference
                image=canny_image,           # The structure reference (ControlNet)
                controlnet_conditioning_scale=0.5, # Structure strength (lower = more style freedom)
                num_inference_steps=20,
                guidance_scale=5.0,
                cross_attention_kwargs={"scale": float(lora_scale)} if lora_scale > 0 else None,
            ).images

            if not images:
                raise RuntimeError("Pipeline returned no images")

            return images[0]

        except Exception as e:
            print(f"❌ IP-Adapter generation failed: {e}")
            raise RuntimeError(f"IP-Adapter processing error: {str(e)}")

    def process_image(self, face_image_path, prompt, style, engine="instantid"):
        """Process image using selected engine"""
        
        # Switch engine if needed
        if engine == "ip_adapter":
            if self.current_engine != "ip_adapter":
                self.load_ip_adapter_engine()
                self.current_lora = None # Reset LoRA state for new pipeline
        else:
            if self.current_engine != "instantid":
                # Reload InstantID (this calls load_models which loads InstantID by default)
                self.load_models()
                self.current_lora = None # Reset LoRA state for new pipeline

        if not self.pipe:
            raise RuntimeError("Models not loaded")

        # Load and prepare the face image
        print(f"\n📸 Loading face image from: {face_image_path}")
        face_image = load_image(face_image_path)
        face_image = face_image.resize((1024, 1024), Image.LANCZOS)





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
            # EXISTING STYLES
            "anime": "anime art style, vibrant colors, cel shading, manga illustration, Japanese animation",
            "cartoon": "cartoon style, bold outlines, flat colors, animated character design, Western animation",
            "bollywood": "Bollywood movie star, dramatic Indian cinema style, vibrant colors, cinematic lighting",
            "cinematic": "cinematic photography, professional film still, dramatic lighting, depth of field",
            "natural": "natural photography, realistic, soft lighting, photorealistic",
            "corporate": "corporate headshot, professional business portrait, neutral background",
            "artistic": "artistic portrait, painterly style, creative interpretation",
            "vintage": "vintage photography, classic portrait, timeless aesthetic, film grain",
            "glamour": "glamour photography, elegant portrait, sophisticated lighting",
            "pixar": "Pixar animation style, 3D character, glossy rendering, animated feature film",
            
            # NEW VIRAL EFFECTS (LoRA-based)
            "ps2": "ps2 graphics, playstation 2 game character, low poly, early 2000s video game graphics, retro gaming",
            "pixel": "16-bit pixel art portrait, retro game sprite, dithered shading, pixel perfect, classic video game",
            "aesthetic": "aesthetic portrait, soft pastel colors, dreamy atmosphere, instagram aesthetic, soft focus, ethereal",
            
            # NEW VIRAL EFFECTS (Prompt-only, no LoRA needed)
            "yearbook": "professional yearbook portrait, studio lighting, formal attire, clean white background, 1990s school photo aesthetic, neutral expression, passport photo style",
            "kpop": "k-pop idol portrait, korean beauty aesthetic, glass skin, soft lighting, pastel colors, kpop mv style, korean drama cinematography, perfect skin, dewy makeup",
            "bollywood_poster": "dramatic bollywood movie poster, cinematic lighting, intense expression, vibrant colors, hand-painted poster art style, 1990s hindi film aesthetic, theatrical pose",
            "y2k": "y2k aesthetic, 2000s digital camera photo, low quality, flash photography, early 2000s party photo, nostalgic, disposable camera feel",
            "couple_aesthetic": "romantic couple portrait, soft pastel colors, dreamy atmosphere, aesthetic photography, golden hour lighting, instagram couple goals, soft focus",
            "mermaid": "mermaid portrait, shimmering fish scales, iridescent skin, underwater glow, flowing hair, ethereal beauty, ocean depths, fantasy creature",
            "sigma": "dramatic black and white portrait, intense gaze, cinematic lighting, powerful presence, sigma male aesthetic, motivational poster style",
            "thug_life": "cool portrait, confident expression, urban style, street photography, hip hop aesthetic",
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
        print(f"⚙️  Engine: {engine}")

        # Dispatch to correct engine
        if engine == "ip_adapter":
            return self.process_image_ip_adapter(
                face_image, 
                full_prompt, 
                negative_prompt, 
                style, 
                lora_scale
            )

        # --- INSTANTID LOGIC BELOW ---
        
        if not self.app:
             raise RuntimeError("Face analysis model not loaded (Required for InstantID)")

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

