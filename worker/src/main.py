"""
Jhakaas AI Worker - FastAPI Application

This module provides the main FastAPI application for the Jhakaas AI worker service.
It handles image generation requests using InstantID with style transfer.
"""

import os
import uuid
import time
import asyncio
from datetime import datetime
from typing import Optional, Literal
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextvars import ContextVar

import torch
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field, validator

from src.config import settings
from src.logger import setup_logging, get_logger, request_id_var
from src.model_manager import ModelManager
from src import utils

# Setup logging
setup_logging(
    log_level=settings.log_level,
    use_json=settings.use_json_logging
)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Jhakaas AI Worker",
    version="1.0.0",
    description="AI-powered photo enhancement with style transfer"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Model Manager
manager = ModelManager(settings.model_bucket)

# Thread pool for async processing
executor = ThreadPoolExecutor(max_workers=1)


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateRequest(BaseModel):
    """Request model for image generation."""
    
    image_url: HttpUrl = Field(
        ...,
        description="URL of the input face image",
        example="https://storage.googleapis.com/bucket/image.jpg"
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Text prompt for image generation",
        example="professional headshot, studio lighting"
    )
    style: Literal[
        # Existing styles
        "natural", "anime", "cartoon", "bollywood", "cinematic",
        "vintage", "glamour", "corporate", "artistic", "pixar",
        # New viral effects (LoRA-based)
        "clay", "ps2", "pixel", "aesthetic",
        # New viral effects (prompt-only)
        "yearbook", "kpop", "bollywood_poster", "y2k",
        "couple_aesthetic", "mermaid", "sigma", "thug_life"
    ] = Field(
        default="cinematic",
        description="Style to apply to the image"
    )
    
    @validator('image_url')
    def validate_image_url(cls, v):
        """Validate that image URL is from allowed domains."""
        url_str = str(v)
        if not any(domain in url_str for domain in settings.allowed_image_domains):
            logger.warning(
                "invalid_image_domain",
                url=url_str,
                allowed_domains=settings.allowed_image_domains
            )
            raise ValueError(
                f"Image URL must be from allowed domains: {settings.allowed_image_domains}"
            )
        return v
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate prompt length."""
        if len(v) > settings.max_prompt_length:
            raise ValueError(
                f"Prompt too long: {len(v)} chars (max: {settings.max_prompt_length})"
            )
        return v.strip()


class GenerateResponse(BaseModel):
    """Response model for successful generation."""
    
    status: str = "success"
    output_url: str
    request_id: str
    processing_time_ms: int
    params: dict


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str
    error_code: str
    request_id: str
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health checks."""
    
    status: str
    gpu_available: bool
    models_loaded: bool
    gpu_memory_free_gb: Optional[float] = None


# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking."""
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        request_id=req_id
    )
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=req_id
        )
        
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Processing-Time-Ms"] = str(duration_ms)
        return response
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.exception(
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            request_id=req_id,
            error=str(e)
        )
        raise


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            request_id=request_id_var.get(),
            timestamp=datetime.utcnow().isoformat() + 'Z'
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id_var.get()
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            request_id=request_id_var.get(),
            timestamp=datetime.utcnow().isoformat() + 'Z'
        ).dict()
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    logger.info("service_starting", environment=settings.environment)
    
    try:
        manager.load_models()
        logger.info("service_ready", models_loaded=True)
    except RuntimeError as e:
        logger.error("model_load_failed", error=str(e), error_type="RuntimeError")
        # Don't raise - allow service to start for health checks
    except Exception as e:
        logger.exception("unexpected_startup_error", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("service_shutting_down")
    
    try:
        # Cleanup GPU memory
        if manager.pipe:
            del manager.pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("gpu_memory_cleared")
        
        # Shutdown executor
        executor.shutdown(wait=True, cancel_futures=True)
        logger.info("executor_shutdown")
        
    except Exception as e:
        logger.exception("shutdown_error", error=str(e))
    
    logger.info("service_stopped")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health/liveness", response_model=dict, tags=["Health"])
def liveness():
    """
    Liveness probe - is the service running?
    
    Used by Kubernetes/Cloud Run to determine if the container is alive.
    """
    return {"status": "alive"}


@app.get("/health/readiness", response_model=HealthResponse, tags=["Health"])
def readiness():
    """
    Readiness probe - can the service handle requests?
    
    Used by Kubernetes/Cloud Run to determine if the service is ready to receive traffic.
    """
    # Check if models are loaded
    if not manager.pipe:
        logger.warning("readiness_check_failed", reason="models_not_loaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models not loaded"
        )
    
    # Check GPU availability
    if not torch.cuda.is_available():
        logger.error("readiness_check_failed", reason="gpu_not_available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPU not available"
        )
    
    # Check GPU memory
    gpu_memory_free_gb = None
    try:
        gpu_memory = torch.cuda.get_device_properties(0).total_memory
        gpu_memory_allocated = torch.cuda.memory_allocated(0)
        gpu_memory_free = gpu_memory - gpu_memory_allocated
        gpu_memory_free_gb = gpu_memory_free / 1e9
        
        if gpu_memory_free < 1e9:  # Less than 1GB free
            logger.warning(
                "low_gpu_memory",
                free_gb=gpu_memory_free_gb,
                allocated_gb=gpu_memory_allocated / 1e9
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Low GPU memory"
            )
    except Exception as e:
        logger.warning("gpu_memory_check_failed", error=str(e))
    
    return HealthResponse(
        status="ready",
        gpu_available=True,
        models_loaded=True,
        gpu_memory_free_gb=gpu_memory_free_gb
    )


# Backward compatibility
@app.get("/health", tags=["Health"])
def health_check():
    """Legacy health check endpoint."""
    try:
        readiness_response = readiness()
        return readiness_response.dict()
    except HTTPException:
        return {
            "status": "unhealthy",
            "gpu_available": torch.cuda.is_available(),
            "models_loaded": manager.pipe is not None
        }


# ============================================================================
# Main API Endpoints
# ============================================================================

@app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate_image(request: GenerateRequest):
    """
    Generate an enhanced image with style transfer.
    
    This endpoint:
    1. Downloads the input image from the provided URL
    2. Processes it using InstantID with the specified style
    3. Uploads the result to GCS
    4. Returns the output URL
    
    Raises:
        HTTPException: If processing fails or times out
    """
    req_id = request_id_var.get()
    start_time = time.time()
    input_path = None
    
    logger.info(
        "generation_started",
        style=request.style,
        prompt_length=len(request.prompt),
        request_id=req_id
    )
    
    # Check if models are loaded
    if not manager.pipe:
        logger.error("generation_failed", reason="models_not_loaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Models not loaded"
        )
    
    try:
        # 1. Download Input Image
        logger.debug("downloading_image", url=str(request.image_url))
        input_path = utils.download_image(str(request.image_url))
        logger.info("image_downloaded", path=input_path)
        
        # 2. Process Image with timeout
        logger.debug("processing_image", timeout=settings.processing_timeout_seconds)
        
        try:
            # Run in thread pool with timeout
            loop = asyncio.get_event_loop()
            result_image = await asyncio.wait_for(
                loop.run_in_executor(
                    executor,
                    manager.process_image,
                    input_path,
                    request.prompt,
                    request.style
                ),
                timeout=settings.processing_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(
                "processing_timeout",
                timeout=settings.processing_timeout_seconds,
                style=request.style
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Processing timeout after {settings.processing_timeout_seconds}s"
            )
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info("image_processed", processing_time_ms=processing_time)
        
        # 3. Upload Result
        logger.debug("uploading_result")
        output_url = utils.upload_image(result_image)
        logger.info("result_uploaded", url=output_url)
        
        # 4. Cleanup
        utils.cleanup_file(input_path)
        
        total_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            "generation_completed",
            total_time_ms=total_time,
            processing_time_ms=processing_time,
            style=request.style
        )
        
        return GenerateResponse(
            status="success",
            output_url=output_url,
            request_id=req_id,
            processing_time_ms=total_time,
            params=request.dict()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except ValueError as e:
        # Handle validation errors
        logger.error("validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except RuntimeError as e:
        # Handle runtime errors (e.g., model errors)
        logger.error("runtime_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {str(e)}"
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.exception("unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
        
    finally:
        # Always cleanup temp files
        if input_path:
            utils.cleanup_file(input_path)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_config=None  # Use our custom logging
    )
