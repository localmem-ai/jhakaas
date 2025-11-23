"""
Centralized configuration management for Jhakaas Worker.

This module provides type-safe configuration using Pydantic BaseSettings.
Configuration can be loaded from:
- Environment variables
- .env file (for local development)
- Default values
"""

import os
from typing import Literal
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Environment
    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        description="Deployment environment"
    )
    
    # Service Configuration
    service_name: str = Field(
        default="jhakaas-worker",
        description="Service name for logging"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # GCS Buckets
    model_bucket: str = Field(
        default="jhakaas-models-dev",
        description="GCS bucket for AI models"
    )
    images_bucket: str = Field(
        default="jhakaas-images-dev",
        description="GCS bucket for generated images"
    )
    
    # Paths
    gcs_models_path: str = Field(
        default="/gcs/models",
        description="Mount path for GCS models"
    )
    cache_dir: str = Field(
        default="/tmp/hf_cache",
        description="HuggingFace cache directory"
    )
    insightface_root: str = Field(
        default="/tmp/insightface",
        description="InsightFace models directory"
    )
    
    # Model Parameters
    guidance_scale: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="CFG guidance scale for image generation"
    )
    inference_steps: int = Field(
        default=15,
        ge=10,
        le=50,
        description="Number of inference steps"
    )
    controlnet_scale: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="ControlNet conditioning scale"
    )
    ip_adapter_scale: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="IP-Adapter scale for face preservation"
    )
    lora_scale: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="LoRA weight scale for style transfer"
    )
    
    # Image Processing Limits
    max_image_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum image upload size in MB"
    )
    max_image_dimension: int = Field(
        default=4096,
        ge=512,
        le=8192,
        description="Maximum image width/height in pixels"
    )
    max_prompt_length: int = Field(
        default=500,
        ge=1,
        le=1000,
        description="Maximum prompt length in characters"
    )
    
    # Timeouts
    processing_timeout_seconds: int = Field(
        default=240,
        ge=30,
        le=300,
        description="Maximum processing time per request"
    )
    download_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Timeout for downloading input images"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum requests per minute per IP"
    )
    
    # Allowed Styles
    allowed_styles: list[str] = Field(
        default=[
            # Existing styles
            "natural",
            "anime",
            "cartoon",
            "bollywood",
            "cinematic",
            "vintage",
            "glamour",
            "corporate",
            "artistic",
            "pixar",
            # New viral effects (LoRA-based)
            "clay",
            "ps2",
            "pixel",
            "aesthetic",
            # New viral effects (prompt-only)
            "yearbook",
            "kpop",
            "bollywood_poster",
            "y2k",
            "couple_aesthetic",
            "mermaid",
            "sigma",
            "thug_life"
        ],
        description="List of allowed style values"
    )
    
    # Allowed Image Domains (for security)
    allowed_image_domains: list[str] = Field(
        default=[
            "storage.googleapis.com",
            "storage.cloud.google.com",
        ],
        description="Allowed domains for image URLs"
    )
    
    # GPU Settings
    enable_xformers: bool = Field(
        default=True,
        description="Enable xFormers memory efficient attention"
    )
    enable_attention_slicing: bool = Field(
        default=True,
        description="Enable attention slicing for memory efficiency"
    )
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        if v not in ["dev", "staging", "prod"]:
            raise ValueError(f"Invalid environment: {v}")
        return v
    
    @validator('cache_dir', 'insightface_root')
    def validate_paths(cls, v):
        """Ensure paths are absolute."""
        if not os.path.isabs(v):
            raise ValueError(f"Path must be absolute: {v}")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "prod"
    
    @property
    def use_json_logging(self) -> bool:
        """Use JSON logging in production."""
        return self.environment in ["staging", "prod"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow environment variables to override
        env_prefix = ""


# Global settings instance
settings = Settings()


# Example usage:
# from src.config import settings
# print(f"Max image size: {settings.max_image_size_mb}MB")
# if settings.is_production:
#     print("Running in production mode")
