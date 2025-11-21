#!/bin/bash
# deploy.sh
# Deploys Jhakaas AI Worker to Cloud Run with GPU
# Usage: ./deploy.sh

# Fixed configuration for Jhakaas
PROJECT_ID=${1:-jhakaas-dev}
REGION=${2:-asia-southeast1}
GCLOUD="/opt/homebrew/share/google-cloud-sdk/bin/gcloud"

echo "Deploying Worker to $PROJECT_ID in $REGION..."

# 1. Submit Build to Cloud Build
echo "Submitting Build..."
$GCLOUD builds submit --config worker/cloudbuild.yaml \
  --substitutions=_REGION=$REGION \
  --project $PROJECT_ID \
  worker/

# 2. Deploy to Cloud Run (using the image we just built)
# Note: We use Terraform for the initial infrastructure, but this script
# is useful for quick code updates.
# However, for a pure GitOps approach, we should rely on Terraform or CI/CD.
# This script updates the image of the existing service.

IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/jhakaas-repo/worker:latest"

echo "Updating Cloud Run Service..."
$GCLOUD run services update jhakaas-worker \
  --image $IMAGE_URI \
  --region $REGION \
  --project $PROJECT_ID

echo "Deployment Complete!"
