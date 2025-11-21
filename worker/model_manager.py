import os
import torch
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, AutoencoderKL
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

        # 1. Load Face Analysis (InsightFace)
        self.app = FaceAnalysis(name='antelopev2', root='./', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

        # 2. Load ControlNet (InstantID)
        # In production, these paths would be local after downloading from GCS
        # For now, we assume they are in ./models/ or downloaded via cache
        controlnet_path = "InstantX/InstantID"
        
        controlnet = ControlNetModel.from_pretrained(
            controlnet_path, 
            subfolder="ControlNetModel",
            torch_dtype=torch.float16
        )

        # 3. Load SDXL
        base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"
        
        self.pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
            base_model_path,
            controlnet=controlnet,
            torch_dtype=torch.float16
        ).to(self.device)
        
        self.pipe.load_ip_adapter_instantid(controlnet_path)
        
        print("Models loaded successfully!")

    def process_image(self, face_image_path, prompt, style):
        if not self.pipe:
            raise RuntimeError("Models not loaded")

        # 1. Detect Face
        image = cv2.imread(face_image_path)
        faces = self.app.get(image)
        if len(faces) == 0:
            raise ValueError("No face detected in image")
        
        face_info = faces[0]
        
        # 2. Prepare Inputs
        face_emb = face_info['embedding']
        # Keypoints for InstantID
        face_kps = draw_kps(image, face_info['kps'])
        
        # 3. Generate
        image = self.pipe(
            prompt=prompt,
            image_embeds=face_emb,
            image=face_kps,
            controlnet_conditioning_scale=0.8,
            ip_adapter_scale=0.8,
            num_inference_steps=30,
            guidance_scale=5,
        ).images[0]
        
        return image

def draw_kps(image_pil, kps, color_list=[(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255)]):
    # Helper to draw keypoints for ControlNet
    # Simplified for brevity
    return image_pil
