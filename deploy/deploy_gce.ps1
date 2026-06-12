# Deploy YOLO model to Compute Engine with V100 GPU
# This script creates a VM, pulls the container, and runs it

$GCLOUD = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$PROJECT = "n8n11-470807"
$REGION = "us-central1"
$ZONE = "us-central1-a"
$VM_NAME = "yolo-inference-server"
$IMAGE_URI = "us-central1-docker.pkg.dev/$PROJECT/yolo-deploy/yolo-gpu-server:latest"

Write-Host "=== Step 1: Creating firewall rule for port 8080 ===" -ForegroundColor Cyan
& $GCLOUD compute firewall-rules create allow-yolo-8080 `
    --project=$PROJECT `
    --direction=INGRESS `
    --priority=1000 `
    --network=default `
    --action=ALLOW `
    --rules=tcp:8080 `
    --source-ranges=0.0.0.0/0 `
    --target-tags=yolo-server `
    --description="Allow HTTP traffic on port 8080 for YOLO inference server" `
    2>&1

Write-Host ""
Write-Host "=== Step 2: Creating VM with V100 GPU ===" -ForegroundColor Cyan

# Startup script that installs NVIDIA drivers, Docker, and runs the container
$STARTUP_SCRIPT = @"
#!/bin/bash
set -e

# Log everything
exec > /var/log/startup-script.log 2>&1
echo "=== Startup script started at `$(date) ==="

# Install NVIDIA GPU drivers
echo "Installing NVIDIA GPU drivers..."
curl -fsSL https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py -o install_gpu_driver.py
python3 install_gpu_driver.py

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
docker pull $IMAGE_URI

echo "Starting YOLO inference server..."
docker run -d \
    --name yolo-server \
    --gpus all \
    -p 8080:8080 \
    --restart unless-stopped \
    $IMAGE_URI

echo "=== Startup script completed at `$(date) ==="
"@

# Save startup script to temp file
$STARTUP_FILE = Join-Path $PSScriptRoot "startup-script.sh"
$STARTUP_SCRIPT | Out-File -FilePath $STARTUP_FILE -Encoding utf8 -NoNewline

& $GCLOUD compute instances create $VM_NAME `
    --project=$PROJECT `
    --zone=$ZONE `
    --machine-type=n1-standard-4 `
    --accelerator=type=nvidia-tesla-v100,count=1 `
    --maintenance-policy=TERMINATE `
    --boot-disk-size=100GB `
    --boot-disk-type=pd-balanced `
    --image-family=ubuntu-2204-lts `
    --image-project=ubuntu-os-cloud `
    --scopes=cloud-platform `
    --tags=yolo-server `
    --metadata-from-file=startup-script=$STARTUP_FILE

Write-Host ""
Write-Host "=== VM Created! ===" -ForegroundColor Green
Write-Host "The startup script will now install GPU drivers, Docker, and start the container."
Write-Host "This takes about 5-10 minutes."
Write-Host ""
Write-Host "To check progress:" -ForegroundColor Yellow
Write-Host "  & '$GCLOUD' compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT -- 'tail -f /var/log/startup-script.log'"
Write-Host ""
Write-Host "To get the external IP:" -ForegroundColor Yellow
Write-Host "  & '$GCLOUD' compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT --format='get(networkInterfaces[0].accessConfigs[0].natIP)'"
Write-Host ""
Write-Host "Once running, test with:" -ForegroundColor Yellow
Write-Host "  curl http://<EXTERNAL_IP>:8080/health"
