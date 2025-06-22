# User Dashboard

A professional dashboard for the Research & Analytics Services workspace with Azure Cosmos DB integration.

## Features

✅ **Complete Messaging System**
- Send/receive messages between agents
- Message status management (read/unread/archived)
- Real-time message filtering and search
- Compose modal with agent selection
- Infinite scroll with pagination

✅ **Cosmos DB Explorer**
- Browse all containers and documents
- Real-time document viewing
- Container statistics and metrics

✅ **Agent Management**
- View active agents and their status
- Agent details and activity monitoring

✅ **Overview Dashboard**
- System metrics and health monitoring
- Container counts and document statistics
- Recent activity feed

## Tech Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: FastAPI (Python)
- **Database**: Azure Cosmos DB
- **Authentication**: Azure Key Vault integration
- **Architecture**: RESTful APIs with caching

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```bash
cd frontend
python3 -m http.server 8080
```

Open http://localhost:8080/professional-dashboard.html

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[Messaging System](docs/MESSAGING_SYSTEM.md)** - Complete guide to the inbox/messaging features
- **[Website Documentation](docs/WEBSITE_DOCUMENTATION.md)** - Overall website architecture and features

### Key Features Documented
- CRUD messaging operations with database persistence
- Folder organization logic (All/Unread/Sent/Archived)
- Advanced UX with hover effects and smooth transitions
- Safari-compatible modal system with ESC key handling
- Security implementation and data validation
- Performance optimizations and caching strategies

## API Endpoints

- `GET /api/v1/messages/{agent}` - Get messages for agent
- `POST /api/v1/messages/` - Send new message  
- `PUT /api/v1/messages/{id}/status` - Update message status
- `PUT /api/v1/messages/{id}/edit` - Edit message content
- `GET /api/v1/cosmos/containers` - List containers
- `GET /api/v1/cosmos/containers/{id}/documents` - Get documents
- `GET /api/v1/agents/` - List active agents
- `GET /api/v1/monitoring/system` - System health

## Development

The dashboard uses a professional dark theme matching the port 5001 color scheme with:
- Gradient headers and clean typography
- Split-layout UI for data viewing
- Real-time updates and refresh buttons
- Proper loading states and error handling
- No external dependencies (vanilla JS)
- Evidence-based development with database verification

## Architecture

```
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # API route handlers
│   │   ├── services/             # Business logic
│   │   └── main.py              # FastAPI app
│   └── requirements.txt
├── frontend/
│   └── professional-dashboard.html  # Single-page app
├── docs/                           # Comprehensive documentation
│   ├── MESSAGING_SYSTEM.md        # Messaging system guide
│   └── WEBSITE_DOCUMENTATION.md   # Website architecture
└── README.md
```

## License

MIT License - Built for Research & Analytics Services workspace.