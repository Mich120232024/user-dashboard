# User Dashboard - Architecture Documentation

## 🏛️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Container Apps                        │
├─────────────────────────────┬───────────────────────────────────┤
│      Frontend Container     │       Backend Container           │
│    (React + TypeScript)     │        (FastAPI + Python)         │
│                             │                                   │
│   ┌──────────────────┐      │    ┌────────────────────┐        │
│   │   Vite Server    │      │    │   Uvicorn Server   │        │
│   │   Port: 3000     │◄─────┼────┤    Port: 8000      │        │
│   └──────────────────┘      │    └──────────┬─────────┘        │
│                             │               │                   │
└─────────────────────────────┴───────────────┼───────────────────┘
                                              │
                        ┌─────────────────────┴─────────────────────┐
                        │                                           │
                ┌───────▼────────┐                      ┌──────────▼─────────┐
                │  Azure Cosmos  │                      │   Azure Redis      │
                │      DB        │                      │     Cache          │
                │  (MongoDB API) │                      │   (SSL/TLS)        │
                └────────────────┘                      └────────────────────┘
```

## 🔧 Technology Stack

### Backend Architecture

#### Core Framework: FastAPI
- **Why FastAPI over Flask:**
  - Native async/await support for better performance
  - Automatic API documentation (OpenAPI/Swagger)
  - Type hints and Pydantic validation
  - 2-3x faster than Flask in benchmarks
  - Built-in WebSocket support

#### Database: Azure Cosmos DB
- **API:** MongoDB API for flexibility
- **Driver:** Motor (async MongoDB driver)
- **Collections:**
  ```
  user_dashboard/
  ├── users           # User accounts and profiles
  ├── sessions        # Active user sessions
  ├── dashboard_data  # Dashboard metrics and data
  └── audit_logs      # System audit trail
  ```

#### Cache: Azure Redis
- **Purpose:** Session storage, real-time data, API caching
- **Connection:** SSL/TLS on port 6380
- **Patterns:**
  - Session tokens with TTL
  - API response caching
  - Real-time dashboard updates
  - Distributed locks

#### Authentication & Security
```python
# JWT Token Structure
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": 1234567890,
  "type": "access|refresh"
}
```
- Access tokens: 30 minutes
- Refresh tokens: 7 days
- Bcrypt password hashing
- CORS configured per environment

### Frontend Architecture

#### Core Framework: React 18 + TypeScript
- **Build Tool:** Vite for fast HMR and optimized builds
- **Routing:** React Router v6
- **State Management:** Zustand (lightweight Redux alternative)
- **Data Fetching:** TanStack Query v5
- **Forms:** React Hook Form
- **Styling:** Tailwind CSS
- **Real-time:** Socket.io client

#### Component Structure
```
src/
├── components/          # Reusable UI components
│   ├── common/         # Buttons, inputs, modals
│   ├── dashboard/      # Dashboard-specific widgets
│   └── layout/         # Header, sidebar, footer
├── pages/              # Route-based page components
├── hooks/              # Custom React hooks
├── store/              # Zustand stores
│   ├── auth.ts        # Authentication state
│   ├── dashboard.ts   # Dashboard data
│   └── ui.ts          # UI preferences
├── api/                # API client functions
└── types/              # TypeScript definitions
```

#### State Management with Zustand
```typescript
// Example store structure
interface AuthState {
  user: User | null
  token: string | null
  login: (credentials: LoginData) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}
```

## 🌐 API Design

### RESTful Endpoints

#### Authentication
```
POST   /api/v1/auth/login      # User login
POST   /api/v1/auth/refresh    # Refresh token
POST   /api/v1/auth/logout     # User logout
GET    /api/v1/auth/me         # Current user info
```

#### Users
```
GET    /api/v1/users           # List users (paginated)
GET    /api/v1/users/{id}      # Get user details
POST   /api/v1/users           # Create user
PUT    /api/v1/users/{id}      # Update user
DELETE /api/v1/users/{id}      # Delete user
```

#### Dashboard
```
GET    /api/v1/dashboard/stats     # Dashboard statistics
GET    /api/v1/dashboard/metrics   # Time-series metrics
GET    /api/v1/dashboard/activity  # Recent activity
```

### WebSocket Events
```
WS     /ws/{client_id}         # WebSocket connection

Events:
- dashboard:update            # Real-time dashboard updates
- notification:new           # New notifications
- user:status_change        # User online/offline
```

### API Response Format
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2025-06-21T10:00:00Z",
    "version": "1.0.0"
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  }
}
```

## 🔄 Data Flow

### Authentication Flow
```
1. User enters credentials
2. Frontend POST /api/v1/auth/login
3. Backend validates credentials
4. Backend generates JWT tokens
5. Frontend stores tokens (Zustand + localStorage)
6. Frontend includes token in API headers
7. Backend validates token on each request
```

### Real-time Updates Flow
```
1. Frontend establishes WebSocket connection
2. Backend authenticates WebSocket
3. Backend pushes updates to Redis pub/sub
4. Redis broadcasts to all backend instances
5. Backend sends to connected clients
6. Frontend updates UI optimistically
```

## 🏗️ Infrastructure Patterns

### Container Apps Configuration

#### Scaling Rules
```bicep
scale: {
  minReplicas: 1
  maxReplicas: 5
  rules: [{
    name: 'http-rule'
    http: {
      metadata: {
        concurrentRequests: '50'
      }
    }
  }]
}
```

#### Health Checks
```bicep
probes: [{
  type: 'Liveness'
  httpGet: {
    path: '/health'
    port: 8000
  }
  periodSeconds: 30
}, {
  type: 'Readiness'
  httpGet: {
    path: '/health'
    port: 8000
  }
  periodSeconds: 10
}]
```

### Database Patterns

#### Cosmos DB Design
- **Partitioning:** By user_id for user data
- **Indexing:** Compound indexes on frequently queried fields
- **Consistency:** Session consistency for balance
- **RU Scaling:** Auto-scale 400-4000 RUs

#### Redis Patterns
```python
# Session storage
await redis.setex(f"session:{token}", 1800, user_data)

# API caching
cache_key = f"api:dashboard:stats:{user_id}"
await redis.setex(cache_key, 300, json.dumps(stats))

# Real-time updates
await redis.publish("dashboard:updates", json.dumps(update))
```

## 🔐 Security Architecture

### Defense in Depth
1. **Network Layer:** Azure Container Apps managed ingress
2. **Transport Layer:** HTTPS only with managed certificates
3. **Application Layer:** JWT authentication, CORS
4. **Data Layer:** Encrypted at rest in Cosmos DB/Redis

### Security Headers
```python
# FastAPI middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Additional headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## 📊 Performance Optimization

### Backend Optimizations
1. **Async Operations:** All I/O operations are async
2. **Connection Pooling:** Motor/Redis connection pools
3. **Query Optimization:** Indexed queries, projections
4. **Caching Strategy:** Redis for frequently accessed data

### Frontend Optimizations
1. **Code Splitting:** Vite automatic chunks
2. **Lazy Loading:** React.lazy for routes
3. **Query Caching:** TanStack Query stale-while-revalidate
4. **Asset Optimization:** Vite build optimization

### Caching Strategy
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Browser   │────▶│   Frontend  │────▶│   Backend    │
│   Cache     │     │   Container │     │   Container  │
└─────────────┘     └─────────────┘     └──────┬───────┘
                                               │
                                        ┌──────▼───────┐
                                        │    Redis     │
                                        │    Cache     │
                                        └──────┬───────┘
                                               │
                                        ┌──────▼───────┐
                                        │  Cosmos DB   │
                                        └──────────────┘
```

## 🚀 Deployment Architecture

### Blue-Green Deployment (Future)
```
┌─────────────────────┐         ┌─────────────────────┐
│   Blue (Current)    │         │   Green (New)       │
│   - Backend v1      │         │   - Backend v2      │
│   - Frontend v1     │ ──────▶ │   - Frontend v2     │
└─────────────────────┘         └─────────────────────┘
         ▲                                  │
         │            Traffic               │
         └──────────── Shift ───────────────┘
```

### CI/CD Pipeline (Planned)
```
GitHub Push → GitHub Actions → Build → Test → ACR → Container Apps
     │             │             │       │      │           │
     └─────────────┴─────────────┴───────┴──────┴───────────┘
                        Automated Pipeline
```

## 📈 Monitoring Architecture

### Telemetry Collection
```
Application ──▶ Container Apps Logs ──▶ Log Analytics ──▶ Dashboards
     │                                         │
     └──────▶ Application Insights ◀───────────┘
                      │
                      ▼
                  Alerts & Notifications
```

### Key Metrics
- **Application:** Response time, error rate, throughput
- **Infrastructure:** CPU, memory, replica count
- **Business:** Active users, API usage, feature adoption

## 🔮 Future Architecture Enhancements

1. **Microservices Split**
   - Auth service
   - Dashboard service
   - Notification service

2. **Event-Driven Architecture**
   - Azure Service Bus for async processing
   - Event sourcing for audit trail

3. **Advanced Caching**
   - CDN for static assets
   - GraphQL with DataLoader pattern

4. **Multi-Region**
   - Cosmos DB global distribution
   - Traffic Manager for routing

---

Architecture Version: 1.0.0
Last Updated: 2025-06-21
Status: Production Architecture