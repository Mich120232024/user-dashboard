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

## API Endpoints

- `GET /api/v1/messages/{agent}` - Get messages for agent
- `POST /api/v1/messages/` - Send new message  
- `PUT /api/v1/messages/{id}/status` - Update message status
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
└── README.md
```

## License

MIT License - Built for Research & Analytics Services workspace.