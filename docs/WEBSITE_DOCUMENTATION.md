# User Dashboard Website Documentation

## 🌐 Website Overview

The User Dashboard is a comprehensive web application providing a professional interface for managing the Research & Analytics Services ecosystem. Built with modern web technologies and Azure cloud integration, it serves as the central hub for system management, agent communication, and data visualization.

## 🏗️ Architecture Overview

### Technology Stack
- **Frontend**: Vanilla JavaScript, HTML5, CSS3 (no framework dependencies)
- **Backend**: FastAPI (Python) with async/await patterns
- **Database**: Azure Cosmos DB (serverless, globally distributed)
- **Authentication**: Azure Key Vault integration
- **Deployment**: Container-ready for Azure Container Apps
- **Styling**: Custom CSS with professional dark theme

### Project Structure
```
user-dashboard-clean/
├── frontend/
│   ├── professional-dashboard.html    # Main dashboard SPA
│   ├── test_modal.html               # Testing utilities
│   └── assets/                       # Static resources
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI application
│   │   ├── api/v1/endpoints/         # API route handlers
│   │   └── services/                 # Business logic
│   └── requirements.txt              # Python dependencies
├── docs/                             # Documentation
└── README.md                         # Project overview
```

## 📑 Available Tabs

### 1. Overview
- System health metrics and status
- Real-time performance monitoring
- Quick access to recent activities

### 2. Mailbox (Enhanced)
- **Folder Organization**: All Messages, Unread, Sent, Archived
- **Message Counts**: Real-time count badges for each folder
- **Filtering**: Click folders to filter message view
- **Message Preview**: Shows subject, sender, timestamp, and preview text
- **Time Display**: Smart relative time (e.g., "5m ago", "2h ago")
- **Compose Button**: Quick access to create new messages

### 3. Cosmos Explorer
- Browse all Cosmos DB containers
- View document counts and partition keys
- Drill down into individual documents
- Real-time data updates

### 4. Graph DB
- Interactive network visualization
- Agent relationship mapping
- Cytoscape.js powered diagrams

### 5. Agent Shell
- Direct agent management interface
- Status monitoring and control
- Shell command execution

### 6. Manager
- System administration tools
- User management capabilities
- Configuration controls

### 7. Workspace
- File and project management
- Workspace organization tools
- Resource allocation

### 8. Documentation
- **Azure Integration**: All docs stored in Azure Blob Storage
- **58 Total Documents**: Including 18 core files from HEAD_OF_RESEARCH
- **Categorized View**: Expandable categories with subcategories
- **Search & Filter**: Find documents by name or tags
- **Real-time Loading**: Content fetched directly from Azure

### 9. Architecture (New)
- **HTML Diagram Viewer**: Interactive architecture diagrams
- **Full-Screen Mode**: Detailed diagram examination
- **Smart Categories**: Auto-categorization of diagrams
- **Human-Readable Titles**: Automatic title generation from filenames
- **Secure Sandboxing**: All HTML content in isolated iframes

## 🎨 Design System

### Color Scheme (Port 5001 Reference)
```css
:root {
    --primary-dark: #0a0e27;          /* Deep navy background */
    --primary-blue: #1e3a8a;          /* Primary action blue */
    --accent-blue: #3b82f6;           /* Interactive blue */
    --accent-cyan: #06b6d4;           /* Edit/info cyan */
    --success-green: #10b981;         /* Success states */
    --warning-amber: #f59e0b;         /* Warning/archive */
    --danger-red: #ef4444;            /* Error states */
    --bg-dark: #0f172a;               /* Main background */
    --bg-card: #1e293b;               /* Card backgrounds */
    --bg-hover: #334155;              /* Hover states */
    --text-primary: #f1f5f9;          /* Primary text */
    --text-secondary: #94a3b8;        /* Secondary text */
    --text-muted: #64748b;            /* Muted text */
}
```

### Typography
- **Primary Font**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Monospace Font**: `'SF Mono', Monaco, 'Cascadia Code', monospace`
- **Font Sizes**: 12px (small), 13px (body), 14px (default), 16px (headings)

### UI Components

#### Buttons
- **Primary**: Blue background, white text, hover darkens
- **Secondary**: Transparent background, border, hover fills
- **Hover Effect**: `translateY(-1px)` lift with `0.2s ease` transition

#### Cards
- **Background**: `var(--bg-card)` with subtle border
- **Padding**: 20px standard, 16px compact
- **Border Radius**: 8px for consistency
- **Shadow**: Subtle drop shadows for depth

#### Modals
- **Backdrop**: `rgba(0,0,0,0.7)` with blur effect
- **Content**: Centered card with max 80vh height
- **Animations**: Fade in/out with opacity transitions
- **Accessibility**: Focus management and ESC key support

## 📱 Dashboard Features

### 8-Tab Navigation System

#### 1. Overview Tab
- **Purpose**: System health and metrics dashboard
- **Content**: Container counts, agent status, system monitoring
- **Data Sources**: Cosmos DB, monitoring APIs, agent endpoints

#### 2. Mailbox Tab  
- **Purpose**: Complete messaging system (see MESSAGING_SYSTEM.md)
- **Features**: Send, receive, edit, archive messages
- **Database**: system_inbox container with real-time updates

#### 3. Cosmos Explorer Tab
- **Purpose**: Database management interface  
- **Features**: Browse containers, view documents, real-time queries
- **Security**: Read-only access with governance controls

#### 4. Graph DB Tab
- **Purpose**: Relationship visualization (placeholder)
- **Future**: Cytoscape.js integration for data relationships
- **Placeholder**: "Graph visualization coming soon"

#### 5. Agent Shell Tab
- **Purpose**: AI agent management and monitoring
- **Features**: Agent status, activity logs, performance metrics
- **Data**: Live agent data with fallback mock data

#### 6. Manager Tab
- **Purpose**: Management dashboard (placeholder)
- **Features**: Team metrics, task management
- **Content**: Statistical overview with expansion planned

#### 7. Workspace Tab
- **Purpose**: File system and project management
- **Features**: Directory tree, workspace navigation
- **Structure**: Organized project hierarchy display

#### 8. Research Viz Tab
- **Purpose**: Research data visualization (placeholder)
- **Future**: Advanced analytics and research insights
- **Placeholder**: "Research visualization coming soon"

## 🔌 API Integration

### Endpoint Architecture
- **Base URL**: `http://localhost:8001/api/v1`
- **Authentication**: Azure Key Vault integration
- **Response Format**: JSON with consistent error handling
- **Caching**: 30-second TTL for read operations

### Key Endpoints

#### Health & Monitoring
- `GET /monitoring/system` - System health metrics
- `GET /cosmos/containers` - Database container listing

#### Messaging System
- `GET /messages/{agent}` - Get messages for agent
- `POST /messages/` - Send new message
- `PUT /messages/{id}/edit` - Edit message content
- `PUT /messages/{id}/status` - Update message status

#### Agent Management
- `GET /agents/` - List active agents
- `GET /agents/{name}` - Get agent details

## 🚀 Performance Features

### Caching Strategy
```javascript
const apiCache = new Map();
const CACHE_TTL = 30000; // 30 seconds

async function fetchDataCached(url, skipCache = false) {
    // Check cache first for performance
    // Real API call with caching logic
    // Automatic cache invalidation
}
```

### Optimized Loading
- **Lazy Loading**: Tab content loaded on demand
- **Pagination**: 50 messages per request with infinite scroll
- **Local State**: Immediate UI updates with DB sync
- **Error Recovery**: Graceful fallbacks and retry logic

### Smooth Animations
- **Transitions**: `0.2s ease` for all interactive elements
- **Hover Effects**: Subtle lift animations (`translateY(-1px)`)
- **Modal Transitions**: Fade in/out with opacity
- **Loading States**: Progressive button text updates

## 🔐 Security Implementation

### Authentication Flow
- **Azure Key Vault**: Secure credential storage
- **Environment Variables**: No hardcoded secrets
- **API Security**: Token-based authentication
- **CORS Handling**: Proper cross-origin configuration

### Data Protection
- **Input Validation**: Pydantic models for API validation
- **XSS Prevention**: Content sanitization
- **SQL Injection**: Parameterized queries only
- **Authorization**: Role-based access controls

## 🌐 Deployment Architecture

### Local Development
```bash
# Frontend (port 8080)
cd frontend && python3 -m http.server 8080

# Backend (port 8001)  
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Azure Container Apps Ready
- **Containerized**: Docker support for consistent deployment
- **Environment Config**: Azure-compatible environment variables
- **Health Checks**: Built-in health monitoring endpoints
- **Scaling**: Auto-scaling configuration ready

### Database Configuration
- **Cosmos DB**: Serverless consumption-based billing
- **Containers**: Optimized partition keys for performance
- **Backup**: Automatic Azure backup and recovery
- **Monitoring**: Built-in Azure monitoring integration

## 🔧 Development Workflow

### Code Standards
- **Evidence-Based**: Every feature verified with real data
- **Database-First**: All operations persist to Cosmos DB
- **Professional Integrity**: 100% complete solutions only
- **Security Compliance**: Key Vault authentication mandatory

### Git Workflow
```bash
# Regular commits with detailed messages
git add .
git commit -m "Feature: Add message editing with database persistence"
git push origin main
```

### Testing Approach
- **Manual Testing**: Cross-browser compatibility verification
- **API Testing**: cURL commands for endpoint validation
- **Database Testing**: Real Cosmos DB operations
- **UX Testing**: Safari ESC key handling verification

## 📊 Monitoring & Analytics

### System Metrics
- **API Response Times**: Sub-second performance targets
- **Database Operations**: Query performance monitoring
- **Error Rates**: Zero tolerance for deployment failures
- **User Experience**: Smooth animations and feedback

### Health Indicators
- **Green Status**: All systems operational
- **API Connectivity**: Backend responding properly
- **Database Health**: Cosmos DB queries succeeding
- **Frontend Functionality**: All tabs loading correctly

## 🔄 Maintenance Procedures

### Regular Tasks
- **Git Commits**: Push improvements to repository
- **Documentation Updates**: Keep docs current with features
- **Performance Review**: Monitor response times
- **Security Audit**: Review authentication and authorization

### Troubleshooting Guide
1. **Backend Issues**: Check uvicorn process and restart if needed
2. **Database Errors**: Verify Cosmos DB connection and credentials
3. **Frontend Bugs**: Check browser console for JavaScript errors
4. **API Failures**: Test endpoints with cURL commands

## 🎯 Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration for live data
- **Advanced Search**: Full-text search across messages and data
- **File Attachments**: Document upload and management
- **Mobile Optimization**: Responsive design improvements
- **Dashboard Customization**: User-configurable layouts

### Technical Debt
- **Framework Migration**: Consider React/Vue for complex interactions
- **State Management**: Implement Redux/Vuex for large-scale state
- **TypeScript**: Add type safety for better development experience
- **Testing Suite**: Automated testing framework implementation

## 📖 User Guide

### Getting Started
1. **Access**: Navigate to `http://localhost:8080/professional-dashboard.html`
2. **Navigation**: Use top tab bar to switch between sections
3. **Messaging**: Click Mailbox tab to send/receive messages
4. **Data**: Use Cosmos Explorer to view database contents

### Common Workflows
- **Send Message**: Mailbox → Compose → Select recipient → Send
- **Edit Message**: Find your sent message → Edit button → Modify → Save
- **Archive Message**: View message → Archive button → Confirm
- **Check System Health**: Overview tab → View metrics and status

---

**Professional Dashboard - Built for Production**  
**Azure-Ready Architecture with Evidence-Based Development**  
**Zero Deployment Failures Standard Maintained**

*Last Updated: 2025-06-22*  
*Maintained by: HEAD_OF_ENGINEERING*  
*Repository: [user-dashboard](https://github.com/Mich120232024/user-dashboard)*