"""
Utility functions for image handling.

This module provides functions for:
- Downloading images from URLs with validation
- Uploading images to Google Cloud Storage
- File cleanup and management
"""

import os
import io
import uuid
import mimetypes
from typing import Optional

import requests
from PIL import Image
from google.cloud import storage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)

# Initialize GCS Client
storage_client = storage.Client()

# Allowed MIME types for images
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp'
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
    reraise=True
)
def download_image(url: str) -> str:
    """
    Downloads image from URL to a temporary file with validation.

    Supports both GCS URLs (gs:// or https://storage.googleapis.com/) with authentication
    and external HTTP/HTTPS URLs.

    Args:
        url: URL of the image to download

    Returns:
        Path to the downloaded temporary file

    Raises:
        ValueError: If image is invalid, too large, or wrong format
        RuntimeError: If download fails after retries
    """
    logger.debug("download_started", url=url)
    filename = None

    try:
        # Check if this is a GCS URL
        is_gcs_url = url.startswith('gs://') or 'storage.googleapis.com' in url

        if is_gcs_url:
            # Download from GCS using authenticated client
            logger.debug("gcs_download", url=url)

            # Parse bucket and blob from URL
            if url.startswith('gs://'):
                # gs://bucket/path/to/file
                parts = url[5:].split('/', 1)
            else:
                # https://storage.googleapis.com/bucket/path/to/file
                parts = url.split('storage.googleapis.com/', 1)[1].split('/', 1)

            bucket_name = parts[0]
            blob_name = parts[1] if len(parts) > 1 else ''

            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Check blob size
            blob.reload()  # Get metadata
            max_bytes = settings.max_image_size_mb * 1024 * 1024
            if blob.size > max_bytes:
                raise ValueError(
                    f"Image too large: {blob.size / 1024 / 1024:.2f}MB "
                    f"(max: {settings.max_image_size_mb}MB)"
                )

            # Create temp file
            filename = f"/tmp/{uuid.uuid4()}.jpg"

            # Download from GCS
            blob.download_to_filename(filename)
            downloaded = blob.size
            logger.debug("gcs_download_complete", size_bytes=downloaded, path=filename)

        else:
            # Download from external URL using HTTP
            response = requests.get(
                url,
                stream=True,
                timeout=settings.download_timeout_seconds,
                headers={'User-Agent': 'Jhakaas-Worker/1.0'}
            )
            response.raise_for_status()

            # Check content length before downloading
            content_length = response.headers.get('content-length')
            max_bytes = settings.max_image_size_mb * 1024 * 1024

            if content_length:
                content_length_int = int(content_length)
                if content_length_int > max_bytes:
                    raise ValueError(
                        f"Image too large: {content_length_int / 1024 / 1024:.2f}MB "
                        f"(max: {settings.max_image_size_mb}MB)"
                    )
                logger.debug("content_length_ok", size_mb=content_length_int / 1024 / 1024)

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if content_type and not any(mime in content_type for mime in ALLOWED_MIME_TYPES):
                raise ValueError(f"Invalid content type: {content_type}")

            # Create temp file
            filename = f"/tmp/{uuid.uuid4()}.jpg"

            # Download with size limit
            downloaded = 0
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            raise ValueError(
                                f"Image exceeds {settings.max_image_size_mb}MB limit during download"
                            )
                        f.write(chunk)

            logger.debug("download_complete", size_bytes=downloaded, path=filename)
        
        # Validate it's actually a valid image
        try:
            with Image.open(filename) as img:
                # Verify image
                img.verify()
                
                # Re-open to get dimensions (verify() closes the file)
                with Image.open(filename) as img2:
                    width, height = img2.size
                    
                    # Check dimensions
                    if width > settings.max_image_dimension or height > settings.max_image_dimension:
                        raise ValueError(
                            f"Image dimensions too large: {width}x{height} "
                            f"(max: {settings.max_image_dimension}x{settings.max_image_dimension})"
                        )
                    
                    # Check format
                    if img2.format.upper() not in ['JPEG', 'JPG', 'PNG', 'WEBP']:
                        raise ValueError(f"Unsupported image format: {img2.format}")
                    
                    logger.info(
                        "image_validated",
                        width=width,
                        height=height,
                        format=img2.format,
                        size_mb=downloaded / 1024 / 1024
                    )
                    
        except (IOError, OSError) as e:
            raise ValueError(f"Invalid or corrupted image file: {e}")
        
        return filename
        
    except requests.Timeout as e:
        logger.error("download_timeout", url=url, timeout=settings.download_timeout_seconds)
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise RuntimeError(f"Download timeout after {settings.download_timeout_seconds}s: {e}")
        
    except requests.RequestException as e:
        logger.error("download_failed", url=url, error=str(e))
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise RuntimeError(f"Failed to download image: {e}")
        
    except ValueError as e:
        # Validation errors - cleanup and re-raise
        logger.warning("image_validation_failed", url=url, error=str(e))
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise
        
    except Exception as e:
        logger.exception("unexpected_download_error", url=url, error=str(e))
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise RuntimeError(f"Unexpected error downloading image: {e}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def upload_image(image: Image.Image, quality: int = 95) -> str:
    """
    Uploads PIL Image to GCS and returns the GCS path.
    
    Args:
        image: PIL Image object to upload
        quality: JPEG quality (1-100)
    
    Returns:
        GCS path in format: gs://bucket/path
    
    Raises:
        RuntimeError: If upload fails after retries
    """
    logger.debug("upload_started", image_size=image.size)
    
    try:
        # Convert to RGB if necessary (for JPEG)
        if image.mode in ('RGBA', 'LA', 'P'):
            logger.debug("converting_image_mode", from_mode=image.mode, to_mode='RGB')
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Save PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        img_byte_arr.seek(0)
        size_bytes = len(img_byte_arr.getvalue())
        
        logger.debug("image_encoded", size_bytes=size_bytes, quality=quality)
        
        # Upload to GCS
        filename = f"generated/{uuid.uuid4()}.jpg"
        bucket = storage_client.bucket(settings.images_bucket)
        blob = bucket.blob(filename)
        
        # Set metadata
        blob.metadata = {
            'generated_by': 'jhakaas-worker',
            'content_type': 'image/jpeg'
        }
        
        blob.upload_from_file(
            img_byte_arr,
            content_type='image/jpeg',
            timeout=30
        )
        
        gcs_path = f"gs://{settings.images_bucket}/{filename}"
        
        logger.info(
            "upload_complete",
            path=gcs_path,
            size_bytes=size_bytes,
            size_mb=size_bytes / 1024 / 1024
        )
        
        return gcs_path
        
    except Exception as e:
        logger.exception("upload_failed", error=str(e))
        raise RuntimeError(f"Failed to upload image: {e}")


def cleanup_file(filepath: Optional[str]):
    """
    Removes temporary file safely.
    
    Args:
        filepath: Path to file to remove (can be None)
    """
    if not filepath:
        return
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug("file_cleaned_up", path=filepath)
    except Exception as e:
        logger.warning("cleanup_failed", path=filepath, error=str(e))


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        filepath: Path to file
    
    Returns:
        File size in MB
    """
    if not os.path.exists(filepath):
        return 0.0
    return os.path.getsize(filepath) / 1024 / 1024

