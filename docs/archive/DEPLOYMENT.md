# User Dashboard - Deployment Documentation

## 🚀 Production Deployment Details

### Current Deployment (2025-06-21)

**Status:** ✅ Successfully Deployed to Azure Container Apps

### URLs
- **Frontend:** https://user-dashboard-frontend.ambitioussmoke-f885b48e.eastus.azurecontainerapps.io
- **Backend:** https://user-dashboard-backend.ambitioussmoke-f885b48e.eastus.azurecontainerapps.io
- **API Docs:** https://user-dashboard-backend.ambitioussmoke-f885b48e.eastus.azurecontainerapps.io/docs

### Azure Resources Configuration

#### Resource Groups
- **Primary RG:** research-analytics-rg (Container Apps, Environment)
- **Cosmos DB RG:** rg-research-analytics-prod
- **Redis RG:** GZC_backend_tools
- **ACR RG:** fxspotstream-rg

#### Services
1. **Azure Cosmos DB**
   - Account: cosmos-research-analytics-prod
   - API: MongoDB API (compatible with Motor async driver)
   - Database: user_dashboard
   - Collections: users, sessions, dashboard_data

2. **Azure Redis Cache**
   - Instance: GZCRedis
   - Port: 6380 (SSL)
   - Usage: Session management, caching, real-time data

3. **Azure Container Registry**
   - Registry: fxspotstreamacr.azurecr.io
   - Images:
     - user-dashboard-backend:latest
     - user-dashboard-frontend:latest

4. **Azure Container Apps**
   - Environment: user-dashboard-env
   - Apps:
     - user-dashboard-backend (0.5 CPU, 1Gi memory)
     - user-dashboard-frontend (0.25 CPU, 0.5Gi memory)
   - Auto-scaling: 1-5 replicas (backend), 1-3 replicas (frontend)

## 🏗️ Architecture Decisions

### Why Container Apps over AKS?
1. **Simplicity** - Managed Kubernetes without cluster management
2. **Cost** - Pay per use, automatic scale to zero
3. **Speed** - Faster deployment and updates
4. **Future-ready** - Can migrate to AKS when needed

### Why Cosmos DB over PostgreSQL?
1. **Existing Infrastructure** - Cosmos DB already provisioned
2. **Global Distribution** - Built-in geo-replication
3. **Flexible Schema** - NoSQL allows rapid iteration
4. **Azure Integration** - Native Azure service with managed backups

### Technology Stack
- **Backend:** FastAPI (async Python) replacing Flask for better performance
- **Frontend:** React + TypeScript + Vite for modern development
- **State:** Zustand replacing Redux for simpler state management
- **Styling:** Tailwind CSS for rapid UI development

## 📋 Deployment Process

### Automated Deployment Script
```bash
cd azure
./deploy-cloudnative.sh
```

### What the Script Does:
1. **Validates** Azure CLI authentication
2. **Builds** images using ACR cloud build (no local Docker required)
3. **Retrieves** connection strings for Cosmos DB and Redis
4. **Deploys** Container Apps using Bicep templates
5. **Configures** ingress, scaling, and health checks
6. **Outputs** production URLs

### Manual Deployment Commands

#### 1. Build Images in ACR
```bash
# Backend
az acr build \
  --registry fxspotstreamacr \
  --image user-dashboard-backend:latest \
  --file backend/Dockerfile \
  backend/

# Frontend
az acr build \
  --registry fxspotstreamacr \
  --image user-dashboard-frontend:latest \
  --file frontend/Dockerfile \
  frontend/
```

#### 2. Get Secrets
```bash
# Cosmos DB
COSMOS_ENDPOINT=$(az cosmosdb show --name cosmos-research-analytics-prod --resource-group rg-research-analytics-prod --query documentEndpoint -o tsv)
COSMOS_KEY=$(az cosmosdb keys list --name cosmos-research-analytics-prod --resource-group rg-research-analytics-prod --query primaryMasterKey -o tsv)

# Redis
REDIS_HOSTNAME=$(az redis show --name GZCRedis --resource-group GZC_backend_tools --query hostName -o tsv)
REDIS_KEY=$(az redis list-keys --name GZCRedis --resource-group GZC_backend_tools --query primaryKey -o tsv)

# ACR
ACR_USERNAME=$(az acr credential show --name fxspotstreamacr --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name fxspotstreamacr --query 'passwords[0].value' -o tsv)
```

#### 3. Deploy with Bicep
```bash
az deployment group create \
  --resource-group research-analytics-rg \
  --template-file container-apps-simple.bicep \
  --parameters location=eastus \
    cosmosEndpoint=$COSMOS_ENDPOINT \
    cosmosKey=$COSMOS_KEY \
    redisHostname=$REDIS_HOSTNAME \
    redisKey=$REDIS_KEY \
    containerRegistry=fxspotstreamacr.azurecr.io \
    acrUsername=$ACR_USERNAME \
    acrPassword=$ACR_PASSWORD
```

## 🔧 Configuration Details

### Backend Environment Variables
```bash
COSMOS_ENDPOINT=https://cosmos-research-analytics-prod.documents.azure.com:443/
COSMOS_KEY=<secure>
COSMOS_DATABASE_NAME=user_dashboard
REDIS_URL=rediss://:password@GZCRedis.redis.cache.windows.net:6380
SECRET_KEY=<generated>
BACKEND_CORS_ORIGINS=["*"]
ENVIRONMENT=production
DEBUG=false
```

### Frontend Configuration
- API URL dynamically set to backend Container App URL
- Built with production optimizations
- Assets served with caching headers

### Scaling Configuration
- **Backend:** 1-5 replicas, scales at 50 concurrent requests
- **Frontend:** 1-3 replicas, scales at 100 concurrent requests
- **CPU:** Bursting allowed for traffic spikes
- **Memory:** Fixed allocation per container

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors with ACR**
   - Solution: Enable admin user on ACR
   - Command: `az acr update --name fxspotstreamacr --admin-enabled true`

2. **Container Apps Not Starting**
   - Check logs: `az containerapp logs show -n user-dashboard-backend -g research-analytics-rg`
   - Verify secrets are correctly set
   - Ensure Cosmos DB firewall allows Container Apps

3. **CORS Issues**
   - Backend CORS_ORIGINS must include frontend URL
   - Container Apps ingress must allow external traffic

4. **Redis Connection Failures**
   - Verify SSL is enabled (port 6380)
   - Check Redis firewall rules
   - Ensure password is URL-encoded in connection string

### Health Checks
- Backend: GET /health
- Frontend: Static file serving check
- Both configured with liveness and readiness probes

## 🔐 Security Considerations

1. **Secrets Management**
   - All secrets stored as Container App secrets
   - No hardcoded credentials in code or images
   - ACR authentication using admin credentials (managed identity planned)

2. **Network Security**
   - HTTPS enforced by Container Apps
   - Managed certificates by Microsoft
   - Backend accessible only through Container Apps ingress

3. **Authentication**
   - JWT tokens with refresh rotation
   - Prepared for Azure AD integration
   - Secure cookie storage for tokens

## 📊 Monitoring and Logs

### View Logs
```bash
# Backend logs
az containerapp logs show \
  -n user-dashboard-backend \
  -g research-analytics-rg \
  --follow

# Frontend logs
az containerapp logs show \
  -n user-dashboard-frontend \
  -g research-analytics-rg \
  --follow
```

### Metrics
- Available in Azure Portal under Container Apps
- CPU and memory usage per replica
- Request count and latency
- Scaling events

## 🔄 Update Process

1. **Update Code**
   - Make changes in backend/ or frontend/
   - Test locally with docker-compose

2. **Build New Images**
   ```bash
   az acr build --registry fxspotstreamacr --image user-dashboard-backend:v2 backend/
   ```

3. **Update Container App**
   ```bash
   az containerapp update \
     -n user-dashboard-backend \
     -g research-analytics-rg \
     --image fxspotstreamacr.azurecr.io/user-dashboard-backend:v2
   ```

## 📈 Performance Optimization

1. **Image Optimization**
   - Multi-stage builds to reduce size
   - Layer caching for faster builds
   - Production dependencies only

2. **Application Performance**
   - FastAPI async endpoints
   - Redis caching for frequent queries
   - Frontend code splitting and lazy loading

3. **Azure Optimization**
   - Container Apps auto-scaling
   - Cosmos DB auto-scaling RUs
   - CDN integration possible for static assets

## 🎯 Next Steps

1. **CI/CD Pipeline**
   - GitHub Actions integration
   - Automated testing before deployment
   - Blue-green deployments

2. **Enhanced Security**
   - Managed identity for ACR access
   - Azure AD integration
   - API rate limiting

3. **Monitoring Enhancement**
   - Application Insights integration
   - Custom dashboards
   - Alerting rules

4. **Production Readiness**
   - Backup strategies
   - Disaster recovery plan
   - Load testing

---

Deployment Date: 2025-06-21
Last Updated: 2025-06-21
Status: Production Live ✅