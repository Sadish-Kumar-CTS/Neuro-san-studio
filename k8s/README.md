# Kubernetes Deployment for Neuro SAN Studio

This directory contains Kubernetes manifests for deploying Neuro SAN Studio with ArgoCD.

## Prerequisites

1. **Kubernetes Cluster** in us-west-2 region
2. **ArgoCD** installed in the cluster
3. **NGINX Ingress Controller**
4. **cert-manager** for SSL certificates
5. **ECR Access** configured for the cluster

## Quick Start

### 1. Install Prerequisites

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### 2. Configure Secrets

Update `secrets.yaml` with your base64-encoded OpenAI API key:

```bash
echo -n "your-openai-api-key" | base64
```

Replace `REPLACE_WITH_BASE64_ENCODED_OPENAI_KEY` in `secrets.yaml` with the output.

### 3. Update Email in ClusterIssuer

Edit `cluster-issuer.yaml` and replace `your-email@example.com` with your actual email.

### 4. Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 5. Apply ClusterIssuer

```bash
kubectl apply -f cluster-issuer.yaml
```

## Files Description

- `deployment.yaml` - Main application deployment
- `service.yaml` - Service to expose the application
- `ingress.yaml` - Ingress for external access with SSL
- `secrets.yaml` - Secret for API keys (template)
- `configmap.yaml` - Configuration for the application
- `argocd-application.yaml` - ArgoCD application definition
- `kustomization.yaml` - Kustomize configuration
- `cluster-issuer.yaml` - Let's Encrypt certificate issuer
- `deploy.sh` - Deployment script

## ECR Configuration

The deployment uses ECR repository: `876092575456.dkr.ecr.us-west-2.amazonaws.com/neurosan_cognizant_sso`

Ensure your cluster has proper IAM roles to pull from ECR.

## Domain Configuration

The application will be available at: `https://neuro-san-log.dev`

Make sure your DNS points to the ingress controller's load balancer.

## Monitoring

Check deployment status:

```bash
kubectl get pods -n argocd
kubectl get ingress -n argocd
kubectl get certificates -n argocd
```

## Troubleshooting

1. **Pod not starting**: Check logs with `kubectl logs -n argocd deployment/neuro-san-studio`
2. **SSL issues**: Verify cert-manager is running and ClusterIssuer is applied
3. **Ingress issues**: Ensure NGINX Ingress Controller is properly installed
4. **ECR pull issues**: Verify IAM roles and ECR permissions