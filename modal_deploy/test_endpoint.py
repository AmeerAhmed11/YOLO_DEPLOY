import requests
import argparse
import base64
import os

def test_endpoint(url, image_path, use_json=False):
    """
    Tests the Modal FastAPI endpoint using either form-data or JSON payload.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found.")
        return

    print(f"Testing endpoint: {url}/predict")
    print(f"Sending image: {image_path}")

    try:
        if use_json:
            # Test JSON format (base64)
            print("Mode: JSON Base64")
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            payload = {"image_base64": encoded_string}
            response = requests.post(f"{url}/predict", json=payload)
        else:
            # Test multipart/form-data format
            print("Mode: multipart/form-data")
            with open(image_path, "rb") as image_file:
                files = {"content": image_file}
                response = requests.post(f"{url}/predict", files=files)

        print(f"\nResponse Status: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            import json
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error Response: {response.text}")

    except Exception as e:
        print(f"Failed to connect to endpoint: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Modal API endpoint")
    parser.add_argument("--url", type=str, required=True, help="Modal deployment URL (e.g. https://your-workspace--yolo-inference-fastapi-app.modal.run)")
    parser.add_argument("--image", type=str, default="../frontend/static/test_image.jpg", help="Path to test image")
    parser.add_argument("--json", action="store_true", help="Send payload as JSON base64 instead of form-data")
    
    args = parser.parse_args()
    
    # ensure it doesn't have trailing slash
    url = args.url.rstrip("/")
    test_endpoint(url, args.image, args.json)
