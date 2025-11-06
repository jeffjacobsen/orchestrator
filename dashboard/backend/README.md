# Orchestrator Dashboard Backend

FastAPI backend for the Claude Multi-Agent Orchestrator Dashboard.

## Features

- **FastAPI** with async support
- **SQLAlchemy 2.0** with async engine
- **Alembic** for database migrations
- **Bearer token authentication** (Phase 1)
- **CORS** configured for frontend
- **Pydantic** for validation
- **SQLite** for development (PostgreSQL migration path ready)

## Setup

### 1. Install Dependencies

```bash
cd dashboard/backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Important**: Change `SECRET_KEY` and `API_KEY` in production!

### 3. Initialize Database

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Run Development Server

```bash
# From backend directory
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

### Health Checks

- `GET /health` - Health check
- `GET /ready` - Readiness check

### Agents (v1)

- `GET /api/v1/agents` - List agents (with pagination and filtering)
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `POST /api/v1/agents` - Create new agent
- `DELETE /api/v1/agents/{agent_id}` - Delete agent

### Tasks (v1)

- `GET /api/v1/tasks` - List tasks (with pagination and filtering)
- `GET /api/v1/tasks/{task_id}` - Get task details
- `POST /api/v1/tasks` - Create new task
- `DELETE /api/v1/tasks/{task_id}` - Delete task

## Authentication

All API endpoints (except health checks) require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/v1/agents
```

Set your API key in `.env`:
```
API_KEY=your-api-key-here
```

## Database Migrations

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1
```

### Migration to PostgreSQL

When ready to migrate from SQLite to PostgreSQL:

1. Update `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/orchestrator
   ```

2. Install PostgreSQL driver:
   ```bash
   pip install asyncpg
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

## Development

### Code Quality

```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Testing

```bash
pytest
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── agents.py      # Agent endpoints
│   │       └── tasks.py       # Task endpoints
│   ├── core/
│   │   ├── config.py          # Settings
│   │   ├── database.py        # DB configuration
│   │   └── security.py        # Authentication
│   ├── models/
│   │   ├── agent.py           # Agent model
│   │   └── task.py            # Task model
│   ├── schemas/
│   │   ├── agent.py           # Agent schemas
│   │   ├── task.py            # Task schemas
│   │   └── common.py          # Common schemas
│   └── main.py                # FastAPI app
├── alembic/
│   ├── versions/              # Migration files
│   └── env.py                 # Alembic config
├── requirements.txt
└── .env
```

## Next Steps (Phase 1)

- [x] Core API structure
- [x] Database models and schemas
- [x] Authentication (Bearer token)
- [ ] WebSocket for real-time updates
- [ ] Integration with existing orchestrator
- [ ] Frontend integration
