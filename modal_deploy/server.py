import modal
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import base64
import numpy as np
import cv2

# Define the Modal application
app = modal.App("yolo-inference")

# Define the container image with necessary dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "fastapi[standard]",
        "python-multipart",
        "ultralytics>=8.1.0",
        "tensorrt>=8.6.0",
        "opencv-python-headless",
        "numpy",
        "pillow"
    )
    # Upload the local TensorRT engine file to the container's /root/ directory
    # Note: We deploy from the root workspace directory, so relative path is correct.
    .add_local_file("modal_deploy/best.engine", remote_path="/root/best.engine")
)

# Initialize the underlying FastAPI app
web_app = FastAPI(title="YOLOv8 Detection API")

# Define our Inference Class to run on a Modal GPU container
@app.cls(image=image, gpu="T4", scaledown_window=600)
class YOLOModel:
    @modal.enter()
    def load_model(self):
        """
        Runs once when a new container spins up.
        Loads the TensorRT engine into GPU memory.
        """
        from ultralytics import YOLO
        import torch

        print("Initializing GPU and loading YOLO model...")
        # Since it's compiled for TensorRT, it must run on GPU
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = YOLO("/root/best.engine", task='detect')
        print(f"Model loaded successfully on {self.device}.")
        
        # Custom class names map
        self.class_names = {0: "accident", 1: "bus", 2: "car", 3: "truck"}

    @modal.method()
    def predict(self, image_bytes: bytes):
        """
        Runs inference on the GPU for each API request.
        """
        # Decode the image bytes using OpenCV
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Run YOLO prediction
        results = self.model.predict(img, conf=0.25, verbose=False)
        result = results[0]

        # Format output to match LitServe response structure
        boxes = []
        labels = []
        scores = []

        if result.boxes:
            for box in result.boxes:
                coords = box.xyxy[0].tolist() 
                conf = box.conf.item()
                cls_id = int(box.cls.item())
                cls_name = self.class_names.get(cls_id, f"unknown_{cls_id}")
                
                boxes.append(coords)
                labels.append(cls_name)
                scores.append(conf)

        return {
            "predictions": [{
                "boxes": boxes,
                "labels": labels,
                "scores": scores,
            }]
        }

# Define the ASGI wrapper to expose our FastAPI server via Modal
@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    
    @web_app.post("/predict")
    async def predict_endpoint(request: Request):
        """
        FastAPI endpoint that decodes HTTP requests exactly like the old LitServe API
        and forwards the byte payload to the GPU container for inference.
        """
        content_type = request.headers.get("content-type", "")
        image_bytes = None

        try:
            # 1. Handle multipart/form-data (e.g. curl -F "content=@image.jpg")
            if "multipart/form-data" in content_type:
                form = await request.form()
                if "content" not in form:
                    return JSONResponse(status_code=400, content={"error": "Missing 'content' field in form-data."})
                image_bytes = await form["content"].read()

            # 2. Handle JSON with base64 string
            elif "application/json" in content_type:
                json_data = await request.json()
                
                # Unwrap LitServe style 'instances' format
                if "instances" in json_data and isinstance(json_data["instances"], list) and len(json_data["instances"]) > 0:
                    json_data = json_data["instances"][0]
                    
                b64_string = json_data.get("image_base64") or json_data.get("b64") or json_data.get("content")
                if not b64_string:
                    return JSONResponse(status_code=400, content={"error": "Invalid JSON format. Expected 'image_base64' string."})
                
                # Strip data:image/jpeg;base64, prefix if it exists
                if "," in b64_string:
                    b64_string = b64_string.split(",")[1]
                image_bytes = base64.b64decode(b64_string)

            else:
                return JSONResponse(status_code=400, content={"error": "Unsupported Content-Type. Use form-data or JSON."})

            if not image_bytes:
                return JSONResponse(status_code=400, content={"error": "No image data received."})

            # Instantiate our Modal class and trigger the remote inference function
            yolo_service = YOLOModel()
            result = yolo_service.predict.remote(image_bytes)
            return result

        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    @web_app.get("/health")
    def health_check():
        return {"status": "healthy"}

    return web_app
