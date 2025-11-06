# UI Dashboard Proposal - Claude Multi-Agent Orchestrator

**Version:** 2.0 (Revised)
**Date:** 2025-11-05
**Status:** Proposal - Phase 5 Implementation
**Revision Notes:** Incorporated review feedback, added missing integrations, enhanced security and testing strategies

---

## Executive Summary

This proposal outlines the design and implementation plan for a web-based observability dashboard for the Claude Multi-Agent Orchestrator. The dashboard will provide real-time visibility into agent fleet operations, cost analytics, task execution, and workflow management through an intuitive web interface.

**Key Benefits:**
- **Real-time Visibility**: Monitor agent fleet status, costs, and activities in real-time
- **Cost Management**: Track spending, set budgets, and receive intelligent alerts
- **Operational Control**: Create, monitor, and manage agents through a web UI
- **Analytics & Insights**: Historical analysis of task execution and performance
- **Enhanced UX**: Visual workflow design, agent conversation browsing, and prompt preview
- **Smart Workflows**: Integration with ANALYST optimization and prompt engineering

**NEW in v2.0:**
- Integration with v0.1.3 ANALYST workflow optimization
- Prompt engineering system integration (prompts.py module)
- Agent file logging viewer (JSONL support)
- Enhanced security from Phase 1
- SQLAlchemy database abstraction for future PostgreSQL migration
- Comprehensive error handling strategy
- Specific performance targets and testing coverage

---

## 1. Project Goals

### Primary Objectives

1. **Real-Time Fleet Monitoring**
   - Live agent status grid with activity indicators
   - Visual workflow progress tracking
   - Context window usage visualization with warnings
   - Active agent counter and role distribution
   - **NEW**: ANALYST usage tracking (when included/excluded)

2. **Cost Observability & Control**
   - Real-time cost accumulation display
   - Interactive cost analytics charts
   - Budget tracking with intelligent alerts
   - Cost breakdown by agent/role/task
   - **NEW**: Cost comparison for workflows with/without ANALYST

3. **Historical Analytics**
   - Task execution history with timeline view
   - Performance trends over time
   - Success/failure rate analysis
   - Agent lifecycle patterns
   - **NEW**: Workflow efficiency analysis

4. **Operational Control**
   - Manual agent creation with custom roles
   - **NEW**: System prompt preview and customization
   - Agent deletion and cleanup
   - Task submission via web UI
   - **NEW**: Smart workflow template selection with complexity estimation

5. **Enhanced Debugging**
   - Agent conversation viewer
   - **NEW**: Agent file logging viewer (prompt.txt, text.txt, tools.jsonl, summary.jsonl)
   - File diff viewer (consumed vs produced)
   - Tool call inspection with JSONL parsing
   - Error logs and diagnostics

### Success Metrics

- **Usability**: Users can monitor agent operations without CLI
- **Performance**: Dashboard updates within 500ms of state changes (p95 < 500ms API response)
- **Cost Awareness**: Clear cost visibility reduces unexpected spending by 50%
- **Debugging Efficiency**: Reduce time to diagnose issues by 70%
- **Reliability**: 99.5% uptime over 30 days in production

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
│  │  • Theme: Dark/Light mode (system default)       │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────────────┘
               │ HTTP + WebSocket (Bearer Token Auth)
┌──────────────▼──────────────────────────────────────────┐
│              FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  REST API Endpoints (with Pydantic validation)   │  │
│  │  • /api/v1/agents - CRUD operations              │  │
│  │  • /api/v1/tasks - Task management               │  │
│  │  • /api/v1/metrics - Analytics queries           │  │
│  │  • /api/v1/prompts - Prompt preview/generation   │  │
│  │  • /api/v1/workflows - Workflow management       │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  WebSocket Server (authenticated)                │  │
│  │  • /ws/fleet - Real-time fleet updates           │  │
│  │  • /ws/tasks/{id} - Per-task progress            │  │
│  │  • /ws/costs - Real-time cost updates            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  SQLAlchemy ORM + Alembic Migrations            │  │
│  │  • Database-agnostic abstraction                 │  │
│  │  • Support SQLite (dev) & PostgreSQL (prod)      │  │
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
│  │  • PromptGenerator (NEW - prompts.py module)     │  │
│  │  • Database (SQLite/PostgreSQL via SQLAlchemy)   │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Database Architecture (NEW)

**SQLAlchemy + Alembic for Migration-Ready Design**

```python
# models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Support both SQLite and PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./orchestrator.db"  # Default: SQLite
    # Production: "postgresql://user:pass@localhost/orchestrator"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

**Migration Triggers (when to move to PostgreSQL):**
- >1000 concurrent API requests/second
- Multi-instance deployment required
- Need for advanced queries (full-text search, JSON operations)
- Team size > 10 concurrent users

### 2.3 Integration Points

**Existing Infrastructure to Leverage:**

1. **AgentMonitor Callbacks**
   - Register dashboard event publisher as callback
   - Receive real-time events: agent_created, agent_deleted, status_changed, etc.
   - Forward events to WebSocket clients

2. **Orchestrator API**
   - Wrap existing methods in FastAPI endpoints
   - `Orchestrator.get_status()` → `/api/v1/status`
   - `Orchestrator.list_agents()` → `/api/v1/agents`
   - `Orchestrator.execute()` → `/api/v1/tasks` (POST)

3. **Prompt Engineering Module (NEW)**
   - `get_role_prompt()` → `/api/v1/prompts/role/{role}`
   - `get_complexity_aware_analyst_prompt()` → `/api/v1/prompts/analyst`
   - `get_analyst_prompt_with_context()` → `/api/v1/prompts/preview`

4. **Agent File Logging (NEW)**
   - Read agent JSONL logs (tools.jsonl, summary.jsonl)
   - Parse and display in timeline view
   - Download individual log files

5. **Workflow Selection Logic**
   - `TaskPlanner._estimate_task_complexity()` → exposed via API
   - Real-time complexity estimation as user types
   - Show which agents will be used before execution

---

## 3. Technology Stack (Validated)

### 3.1 Frontend Stack

**Framework: React 18+ with TypeScript** ✅ Approved
- Mature ecosystem, excellent TypeScript support
- Proven for real-time dashboards

**UI Components: shadcn/ui + TailwindCSS** ✅ Approved
- Accessible by default (WCAG 2.1 AA)
- Dark mode support from Day 1

**State Management: React Query + Zustand** ✅ Approved
- React Query for server state
- Zustand for client state (UI preferences, filters)

**Charts: Recharts** ✅ Approved
- React-native, TypeScript support

**Build Tool: Vite**
- Fast dev server with HMR
- Optimized production builds
- Bundle size target: <500KB gzipped

### 3.2 Backend Stack

**Framework: FastAPI** ✅ Approved
- Async Python, WebSocket support
- Auto-generated OpenAPI docs
- Pydantic validation (already used in orchestrator)

**ORM: SQLAlchemy + Alembic** ✅ NEW
- Database abstraction (SQLite → PostgreSQL path)
- Schema migrations with Alembic
- Type-safe queries

**Authentication: Bearer Token (Phase 1) → OAuth2/JWT (Phase 5)** ✅ Modified
- Start with simple API key authentication
- Upgrade to OAuth2 in Phase 5

**Validation: Pydantic Models** ✅
- Request/response validation
- Type safety across API

### 3.3 Development Tools (NEW)

**Code Generation:**
- `openapi-typescript-codegen` for TypeScript API client
- Keeps frontend/backend types in sync

**Component Development:**
- Storybook for isolated component development
- Living documentation for UI components

**Testing:**
- Backend: pytest, pytest-asyncio
- Frontend: Vitest, React Testing Library, Playwright
- Load testing: Locust

---

## 4. Feature Breakdown & Implementation Phases

### Phase 1: Core Dashboard (2-3 weeks)

**MVP Features:**

1. **Fleet Status Overview**
   - Real-time agent count (total, active, by status)
   - Role distribution pie chart
   - **NEW**: ANALYST usage indicator (included/excluded count)
   - Cost accumulation display
   - Token usage summary

2. **Agent List View**
   - Table with: ID, Role, Status, Cost, Tokens, Created At
   - Status badges with colors (running=green, completed=blue, etc.)
   - Sort by: status, cost, time, role
   - Filter by: status, role
   - **NEW**: Filter by "includes ANALYST" / "excludes ANALYST"
   - Pagination for large fleets (virtual scrolling at >100 rows)

3. **Real-Time Updates**
   - WebSocket connection indicator with retry status
   - Auto-refresh on events
   - Live status badge updates
   - Cost ticker animation
   - **NEW**: Reconnection with event replay (5-min buffer)

4. **Agent Details Modal**
   - Click agent row → open detailed view
   - Show: metrics, configuration, timestamps
   - Tool calls count with breakdown
   - Files read/written with links
   - Execution time and cost breakdown
   - **NEW**: System prompt preview

5. **Basic Navigation**
   - Header with logo and status indicators
   - Sidebar with: Dashboard, Agents, Tasks, Analytics, Settings
   - Responsive layout (desktop-first, mobile-friendly)
   - **NEW**: Dark/Light mode toggle (persisted)
   - **NEW**: Keyboard shortcuts (Cmd+K command palette)

6. **Security & Error Handling** ✅ NEW
   - API key authentication (Bearer token)
   - CORS configuration
   - Input validation with Pydantic
   - Rate limiting (100 req/min per IP)
   - React Error Boundaries for crash recovery
   - Toast notifications for user errors
   - Structured error responses

**Backend API Endpoints:**
```
GET  /api/v1/status            # Fleet status summary
GET  /api/v1/agents            # List all agents (with filters)
GET  /api/v1/agents/{id}       # Agent details
POST /api/v1/agents            # Create agent
DELETE /api/v1/agents/{id}     # Delete agent
GET  /api/v1/prompts/role/{role}  # Get role prompt (NEW)
WS   /ws/fleet                 # Real-time fleet updates
GET  /health                   # Health check endpoint (NEW)
```

**Performance Targets** ✅ NEW:
- Dashboard initial load: <2s
- WebSocket message latency: <100ms
- API response time (p95): <500ms
- Support 100 active agents, 1000 total in DB
- Frontend bundle: <500KB gzipped

**Deliverable:** Functional dashboard for monitoring existing agents with basic auth

---

### Phase 2: Task Management & Workflow Intelligence (2-3 weeks)

**Features:**

1. **Smart Task Execution UI** ✅ ENHANCED
   - Prompt input form with syntax highlighting
   - **NEW**: Real-time complexity estimation as user types
   - **NEW**: Visual indicator: "Simple task - skipping ANALYST ✓"
   - **NEW**: Workflow preview showing which agents will be used
   - Task type selector (auto, feature_implementation, bug_fix, etc.)
   - Execution mode toggle (sequential/parallel)
   - **NEW**: Override option: "Force include ANALYST" checkbox
   - Template preview with cost estimate
   - Submit button with loading state

2. **Prompt Engineering Integration** ✅ NEW
   - System prompt preview for selected role
   - Complexity-aware prompt variations (simple vs complex)
   - Task-specific context preview
   - Custom instructions input
   - Prompt comparison view (before/after customization)

3. **Task History View**
   - Table with: Task ID, Prompt (truncated), Status, Cost, Duration
   - **NEW**: ANALYST included/excluded indicator
   - Timeline visualization of task execution
   - Filter by: status, date range, task type, ANALYST usage
   - Search by prompt content

4. **Task Details Page**
   - Full prompt display
   - Workflow diagram showing agent sequence
   - **NEW**: Highlight if ANALYST was included and why
   - Per-agent breakdown (cost, tokens, duration)
   - Result preview with syntax highlighting
   - Re-run button with options

5. **Live Task Execution View**
   - Real-time progress bar with workflow steps
   - Current agent activity indicator
   - Streaming cost updates
   - Elapsed time counter
   - Cancel task button
   - **NEW**: Show system prompts used for each agent

6. **Workflow Comparison** ✅ NEW
   - Side-by-side comparison: simple vs complex workflow
   - Historical data: "Similar tasks usually cost $X"
   - Recommendation engine based on past executions

**Backend API Endpoints:**
```
GET  /api/v1/tasks             # List all tasks (with filters)
GET  /api/v1/tasks/{id}        # Task details
POST /api/v1/tasks             # Submit new task
POST /api/v1/tasks/estimate    # Estimate task complexity (NEW)
DELETE /api/v1/tasks/{id}      # Cancel running task
GET  /api/v1/prompts/preview   # Preview prompt for task (NEW)
GET  /api/v1/workflows/recommend  # Recommend workflow (NEW)
WS   /ws/tasks/{id}            # Real-time task progress
```

**Deliverable:** Full task execution with intelligent workflow selection and prompt preview

---

### Phase 3: Analytics & Cost Management (2-3 weeks)

*Note: Extended from 2 weeks due to analytics complexity*

**Features:**

1. **Cost Dashboard**
   - Current session cost with trend indicator
   - Daily/weekly/monthly cost charts
   - **NEW**: Cost comparison: tasks with/without ANALYST
   - Cost breakdown by: agent role, task type, date
   - Top 10 most expensive agents/tasks
   - Cost per token analysis
   - **NEW**: Workflow efficiency metrics

2. **Budget Management**
   - Set budget limits (per day/week/month)
   - Budget progress bar with projection
   - Alert configuration (in-app, email, webhook)
   - Cost projections based on current usage
   - Budget history and adjustments
   - **NEW**: Anomaly detection (unusual cost spikes)

3. **Performance Analytics**
   - Token usage over time (input vs output vs cache_read)
   - Cache efficiency tracking
   - Tool call frequency analysis
   - Agent execution time distributions
   - Success/failure rates by task type
   - **NEW**: ANALYST ROI analysis (cost vs benefit)

4. **Intelligent Alerts** ✅ NEW
   - Cost spike detection (>2x normal)
   - Context window warnings (>80% capacity)
   - Stuck agent detection (no progress in 10min)
   - Failed task pattern detection
   - Budget threshold alerts

5. **Historical Trends**
   - Cost trends over 30/60/90 days
   - Agent creation rate over time
   - Peak usage hours heatmap
   - Task completion times histogram
   - **NEW**: Workflow evolution tracking

6. **Export & Reporting**
   - Export data as CSV/JSON
   - Generate PDF reports with charts
   - Custom date range selection
   - **NEW**: Scheduled email reports
   - API for programmatic export

**Backend API Endpoints:**
```
GET  /api/v1/metrics/costs         # Cost analytics
GET  /api/v1/metrics/performance   # Performance metrics
GET  /api/v1/metrics/trends        # Historical trends
GET  /api/v1/metrics/analyst-roi   # ANALYST ROI analysis (NEW)
POST /api/v1/budgets               # Set budget limits
GET  /api/v1/budgets               # Get budget status
POST /api/v1/alerts/rules          # Configure alerts (NEW)
GET  /api/v1/alerts                # Get active alerts (NEW)
POST /api/v1/reports/export        # Export data
```

**Database Optimization** ✅ NEW:
- Indexes on: timestamp, agent_id, task_id, status
- Aggregation tables for daily/weekly summaries
- Pagination with cursor-based approach
- 5-minute cache for analytics queries

**Deliverable:** Comprehensive cost visibility and intelligent alerting

---

### Phase 4: Advanced Features & Debugging (2-3 weeks)

**Features:**

1. **Agent Conversation Viewer**
   - Message-by-message conversation display
   - Thinking blocks (collapsed by default, expandable)
   - Tool calls with inputs/outputs (JSON formatted)
   - Timestamps for each message
   - Search within conversation
   - Copy message content
   - **NEW**: Export conversation as markdown

2. **Agent File Logging Viewer** ✅ NEW
   - View agent logs: prompt.txt, text.txt, tools.jsonl, summary.jsonl
   - JSONL parser with syntax highlighting
   - Timeline view of all agent actions
   - Filter by: tool type, timestamp, outcome
   - Download individual log files
   - Link file operations to file viewer

3. **File Tracking Viewer**
   - Two-column view: Consumed | Produced
   - File path with line count
   - Diff viewer for modified files
   - Syntax highlighting by file type
   - Download files
   - File change history timeline

4. **Custom Agent Creation**
   - Form with: Role, Custom Instructions, Model, Tools
   - **NEW**: System prompt preview (using prompts.py)
   - **NEW**: Complexity selector (simple/complex prompts)
   - Template selector (start from existing role)
   - Save custom templates
   - Test agent with sample prompt
   - Clone existing agent configuration

5. **Workflow Designer (Visual)**
   - Drag-and-drop workflow builder
   - Node types: Analyst, Planner, Builder, Tester, Reviewer
   - Connect nodes to define flow
   - Sequential vs parallel branch configuration
   - **NEW**: Complexity-based template suggestions
   - Save and name custom workflows
   - Load workflow templates
   - Export/import workflows (JSON)

6. **Agent Templating System** ✅ NEW
   - Save agent configurations as reusable templates
   - Template library with categories
   - Share templates (export/import)
   - Version control for templates
   - Fork and customize existing templates

**Backend API Endpoints:**
```
GET  /api/v1/agents/{id}/conversation  # Full conversation history
GET  /api/v1/agents/{id}/logs          # Agent log files (NEW)
GET  /api/v1/agents/{id}/logs/tools    # Parsed tools.jsonl (NEW)
GET  /api/v1/agents/{id}/files         # Files consumed/produced
POST /api/v1/workflows                 # Save custom workflow
GET  /api/v1/workflows                 # List saved workflows
POST /api/v1/templates                 # Save agent template (NEW)
GET  /api/v1/templates                 # List templates (NEW)
```

**Deliverable:** Power-user features for advanced debugging and workflow customization

---

### Phase 5: Polish, Security & Production (2-3 weeks)

*Note: Extended from 1-2 weeks for proper security implementation*

**Features:**

1. **Authentication & Security**
   - OAuth2/JWT authentication (upgrade from API key)
   - User roles: Admin, Developer, Viewer
   - API key management UI
   - Session management with refresh tokens
   - CSRF protection
   - **NEW**: Audit logging (all user actions)
   - **NEW**: IP address tracking
   - **NEW**: Two-factor authentication (optional)

2. **Settings & Configuration**
   - Theme toggle (dark/light mode) - *Already in Phase 1*
   - Dashboard layout customization (widget placement)
   - Auto-refresh interval configuration
   - Notification preferences
   - Export preferences (format, frequency)
   - **NEW**: Keyboard shortcuts configuration
   - **NEW**: Webhook integrations (Slack, Discord)

3. **Performance Optimizations**
   - Virtual scrolling for large lists (>100 rows)
   - Lazy loading for heavy components
   - WebSocket connection pooling
   - Database query optimization (via SQLAlchemy)
   - Caching strategies (Redis optional)
   - **NEW**: Code splitting by route
   - **NEW**: Image optimization
   - **NEW**: Service worker for offline support

4. **Accessibility Enhancements** ✅ NEW
   - WCAG 2.1 AA compliance verified
   - Keyboard navigation for all features
   - Screen reader tested (NVDA/JAWS)
   - Color contrast ratios: 4.5:1 minimum
   - Focus indicators visible
   - ARIA labels on all interactive elements
   - Skip navigation links
   - Reduced motion support

5. **Production Deployment**
   - Docker Compose setup (multi-service)
   - Environment configuration guide
   - Health check endpoints (/health, /ready)
   - Logging and monitoring setup (structured JSON logs)
   - Backup and recovery procedures (automated scripts)
   - **NEW**: CI/CD pipeline (GitHub Actions)
   - **NEW**: Automated testing in pipeline
   - **NEW**: Blue-green deployment support

6. **Monitoring & Observability** ✅ NEW
   - Structured logging (JSON format)
   - Application metrics (Prometheus format optional)
   - Error tracking (Sentry integration optional)
   - Performance monitoring (Lighthouse scores)
   - Uptime monitoring
   - Log retention: 30 days

7. **Documentation**
   - User guide with screenshots
   - API documentation (auto-generated from OpenAPI)
   - Deployment guide (step-by-step)
   - Troubleshooting section with common issues
   - **NEW**: Video tutorials (5-10 min each)
   - **NEW**: FAQ section
   - **NEW**: Keyboard shortcuts reference card

**Deliverable:** Production-ready dashboard with enterprise features

---

## 5. Implementation Timeline (Revised)

| Phase | Duration | Features | Dependencies | Risk Buffer |
|-------|----------|----------|--------------|-------------|
| Phase 1 | 2-3 weeks | Core dashboard, auth, error handling | None | 20% |
| Phase 2 | 2-3 weeks | Task mgmt, workflow intelligence | Phase 1 | 20% |
| Phase 3 | 2-3 weeks | Cost analytics, budgets, alerts | Phase 1, 2 | 25% |
| Phase 4 | 2-3 weeks | Conversation viewer, file logs | Phase 1, 2 | 20% |
| Phase 5 | 2-3 weeks | Security, polish, production | All phases | 25% |

**Total Estimated Time:** 10-15 weeks (2.5-3.5 months)

**Revised from:** 8-12 weeks (added buffers for complexity)

**Suggested Approach:**
- Iterative delivery with **weekly demos**
- Sprint planning every 2 weeks
- Continuous integration/deployment from Day 1
- User feedback incorporated between phases

---

## 6. Error Handling Strategy ✅ NEW

### 6.1 Backend Error Handling

**Structured Error Responses:**
```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    code: str           # "AGENT_NOT_FOUND", "VALIDATION_ERROR", etc.
    message: str        # Human-readable message
    details: dict       # Additional context
    request_id: str     # For debugging
    timestamp: str

# Example usage in FastAPI
@app.exception_handler(AgentNotFoundError)
async def agent_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            code="AGENT_NOT_FOUND",
            message=f"Agent {exc.agent_id} not found",
            details={"agent_id": exc.agent_id},
            request_id=request.state.request_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        ).dict()
    )
```

**Logging Levels:**
- **DEBUG**: Detailed diagnostic info (dev only)
- **INFO**: General operational messages
- **WARNING**: Unusual but handled situations
- **ERROR**: Errors that need attention
- **CRITICAL**: System failures requiring immediate action

**Error Boundaries:**
- Try/except blocks around all agent operations
- Database transaction rollbacks on errors
- Graceful degradation when services unavailable

### 6.2 Frontend Error Handling

**React Error Boundaries:**
```typescript
// ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    // Log to error tracking service
    logErrorToService(error, errorInfo);

    // Show user-friendly error message
    toast.error("Something went wrong. We've been notified.");
  }
}
```

**Retry Logic:**
```typescript
// API client with exponential backoff
const fetchWithRetry = async (url, options, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetch(url, options);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await delay(Math.pow(2, i) * 1000); // Exponential backoff
    }
  }
};
```

**WebSocket Reconnection:**
```typescript
// Auto-reconnect with exponential backoff
const reconnectWebSocket = () => {
  const maxDelay = 30000; // 30 seconds max
  let delay = 1000;

  const connect = () => {
    ws = new WebSocket(WS_URL);

    ws.onclose = () => {
      setTimeout(() => {
        delay = Math.min(delay * 2, maxDelay);
        connect();
      }, delay);
    };
  };
};
```

**User-Facing Errors:**
- Toast notifications for transient errors
- Inline validation messages for forms
- Error states in UI (empty states, retry buttons)
- Graceful degradation (show cached data if API fails)

---

## 7. Testing Strategy (Enhanced)

### 7.1 Backend Testing

**Unit Tests:**
- Test API endpoints with pytest
- Mock Orchestrator calls with pytest-mock
- Test WebSocket event publishing
- Test error handling and edge cases
- **Target Coverage: >80% overall, 100% for critical paths**

**Integration Tests:**
- Test full API → Orchestrator flow
- Test WebSocket connections and broadcasting
- Test database operations (using test database)
- Test authentication flow
- **Target Coverage: >60%**

**Load Tests (using Locust):**
- Simulate 100 concurrent WebSocket connections
- Test API throughput: target 500 req/s
- Test database query performance under load
- Test memory usage with 1000 agents in DB

**Example Test:**
```python
@pytest.mark.asyncio
async def test_create_agent_endpoint():
    """Test agent creation via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agents",
            json={
                "role": "ANALYST",
                "complexity": "complex"
            },
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "agent_id" in data
        assert data["role"] == "ANALYST"
```

### 7.2 Frontend Testing

**Unit Tests (Vitest + React Testing Library):**
- Test React components in isolation
- Test hooks and utilities
- Test state management (Zustand stores)
- **Target Coverage: >70%**

**Integration Tests:**
- Test user flows (create agent, submit task, etc.)
- Test WebSocket connection handling
- Test error scenarios and recovery
- Test form validation

**E2E Tests (Playwright):**
- Test critical paths (dashboard → create agent → monitor)
- Test real-time updates
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Mobile responsiveness testing
- **Top 5 user journeys must have E2E tests**

**Accessibility Tests:**
- Automated WCAG checks (axe-core)
- Manual screen reader testing (NVDA/JAWS)
- Keyboard navigation verification
- Color contrast validation

**Example E2E Test:**
```typescript
test('user can create agent and monitor status', async ({ page }) => {
  // Navigate to dashboard
  await page.goto('/dashboard');

  // Open create agent dialog
  await page.click('[data-testid="create-agent-button"]');

  // Fill in form
  await page.selectOption('[name="role"]', 'ANALYST');
  await page.fill('[name="custom_instructions"]', 'Test agent');

  // Submit
  await page.click('[data-testid="submit-button"]');

  // Verify agent appears in list
  await expect(page.locator('[data-testid="agent-list"]')).toContainText('ANALYST');

  // Verify real-time status updates
  await expect(page.locator('[data-testid="agent-status"]')).toHaveText('RUNNING');
});
```

### 7.3 Performance Testing

**Frontend Performance:**
- Lighthouse CI in pipeline (target scores: >90)
- Bundle size monitoring (<500KB gzipped)
- First Contentful Paint: <1.5s
- Time to Interactive: <3.5s
- Cumulative Layout Shift: <0.1

**Backend Performance:**
- API response time monitoring (p95 < 500ms)
- Database query performance profiling
- WebSocket message latency (<100ms)
- Memory usage monitoring (< 1GB for 1000 agents)

---

## 8. Performance Targets ✅ NEW

### 8.1 Dashboard Performance

| Metric | Target | Acceptable | Tool |
|--------|--------|------------|------|
| Initial Load Time | <2s | <3s | Lighthouse |
| Time to Interactive | <3.5s | <5s | Lighthouse |
| First Contentful Paint | <1.5s | <2s | Lighthouse |
| Cumulative Layout Shift | <0.1 | <0.25 | Lighthouse |
| Bundle Size (gzipped) | <500KB | <750KB | webpack-bundle-analyzer |

### 8.2 API Performance

| Metric | Target (p95) | Acceptable (p95) | Tool |
|--------|--------------|------------------|------|
| GET /agents | <200ms | <500ms | Prometheus |
| POST /agents | <500ms | <1s | Prometheus |
| GET /tasks | <200ms | <500ms | Prometheus |
| POST /tasks | <1s | <2s | Prometheus |
| WebSocket latency | <100ms | <250ms | Custom metrics |

### 8.3 Scalability Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent users | 50-100 | Phase 1-4 target |
| Active agents in DB | 100 | Real-time monitoring |
| Total agents in DB | 1,000 | Historical data |
| Historical retention | 90 days | Hot data, queryable |
| WebSocket connections | 100 | Concurrent connections |
| API requests/second | 500 | Sustained load |

---

## 9. Security Considerations (Enhanced)

### 9.1 Phase 1 Security (Day 1)

**Authentication:**
- Simple Bearer token authentication
- API keys stored in environment variables
- Token validation on all endpoints

**API Security:**
- CORS configuration (allowed origins whitelist)
- Rate limiting: 100 req/min per IP
- Request validation with Pydantic
- Input sanitization (prevent XSS, SQL injection)

**Data Security:**
- HTTPS only (even in dev with self-signed cert)
- Secure cookies (httpOnly, secure, sameSite)
- No sensitive data in logs

### 9.2 Phase 5 Security (Production)

**Authentication:**
- OAuth2 with JWT tokens
- Support for Google, GitHub, email/password
- Session management with refresh tokens
- Token expiration: 1 hour (access), 7 days (refresh)
- **Optional**: Two-factor authentication

**Authorization:**
- Role-based access control:
  - **Admin**: Full access (create, delete, configure)
  - **Developer**: Create agents/tasks, view all
  - **Viewer**: Read-only access
- API endpoint permissions per role
- Agent/task ownership model

**Audit Logging:**
- Log all user actions (create, delete, execute)
- IP address and user agent tracking
- Timestamp with timezone
- Immutable audit log
- Export audit logs for compliance

**Data Security:**
- API key rotation policy (90 days)
- Secrets management (environment variables, HashiCorp Vault for production)
- Database encryption at rest (optional)
- Sensitive data redaction in logs

**Security Headers:**
```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## 10. Deployment Strategy (Enhanced)

### 10.1 Development Deployment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build: ./backend
    volumes:
      - ./backend:/app
      - ./orchestrator.db:/app/orchestrator.db
    environment:
      - DATABASE_URL=sqlite:///./orchestrator.db
      - ENV=development
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --reload --host 0.0.0.0

  frontend:
    build: ./frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    command: npm run dev
```

### 10.2 Production Deployment

**Infrastructure:**
- VPS or cloud instance (AWS EC2 t3.medium, DigitalOcean droplet)
- Minimum: 2 CPU cores, 4GB RAM, 40GB SSD
- Nginx reverse proxy for SSL termination and load balancing
- Domain with DNS configured (A record to server IP)

**Services:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENV=production
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

  frontend:
    build:
      context: ./frontend
      target: production
    volumes:
      - frontend_build:/usr/share/nginx/html
```

**Monitoring:**
- Application logs (structured JSON to stdout)
- Log aggregation: Promtail + Loki (or CloudWatch)
- Error tracking: Sentry (optional, $26/month or self-hosted)
- Uptime monitoring: UptimeRobot (free tier) or custom
- Performance monitoring: Lighthouse CI in GitHub Actions

**Backup Strategy:**
```bash
# Automated backup script
#!/bin/bash
# Daily backup at 2 AM via cron

DATE=$(date +%Y-%m-%d)
DB_PATH="/app/orchestrator.db"
BACKUP_DIR="/backups"
RETENTION_DAYS=30

# Create backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/orchestrator-$DATE.db"

# Compress
gzip $BACKUP_DIR/orchestrator-$DATE.db

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/orchestrator-$DATE.db.gz s3://my-backups/orchestrator/

# Clean old backups
find $BACKUP_DIR -name "*.db.gz" -mtime +$RETENTION_DAYS -delete

# Test restore (weekly)
if [ $(date +%u) -eq 7 ]; then
  gunzip -c $BACKUP_DIR/orchestrator-$DATE.db.gz > /tmp/test-restore.db
  sqlite3 /tmp/test-restore.db "PRAGMA integrity_check;"
fi
```

**CI/CD Pipeline (GitHub Actions):**
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov
      - name: Run frontend tests
        run: |
          cd frontend
          npm install
          npm run test
          npm run test:e2e

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker images
        run: docker build -t orchestrator-dashboard:${{ github.sha }} .
      - name: Push to registry
        run: docker push orchestrator-dashboard:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          ssh user@server "cd /app && \
            docker pull orchestrator-dashboard:${{ github.sha }} && \
            docker-compose up -d"
```

---

## 11. Cost Estimates (Revised)

### 11.1 Development Costs

| Phase | Hours | Days (8h/day) |
|-------|-------|---------------|
| Phase 1 | 120-160 | 15-20 |
| Phase 2 | 120-160 | 15-20 |
| Phase 3 | 120-160 | 15-20 |
| Phase 4 | 120-160 | 15-20 |
| Phase 5 | 120-160 | 15-20 |
| **Total** | **600-800 hours** | **75-100 days** |

**With 1 full-time developer:** 3-4 months
**With 2 developers:** 2-2.5 months

### 11.2 Infrastructure Costs (Annual)

| Service | Cost/Month | Cost/Year | Notes |
|---------|------------|-----------|-------|
| VPS Hosting | $20-40 | $240-480 | DigitalOcean/AWS EC2 |
| Domain | $1.25 | $15 | .com domain |
| SSL Certificate | $0 | $0 | Let's Encrypt |
| Backups (S3) | $2-5 | $24-60 | 50GB storage |
| Sentry (optional) | $26 | $312 | Error tracking |
| Email Service | $10 | $120 | For alerts |
| **Total (Basic)** | **$23-46** | **$279-555** |
| **Total (Full)** | **$59-82** | **$711-987** |

### 11.3 Expected ROI

**Cost Savings:**
- Reduced debugging time: **70% faster** issue resolution
  - Before: 30 min/issue × 10 issues/week = 5 hours/week
  - After: 9 min/issue × 10 issues/week = 1.5 hours/week
  - **Savings: 3.5 hours/week = 182 hours/year**

- Proactive cost management: **30-50% cost reduction** through visibility
  - Before: Unclear spending, unexpected bills
  - After: Budget alerts, workflow optimization
  - **Savings: $500-1000/year** (assuming $2000/year base spend)

- Improved developer productivity: **2-3x faster** agent management vs CLI
  - Before: 5 min to check agent status, find logs
  - After: 30 sec with visual dashboard
  - **Savings: ~1 hour/week = 52 hours/year**

**Total Annual Savings:** ~234 hours + $500-1000 = **$20,000-30,000** (assuming $100/hour developer cost)

**Payback Period:** 1-2 months

---

## 12. Open Questions & Decisions

### 12.1 Technical Decisions ✅ RESOLVED

1. **Database Migration Path**
   - ✅ **Decision**: Start with SQLite + SQLAlchemy abstraction
   - Migrate to PostgreSQL when: >1000 req/s or multi-instance needed
   - Alembic for schema migrations from Day 1

2. **Real-Time Update Frequency** ✅ ENHANCED
   - ✅ **Decision**: Configurable per data type
   ```typescript
   const UPDATE_INTERVALS = {
     agent_status: 500ms,
     cost_updates: 250ms,
     task_progress: 100ms,
     agent_list: 1000ms,
   }
   ```

3. **Historical Data Retention** ✅ ENHANCED
   - ✅ **Decision**: Tiered retention
     - Hot (queryable): 90 days
     - Warm (archived): 365 days
     - Cold (export only): Forever (compressed JSON)

4. **Multi-User Support Priority**
   - ✅ **Decision**: Phase 5, assume single user for Phases 1-4

### 12.2 UX Decisions ✅ RESOLVED

1. **Default View**
   - ✅ **Decision**: Fleet overview with active agents list
   - Customizable in Phase 5 (user preferences)

2. **Agent Cleanup Behavior**
   - ✅ **Decision**: Manual cleanup by default
   - Auto-cleanup toggle in Phase 5 settings
   - Batch operations in Phase 4

3. **Cost Display Format**
   - ✅ **Decision**: Adaptive formatting
     - <$0.01: Show in cents with 4 decimals ($0.0012)
     - $0.01-$1: Show in cents with 2 decimals ($0.23)
     - >$1: Show in dollars ($12.34)

4. **Alert Preferences**
   - ✅ **Decision**: Enabled by default
     - Budget exceeded: ON
     - Context window warning: ON
     - High cost per agent: OFF (opt-in)
     - Anomaly detection: ON (Phase 3)

---

## 13. Next Steps

### Week 1: Setup & Foundation

1. **✅ Proposal Approval**
   - ✅ Review and approve tech stack
   - ✅ Prioritize Phase 1-5 features
   - ✅ Confirm timeline and resources

2. **Project Initialization**
   - Create `backend/` and `frontend/` directories
   - Initialize FastAPI project with SQLAlchemy + Alembic
   - Initialize React + TypeScript + Vite project
   - Set up Docker Compose for local development
   - Configure ESLint, Prettier, pre-commit hooks

3. **CI/CD Setup**
   - GitHub Actions for testing
   - Automated linting and type checking
   - Deployment pipeline (to staging)

4. **Design System**
   - Create Figma mockups for Phase 1 screens
   - Define design tokens (colors, typography, spacing)
   - Set up Storybook for component development
   - Build 5-10 core components (Button, Input, Card, Table, Modal)

### Week 2-3: Phase 1 Implementation

**Backend:**
- [ ] SQLAlchemy models and Alembic migrations
- [ ] FastAPI endpoints for fleet status
- [ ] WebSocket server with event publishing
- [ ] Bearer token authentication
- [ ] Integration with existing Orchestrator
- [ ] Unit and integration tests (>80% coverage)

**Frontend:**
- [ ] Dashboard layout with sidebar navigation
- [ ] Agent list component with filtering/sorting
- [ ] Real-time WebSocket connection
- [ ] React Query setup for data fetching
- [ ] Dark/light mode toggle
- [ ] Error boundaries and toast notifications

**Integration:**
- [ ] End-to-end testing with Playwright
- [ ] Load testing with Locust (100 concurrent users)
- [ ] Deploy to staging environment

### Week 4+: Continue with Phases 2-5

Follow the phased approach with weekly demos and iterative feedback.

---

## 14. Appendix

### A. Technology Comparison

**Why React over SvelteKit:**
| Criteria | React | SvelteKit | Winner |
|----------|-------|-----------|--------|
| Ecosystem maturity | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | React |
| Component libraries | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | React |
| TypeScript support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | React |
| Developer availability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | React |
| Bundle size | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | SvelteKit |
| Learning curve | ⭐⭐⭐ | ⭐⭐⭐⭐ | SvelteKit |

**Decision**: React for maturity and ecosystem

**Why FastAPI over Flask/Django:**
| Criteria | FastAPI | Flask | Django | Winner |
|----------|---------|-------|--------|--------|
| Async support | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | FastAPI |
| WebSocket support | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | FastAPI |
| Type validation | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | FastAPI |
| Auto docs | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | FastAPI |
| Maturity | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Flask/Django |

**Decision**: FastAPI for modern async Python and WebSocket support

### B. API Versioning Strategy

**URL Versioning:** `/api/v1/`, `/api/v2/`

**Breaking Changes:**
- Increment major version (v1 → v2)
- Maintain v1 for 6 months after v2 release
- Deprecation warnings in v1 responses

**Non-Breaking Changes:**
- Add new fields (optional)
- Add new endpoints
- Maintain backwards compatibility

### C. Database Schema (Preview)

```python
# models/agent.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum
from sqlalchemy.orm import relationship

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    role = Column(Enum(AgentRole), nullable=False)
    status = Column(Enum(AgentStatus), nullable=False)
    model = Column(String(100), nullable=False)
    system_prompt = Column(Text)
    cost = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="agent")
    files = relationship("File", back_populates="agent")
```

### D. Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + K` | Open command palette |
| `Cmd/Ctrl + N` | Create new agent |
| `Cmd/Ctrl + T` | Create new task |
| `Cmd/Ctrl + ,` | Open settings |
| `Cmd/Ctrl + D` | Toggle dark mode |
| `/` | Focus search |
| `Escape` | Close modal/dialog |
| `?` | Show keyboard shortcuts |

### E. Glossary

- **Fleet**: Collection of all agents managed by the orchestrator
- **Agent**: Individual Claude AI instance with specific role
- **Task**: High-level user request decomposed into subtasks
- **Workflow**: Sequence or parallel execution of agent roles
- **ANALYST**: Agent role for research and analysis (optional in v0.1.3)
- **Complexity**: Estimation of task difficulty (simple vs complex)
- **System Prompt**: Instructions given to agent defining its behavior
- **Hot/Warm/Cold Data**: Tiered storage based on access frequency

---

## Conclusion

This revised proposal (v2.0) incorporates comprehensive feedback and addresses all identified gaps from the initial proposal. The dashboard will provide a production-ready, intelligent interface for the Claude Multi-Agent Orchestrator with deep integration of recent v0.1.3 improvements.

**Key Improvements in v2.0:**
✅ Integration with v0.1.3 ANALYST optimization
✅ Prompt engineering system integration (prompts.py)
✅ Agent file logging viewer (JSONL support)
✅ SQLAlchemy + Alembic for database abstraction
✅ Security from Phase 1 (not deferred)
✅ Comprehensive error handling strategy
✅ Specific performance targets
✅ Enhanced testing strategy with coverage targets
✅ Realistic timeline with risk buffers
✅ Detailed cost estimates and ROI analysis

**Recommended Immediate Actions:**
1. ✅ Approve this revised proposal
2. Create design mockups for Phase 1 screens
3. Initialize project structure (backend + frontend)
4. Set up CI/CD pipeline
5. Begin Phase 1 implementation Week 2

**Questions or Clarifications?**
This proposal is ready for implementation. Let's build an exceptional dashboard for the orchestrator!

---

**Prepared by:** Claude AI Assistant
**Original Date:** 2025-11-06
**Revised Date:** 2025-11-05
**Version:** 2.0 - Comprehensive Revision
**Status:** Ready for Approval
