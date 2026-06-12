$ErrorActionPreference = "Stop"

# Load environment variables from .env if it exists
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        if (![string]::IsNullOrWhiteSpace($line) -and !$line.StartsWith("#")) {
            $name, $value = $line.Split("=", 2)
            Set-Item -Path "env:$($name.Trim())" -Value $value.Trim()
        }
    }
}

# Required variables
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "n8n11-470807" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$REPO_NAME = if ($env:ARTIFACT_REPO) { $env:ARTIFACT_REPO } else { "yolo-deploy" }
$IMAGE_NAME = if ($env:IMAGE_NAME) { $env:IMAGE_NAME } else { "yolo-tensorrt-server" }
$ENDPOINT_NAME = if ($env:ENDPOINT_NAME) { $env:ENDPOINT_NAME } else { "yolo-endpoint" }
$MODEL_DISPLAY_NAME = "yolo-tensorrt"

Write-Host "Deploying to GCP Project: $PROJECT_ID, Region: $REGION"

# 1. Enable APIs
Write-Host "Enabling required APIs..."
gcloud services enable artifactregistry.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com --project=$PROJECT_ID

# 2. Create Artifact Registry repository if it doesn't exist
Write-Host "Checking Artifact Registry repository..."
$repoExists = $false
try {
    # Suppress output, check LASTEXITCODE
    $null = gcloud artifacts repositories describe $REPO_NAME --project=$PROJECT_ID --location=$REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        $repoExists = $true
    }
} catch {
}

if (-not $repoExists) {
    Write-Host "Creating repository $REPO_NAME..."
    gcloud artifacts repositories create $REPO_NAME `
        --repository-format=docker `
        --location=$REGION `
        --project=$PROJECT_ID `
        --description="Docker repository for YOLO deployment"
} else {
    Write-Host "Repository $REPO_NAME already exists."
}

# 3. Build and push container image using Cloud Build (No local Docker needed!)
$FULL_IMAGE_NAME = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:latest"
Write-Host "Building and pushing container image via Google Cloud Build..."
gcloud builds submit .. --config=cloudbuild.yaml --substitutions=_IMAGE_NAME=$FULL_IMAGE_NAME --project=$PROJECT_ID

# 5. Upload model to Vertex AI
Write-Host "Uploading model to Vertex AI Model Registry..."
$MODEL_UPLOAD_OP = gcloud ai models upload `
    --project=$PROJECT_ID `
    --region=$REGION `
    --display-name=$MODEL_DISPLAY_NAME `
    --container-image-uri=$FULL_IMAGE_NAME `
    --container-health-route="/health" `
    --container-predict-route="/predict" `
    --container-ports=8080 `
    --format="value(model)"

Write-Host "Model uploaded successfully. ID: $MODEL_UPLOAD_OP"

# 6. Create Endpoint
Write-Host "Checking if endpoint $ENDPOINT_NAME exists..."
$ENDPOINT_ID = gcloud ai endpoints list `
    --project=$PROJECT_ID `
    --region=$REGION `
    --filter="displayName=$ENDPOINT_NAME" `
    --format="value(name)" | Select-Object -First 1

if ([string]::IsNullOrEmpty($ENDPOINT_ID)) {
    Write-Host "Creating endpoint $ENDPOINT_NAME..."
    $ENDPOINT_ID = gcloud ai endpoints create `
        --project=$PROJECT_ID `
        --region=$REGION `
        --display-name=$ENDPOINT_NAME `
        --format="value(name)"
}

Write-Host "Endpoint ID: $ENDPOINT_ID"

# 7. Deploy Model to Endpoint
Write-Host "Deploying model to endpoint (this takes 10-15 minutes)..."
gcloud ai endpoints deploy-model $ENDPOINT_ID `
    --project=$PROJECT_ID `
    --region=$REGION `
    --model=$MODEL_UPLOAD_OP `
    --display-name="${MODEL_DISPLAY_NAME}-deployed" `
    --machine-type=n1-standard-4 `
    --accelerator=type=nvidia-tesla-t4,count=1 `
    --min-replica-count=0 `
    --max-replica-count=3

Write-Host "========================================="
Write-Host "Deployment Complete!"
Write-Host "Endpoint ID: $ENDPOINT_ID"
Write-Host "Make sure to update VERTEX_ENDPOINT_ID in your frontend .env file."
Write-Host "========================================="
