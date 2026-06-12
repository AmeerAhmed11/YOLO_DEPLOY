import os
import io
import base64
import logging
import tempfile
from typing import List

import cv2
import numpy as np
import requests as http_requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YOLO Vehicle & Accident Detection")

# Serve the static HTML/JS/CSS files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_dir):
    static_dir = "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Backend inference server URL (Modal)
BACKEND_URL = os.getenv("BACKEND_URL", "https://amee14r--yolo-inference-fastapi-app.modal.run")

logger.info(f"Backend inference server: {BACKEND_URL}")


@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/health")
async def health():
    """Check backend server health."""
    try:
        r = http_requests.get(f"{BACKEND_URL}/health", timeout=5)
        return r.json()
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}


@app.post("/api/predict")
async def predict_image(file: UploadFile = File(...)):
    """Predict objects in an uploaded image."""
    try:
        image_bytes = await file.read()
        b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
        
        # Send directly to Compute Engine backend
        payload = {"instances": [{"image_base64": b64_encoded}]}
        
        logger.info(f"Sending prediction request for {file.filename}")
        r = http_requests.post(
            f"{BACKEND_URL}/predict",
            json=payload,
            timeout=60  # CPU inference can take a few seconds
        )
        
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        
        return r.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict/video")
async def predict_video(file: UploadFile = File(...), fps_skip: int = Form(5)):
    """Process a video file, extract frames, and get predictions for each."""
    
    # Save video temporarily to process with OpenCV
    temp_dir = tempfile.gettempdir()
    temp_video_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_video_path, "wb") as f:
            f.write(await file.read())
            
        cap = cv2.VideoCapture(temp_video_path)
        if not cap.isOpened():
            raise ValueError("Failed to open video file")
            
        frame_count = 0
        predictions_per_frame = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % fps_skip == 0:
                # Encode frame to JPG, then Base64
                _, buffer = cv2.imencode('.jpg', frame)
                b64_encoded = base64.b64encode(buffer).decode('utf-8')
                
                payload = {"instances": [{"image_base64": b64_encoded}]}
                
                try:
                    r = http_requests.post(
                        f"{BACKEND_URL}/predict",
                        json=payload,
                        timeout=60
                    )
                    if r.status_code == 200:
                        data = r.json()
                        preds = data.get("predictions", [{}])[0]
                        predictions_per_frame.append({
                            "frame_index": frame_count,
                            "predictions": preds
                        })
                except Exception as e:
                    logger.error(f"Failed on frame {frame_count}: {e}")
            
            frame_count += 1
            
        cap.release()
        return {"video_predictions": predictions_per_frame}

    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
