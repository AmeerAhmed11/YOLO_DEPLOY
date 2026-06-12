import litserve as ls
from ultralytics import YOLO
import io
import base64
from PIL import Image
import numpy as np
import cv2

# Custom class names for the YOLO model as specified previously
CLASS_NAMES = {0: "accident", 1: "bus", 2: "car", 3: "truck"}

class YOLOLitAPI(ls.LitAPI):
    def setup(self, device):
        # The device parameter is provided by LitServe (e.g., "cuda:0" or "cpu")
        # Ultralytics automatically handles moving the model to the correct device
        print(f"Loading model on {device}...")
        self.model = YOLO("best.engine", task='detect')
        print("Model loaded successfully.")

    def decode_request(self, request):
        """
        Convert the incoming request payload into a format the model can process.
        The request is expected to contain a base64 encoded image string.
        """
        # Support multiple common formats for the image payload
        b64_img = None
        
        # Format 1: direct file upload via curl -F "content=@image.jpg"
        if "content" in request:
            image_bytes = request["content"].file.read()
            # Convert bytes to cv2 image
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return img

        # Format 2: JSON payload with base64 string
        if isinstance(request, dict):
            b64_img = request.get("image_base64") or request.get("b64") or request.get("content")

        if not b64_img:
            raise ValueError("Invalid request format. Expected 'content' (file) or JSON with 'image_base64' string.")

        image_bytes = base64.b64decode(b64_img)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img

    def predict(self, x):
        """
        Run inference using the YOLO model.
        """
        # x is the cv2 image returned from decode_request
        # Run inference (conf=0.25 is a sensible default)
        results = self.model.predict(x, conf=0.25, verbose=False)
        return results[0]

    def encode_response(self, result):
        """
        Format the model's output into a JSON response.
        """
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

        return {
            "predictions": [{
                "boxes": boxes,
                "labels": labels,
                "scores": scores,
                # Optionally return dimensions if needed
                # "image_width": w,
                # "image_height": h
            }]
        }

if __name__ == "__main__":
    # Initialize the API
    api = YOLOLitAPI()
    
    # Configure the server
    # LitServe automatically handles batching and workers
    server = ls.LitServer(
        api, 
        accelerator="auto", # Automatically use GPU if available
        max_batch_size=8,   # Batch up to 8 requests for better GPU utilization
        batch_timeout=0.01  # Wait max 10ms to form a batch
    )
    
    # Start the server on port 8000
    server.run(port=8000)
