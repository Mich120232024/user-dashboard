# User Management Dashboard

## 📋 Overview
A comprehensive dashboard for managing Research & Analytics Services agents, monitoring system health, and visualizing data relationships.

## 🚀 Quick Start

### Using Docker Compose (Recommended)
```bash
# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
# Open dashboard.html in browser or use a local server
python -m http.server 8000
```

## 🏗️ Architecture

### Services
- **Backend**: Flask API server (Python)
- **Frontend**: Static HTML/JS/CSS
- **Redis**: Caching and session storage
- **Nginx**: Static file serving and reverse proxy

### Key Features
- Real-time agent monitoring
- Cosmos DB integration
- Memory layer visualization
- System health metrics
- Document viewer
- Graph visualization

## 📁 Project Structure
```
user-dashboard/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── api/               # API endpoints
│   └── utils/             # Utility functions
├── frontend/
│   ├── dashboard.html     # Main dashboard
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript modules
├── docker-compose.yml     # Container orchestration
├── Dockerfile            # Container definition
└── nginx.conf           # Web server config
```

## 🔧 Configuration

### Environment Variables
See `.env.example` for all required variables:
- `COSMOS_ENDPOINT`: Azure Cosmos DB endpoint
- `COSMOS_KEY`: Cosmos DB primary key
- `REDIS_URL`: Redis connection string
- `BLOB_CONNECTION_STRING`: Azure Blob Storage

### Ports
- Backend API: 5001
- Frontend: 80
- Redis: 6379

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=backend tests/
```

## 📊 API Documentation

### Endpoints
- `GET /api/stats` - System statistics
- `GET /api/live/agents` - Active agents list
- `GET /api/memory/layers` - Memory architecture
- `GET /api/cosmos/overview` - Database overview
- `GET /health` - Health check

## 🚢 Deployment

### Build and Push
```bash
# Build image
docker build -t user-dashboard:latest .

# Tag for registry
docker tag user-dashboard:latest myregistry.azurecr.io/user-dashboard:latest

# Push to registry
docker push myregistry.azurecr.io/user-dashboard:latest
```

### Deploy to Azure
```bash
# Using Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name user-dashboard \
  --image myregistry.azurecr.io/user-dashboard:latest \
  --dns-name-label my-dashboard \
  --ports 80
```

## 🐛 Troubleshooting

### Common Issues
1. **Modals not opening**: Check browser console for JS errors
2. **API 404 errors**: Ensure backend is running on port 5001
3. **Redis connection failed**: Check Redis is running and accessible
4. **Cosmos DB timeout**: Verify credentials and network access

### Debug Mode
```bash
# Enable debug logging
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
```

## 📝 License
Internal use only - Research & Analytics Services

## 👥 Contributors
- HEAD_OF_ENGINEERING
- Full Stack Software Engineer
- Data Analyst

---
*Last Updated: 2025-06-20*