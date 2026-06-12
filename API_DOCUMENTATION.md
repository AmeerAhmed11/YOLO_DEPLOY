# YOLO Inference API Documentation

This document describes how to integrate and use the serverless YOLO26m object detection API powered by Modal. The API runs on a dedicated T4 GPU and provides high-speed inference for vehicle and accident detection.

## Base Endpoint
**URL:** `https://amee14r--yolo-inference-fastapi-app.modal.run`

## Health Check
Use this endpoint to verify that the container is awake and responding.
* **URL:** `/health`
* **Method:** `GET`
* **Response:**
  ```json
  {
      "status": "healthy"
  }
  ```

---

## Predict Endpoint
Use this endpoint to submit images for object detection.
* **URL:** `/predict`
* **Method:** `POST`

The API supports **two different payload formats** for maximum compatibility with different frameworks and clients.

### Option 1: Multipart Form Data (Direct File Upload)
Best for raw scripts, cURL, or uploading files directly from an HTML form without encoding.

* **Content-Type:** `multipart/form-data`
* **Body Key:** `content` (must contain the binary image file)

**Example using cURL:**
```bash
curl -X POST -F "content=@my_image.jpg" https://amee14r--yolo-inference-fastapi-app.modal.run/predict
```

**Example using Python (`requests`):**
```python
import requests

url = "https://amee14r--yolo-inference-fastapi-app.modal.run/predict"
image_path = "car.jpg"

with open(image_path, "rb") as img:
    response = requests.post(url, files={"content": img})

print(response.json())
```

### Option 2: JSON with Base64 Payload
Best for web frontends, server-to-server communication, or platforms where multipart form data is difficult to construct (like Vertex AI integration).

* **Content-Type:** `application/json`
* **Body:** You can supply the base64 string using either direct keys or wrapped inside an `instances` array.

**Accepted JSON structures:**
```json
// Direct format
{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..." 
}

// Or wrapped format (Google Vertex AI style)
{
    "instances": [
        {"image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."}
    ]
}
```
*(Note: You can use `image_base64`, `b64`, or `content` as the key name for the string)*

**Example using Javascript (Browser/Node.js):**
```javascript
const imageUrl = "https://amee14r--yolo-inference-fastapi-app.modal.run/predict";

// Assuming you have a base64 string of your image
const base64String = "iVBORw0KGgoAAAANSUhEUgAA..."; 

const response = await fetch(imageUrl, {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        image_base64: base64String
    })
});

const data = await response.json();
console.log(data);
```

---

## Response Format

A successful `200 OK` response will return a JSON object containing the `predictions` array. 
* **boxes**: The bounding box coordinates `[x_min, y_min, x_max, y_max]`.
* **labels**: The string label of the detected object (`accident`, `bus`, `car`, `truck`).
* **scores**: The confidence score of the prediction (`0.0` to `1.0`).

```json
{
  "predictions": [
    {
      "boxes": [
        [150.5, 200.2, 400.0, 550.8],
        [600.0, 300.0, 850.5, 450.0]
      ],
      "labels": [
        "car",
        "accident"
      ],
      "scores": [
        0.9542,
        0.8810
      ]
    }
  ]
}
```

## Error Handling
If a request fails, the API returns standard HTTP status codes with an `error` key explaining the issue.

* **400 Bad Request:** Missing fields, empty payloads, or invalid base64 encoding.
  ```json
  {"error": "Invalid JSON format. Expected 'image_base64' string."}
  ```
* **500 Internal Server Error:** An issue occurred on the GPU or during inference.

---

## Performance & Cold Starts
This API is hosted on Modal's Serverless GPU infrastructure. 
* **Cold Starts:** If the API has not received traffic in the last 10 minutes, the container spins down to save cost. The *first* request after a spin-down will take **5-15 seconds** while Modal provisions a new T4 GPU and loads the TensorRT model.
* **Warm Requests:** Subsequent requests immediately following the first will process extremely quickly (typically <100ms) directly on the GPU.
