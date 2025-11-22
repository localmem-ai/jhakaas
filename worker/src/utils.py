import os
import requests
import uuid
from google.cloud import storage
from PIL import Image
import io

# Initialize GCS Client
storage_client = storage.Client()
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "jhakaas-images-dev")

def download_image(url: str) -> str:
    """Downloads image from URL to a temporary file and returns the path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Create temp file
        filename = f"/tmp/{uuid.uuid4()}.jpg"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filename
    except Exception as e:
        raise RuntimeError(f"Failed to download image: {e}")

def upload_image(image: Image.Image) -> str:
    """Uploads PIL Image to GCS and returns the public URL (or signed URL path)."""
    try:
        # Save PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        # Upload to GCS
        filename = f"generated/{uuid.uuid4()}.jpg"
        bucket = storage_client.bucket(IMAGES_BUCKET)
        blob = bucket.blob(filename)
        blob.upload_from_file(img_byte_arr, content_type='image/jpeg')
        
        # Return internal GCS path or public URL
        # For now, returning the gs:// path which the frontend can convert to Signed URL
        return f"gs://{IMAGES_BUCKET}/{filename}"
    except Exception as e:
        raise RuntimeError(f"Failed to upload image: {e}")

def cleanup_file(filepath: str):
    """Removes temporary file."""
    if os.path.exists(filepath):
        os.remove(filepath)
