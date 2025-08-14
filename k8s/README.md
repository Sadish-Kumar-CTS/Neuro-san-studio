# Kubernetes Deployment for Neuro SAN Studio

This directory contains Kubernetes manifests for deploying Neuro SAN Studio with ArgoCD on AWS EKS.

## Architecture

- **Application**: Neuro SAN Studio multi-agent framework
- **Container Registry**: AWS ECR (`876092575456.dkr.ecr.us-west-2.amazonaws.com/neurosan_cognizant_sso`)
- **Ingress**: AWS Load Balancer Controller with external-dns
- **Domain**: `neuro-san.dev.evolution.ml`
- **Namespace**: `argocd`

## Prerequisites

1. **AWS EKS Cluster** in us-west-2 region
2. **ArgoCD** installed in the cluster
3. **AWS Load Balancer Controller** 
4. **external-dns** configured for Route53
5. **ECR Access** configured for the cluster
6. **OpenAI API Key**

## Quick Start

### 1. Install Prerequisites

```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# Install external-dns (configure with your Route53 hosted zone)
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/external-dns/master/docs/tutorials/aws.yaml
```

### 2. Configure Secrets

Update your OpenAI API key:

```bash
# Encode your OpenAI API key
echo -n "your-openai-api-key" | base64

# Update secrets.yaml with the encoded key
# Replace REPLACE_WITH_BASE64_ENCODED_OPENAI_KEY with your encoded key
```

### 3. Deploy Application

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 4. Deploy with ArgoCD (Alternative)

```bash
# Quick ArgoCD deployment
chmod +x deploy-argocd.sh
./deploy-argocd.sh
```

## File Structure

```
k8s/
├── argocd-application.yaml    # ArgoCD application definition
├── cluster-issuer.yaml        # Let's Encrypt certificate issuer (unused)
├── configmap.yaml            # Application configuration
├── deploy-argocd.sh          # Quick ArgoCD deployment script
├── deploy.sh                 # Main deployment script
├── deployment.yaml           # Kubernetes deployment manifest
├── ingress.yaml              # AWS ALB ingress configuration
├── kustomization.yaml        # Kustomize configuration
├── secrets.yaml              # Secret template for API keys
└── service.yaml              # LoadBalancer service
```

## Configuration Details

### Deployment
- **Replicas**: 2 pods for high availability
- **Image**: ECR repository with latest tag
- **Ports**: 8080 (HTTP), 30011 (gRPC)
- **Resources**: 512Mi-1Gi memory, 250m-500m CPU
- **Security**: Non-root user (1001), no privilege escalation

### Service
- **Type**: LoadBalancer (AWS ALB)
- **Ports**: 80→8080 (HTTP), 30011→30011 (gRPC)
- **Annotations**: AWS internet-facing load balancer

### Ingress
- **Controller**: AWS Load Balancer Controller
- **Domain**: `neuro-san.dev.evolution.ml`
- **Features**: external-dns integration, health checks
- **Protocol**: HTTP (port 80)

### Secrets
- **OpenAI API Key**: Base64 encoded in `neuro-san-secrets`

## Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `AGENT_HTTP_PORT` | 8080 | HTTP server port |
| `AGENT_PORT` | 30011 | gRPC server port |
| `AGENT_SERVICE_LOG_LEVEL` | INFO | Logging level |
| `OPENAI_API_KEY` | (secret) | OpenAI API key |

## DNS Configuration

Ensure your Route53 hosted zone for `dev.evolution.ml` is configured and external-dns has proper IAM permissions:

```bash
# Test DNS resolution
nslookup neuro-san.dev.evolution.ml

# Flush local DNS cache if needed
ipconfig /flushdns  # Windows
sudo dscacheutil -flushcache  # macOS
```

## Monitoring & Troubleshooting

### Check Deployment Status
```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
kubectl get ingress -n argocd
kubectl describe ingress neuro-san-studio-ingress -n argocd
```

### View Logs
```bash
kubectl logs -n argocd deployment/neuro-san-studio -f
```

### Common Issues

1. **Pod not starting**: Check ECR permissions and image availability
2. **DNS not resolving**: Verify external-dns configuration and Route53 setup
3. **Load balancer not created**: Check AWS Load Balancer Controller installation
4. **API key issues**: Verify base64 encoding in secrets.yaml

### ArgoCD Application

The ArgoCD application syncs from:
- **Repository**: `https://github.com/Sadish-Kumar-CTS/Neuro-san-studio.git`
- **Path**: `k8s`
- **Sync Policy**: Automated with prune and self-heal

## Access

Once deployed, access the application at:
- **URL**: `http://neuro-san.dev.evolution.ml`
- **Health Check**: `http://neuro-san.dev.evolution.ml/`

## Security Notes

- Application runs as non-root user (1001)
- No privilege escalation allowed
- API keys stored in Kubernetes secrets
- Load balancer configured for internet access

## Scaling

To scale the deployment:
```bash
kubectl scale deployment neuro-san-studio --replicas=3 -n argocd
```