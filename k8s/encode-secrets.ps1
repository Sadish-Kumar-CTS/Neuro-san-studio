# PowerShell script to encode AWS credentials for Kubernetes secrets
Write-Host "AWS Credentials Encoder for Kubernetes Secrets" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Get credentials from user
$accessKeyId = Read-Host "Enter your AWS Access Key ID"
$secretAccessKey = Read-Host "Enter your AWS Secret Access Key" -AsSecureString
$region = Read-Host "Enter your AWS Region (e.g., us-west-2)"
$openaiKey = Read-Host "Enter your OpenAI API Key" -AsSecureString

# Convert SecureString to plain text for encoding
$secretAccessKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretAccessKey))
$openaiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($openaiKey))

# Encode to base64
$encodedAccessKeyId = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($accessKeyId))
$encodedSecretAccessKey = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($secretAccessKeyPlain))
$encodedRegion = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($region))
$encodedOpenaiKey = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($openaiKeyPlain))

# Update secrets.yaml
$secretsContent = @"
apiVersion: v1
kind: Secret
metadata:
  name: neuro-san-secrets
  namespace: argocd
type: Opaque
data:
  # Base64 encoded OpenAI API key
  openai-api-key: "$encodedOpenaiKey"
  
  # DynamoDB AWS credentials
  aws-access-key-id: "$encodedAccessKeyId"
  aws-secret-access-key: "$encodedSecretAccessKey"
  aws-region: "$encodedRegion"
"@

# Write to file
$secretsContent | Out-File -FilePath "secrets.yaml" -Encoding UTF8

Write-Host "`nSecrets encoded and saved to secrets.yaml!" -ForegroundColor Green
Write-Host "You can now run: kubectl apply -f secrets.yaml" -ForegroundColor Yellow

# Clear sensitive variables
$secretAccessKeyPlain = $null
$openaiKeyPlain = $null