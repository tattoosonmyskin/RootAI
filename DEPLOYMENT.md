# RootAI v3.0 Deployment Guide

## Deployment Options

RootAI v3.0 supports both CPU and GPU deployment modes:
- **CPU Mode**: Lower cost, suitable for development and moderate traffic
- **GPU Mode**: Higher performance, recommended for production with high traffic

## CPU Deployment (Recommended for Most Users)

### Prerequisites

1. Docker installed locally
2. Cloud platform account (GCP, AWS, Azure, etc.)
3. No GPU requirements

### Local CPU Deployment

```bash
# Build CPU Docker image
docker build -t rootai:v3.0-cpu .

# Run locally with CPU mode
docker run -p 8080:8080 \
  -e ROOTAI_USE_GPU=false \
  -e RATE_LIMIT_REQUESTS=100 \
  -e RATE_LIMIT_WINDOW=60 \
  rootai:v3.0-cpu

# Test the API
curl http://localhost:8080/health
```

## GPU Deployment (For High Performance)

### Prerequisites

1. NVIDIA GPU with CUDA 11.8+ support
2. Docker with NVIDIA Container Toolkit
3. Cloud platform with GPU support

### Local GPU Deployment

```bash
# Build GPU Docker image
docker build --build-arg ROOTAI_USE_GPU=true -t rootai:v3.0-gpu .

# Run locally with GPU mode
docker run --gpus all -p 8080:8080 \
  -e ROOTAI_USE_GPU=true \
  rootai:v3.0-gpu

# Test the API
curl http://localhost:8080/health
```

## Google Cloud Platform Deployment

### CPU Deployment on Cloud Run (Recommended)

#### Prerequisites

1. Google Cloud account with billing enabled
2. `gcloud` CLI installed and authenticated
3. Docker installed locally

#### Step 1: Project Setup

```bash
# Set project ID
export PROJECT_ID="rootai-production"
export REGION="us-central1"

# Create project (if needed)
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com
```

#### Step 2: Build and Push Docker Image (CPU Mode)

```bash
# Build CPU image using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/rootai:v3.0-cpu

# Or build locally and push
docker build -t gcr.io/$PROJECT_ID/rootai:v3.0-cpu .
docker push gcr.io/$PROJECT_ID/rootai:v3.0-cpu
```

#### Step 3: Deploy to Cloud Run (CPU Mode)

```bash
# Deploy with recommended CPU settings
gcloud run deploy rootai \
  --image gcr.io/$PROJECT_ID/rootai:v3.0-cpu \
  --platform managed \
  --region $REGION \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1 \
  --allow-unauthenticated \
  --set-env-vars "PORT=8080,ROOTAI_USE_GPU=false,RATE_LIMIT_REQUESTS=100,RATE_LIMIT_WINDOW=60"

# Get service URL
gcloud run services describe rootai \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)'
```

### GPU Deployment on GCE or GKE

For GPU deployments, use Google Compute Engine or Google Kubernetes Engine:

```bash
# Build GPU image
docker build --build-arg ROOTAI_USE_GPU=true \
  -t gcr.io/$PROJECT_ID/rootai:v3.0-gpu .
docker push gcr.io/$PROJECT_ID/rootai:v3.0-gpu

# Deploy on GCE with GPU
gcloud compute instances create-with-container rootai-gpu \
  --container-image=gcr.io/$PROJECT_ID/rootai:v3.0-gpu \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --maintenance-policy=TERMINATE \
  --container-env=ROOTAI_USE_GPU=true
```

#### Step 4: Configure Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service rootai \
  --domain api.rootai.example.com \
  --region $REGION
```

### Step 5: Set Up Monitoring

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
gcloud monitoring uptime create rootai-health \
  --resource-type=uptime-url \
  --host=YOUR_SERVICE_URL \
  --path=/health
```

## Cost Optimization

### Estimated Monthly Costs

#### CPU Mode (Cloud Run)

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| Cloud Run (CPU) | 4GB RAM, 2 CPU, 10K requests | $150-300 |
| Container Registry | 10GB storage | $2.50 |
| Cloud Build | 10 builds/month | $0.50 |
| Bandwidth | 100GB egress | $12 |
| **Total (CPU)** | | **~$165-315/month** |

#### GPU Mode (GCE with T4 GPU)

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| GCE with GPU | n1-standard-4 + T4 GPU | $400-500 |
| Container Registry | 10GB storage | $2.50 |
| Persistent Disk | 100GB SSD | $17 |
| Bandwidth | 100GB egress | $12 |
| **Total (GPU)** | | **~$430-530/month** |

**Recommendation**: Start with CPU mode for development and moderate traffic. Upgrade to GPU mode only if you need higher performance for production workloads.

### Budget Alerts

```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="RootAI Monthly Budget" \
  --budget-amount=2000 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

## Performance Tuning

### CPU Mode - High Traffic Optimization

```bash
# Update Cloud Run for high traffic (CPU mode)
gcloud run services update rootai \
  --region $REGION \
  --memory 8Gi \
  --cpu 4 \
  --max-instances 20 \
  --concurrency 80 \
  --set-env-vars "ROOTAI_USE_GPU=false,RATE_LIMIT_REQUESTS=200,RATE_LIMIT_WINDOW=60"
```

### GPU Mode - Maximum Performance

```bash
# For GPU mode on GKE or GCE
# Increase instance size and GPU count for maximum performance
gcloud compute instances create-with-container rootai-gpu-large \
  --container-image=gcr.io/$PROJECT_ID/rootai:v3.0-gpu \
  --accelerator=type=nvidia-tesla-t4,count=2 \
  --machine-type=n1-standard-8 \
  --container-env=ROOTAI_USE_GPU=true,RATE_LIMIT_REQUESTS=500
```

### For Cost Optimization

```bash
gcloud run services update rootai \
  --region $REGION \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 5 \
  --min-instances 0
```

## Monitoring and Logging

### View Logs

```bash
# Real-time logs
gcloud run services logs read rootai \
  --region $REGION \
  --limit 50 \
  --follow

# Filter by severity
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=rootai AND severity>=ERROR" \
  --limit 50
```

### Check Metrics

```bash
# Request count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --interval-start-time=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval-end-time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
```

## Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test endpoint
ab -n 1000 -c 10 -p request.json -T application/json \
  https://YOUR_SERVICE_URL/reason

# request.json
echo '{"query": "Test query", "k": 5}' > request.json
```

## Rollback Procedure

```bash
# List revisions
gcloud run revisions list \
  --service rootai \
  --region $REGION

# Rollback to previous revision
gcloud run services update-traffic rootai \
  --region $REGION \
  --to-revisions REVISION_NAME=100
```

## Security Best Practices

1. **Authentication**: Add Identity-Aware Proxy (IAP)
```bash
gcloud run services update rootai \
  --region $REGION \
  --no-allow-unauthenticated
```

2. **Secrets Management**: Use Secret Manager
```bash
# Create secret
echo -n "secret-value" | gcloud secrets create rootai-api-key --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding rootai-api-key \
  --member=serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

3. **VPC Connector**: For private resources
```bash
gcloud compute networks vpc-access connectors create rootai-connector \
  --region $REGION \
  --network default \
  --range 10.8.0.0/28
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Increase memory: `--memory 8Gi`
   - Check logs for memory errors

2. **Timeout Errors**
   - Increase timeout: `--timeout 600`
   - Optimize model loading

3. **Cold Starts**
   - Set min instances: `--min-instances 1`
   - Use startup CPU boost

### Debug Mode

```bash
# Deploy with debug logging
gcloud run services update rootai \
  --region $REGION \
  --set-env-vars "LOG_LEVEL=DEBUG"
```

## Maintenance

### Update Service

```bash
# Build new version
gcloud builds submit --tag gcr.io/$PROJECT_ID/rootai:v3.1

# Deploy with traffic splitting (canary)
gcloud run services update rootai \
  --image gcr.io/$PROJECT_ID/rootai:v3.1 \
  --region $REGION \
  --no-traffic

# Gradually shift traffic
gcloud run services update-traffic rootai \
  --region $REGION \
  --to-revisions LATEST=50,PREVIOUS=50
```

### Cleanup Old Images

```bash
# List images
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Delete old images
gcloud container images delete gcr.io/$PROJECT_ID/rootai:v2.0 --quiet
```

## Support

For deployment issues:
- Check Cloud Run logs
- Review budget alerts
- Contact support at support@rootai.example.com

---

**Estimated deployment time**: 15-30 minutes
**Budget required**: $2,000 for production deployment
**Target performance**: 85%+ MMLU accuracy with <1s response time
