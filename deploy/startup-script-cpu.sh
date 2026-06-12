#!/bin/bash
set -e

# Log everything
exec > /var/log/startup-script.log 2>&1
echo "=== Startup script started at $(date) ==="

# Install Docker
echo "Installing Docker..."
apt-get update
apt-get install -y docker.io

# Start Docker
systemctl start docker
systemctl enable docker

# Authenticate Docker with Artifact Registry
echo "Authenticating Docker with Artifact Registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Pull and run the container (CPU mode - no --gpus flag)
echo "Pulling container image..."
docker pull us-central1-docker.pkg.dev/n8n11-470807/yolo-deploy/yolo-gpu-server:latest

echo "Starting YOLO inference server (CPU mode)..."
docker run -d \
    --name yolo-server \
    -p 8080:8080 \
    --restart unless-stopped \
    us-central1-docker.pkg.dev/n8n11-470807/yolo-deploy/yolo-gpu-server:latest

echo "=== Startup script completed at $(date) ==="
