#!/bin/bash
set -e

if [ -f .env ]; then
  export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

PROJECT_ID=${GCP_PROJECT_ID:-n8n11-470807}
REGION=${GCP_REGION:-us-central1}
ENDPOINT_ID=${VERTEX_ENDPOINT_ID:-"PLACEHOLDER"}

if [ "$ENDPOINT_ID" = "PLACEHOLDER" ]; then
    echo "ERROR: VERTEX_ENDPOINT_ID must be set in your environment before deploying to Cloud Run."
    echo "First run setup_gcp.sh or deploy_vertex.py, copy the Endpoint ID, and update your .env file."
    exit 1
fi

echo "Deploying frontend to Cloud Run..."
gcloud run deploy yolo-frontend \
  --source=../frontend \
  --project=$PROJECT_ID \
  --region=$REGION \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,VERTEX_ENDPOINT_ID=$ENDPOINT_ID" \
  --memory=1Gi \
  --cpu=1

echo "Cloud Run deployment complete!"
