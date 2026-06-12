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

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "n8n11-470807" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$ENDPOINT_ID = if ($env:VERTEX_ENDPOINT_ID) { $env:VERTEX_ENDPOINT_ID } else { "PLACEHOLDER" }

if ($ENDPOINT_ID -eq "PLACEHOLDER") {
    Write-Host "ERROR: VERTEX_ENDPOINT_ID must be set in your environment before deploying to Cloud Run." -ForegroundColor Red
    Write-Host "First run setup_gcp.ps1 or deploy_vertex.py, copy the Endpoint ID, and update your .env file."
    exit 1
}

Write-Host "Deploying frontend to Cloud Run..."
gcloud run deploy yolo-frontend `
  --source=../frontend `
  --project=$PROJECT_ID `
  --region=$REGION `
  --allow-unauthenticated `
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,VERTEX_ENDPOINT_ID=$ENDPOINT_ID" `
  --memory=1Gi `
  --cpu=1

Write-Host "Cloud Run deployment complete!"
