import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from src.model_manager import ModelManager
from src import utils

app = FastAPI(title="Jhakaas AI Worker")

# Initialize Model Manager
BUCKET_NAME = os.environ.get("MODEL_BUCKET", "jhakaas-models-dev")
manager = ModelManager(BUCKET_NAME)

# Load models on startup (or lazy load)
@app.on_event("startup")
async def startup_event():
    try:
        manager.load_models()
    except Exception as e:
        print(f"Failed to load models: {e}")

class GenerateRequest(BaseModel):
    image_url: str
    prompt: str
    style: str = "cinematic"

@app.get("/health")
def health_check():
    gpu_available = torch.cuda.is_available()
    return {
        "status": "healthy",
        "gpu_available": gpu_available,
        "models_loaded": manager.pipe is not None
    }

@app.post("/generate")
async def generate_image(request: GenerateRequest):
    if not manager.pipe:
        return {"error": "Models not loaded", "mock_mode": True}
    
    try:
        # 1. Download Input Image
        input_path = utils.download_image(request.image_url)
        
        # 2. Process Image (AI Magic)
        # Note: This is a blocking call, in production we might want to run this in a threadpool
        # but for Cloud Run (1 request per instance), blocking is fine.
        result_image = manager.process_image(input_path, request.prompt, request.style)
        
        # 3. Upload Result
        output_url = utils.upload_image(result_image)
        
        # 4. Cleanup
        utils.cleanup_file(input_path)
        
        return {
            "status": "success",
            "output_url": output_url,
            "params": request.dict()
        }
        
    except Exception as e:
        # Cleanup on error
        if 'input_path' in locals():
            utils.cleanup_file(input_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
