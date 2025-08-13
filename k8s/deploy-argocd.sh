#!/bin/bash

# Quick ArgoCD deployment script

set -e

echo "🚀 Deploying Neuro SAN Studio to ArgoCD..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

# Create namespace
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets (update with your OpenAI API key first)
echo "🔐 Please enter your OpenAI API key:"
read -s OPENAI_KEY
ENCODED_KEY=$(echo -n "$OPENAI_KEY" | base64)

# Create secret
kubectl create secret generic neuro-san-secrets \
  --from-literal=openai-api-key="$OPENAI_KEY" \
  --namespace=argocd \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply all manifests
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Apply ArgoCD application
kubectl apply -f argocd-application.yaml

echo "✅ Deployment completed!"
echo "📋 Check status: kubectl get pods -n argocd"