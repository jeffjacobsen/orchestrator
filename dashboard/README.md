# Orchestrator Dashboard

Real-time web dashboard for the Claude Multi-Agent Orchestrator system.

## 🎯 Phase 1 Core Dashboard

This is the initial implementation (Phase 1) of the comprehensive dashboard proposal ([DASHBOARD_PROPOSAL_V2.md](../DASHBOARD_PROPOSAL_V2.md)).

### Features Implemented

- ✅ FastAPI backend with SQLAlchemy + Alembic
- ✅ React 18 + TypeScript + Vite frontend
- ✅ Bearer token authentication
- ✅ Agent list view with real-time updates (5s polling)
- ✅ Dark/light mode toggle
- ✅ Docker Compose for local development
- ✅ Responsive design with TailwindCSS
- ✅ CORS configured for frontend/backend communication

### Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy 2.0 (async ORM)
- Alembic (database migrations)
- SQLite (development) / PostgreSQL (production ready)
- Pydantic (validation)

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Query (data fetching)
- Lucide React (icons)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional, recommended)

### Option 1: Docker Compose (Recommended)

```bash
# From dashboard directory
cd dashboard

# Copy environment file
cp .env.example .env

# Edit .env with your API key
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

### Option 2: Manual Setup

#### Backend Setup

```bash
cd dashboard/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Run database migrations
alembic upgrade head

# Start backend server
python -m app.main
```

Backend will be available at http://localhost:8000

#### Frontend Setup

```bash
cd dashboard/frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your API key
nano .env

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

## 📖 Usage

### Authentication

All API requests require a Bearer token. Set your API key in `.env`:

```env
API_KEY=your-secure-api-key-here
```

Then use it in requests:

```bash
curl -H "Authorization: Bearer your-secure-api-key-here" \
  http://localhost:8000/api/v1/agents
```

The frontend automatically includes the API key from environment variables.

### API Endpoints

#### Health Checks
- `GET /health` - Health check
- `GET /ready` - Readiness check

#### Agents
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `POST /api/v1/agents` - Create new agent
- `DELETE /api/v1/agents/{agent_id}` - Delete agent

#### Tasks
- `GET /api/v1/tasks` - List all tasks
- `GET /api/v1/tasks/{task_id}` - Get task details
- `POST /api/v1/tasks` - Create new task
- `DELETE /api/v1/tasks/{task_id}` - Delete task

See full API documentation at http://localhost:8000/api/docs

### Frontend Features

#### Dark Mode
Click the sun/moon icon in the header to toggle dark mode. Preference is saved to localStorage.

#### Agent List
- Real-time updates (polls every 5 seconds)
- Shows agent status, role, tokens, cost
- Color-coded by status and role
- Duration tracking for active agents

## 🔧 Development

### Backend Development

```bash
cd dashboard/backend

# Run tests
pytest

# Type checking
mypy app/

# Format code
black app/
isort app/

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd dashboard/frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
dashboard/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Database migrations
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   ├── types/           # TypeScript types
│   │   ├── lib/             # Utilities
│   │   └── App.tsx          # Main app
│   ├── package.json         # Node dependencies
│   └── Dockerfile
├── docker-compose.yml       # Docker orchestration
└── README.md
```

## 🔒 Security Notes

**Important for Production:**

1. **Change default keys** in `.env`:
   ```env
   SECRET_KEY=use-a-strong-random-secret-here
   API_KEY=use-a-strong-random-api-key-here
   ```

2. **Use HTTPS** in production

3. **Configure CORS** properly:
   ```env
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

4. **Use PostgreSQL** for production:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@host/db
   ```

5. **Phase 5 will add**: OAuth2/JWT, RBAC, rate limiting

## 🛠️ Database Migrations

### SQLite to PostgreSQL

When ready to migrate:

1. Install PostgreSQL driver:
   ```bash
   pip install asyncpg
   ```

2. Update `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/orchestrator
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

The SQLAlchemy abstraction makes this seamless!

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Check database file permissions
- Verify `.env` file exists
- Check logs: `docker-compose logs backend`

### Frontend won't connect to backend
- Verify backend is running: http://localhost:8000/health
- Check CORS configuration in backend `.env`
- Verify API key matches between frontend and backend
- Check browser console for errors

### Database errors
- Delete `orchestrator.db` and run `alembic upgrade head` to recreate
- Check alembic migrations are up to date

## 📋 Next Steps (Phase 2+)

See [DASHBOARD_PROPOSAL_V2.md](../DASHBOARD_PROPOSAL_V2.md) for the complete roadmap:

- [ ] WebSocket for real-time updates (eliminate polling)
- [ ] Task execution UI with complexity estimation
- [ ] Prompt engineering integration
- [ ] Workflow preview and ANALYST inclusion controls
- [ ] Cost analytics and charts
- [ ] Agent conversation viewer
- [ ] File logging viewer
- [ ] And much more...

## 🤝 Contributing

This is Phase 1 of a 5-phase implementation. Contributions welcome!

1. Check [DASHBOARD_PROPOSAL_V2.md](../DASHBOARD_PROPOSAL_V2.md) for planned features
2. Open an issue to discuss major changes
3. Create a branch and submit a PR

## 📝 License

Part of the Claude Multi-Agent Orchestrator project.

---

**Status**: Phase 1 Core Dashboard ✅ Completed
**Next**: Phase 2 Task Management & Workflow Intelligence
