#!/bin/bash

# Build and push Docker image to ECR

set -e

# Configuration
ECR_REGISTRY="876092575456.dkr.ecr.us-west-2.amazonaws.com"
ECR_REPOSITORY="neurosan_cognizant_sso"
AWS_REGION="us-west-2"

# Get image tag (use git commit hash or provide as argument)
if [ -n "$1" ]; then
    IMAGE_TAG="$1"
else
    IMAGE_TAG=$(git rev-parse --short HEAD)
fi

FULL_IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo "🏗️  Building and pushing Docker image..."
echo "📦 Image: ${FULL_IMAGE_NAME}"

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -f deploy/Dockerfile -t ${FULL_IMAGE_NAME} .

# Tag as latest
docker tag ${FULL_IMAGE_NAME} ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

# Push the image
echo "🚀 Pushing Docker image..."
docker push ${FULL_IMAGE_NAME}
docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

echo "✅ Successfully built and pushed:"
echo "   ${FULL_IMAGE_NAME}"
echo "   ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"

# Update kustomization.yaml with new tag
echo "📝 Updating kustomization.yaml..."
sed -i "s|newTag: .*|newTag: ${IMAGE_TAG}|" k8s/kustomization.yaml

echo "🎉 Build and push completed!"
echo "💡 To deploy: cd k8s && ./deploy.sh"