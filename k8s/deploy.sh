#!/bin/bash

# Deployment script for Neuro SAN Studio on Kubernetes with ArgoCD

set -e

echo "🚀 Deploying Neuro SAN Studio to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if ArgoCD CLI is available
if ! command -v argocd &> /dev/null; then
    echo "⚠️  ArgoCD CLI is not installed. You can install it or apply the application manually."
fi

# Create namespace if it doesn't exist
echo "📦 Creating namespace..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets (you need to update the secret with actual values)
echo "🔐 Applying secrets..."
echo "⚠️  Please update k8s/secrets.yaml with your actual base64-encoded OpenAI API key before applying!"
read -p "Have you updated the secrets.yaml file? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f secrets.yaml
else
    echo "❌ Please update secrets.yaml first, then run this script again."
    exit 1
fi

# Apply other Kubernetes resources
echo "🔧 Applying Kubernetes resources..."
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Apply ArgoCD application if ArgoCD CLI is available
if command -v argocd &> /dev/null; then
    echo "🔄 Applying ArgoCD application..."
    kubectl apply -f argocd-application.yaml
else
    echo "📝 To set up ArgoCD application, apply the following file manually:"
    echo "   kubectl apply -f argocd-application.yaml"
fi

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Ensure NGINX Ingress Controller is installed in your cluster"
echo "2. Install cert-manager for SSL certificates:"
echo "   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml"
echo "3. Create ClusterIssuer for Let's Encrypt:"
echo "   kubectl apply -f cluster-issuer.yaml"
echo "4. Check deployment status:"
echo "   kubectl get pods -n argocd"
echo "5. Access the application at: https://neuro-san-log.dev"