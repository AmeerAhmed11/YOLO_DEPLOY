#!/bin/bash
set -e

# Log everything
exec > /var/log/startup-script.log 2>&1
echo "=== Startup script started at $(date) ==="

# Install NVIDIA GPU drivers
echo "Installing NVIDIA GPU drivers..."
curl -fsSL https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py -o /tmp/install_gpu_driver.py
python3 /tmp/install_gpu_driver.py

# Verify GPU
echo "Verifying GPU..."
nvidia-smi

# Install Docker
echo "Installing Docker..."
apt-get update
apt-get install -y docker.io

# Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Authenticate Docker with Artifact Registry
echo "Authenticating Docker with Artifact Registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Pull and run the container
echo "Pulling container image..."
docker pull us-central1-docker.pkg.dev/n8n11-470807/yolo-deploy/yolo-gpu-server:latest

echo "Starting YOLO inference server..."
docker run -d \
    --name yolo-server \
    --gpus all \
    -p 8080:8080 \
    --restart unless-stopped \
    us-central1-docker.pkg.dev/n8n11-470807/yolo-deploy/yolo-gpu-server:latest

echo "=== Startup script completed at $(date) ==="
