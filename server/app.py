import base64
import json
import logging
import os
import io

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YOLO Vertex AI Serving Container")

# Custom class names for the YOLO26m model as specified
CLASS_NAMES = {0: "accident", 1: "bus", 2: "car", 3: "truck"}

# Path where the model will be stored inside the container
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/best.engine")

# Load model globally on startup to avoid loading it on every request
logger.info(f"Loading YOLO model from {MODEL_PATH}")
try:
    model = YOLO(MODEL_PATH)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    # We don't exit immediately so the healthcheck might still report an issue or allow debugging, 
    # but in a real-world setting you might want to fail fast.
    model = None


@app.get("/health")
async def health_check():
    """Vertex AI Health Check Endpoint."""
    if model is None:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "reason": "Model not loaded"})
    return {"status": "healthy"}


@app.post("/predict")
async def predict(request: Request):
    """Vertex AI Predict Endpoint."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format.")

    instances = data.get("instances")
    if not instances or not isinstance(instances, list):
        raise HTTPException(status_code=400, detail="Request must contain a list of 'instances'.")

    predictions_response = []

    for instance in instances:
        # Vertex AI typically sends base64 encoded strings for image bytes.
        # Key could be "image_base64", "b64", or something else. We'll support standard structures.
        b64_img = instance.get("image_base64")
        if not b64_img:
            # Fallback if vertex wraps bytes
            b64_img = instance.get("b64")
            
        if not b64_img:
            raise HTTPException(status_code=400, detail="Instance missing 'image_base64' key.")

        try:
            image_bytes = base64.b64decode(b64_img)
            # Use OpenCV to decode the image
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Could not decode image.")
            
        except Exception as e:
            logger.error(f"Image decoding failed: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to decode image from base64.")

        h, w = img.shape[:2]

        try:
            # Run inference
            # conf=0.25 is a sensible default, could be parameterized
            results = model.predict(img, conf=0.25, verbose=False)
            
            result = results[0]
            boxes = []
            labels = []
            scores = []
            
            if result.boxes:
                for box in result.boxes:
                    # Bounding box coordinates (x1, y1, x2, y2)
                    coords = box.xyxy[0].tolist() 
                    conf = box.conf.item()
                    cls_id = int(box.cls.item())
                    
                    # Map to custom class names
                    cls_name = CLASS_NAMES.get(cls_id, f"unknown_{cls_id}")
                    
                    boxes.append(coords)
                    labels.append(cls_name)
                    scores.append(conf)

            predictions_response.append({
                "boxes": boxes,
                "labels": labels,
                "scores": scores,
                "image_width": w,
                "image_height": h
            })

        except Exception as e:
            logger.error(f"Inference failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Inference failed.")

    return {"predictions": predictions_response}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("AIP_HTTP_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
