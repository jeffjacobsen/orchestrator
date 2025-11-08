# Integration Guide

This guide explains how to integrate the Claude Multi-Agent Orchestrator into your own applications, monitoring systems, and workflows.

## Architecture Overview

### Current Architecture (Verified Clean Separation)

The orchestrator is designed with **clean separation of concerns**. As of v0.1.5:

**Verification Results**:
```bash
# Orchestrator core has ZERO dependencies on dashboard
$ grep -r "from.*dashboard\|import.*dashboard" src/orchestrator/
# No matches found ✅

# Dashboard depends on orchestrator (correct direction)
$ grep -r "from orchestrator\|import.*orchestrator" dashboard/backend/
# Found only in orchestrator_executor.py (wrapper layer) ✅
```

This means:

```
┌─────────────────────────────────────────────────────────┐
│                   Your Application                       │
│  (GitHub Issues, Telegram, Slack, Custom Backend)       │
└─────────────────────────┬───────────────────────────────┘
                          │
                          │ Uses orchestrator as library
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Orchestrator Core (src/orchestrator/)       │
│  • Task Planning & Execution                             │
│  • Agent Management (CRUD)                               │
│  • Workflow Orchestration                                │
│  • Observability & Metrics                               │
│  • Zero dependencies on any specific UI/API              │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Optional: Use dashboard
                          ↓
┌─────────────────────────────────────────────────────────┐
│       Sample Dashboard (dashboard/)                      │
│  • FastAPI backend                                       │
│  • React frontend                                        │
│  • WebSocket updates                                     │
│  • One possible way to monitor orchestrator              │
└─────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Orchestrator Core is Independent**: No dependencies on dashboard, FastAPI, React, or any specific monitoring system
2. **Dashboard is Optional**: The sample dashboard is just one way to monitor and control the orchestrator
3. **Library-First Design**: Import orchestrator as a Python library in any application
4. **Callbacks for Integration**: Use callbacks to hook into orchestrator events

---

## Integration Patterns

### Pattern 1: Direct Python Integration

Use the orchestrator as a Python library in your application:

```python
import asyncio
from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole

async def my_application():
    """Your custom application using orchestrator"""

    # Create orchestrator instance
    orchestrator = Orchestrator(
        enable_monitoring=True,
        working_directory="/path/to/your/project"
    )

    try:
        await orchestrator.start()

        # Execute tasks programmatically
        result = await orchestrator.execute(
            prompt="Analyze recent GitHub issues and suggest priorities",
            task_type="investigation"
        )

        # Access results
        print(f"Task completed: {result.success}")
        print(f"Cost: ${result.metrics.total_cost:.4f}")

        # Send results to your system (Slack, database, etc.)
        await send_to_slack(result.output)

    finally:
        await orchestrator.stop()

asyncio.run(my_application())
```

### Pattern 2: Event-Driven Integration

Hook into orchestrator events using callbacks:

```python
from orchestrator import Orchestrator
from orchestrator.observability.monitor import AgentMonitor

async def on_agent_created(agent_id: str, role: str):
    """Called when a new agent is created"""
    await telegram_bot.send_message(f"🤖 Agent created: {role}")

async def on_task_completed(task_id: str, result: dict):
    """Called when a task completes"""
    await github_api.post_comment(
        issue_id=task_id,
        comment=f"Task completed! Cost: ${result['cost']}"
    )

async def on_progress_update(agent_id: str, status: str, activity: str):
    """Called on agent progress updates"""
    await websocket.broadcast({
        "type": "progress",
        "agent_id": agent_id,
        "status": status,
        "activity": activity
    })

# Create orchestrator with callbacks
orchestrator = Orchestrator(
    enable_monitoring=True,
    progress_callback=on_progress_update
)

# Set up custom monitoring
monitor = AgentMonitor()
monitor.on_agent_created = on_agent_created
monitor.on_task_completed = on_task_completed
```

### Pattern 3: Message Queue Integration

Integrate with message queues (RabbitMQ, Redis, Kafka):

```python
import asyncio
from orchestrator import Orchestrator
import aio_pika  # RabbitMQ client

class QueueOrchestrator:
    def __init__(self, queue_url: str):
        self.orchestrator = Orchestrator(enable_monitoring=True)
        self.queue_url = queue_url

    async def start(self):
        """Start listening to message queue"""
        await self.orchestrator.start()

        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(self.queue_url)
        channel = await connection.channel()
        queue = await channel.declare_queue('orchestrator_tasks', durable=True)

        # Process messages
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    task_data = json.loads(message.body)

                    # Execute task from queue
                    result = await self.orchestrator.execute(
                        prompt=task_data['prompt'],
                        task_type=task_data.get('task_type', 'auto')
                    )

                    # Publish result to results queue
                    await channel.default_exchange.publish(
                        aio_pika.Message(body=json.dumps(result).encode()),
                        routing_key='orchestrator_results'
                    )

# Usage
queue_orchestrator = QueueOrchestrator("amqp://localhost")
asyncio.run(queue_orchestrator.start())
```

### Pattern 4: HTTP API Wrapper

Create your own API around the orchestrator:

```python
from fastapi import FastAPI, BackgroundTasks
from orchestrator import Orchestrator

app = FastAPI()
orchestrator = Orchestrator(enable_monitoring=True)

@app.on_event("startup")
async def startup():
    await orchestrator.start()

@app.on_event("shutdown")
async def shutdown():
    await orchestrator.stop()

@app.post("/tasks")
async def create_task(
    prompt: str,
    task_type: str = "auto",
    background_tasks: BackgroundTasks = None
):
    """Your custom API endpoint"""

    # Execute in background
    async def execute_task():
        result = await orchestrator.execute(
            prompt=prompt,
            task_type=task_type
        )
        # Store results in your database
        await your_database.save_task(result)

    background_tasks.add_task(execute_task)

    return {"status": "started", "message": "Task execution started"}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Retrieve task from your database"""
    return await your_database.get_task(task_id)
```

---

## Integration Examples

### Example 1: GitHub Issues Bot

Automatically process GitHub issues with the orchestrator:

```python
import asyncio
from github import Github
from orchestrator import Orchestrator

class GitHubIssuesBot:
    def __init__(self, github_token: str, repo_name: str):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)
        self.orchestrator = Orchestrator(
            enable_monitoring=True,
            working_directory=f"/path/to/{repo_name}"
        )

    async def process_issues_with_label(self, label: str):
        """Process all issues with specific label"""
        await self.orchestrator.start()

        try:
            issues = self.repo.get_issues(
                state='open',
                labels=[label]
            )

            for issue in issues:
                # Create orchestrator task from issue
                result = await self.orchestrator.execute(
                    prompt=f"""
                    GitHub Issue #{issue.number}: {issue.title}

                    {issue.body}

                    Please analyze this issue and provide:
                    1. Root cause analysis
                    2. Suggested fix
                    3. Implementation plan
                    """,
                    task_type="bug_fix" if "bug" in label else "investigation"
                )

                # Post results as comment
                issue.create_comment(f"""
                ## Orchestrator Analysis

                {result.output}

                **Cost**: ${result.metrics.total_cost:.4f}
                **Agents Used**: {len(result.agents)}
                **Duration**: {result.metrics.execution_time_seconds:.1f}s
                """)

                # Remove label after processing
                issue.remove_from_labels(label)

        finally:
            await self.orchestrator.stop()

# Usage
bot = GitHubIssuesBot(
    github_token="your_token",
    repo_name="username/repo"
)
asyncio.run(bot.process_issues_with_label("needs-analysis"))
```

### Example 2: Telegram Bot Integration

Control orchestrator via Telegram:

```python
from telegram.ext import Application, CommandHandler, MessageHandler
from orchestrator import Orchestrator

class TelegramOrchestratorBot:
    def __init__(self, telegram_token: str):
        self.app = Application.builder().token(telegram_token).build()
        self.orchestrator = Orchestrator(enable_monitoring=True)

        # Register handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("task", self.task_command))
        self.app.add_handler(CommandHandler("status", self.status_command))

    async def start_command(self, update, context):
        """Start command handler"""
        await self.orchestrator.start()
        await update.message.reply_text(
            "🤖 Orchestrator Bot started!\n"
            "Use /task <description> to execute a task"
        )

    async def task_command(self, update, context):
        """Execute task from Telegram message"""
        task_description = ' '.join(context.args)

        if not task_description:
            await update.message.reply_text("Please provide a task description")
            return

        # Show typing indicator
        await update.message.reply_text("⏳ Executing task...")

        # Execute task
        result = await self.orchestrator.execute(
            prompt=task_description,
            task_type="auto"
        )

        # Send results
        await update.message.reply_text(f"""
        ✅ Task Completed!

        **Result**: {result.output[:500]}...

        **Metrics**:
        • Cost: ${result.metrics.total_cost:.4f}
        • Duration: {result.metrics.execution_time_seconds:.1f}s
        • Agents: {len(result.agents)}
        """)

    async def status_command(self, update, context):
        """Get orchestrator status"""
        status = self.orchestrator.get_status()

        await update.message.reply_text(f"""
        📊 Orchestrator Status

        **Active Agents**: {status['fleet']['active_count']}
        **Total Cost**: ${status['fleet']['total_cost']:.4f}
        **Tasks Completed**: {status['monitoring']['tasks_completed']}
        """)

    def run(self):
        """Start bot"""
        self.app.run_polling()

# Usage
bot = TelegramOrchestratorBot(telegram_token="your_token")
bot.run()
```

### Example 3: Slack Integration

Process Slack slash commands:

```python
from slack_bolt.async_app import AsyncApp
from orchestrator import Orchestrator

class SlackOrchestratorApp:
    def __init__(self, slack_token: str, signing_secret: str):
        self.app = AsyncApp(
            token=slack_token,
            signing_secret=signing_secret
        )
        self.orchestrator = Orchestrator(enable_monitoring=True)

        # Register slash command
        @self.app.command("/orchestrator")
        async def handle_orchestrator_command(ack, say, command):
            await ack()

            task_description = command['text']
            user_id = command['user_id']

            # Send immediate response
            await say(f"<@{user_id}> Starting task: {task_description}")

            # Execute task
            result = await self.orchestrator.execute(
                prompt=task_description,
                task_type="auto"
            )

            # Send results with rich formatting
            await say(
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Task Completed* :white_check_mark:\n\n{result.output}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"💰 Cost: ${result.metrics.total_cost:.4f} | "
                                        f"⏱️ Duration: {result.metrics.execution_time_seconds:.1f}s | "
                                        f"🤖 Agents: {len(result.agents)}"
                            }
                        ]
                    }
                ]
            )

    async def start(self):
        """Start Slack app"""
        await self.orchestrator.start()
        await self.app.start(port=3000)

# Usage
app = SlackOrchestratorApp(
    slack_token="xoxb-your-token",
    signing_secret="your-signing-secret"
)
asyncio.run(app.start())
```

---

## Custom Monitoring Solutions

### Option 1: Custom Database Integration

Use your own database instead of the sample dashboard:

```python
from orchestrator import Orchestrator
from your_database import YourDatabase

class CustomMonitoredOrchestrator:
    def __init__(self, db_connection_string: str):
        self.db = YourDatabase(db_connection_string)
        self.orchestrator = Orchestrator(
            enable_monitoring=True,
            progress_callback=self.on_progress
        )

    async def on_progress(self, status: str, activity: str):
        """Custom progress tracking"""
        await self.db.insert({
            "timestamp": datetime.now(),
            "status": status,
            "activity": activity,
            "orchestrator_id": self.orchestrator.orchestrator_id
        })

    async def execute_with_tracking(self, prompt: str, **kwargs):
        """Execute task with full database tracking"""
        # Create task record
        task_id = await self.db.create_task(prompt=prompt, **kwargs)

        try:
            # Execute
            result = await self.orchestrator.execute(prompt=prompt, **kwargs)

            # Update task record
            await self.db.update_task(
                task_id=task_id,
                status="completed",
                result=result.output,
                cost=result.metrics.total_cost,
                duration=result.metrics.execution_time_seconds
            )

            return result

        except Exception as e:
            await self.db.update_task(
                task_id=task_id,
                status="failed",
                error=str(e)
            )
            raise
```

### Option 2: Real-time Metrics Streaming

Stream metrics to your monitoring system:

```python
from orchestrator import Orchestrator
import prometheus_client
from prometheus_client import Counter, Histogram

class PrometheusOrchestrator:
    def __init__(self):
        # Define metrics
        self.tasks_total = Counter(
            'orchestrator_tasks_total',
            'Total number of tasks executed'
        )
        self.task_duration = Histogram(
            'orchestrator_task_duration_seconds',
            'Task execution duration'
        )
        self.task_cost = Histogram(
            'orchestrator_task_cost_usd',
            'Task execution cost in USD'
        )

        self.orchestrator = Orchestrator(enable_monitoring=True)

    async def execute_with_metrics(self, prompt: str, **kwargs):
        """Execute task and export Prometheus metrics"""
        self.tasks_total.inc()

        with self.task_duration.time():
            result = await self.orchestrator.execute(prompt=prompt, **kwargs)

        self.task_cost.observe(result.metrics.total_cost)

        return result

# Start Prometheus metrics server
prometheus_client.start_http_server(8000)
```

---

## Best Practices for Integration

### 1. Keep Orchestrator Core Clean
- **DON'T** modify `src/orchestrator/` to add dashboard-specific code
- **DO** create wrapper classes in your application layer
- **DO** use callbacks and events for integration

### 2. Separate Concerns
```python
# ✅ Good: Wrapper pattern
class MyOrchestrator:
    def __init__(self):
        self.orchestrator = Orchestrator()  # Core remains independent
        self.my_monitoring = MyMonitoring()

    async def execute_task(self, prompt: str):
        result = await self.orchestrator.execute(prompt)
        await self.my_monitoring.track(result)
        return result

# ❌ Bad: Modifying core
from orchestrator.core.orchestrator import Orchestrator
# Don't modify the Orchestrator class to add your specific logic
```

### 3. Use Environment Variables
```python
# Make your integration configurable
import os

MONITORING_BACKEND = os.getenv("MONITORING_BACKEND", "none")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", None)

if MONITORING_BACKEND == "prometheus":
    monitor = PrometheusMonitor()
elif MONITORING_BACKEND == "datadog":
    monitor = DatadogMonitor()
else:
    monitor = NoOpMonitor()
```

### 4. Handle Errors Gracefully
```python
async def safe_execute(orchestrator, prompt: str):
    """Execute with proper error handling"""
    try:
        result = await orchestrator.execute(prompt)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return {"success": False, "error": str(e)}
```

---

## Testing Your Integration

### Unit Tests
```python
import pytest
from orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_my_integration():
    """Test custom integration"""
    orchestrator = Orchestrator(enable_monitoring=False)
    await orchestrator.start()

    try:
        result = await orchestrator.execute(
            prompt="Simple test task",
            task_type="auto"
        )
        assert result.success == True
    finally:
        await orchestrator.stop()
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_github_integration():
    """Test GitHub bot integration"""
    bot = GitHubIssuesBot(token="test_token", repo="test/repo")

    # Mock GitHub API
    with patch.object(bot.repo, 'get_issues') as mock_issues:
        mock_issues.return_value = [mock_issue]
        await bot.process_issues_with_label("test-label")
```

---

## Migration from Sample Dashboard

If you want to replace the sample dashboard with your own system:

1. **Keep using orchestrator core**: No changes needed to `src/orchestrator/`
2. **Remove dashboard dependency**: Delete or ignore `dashboard/` directory
3. **Implement your own API**: Use patterns from this guide
4. **Migrate data**: Export data from sample dashboard database if needed

```bash
# Export existing task data
sqlite3 dashboard/backend/orchestrator.db ".dump tasks" > tasks_export.sql

# Import to your database
psql your_database < tasks_export.sql  # PostgreSQL example
```

---

## Getting Help

- **Core orchestrator issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Integration questions**: Tag with `integration` label
- **Share your integration**: PRs welcome for new examples!

---

## Examples Repository

See more integration examples at:
- `examples/integrations/github_bot.py`
- `examples/integrations/telegram_bot.py`
- `examples/integrations/slack_app.py`
- `examples/integrations/custom_api.py`

---

**Remember**: The orchestrator core (`src/orchestrator/`) is designed to be library-first and integration-agnostic. The sample dashboard is just one possible way to use it!
