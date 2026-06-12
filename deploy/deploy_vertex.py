import os
from google.cloud import aiplatform

def deploy_model():
    # Load settings from environment
    project_id = os.getenv("GCP_PROJECT_ID", "n8n11-470807")
    region = os.getenv("GCP_REGION", "us-central1")
    repo_name = os.getenv("ARTIFACT_REPO", "yolo-deploy")
    image_name = os.getenv("IMAGE_NAME", "yolo-tensorrt-server")
    endpoint_name = os.getenv("ENDPOINT_NAME", "yolo-endpoint")
    
    full_image_uri = f"{region}-docker.pkg.dev/{project_id}/{repo_name}/{image_name}:latest"
    
    aiplatform.init(project=project_id, location=region)
    
    print(f"Uploading model using image: {full_image_uri}")
    model = aiplatform.Model.upload(
        display_name="yolo-tensorrt",
        serving_container_image_uri=full_image_uri,
        serving_container_health_route="/health",
        serving_container_predict_route="/predict",
        serving_container_ports=[8080],
    )
    print(f"Model uploaded: {model.resource_name}")
    
    # Check if endpoint exists
    endpoints = aiplatform.Endpoint.list(filter=f"display_name={endpoint_name}")
    if endpoints:
        endpoint = endpoints[0]
        print(f"Using existing endpoint: {endpoint.resource_name}")
    else:
        print(f"Creating new endpoint: {endpoint_name}")
        endpoint = aiplatform.Endpoint.create(display_name=endpoint_name)
        print(f"Endpoint created: {endpoint.resource_name}")
        
    print("Deploying model to endpoint... (This takes 10-15 minutes)")
    # Deploying with T4 GPU and scale-to-zero
    model.deploy(
        endpoint=endpoint,
        machine_type="n1-standard-4",
        accelerator_type="NVIDIA_TESLA_T4",
        accelerator_count=1,
        min_replica_count=0,
        max_replica_count=3,
        traffic_percentage=100,
        sync=True,
    )
    
    print(f"Model deployed successfully!")
    print(f"Endpoint ID: {endpoint.name}")

if __name__ == "__main__":
    deploy_model()
