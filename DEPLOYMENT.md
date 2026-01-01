# RootAI v3.0 Deployment Guide

## Google Cloud Platform Deployment

### Prerequisites

1. Google Cloud account with billing enabled
2. `gcloud` CLI installed and authenticated
3. Docker installed locally
4. $2K budget allocated

### Step 1: Project Setup

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

### Step 2: Build and Push Docker Image

```bash
# Build image
docker build -t gcr.io/$PROJECT_ID/rootai:v3.0 .

# Test locally
docker run -p 8080:8080 gcr.io/$PROJECT_ID/rootai:v3.0

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/rootai:v3.0

# Or use Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/rootai:v3.0
```

### Step 3: Deploy to Cloud Run

```bash
# Deploy with recommended settings
gcloud run deploy rootai \
  --image gcr.io/$PROJECT_ID/rootai:v3.0 \
  --platform managed \
  --region $REGION \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1 \
  --allow-unauthenticated \
  --set-env-vars "PORT=8080"

# Get service URL
gcloud run services describe rootai \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)'
```

### Step 4: Configure Custom Domain (Optional)

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

### Estimated Monthly Costs (with $2K budget)

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| Cloud Run | 4GB RAM, 2 CPU, 10K requests | $150-300 |
| Container Registry | 10GB storage | $2.50 |
| Cloud Build | 10 builds/month | $0.50 |
| Bandwidth | 100GB egress | $12 |
| **Total** | | **~$165-315/month** |

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

### For High Traffic (85% MMLU target)

```bash
gcloud run services update rootai \
  --region $REGION \
  --memory 8Gi \
  --cpu 4 \
  --max-instances 20 \
  --concurrency 80
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
