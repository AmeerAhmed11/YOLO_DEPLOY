import os
import sys
import base64
import time
from google.cloud import aiplatform

def test_endpoint(image_path):
    project_id = os.getenv("GCP_PROJECT_ID", "n8n11-470807")
    region = os.getenv("GCP_REGION", "us-central1")
    endpoint_id = os.getenv("VERTEX_ENDPOINT_ID")
    
    if not endpoint_id:
        print("ERROR: VERTEX_ENDPOINT_ID environment variable not set.")
        sys.exit(1)
        
    print(f"Connecting to Endpoint: {endpoint_id}")
    aiplatform.init(project=project_id, location=region)
    
    try:
        endpoint = aiplatform.Endpoint(endpoint_id)
    except Exception as e:
        print(f"Failed to find endpoint: {e}")
        sys.exit(1)
        
    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found at {image_path}")
        sys.exit(1)
        
    print(f"Reading image: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
    instances = [{"image_base64": b64_encoded}]
    
    print("Sending prediction request... (might take 5-10 minutes if scale-to-zero triggered)")
    start_time = time.time()
    try:
        prediction = endpoint.predict(instances=instances)
        latency = time.time() - start_time
        print(f"Prediction successful! Latency: {latency:.2f} seconds")
        print("\nResponse:")
        print(prediction.predictions)
    except Exception as e:
        print(f"Prediction failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_endpoint.py <path_to_image>")
        sys.exit(1)
        
    test_endpoint(sys.argv[1])
