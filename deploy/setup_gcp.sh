#!/bin/bash
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Required variables
PROJECT_ID=${GCP_PROJECT_ID:-n8n11-470807}
REGION=${GCP_REGION:-us-central1}
REPO_NAME=${ARTIFACT_REPO:-yolo-deploy}
IMAGE_NAME=${IMAGE_NAME:-yolo-tensorrt-server}
ENDPOINT_NAME=${ENDPOINT_NAME:-yolo-endpoint}
MODEL_DISPLAY_NAME="yolo-tensorrt"

echo "Deploying to GCP Project: $PROJECT_ID, Region: $REGION"

# 1. Enable APIs
echo "Enabling required APIs..."
gcloud services enable artifactregistry.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com --project=$PROJECT_ID

# 2. Create Artifact Registry repository if it doesn't exist
echo "Checking Artifact Registry repository..."
if ! gcloud artifacts repositories describe $REPO_NAME --project=$PROJECT_ID --location=$REGION > /dev/null 2>&1; then
  echo "Creating repository $REPO_NAME..."
  gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID \
    --description="Docker repository for YOLO deployment"
else
  echo "Repository $REPO_NAME already exists."
fi

# 3. Authenticate Docker
echo "Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# 4. Build and push container image
FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"
echo "Building container image: $FULL_IMAGE_NAME"
# Note: The context is the parent directory (..) because we need to copy best.engine
docker build -t $FULL_IMAGE_NAME -f ../server/Dockerfile ..

echo "Pushing image..."
docker push $FULL_IMAGE_NAME

# 5. Upload model to Vertex AI
echo "Uploading model to Vertex AI Model Registry..."
# Check if model exists and delete or just create a new version? We'll create a new model for simplicity
MODEL_UPLOAD_OP=$(gcloud ai models upload \
  --project=$PROJECT_ID \
  --region=$REGION \
  --display-name=$MODEL_DISPLAY_NAME \
  --container-image-uri=$FULL_IMAGE_NAME \
  --container-health-route="/health" \
  --container-predict-route="/predict" \
  --container-ports=8080 \
  --format="value(model)")

echo "Model uploaded successfully. ID: $MODEL_UPLOAD_OP"

# 6. Create Endpoint
echo "Checking if endpoint $ENDPOINT_NAME exists..."
ENDPOINT_ID=$(gcloud ai endpoints list \
  --project=$PROJECT_ID \
  --region=$REGION \
  --filter="displayName=$ENDPOINT_NAME" \
  --format="value(name)" | head -n 1)

if [ -z "$ENDPOINT_ID" ]; then
  echo "Creating endpoint $ENDPOINT_NAME..."
  ENDPOINT_ID=$(gcloud ai endpoints create \
    --project=$PROJECT_ID \
    --region=$REGION \
    --display-name=$ENDPOINT_NAME \
    --format="value(name)")
fi

echo "Endpoint ID: $ENDPOINT_ID"

# 7. Deploy Model to Endpoint
echo "Deploying model to endpoint (this takes 10-15 minutes)..."
gcloud ai endpoints deploy-model $ENDPOINT_ID \
  --project=$PROJECT_ID \
  --region=$REGION \
  --model=$MODEL_UPLOAD_OP \
  --display-name="${MODEL_DISPLAY_NAME}-deployed" \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --min-replica-count=0 \
  --max-replica-count=3

echo "========================================="
echo "Deployment Complete!"
echo "Endpoint ID: $ENDPOINT_ID"
echo "Make sure to update VERTEX_ENDPOINT_ID in your frontend .env file."
echo "========================================="
