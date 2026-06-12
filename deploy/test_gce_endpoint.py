import sys
import base64
import time
import requests
import json

SERVER_URL = "http://34.31.71.152:8080"

def test_health():
    print("Testing health endpoint...")
    r = requests.get(f"{SERVER_URL}/health")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    return r.status_code == 200

def test_predict(image_path):
    print(f"\nTesting prediction with: {image_path}")
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "instances": [{"image_base64": b64_encoded}]
    }
    
    print("Sending prediction request...")
    start_time = time.time()
    r = requests.post(f"{SERVER_URL}/predict", json=payload)
    latency = time.time() - start_time
    
    print(f"  Status: {r.status_code}")
    print(f"  Latency: {latency:.2f} seconds")
    
    if r.status_code == 200:
        result = r.json()
        predictions = result.get("predictions", [])
        for i, pred in enumerate(predictions):
            print(f"\n  Image {i+1} results:")
            print(f"    Dimensions: {pred['image_width']}x{pred['image_height']}")
            print(f"    Detections: {len(pred['boxes'])}")
            for j, (box, label, score) in enumerate(zip(pred['boxes'], pred['labels'], pred['scores'])):
                print(f"      [{j+1}] {label}: {score:.2%} at [{box[0]:.0f},{box[1]:.0f},{box[2]:.0f},{box[3]:.0f}]")
    else:
        print(f"  Error: {r.text}")

if __name__ == "__main__":
    test_health()
    
    if len(sys.argv) >= 2:
        test_predict(sys.argv[1])
    else:
        print("\nTo test prediction, run:")
        print("  python test_gce_endpoint.py <path_to_image>")
