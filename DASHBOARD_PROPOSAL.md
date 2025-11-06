# UI Dashboard Proposal - Claude Multi-Agent Orchestrator

**Version:** 1.0
**Date:** 2025-11-06
**Status:** Proposal - Phase 5 Implementation

---

## Executive Summary

This proposal outlines the design and implementation plan for a web-based observability dashboard for the Claude Multi-Agent Orchestrator. The dashboard will provide real-time visibility into agent fleet operations, cost analytics, task execution, and workflow management through an intuitive web interface.

**Key Benefits:**
- **Real-time Visibility**: Monitor agent fleet status, costs, and activities in real-time
- **Cost Management**: Track spending, set budgets, and receive alerts
- **Operational Control**: Create, monitor, and manage agents through a web UI
- **Analytics & Insights**: Historical analysis of task execution and performance
- **Enhanced UX**: Visual workflow design and agent conversation browsing

---

## 1. Project Goals

### Primary Objectives

1. **Real-Time Fleet Monitoring**
   - Live agent status grid with activity indicators
   - Visual workflow progress tracking
   - Context window usage visualization
   - Active agent counter and role distribution

2. **Cost Observability & Control**
   - Real-time cost accumulation display
   - Interactive cost analytics charts
   - Budget tracking with alerts
   - Cost breakdown by agent/role/task

3. **Historical Analytics**
   - Task execution history with timeline view
   - Performance trends over time
   - Success/failure rate analysis
   - Agent lifecycle patterns

4. **Operational Control**
   - Manual agent creation with custom roles
   - Agent deletion and cleanup
   - Task submission via web UI
   - Workflow template selection

5. **Enhanced Debugging**
   - Agent conversation viewer
   - File diff viewer (consumed vs produced)
   - Tool call inspection
   - Error logs and diagnostics

### Success Metrics

- **Usability**: Users can monitor agent operations without CLI
- **Performance**: Dashboard updates within 500ms of state changes
- **Cost Awareness**: Clear cost visibility reduces unexpected spending by 50%
- **Debugging Efficiency**: Reduce time to diagnose issues by 70%

---

## 2. Technical Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser Client                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  React Frontend (TypeScript)                     │  │
│  │  • Component Library: shadcn/ui + TailwindCSS    │  │
│  │  • State Management: React Query + Zustand       │  │
│  │  • Charts: Recharts                              │  │
│  │  • Real-time: WebSocket client                   │  │
│  │  • Routing: React Router                         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────────┘
               │ HTTP + WebSocket
┌──────────────▼──────────────────────────────────────────┐
│              FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  REST API Endpoints                              │  │
│  │  • /api/agents - CRUD operations                 │  │
│  │  • /api/tasks - Task management                  │  │
│  │  • /api/metrics - Analytics queries              │  │
│  │  • /api/status - Fleet status                    │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  WebSocket Server                                │  │
│  │  • /ws/fleet - Real-time fleet updates           │  │
│  │  • /ws/agent/{id} - Per-agent activity stream    │  │
│  │  • /ws/costs - Real-time cost updates            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Event Publisher                                 │  │
│  │  • Subscribe to orchestrator events              │  │
│  │  • Broadcast to WebSocket clients                │  │
│  │  • Event buffering and replay                    │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────────┘
               │ Python API calls
┌──────────────▼──────────────────────────────────────────┐
│         Existing Orchestrator System                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Orchestrator (Core)                             │  │
│  │  • AgentManager (CRUD)                           │  │
│  │  • TaskPlanner & WorkflowExecutor                │  │
│  │  • AgentMonitor (Real-time monitoring)           │  │
│  │  • MetricsCollector (Analytics)                  │  │
│  │  • Database (SQLite persistence)                 │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Real-Time Updates:**
```
Orchestrator Event (agent created, status changed, etc.)
    ↓
AgentMonitor callback
    ↓
Event Publisher (FastAPI service)
    ↓
WebSocket broadcast to connected clients
    ↓
React Query invalidates cache + UI updates
```

**User Actions:**
```
User clicks "Create Agent" in UI
    ↓
React component dispatches action
    ↓
HTTP POST to /api/agents
    ↓
FastAPI handler calls Orchestrator.create_agent()
    ↓
Orchestrator creates agent + triggers monitor event
    ↓
WebSocket broadcasts agent_created event
    ↓
All connected clients update their UI
```

### 2.3 Integration Points

**Existing Infrastructure to Leverage:**

1. **AgentMonitor Callbacks**
   - Register dashboard event publisher as callback
   - Receive real-time events: agent_created, agent_deleted, status_changed, etc.
   - Forward events to WebSocket clients

2. **Orchestrator API**
   - Wrap existing methods in FastAPI endpoints
   - `Orchestrator.get_status()` → `/api/status`
   - `Orchestrator.list_agents()` → `/api/agents`
   - `Orchestrator.execute()` → `/api/tasks` (POST)

3. **MetricsCollector**
   - Query for historical analytics
   - Cost breakdowns by agent/role/task
   - File tracking data

4. **Database**
   - Direct SQLite queries for historical data
   - Task history and trends
   - Agent lifecycle patterns

---

## 3. Technology Stack Recommendation

### 3.1 Frontend Stack

**Framework: React 18+ with TypeScript**

*Justification:*
- Mature ecosystem with extensive libraries
- Excellent TypeScript support for type safety
- Strong community and documentation
- Proven for real-time dashboards
- Better developer availability than SvelteKit

**UI Components: shadcn/ui + TailwindCSS**

*Justification:*
- shadcn/ui provides high-quality, customizable components
- TailwindCSS for rapid, consistent styling
- Accessible by default (ARIA compliance)
- Composable and extensible
- Modern aesthetic matching developer tools

**Alternative Considered:** SvelteKit
- Pros: Smaller bundle size, simpler syntax
- Cons: Smaller ecosystem, fewer UI libraries, less developer familiarity
- **Decision:** React for maturity and ecosystem

**State Management: React Query + Zustand**

*Justification:*
- React Query: Excellent for server state, caching, WebSocket integration
- Zustand: Lightweight client state management (UI state, filters, etc.)
- Avoid Redux complexity for this scale
- Built-in devtools for debugging

**Charts: Recharts**

*Justification:*
- React-native chart library (better integration than Chart.js)
- Composable API with React components
- Responsive and customizable
- Good performance for real-time updates
- TypeScript support

**Real-Time: WebSocket + React Query**

*Justification:*
- Native WebSocket API for bidirectional communication
- React Query integration for automatic cache invalidation
- Simple pub/sub pattern
- Low overhead for frequent updates

### 3.2 Backend Stack

**Framework: FastAPI**

*Justification:*
- Modern async Python framework
- Built-in WebSocket support
- Automatic OpenAPI documentation
- Type validation with Pydantic (already used in orchestrator)
- Excellent performance for I/O-bound operations
- Easy integration with existing async codebase

**API Documentation: Swagger UI (built-in)**

**Authentication: OAuth2/JWT (Phase 2)**

*Note:* Initial version assumes trusted network, production deployment adds authentication

### 3.3 Deployment Stack

**Containerization: Docker + Docker Compose**

*Services:*
- Frontend container (Nginx + static React build)
- Backend container (FastAPI + Uvicorn)
- Shared volume for SQLite database
- Reverse proxy for unified deployment

**Production Considerations:**
- **Hosting:** Single VPS/EC2 instance sufficient for <100 concurrent users
- **Database:** SQLite adequate for single-instance, PostgreSQL for multi-instance
- **Scaling:** Stateless backend allows horizontal scaling with load balancer

---

## 4. Feature Breakdown & Implementation Phases

### Phase 1: Core Dashboard (2-3 weeks)

**MVP Features:**

1. **Fleet Status Overview**
   - Real-time agent count (total, active, by status)
   - Role distribution pie chart
   - Cost accumulation display
   - Token usage summary

2. **Agent List View**
   - Table with: ID, Role, Status, Cost, Tokens, Created At
   - Status badges with colors (running=green, completed=blue, etc.)
   - Sort by: status, cost, time, role
   - Filter by: status, role
   - Pagination for large fleets

3. **Real-Time Updates**
   - WebSocket connection indicator
   - Auto-refresh on events
   - Live status badge updates
   - Cost ticker animation

4. **Agent Details Modal**
   - Click agent row → open detailed view
   - Show: metrics, configuration, timestamps
   - Tool calls count
   - Files read/written
   - Execution time

5. **Basic Navigation**
   - Header with logo and status indicators
   - Sidebar with: Dashboard, Agents, Tasks, Analytics
   - Responsive layout (desktop-first, mobile-friendly)

**Backend API Endpoints:**
```
GET  /api/status            # Fleet status summary
GET  /api/agents            # List all agents (with filters)
GET  /api/agents/{id}       # Agent details
POST /api/agents            # Create agent
DELETE /api/agents/{id}     # Delete agent
WS   /ws/fleet              # Real-time fleet updates
```

**Deliverable:** Functional dashboard for monitoring existing agents

---

### Phase 2: Task Management (1-2 weeks)

**Features:**

1. **Task Execution UI**
   - Prompt input form with syntax highlighting
   - Task type selector (auto, feature_implementation, bug_fix, etc.)
   - Execution mode toggle (sequential/parallel)
   - Template preview (show which agents will be used)
   - Submit button with loading state

2. **Task History View**
   - Table with: Task ID, Prompt (truncated), Status, Cost, Duration
   - Timeline visualization of task execution
   - Filter by: status, date range, task type
   - Search by prompt content

3. **Task Details Page**
   - Full prompt display
   - Workflow diagram showing agent sequence
   - Per-agent breakdown (cost, tokens, duration)
   - Result preview
   - Re-run button

4. **Live Task Execution View**
   - Real-time progress bar with workflow steps
   - Current agent activity indicator
   - Streaming cost updates
   - Elapsed time counter
   - Cancel task button

**Backend API Endpoints:**
```
GET  /api/tasks             # List all tasks (with filters)
GET  /api/tasks/{id}        # Task details
POST /api/tasks             # Submit new task
DELETE /api/tasks/{id}      # Cancel running task
WS   /ws/tasks/{id}         # Real-time task progress
```

**Deliverable:** Full task execution and monitoring via web UI

---

### Phase 3: Analytics & Cost Management (2 weeks)

**Features:**

1. **Cost Dashboard**
   - Current session cost with trend indicator
   - Daily/weekly/monthly cost charts
   - Cost breakdown by: agent role, task type, date
   - Top 10 most expensive agents/tasks
   - Cost per token analysis

2. **Budget Management**
   - Set budget limits (per day/week/month)
   - Budget progress bar
   - Alert configuration (email, webhook, in-app)
   - Cost projections based on current usage
   - Budget history and adjustments

3. **Performance Analytics**
   - Token usage over time (input vs output)
   - Cache read efficiency (cache read tokens vs total)
   - Tool call frequency analysis
   - Agent execution time distributions
   - Success/failure rates by task type

4. **Historical Trends**
   - Cost trends over 30/60/90 days
   - Agent creation rate over time
   - Peak usage hours heatmap
   - Task completion times histogram

5. **Export & Reporting**
   - Export data as CSV/JSON
   - Generate PDF reports with charts
   - Custom date range selection
   - Scheduled email reports

**Backend API Endpoints:**
```
GET  /api/metrics/costs         # Cost analytics
GET  /api/metrics/performance   # Performance metrics
GET  /api/metrics/trends        # Historical trends
POST /api/budgets               # Set budget limits
GET  /api/budgets               # Get budget status
POST /api/reports/export        # Export data
```

**Deliverable:** Comprehensive cost visibility and management

---

### Phase 4: Advanced Features (2-3 weeks)

**Features:**

1. **Agent Conversation Viewer**
   - Message-by-message conversation display
   - Thinking blocks (collapsed by default)
   - Tool calls with inputs/outputs
   - Timestamps for each message
   - Search within conversation
   - Copy message content

2. **File Tracking Viewer**
   - Two-column view: Consumed | Produced
   - File path with line count
   - Diff viewer for modified files
   - Download files
   - File change history timeline

3. **Custom Agent Creation**
   - Form with: Role, Custom Instructions, Model, Tools
   - Template selector (start from existing role)
   - Save custom templates
   - Test agent with sample prompt
   - Clone existing agent configuration

4. **Workflow Designer (Visual)**
   - Drag-and-drop workflow builder
   - Node types: Analyst, Planner, Builder, etc.
   - Connect nodes to define flow
   - Sequential vs parallel branch configuration
   - Save and name custom workflows
   - Load workflow templates

5. **Alert System**
   - Configure alerts: high cost, agent failure, context overflow
   - Multiple notification channels: in-app, email, webhook
   - Alert history and management
   - Snooze/dismiss alerts
   - Custom alert rules

**Backend API Endpoints:**
```
GET  /api/agents/{id}/conversation  # Full conversation history
GET  /api/agents/{id}/files         # Files consumed/produced
POST /api/workflows                 # Save custom workflow
GET  /api/workflows                 # List saved workflows
POST /api/alerts/rules              # Configure alert rules
GET  /api/alerts                    # Get active alerts
```

**Deliverable:** Power-user features for advanced debugging and control

---

### Phase 5: Polish & Production (1-2 weeks)

**Features:**

1. **Authentication & Security**
   - OAuth2/JWT authentication
   - User roles: Admin, Developer, Viewer
   - API key management
   - Session management
   - CSRF protection

2. **Settings & Configuration**
   - Theme toggle (light/dark mode)
   - Dashboard layout customization
   - Auto-refresh interval configuration
   - Notification preferences
   - Export preferences

3. **Performance Optimizations**
   - Virtual scrolling for large lists
   - Lazy loading for heavy components
   - WebSocket connection pooling
   - Database query optimization
   - Caching strategies

4. **Production Deployment**
   - Docker Compose setup
   - Environment configuration guide
   - Health check endpoints
   - Logging and monitoring setup
   - Backup and recovery procedures

5. **Documentation**
   - User guide with screenshots
   - API documentation (Swagger)
   - Deployment guide
   - Troubleshooting section
   - Video tutorials

**Deliverable:** Production-ready dashboard with full documentation

---

## 5. Implementation Timeline

| Phase | Duration | Features | Dependencies |
|-------|----------|----------|--------------|
| Phase 1 | 2-3 weeks | Core dashboard, agent list, real-time updates | None |
| Phase 2 | 1-2 weeks | Task execution, history, live progress | Phase 1 |
| Phase 3 | 2 weeks | Cost analytics, budgets, reports | Phase 1, 2 |
| Phase 4 | 2-3 weeks | Conversation viewer, workflow designer | Phase 1, 2 |
| Phase 5 | 1-2 weeks | Auth, polish, production deployment | All phases |

**Total Estimated Time:** 8-12 weeks (2-3 months)

**Suggested Approach:** Iterative delivery with weekly demos

---

## 6. Backend API Design

### 6.1 REST API Endpoints

**Base URL:** `http://localhost:8000/api/v1`

#### Fleet Management

```yaml
GET /status
Response:
  fleet:
    total_agents: int
    active_agents: int
    by_status: { [status]: count }
    by_role: { [role]: count }
    total_cost: string
    total_tokens: int
  metrics: { ... }
  tasks: { total: int, active: int }
  monitoring: { ... }

GET /agents?status={status}&role={role}&limit={limit}&offset={offset}
Response:
  agents: [
    {
      id: string
      role: string
      status: string
      model: string
      cost: string
      tokens: int
      created_at: string
      updated_at: string
    }
  ]
  total: int
  limit: int
  offset: int

GET /agents/{agent_id}
Response:
  id: string
  role: string
  status: string
  model: string
  custom_instructions: string
  config: { ... }
  metrics: { ... }
  files_read: string[]
  files_written: string[]
  created_at: string
  updated_at: string

POST /agents
Body:
  role: string
  custom_instructions?: string
  model?: string
  tools?: string[]
Response:
  agent_id: string
  status: string

DELETE /agents/{agent_id}
Response:
  success: boolean
  message: string
```

#### Task Management

```yaml
GET /tasks?status={status}&task_type={type}&limit={limit}&offset={offset}
Response:
  tasks: [
    {
      id: string
      prompt: string
      task_type: string
      status: string
      cost: string
      duration_seconds: float
      created_at: string
      completed_at: string
    }
  ]
  total: int

GET /tasks/{task_id}
Response:
  id: string
  prompt: string
  task_type: string
  mode: string
  status: string
  result: { ... }
  subtasks: [ ... ]
  agents: [ ... ]
  cost: string
  created_at: string
  completed_at: string

POST /tasks
Body:
  prompt: string
  task_type?: string
  mode?: "sequential" | "parallel"
  cleanup?: boolean
Response:
  task_id: string
  status: string

DELETE /tasks/{task_id}  # Cancel running task
Response:
  success: boolean
```

#### Analytics & Metrics

```yaml
GET /metrics/costs?start_date={date}&end_date={date}&group_by={agent|role|task|day}
Response:
  breakdown: [
    {
      key: string
      cost: float
      tokens: int
      percentage: float
    }
  ]
  total_cost: float
  period: { start: string, end: string }

GET /metrics/performance?start_date={date}&end_date={date}
Response:
  average_execution_time: float
  success_rate: float
  tool_calls: { total: int, by_tool: { ... } }
  cache_efficiency: float
  token_breakdown: { input: int, output: int, cache_read: int }

GET /metrics/trends?metric={cost|tokens|agents}&period={day|week|month}
Response:
  data_points: [
    { timestamp: string, value: float }
  ]
  trend: "increasing" | "decreasing" | "stable"
```

#### Budgets

```yaml
GET /budgets
Response:
  daily_limit: float
  weekly_limit: float
  monthly_limit: float
  current_usage: {
    daily: float
    weekly: float
    monthly: float
  }
  alerts_enabled: boolean

POST /budgets
Body:
  daily_limit?: float
  weekly_limit?: float
  monthly_limit?: float
  alerts_enabled?: boolean
Response:
  success: boolean
```

#### Workflows

```yaml
GET /workflows
Response:
  workflows: [
    {
      id: string
      name: string
      description: string
      roles: string[]
      created_at: string
    }
  ]

POST /workflows
Body:
  name: string
  description: string
  roles: string[]
  custom_instructions?: { [role]: string }
Response:
  workflow_id: string
```

### 6.2 WebSocket Events

**Connection:** `ws://localhost:8000/ws/fleet`

**Event Format:**
```json
{
  "type": "event_type",
  "timestamp": "2025-11-06T12:34:56Z",
  "data": { ... }
}
```

**Event Types:**

```yaml
agent_created:
  data:
    agent_id: string
    role: string
    status: string

agent_status_changed:
  data:
    agent_id: string
    old_status: string
    new_status: string

agent_deleted:
  data:
    agent_id: string

task_created:
  data:
    task_id: string
    prompt: string
    task_type: string

task_progress:
  data:
    task_id: string
    current_step: string
    progress_percentage: float
    cost: float
    elapsed_time: float

task_completed:
  data:
    task_id: string
    status: "completed" | "failed"
    cost: float
    duration: float

cost_update:
  data:
    total_cost: float
    delta: float
    agent_id?: string

alert_triggered:
  data:
    alert_type: "high_cost" | "budget_exceeded" | "agent_error"
    severity: "warning" | "error"
    message: string
    details: { ... }
```

---

## 7. UI/UX Design Considerations

### 7.1 Design Principles

1. **Clarity Over Complexity**
   - Show most important metrics prominently
   - Progressive disclosure for detailed information
   - Clear visual hierarchy

2. **Real-Time Feedback**
   - Immediate visual feedback for user actions
   - Loading states for async operations
   - Optimistic UI updates where appropriate

3. **Performance**
   - Virtual scrolling for large lists
   - Lazy loading for heavy components
   - Debounced search and filters

4. **Accessibility**
   - WCAG 2.1 AA compliance
   - Keyboard navigation support
   - Screen reader compatibility

### 7.2 Key UI Components

**Dashboard Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Header: Logo | Navigation | User Menu             │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│  Sidebar │        Main Content Area                 │
│          │                                          │
│  • Dash  │  ┌────────────────────────────────────┐ │
│  • Agents│  │  Fleet Status Cards                │ │
│  • Tasks │  │  [Agents] [Cost] [Tokens] [Tasks]  │ │
│  • Analyt│  └────────────────────────────────────┘ │
│  • Alerts│                                          │
│          │  ┌────────────────────────────────────┐ │
│          │  │  Real-Time Cost Chart              │ │
│          │  │  (Line graph)                      │ │
│          │  └────────────────────────────────────┘ │
│          │                                          │
│          │  ┌────────────────────────────────────┐ │
│          │  │  Active Agents Table               │ │
│          │  │  [ID] [Role] [Status] [Cost] [...]│ │
│          │  └────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────┘
```

**Agent Details Modal:**
```
┌─────────────────────────────────────────────────────┐
│  Agent Details: planner-abc123              [Close] │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Status      │  │ Cost        │  │ Tokens      │ │
│  │ COMPLETED ✓ │  │ $0.0234     │  │ 5,432       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                     │
│  Configuration                                      │
│  • Role: PLANNER                                    │
│  • Model: claude-sonnet-4                           │
│  • Created: 2025-11-06 12:34:56                     │
│  • Duration: 23.4s                                  │
│                                                     │
│  Metrics                                            │
│  • Tool Calls: 12                                   │
│  • Messages: 5                                      │
│  • Files Read: 8                                    │
│  • Files Written: 2                                 │
│                                                     │
│  [View Conversation] [View Files] [Delete Agent]    │
└─────────────────────────────────────────────────────┘
```

**Color Palette:**
- Primary: Blue (#3B82F6) - Actions, links
- Success: Green (#10B981) - Completed, positive metrics
- Warning: Yellow (#F59E0B) - Warnings, high usage
- Error: Red (#EF4444) - Errors, alerts
- Neutral: Gray (#6B7280) - Text, borders

**Status Indicators:**
- CREATED: Gray dot
- RUNNING: Animated blue dot
- WAITING: Yellow dot
- COMPLETED: Green checkmark
- FAILED: Red X
- DELETED: Gray strikethrough

---

## 8. Technical Challenges & Solutions

### Challenge 1: Real-Time Performance with Many Agents

**Problem:** WebSocket broadcasts to many clients with high-frequency updates could overwhelm server/clients

**Solutions:**
1. **Event Batching:** Buffer events for 250ms and send batch updates
2. **Selective Subscriptions:** Clients subscribe to specific agents/tasks only
3. **Throttling:** Limit update frequency per client (e.g., max 4 updates/second)
4. **Debouncing:** Coalesce rapid status changes into single update

### Challenge 2: Large Historical Data Queries

**Problem:** Analytics queries on months of data could be slow

**Solutions:**
1. **Database Indexes:** Create indexes on frequently queried columns (timestamp, agent_id, task_id)
2. **Aggregation Tables:** Pre-compute daily/weekly summaries
3. **Pagination:** Limit query results and implement cursor-based pagination
4. **Caching:** Cache analytics results for 5 minutes using Redis/in-memory cache

### Challenge 3: Concurrent Agent Operations

**Problem:** Multiple users creating/deleting agents simultaneously

**Solutions:**
1. **Database Transactions:** Use SQLite transactions for atomic operations
2. **Optimistic Locking:** Version tracking to detect conflicts
3. **Event Sourcing:** Log all operations for audit trail and replay
4. **Rate Limiting:** Limit API requests per user/IP

### Challenge 4: WebSocket Connection Management

**Problem:** Clients disconnecting, reconnecting, needing event replay

**Solutions:**
1. **Connection Registry:** Track active WebSocket connections
2. **Heartbeat Mechanism:** Ping/pong to detect dead connections
3. **Auto-Reconnect:** Client-side exponential backoff reconnection
4. **Event Buffer:** Keep 5-minute event buffer for reconnecting clients
5. **Sequence Numbers:** Track last received event for replay

### Challenge 5: Cost Calculation Accuracy

**Problem:** Ensuring dashboard cost matches orchestrator's tracking

**Solutions:**
1. **Single Source of Truth:** Always query MetricsCollector, never recalculate
2. **Atomic Updates:** Update cost and broadcast event in same transaction
3. **Reconciliation:** Periodic check to verify dashboard totals match database
4. **Event Logging:** Log every cost update for audit trail

---

## 9. Development Environment Setup

### 9.1 Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Docker and Docker Compose (optional, for containerization)
- Git

### 9.2 Project Structure

```
orchestrator/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── api/             # API route handlers
│   │   │   ├── agents.py
│   │   │   ├── tasks.py
│   │   │   ├── metrics.py
│   │   │   └── websockets.py
│   │   ├── models/          # Pydantic models for API
│   │   ├── services/        # Business logic
│   │   │   ├── orchestrator_service.py
│   │   │   └── event_publisher.py
│   │   └── config.py        # Configuration
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Dashboard/
│   │   │   ├── AgentList/
│   │   │   ├── TaskView/
│   │   │   └── Analytics/
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API client
│   │   ├── stores/          # Zustand stores
│   │   ├── types/           # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml       # Multi-container setup
└── docs/
    └── DASHBOARD_API.md     # API documentation
```

### 9.3 Local Development Commands

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

**Docker:**
```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## 10. Security Considerations

### 10.1 Initial Phase (Trusted Network)

- Assume deployment on trusted network (localhost, internal VPN)
- No authentication required for Phase 1-4
- Focus on functionality and UX

### 10.2 Production Security (Phase 5)

**Authentication:**
- OAuth2 with JWT tokens
- Support for multiple providers (Google, GitHub, email/password)
- Session management with refresh tokens

**Authorization:**
- Role-based access control (Admin, Developer, Viewer)
- API endpoint permissions per role
- Agent/task ownership model

**API Security:**
- CORS configuration for allowed origins
- Rate limiting per user/IP
- Request validation with Pydantic
- SQL injection prevention (parameterized queries)
- XSS prevention (React's built-in escaping)

**Data Security:**
- HTTPS only in production
- Secure WebSocket (wss://)
- API key rotation
- Secrets management (environment variables, not hardcoded)

**Audit Logging:**
- Log all user actions (create, delete, execute)
- IP address and timestamp tracking
- Export audit logs for compliance

---

## 11. Testing Strategy

### 11.1 Backend Testing

**Unit Tests:**
- Test API endpoints with pytest
- Mock Orchestrator calls
- Test WebSocket event publishing
- Test error handling

**Integration Tests:**
- Test full API → Orchestrator flow
- Test WebSocket connections and broadcasting
- Test database operations

**Load Tests:**
- Simulate 100 concurrent WebSocket connections
- Test API throughput (requests/second)
- Test database query performance under load

### 11.2 Frontend Testing

**Unit Tests:**
- Test React components with React Testing Library
- Test hooks and utilities
- Test state management (Zustand stores)

**Integration Tests:**
- Test user flows (create agent, submit task, etc.)
- Test WebSocket connection handling
- Test error scenarios

**E2E Tests:**
- Playwright for full user journey testing
- Test critical paths (dashboard → create agent → monitor)
- Test real-time updates

### 11.3 Manual Testing

- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Mobile responsiveness testing
- Accessibility testing (screen reader, keyboard navigation)
- Performance profiling (React DevTools, Chrome DevTools)

---

## 12. Deployment Strategy

### 12.1 Development Deployment

- Docker Compose for local development
- Hot reload for both frontend and backend
- Shared volume for SQLite database
- Environment-specific configs

### 12.2 Staging Deployment

- Deploy to VPS or AWS EC2
- Use Docker Compose with production build
- Environment variables for configuration
- HTTPS with Let's Encrypt
- Monitoring with basic logging

### 12.3 Production Deployment

**Infrastructure:**
- VPS or cloud instance (AWS EC2, DigitalOcean, etc.)
- Minimum: 2 CPU cores, 4GB RAM, 40GB SSD
- Nginx reverse proxy for SSL termination
- Domain with DNS configured

**Services:**
- Frontend: Static build served by Nginx
- Backend: Uvicorn with Gunicorn (multiple workers)
- Database: SQLite (or PostgreSQL for multi-instance)

**Monitoring:**
- Application logs (structured JSON)
- Error tracking (Sentry)
- Performance monitoring (uptime checks)
- Cost alerts (integrated in dashboard)

**Backup:**
- Daily SQLite database backups
- Retention: 30 days
- Automated backup scripts
- Restore testing

**CI/CD:**
- GitHub Actions for automated testing
- Build Docker images on push to main
- Deploy to staging on PR merge
- Manual approval for production deploy

---

## 13. Success Criteria

### Phase 1 (MVP) Success:
- [ ] Dashboard loads in <2 seconds
- [ ] Real-time updates within 500ms of events
- [ ] Displays agent list with accurate status
- [ ] Shows real-time cost accumulation
- [ ] WebSocket connection remains stable for 1+ hour

### Phase 2 (Task Management) Success:
- [ ] User can submit task via web UI
- [ ] Live task progress displays correctly
- [ ] Task history shows all completed tasks
- [ ] Task details view shows accurate metrics

### Phase 3 (Analytics) Success:
- [ ] Cost charts display historical data accurately
- [ ] Budget alerts trigger at configured thresholds
- [ ] Export generates valid CSV/JSON files
- [ ] Analytics queries complete in <3 seconds

### Phase 4 (Advanced Features) Success:
- [ ] Conversation viewer displays all message types
- [ ] File diff viewer shows accurate changes
- [ ] Workflow designer saves and loads correctly
- [ ] Custom agent creation works with all options

### Phase 5 (Production) Success:
- [ ] Authentication works with OAuth2
- [ ] Dashboard supports 50+ concurrent users
- [ ] 99.5% uptime over 30 days
- [ ] All security measures implemented
- [ ] Documentation complete and accurate

---

## 14. Open Questions & Decisions Needed

### Technical Decisions

1. **Database Migration Path**
   - Q: Stick with SQLite or migrate to PostgreSQL?
   - Recommendation: Start with SQLite, add PostgreSQL support in Phase 5 if multi-instance needed

2. **Real-Time Update Frequency**
   - Q: What's the optimal update frequency for cost/status?
   - Recommendation: 250ms for active agents, 1s for inactive, configurable per user

3. **Historical Data Retention**
   - Q: How long to keep agent/task history?
   - Recommendation: 90 days default, configurable, with archive feature

4. **Multi-User Support Priority**
   - Q: How important is multi-user from the start?
   - Recommendation: Phase 5 (production), assume single user for MVP

### UX Decisions

1. **Default View**
   - Q: What should users see when they first open the dashboard?
   - Options: Fleet overview, active agents, recent tasks
   - Recommendation: Fleet overview with active agents list

2. **Agent Cleanup Behavior**
   - Q: Should dashboard auto-cleanup completed agents?
   - Recommendation: Manual cleanup by default, auto-cleanup toggle in settings

3. **Cost Display Format**
   - Q: Show cost in cents ($0.0234) or dollars with more precision?
   - Recommendation: Adaptive (cents for <$1, dollars for >$1)

4. **Alert Preferences**
   - Q: What alerts should be enabled by default?
   - Recommendation: Budget exceeded (default on), high cost per agent (default off)

---

## 15. Next Steps

### Immediate Actions (This Week)

1. **Review & Approval**
   - Stakeholder review of this proposal
   - Prioritize features (must-have vs nice-to-have)
   - Finalize tech stack decisions

2. **Project Setup**
   - Create `backend/` and `frontend/` directories
   - Initialize FastAPI project with basic structure
   - Initialize React project with TypeScript + Vite
   - Set up Docker Compose for local development

3. **Design Mockups**
   - Create Figma/wireframes for key screens
   - Define component library structure
   - Establish design system (colors, typography, spacing)

### Week 2-3: Phase 1 Implementation

1. **Backend Foundation**
   - Implement FastAPI endpoints for fleet status
   - Set up WebSocket server
   - Integrate with existing Orchestrator
   - Write tests for API endpoints

2. **Frontend Foundation**
   - Implement dashboard layout with sidebar
   - Create agent list component
   - Set up React Query for data fetching
   - Implement WebSocket connection

3. **Integration**
   - Connect frontend to backend API
   - Test real-time updates end-to-end
   - Deploy to local environment

### Ongoing

- Weekly demos to stakeholders
- Iterative feedback and adjustments
- Documentation updates
- Test coverage improvements

---

## 16. Appendix

### A. Glossary

- **Fleet**: Collection of all agents managed by the orchestrator
- **Agent**: Individual Claude AI instance with specific role
- **Task**: High-level user request decomposed into subtasks
- **Workflow**: Sequence or parallel execution of agent roles
- **Metrics**: Quantitative measurements (cost, tokens, time, etc.)
- **WebSocket**: Bidirectional communication protocol for real-time updates

### B. References

- [Orchestrator ROADMAP.md](ROADMAP.md) - Project roadmap and Phase 5 plans
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Recharts Documentation](https://recharts.org/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [WebSocket RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)

### C. Estimated Costs

**Development Costs:**
- Phase 1: 80-120 hours
- Phase 2: 40-80 hours
- Phase 3: 60-80 hours
- Phase 4: 80-120 hours
- Phase 5: 40-80 hours
- **Total:** 300-480 hours (2-3 months with 1 full-time developer)

**Infrastructure Costs (Annual):**
- VPS Hosting: $120-240/year ($10-20/month)
- Domain: $15/year
- SSL Certificate: $0 (Let's Encrypt)
- **Total:** ~$135-255/year

**Estimated Cost Savings:**
- Reduced debugging time: 70% faster issue resolution
- Proactive cost management: 30-50% cost reduction through visibility
- Improved developer productivity: 2-3x faster agent management vs CLI

---

## Conclusion

This proposal outlines a comprehensive, phased approach to building a production-ready web dashboard for the Claude Multi-Agent Orchestrator. The dashboard will provide real-time visibility, cost management, and operational control through an intuitive web interface.

**Key Strengths:**
- Leverages existing observability infrastructure
- Incremental delivery with clear milestones
- Modern, proven technology stack
- Comprehensive feature set addressing user needs
- Production-ready security and deployment strategy

**Recommended Next Steps:**
1. Approve tech stack and architecture
2. Prioritize Phase 1-4 features
3. Create design mockups
4. Begin Phase 1 implementation

**Questions?** Let's discuss and refine this proposal together.

---

**Prepared by:** Claude (AI Assistant)
**Date:** 2025-11-06
**Version:** 1.0 - Initial Proposal
