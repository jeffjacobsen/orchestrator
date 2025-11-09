---
description: Deploy dashboard with safety checks and health verification
---

Deploy the dashboard to production with comprehensive safety checks:

1. **Pre-deployment checks**:
   - Verify git status is clean: `git status`
   - If uncommitted changes exist, ask user if they want to commit first
   - Verify current branch: `git branch --show-current`
   - If not on main, ask user if they want to continue

2. **Run tests**:
   - Execute: `cd dashboard/backend && pytest tests/ -v`
   - Execute: `cd ../frontend && npm run build`
   - Return to root: `cd ../..`
   - If tests fail, STOP and report errors

3. **Database migration check**:
   - Check for pending migrations: `cd dashboard/backend && alembic current`
   - If migrations pending, ask user: "Apply migrations? [y/n]"
   - If yes: `alembic upgrade head`

4. **Docker deployment**:
   - Stop existing containers: `cd dashboard && docker-compose down`
   - Build and start: `docker-compose up -d --build`
   - Wait 10 seconds for startup

5. **Health checks**:
   - Test backend: `curl -f http://localhost:8000/health`
   - Test frontend: `curl -f http://localhost:5173`
   - Check WebSocket: `curl -f http://localhost:8000/api/v1/ws/tasks`
   - Report status of each service

6. **Post-deployment verification**:
   - Show logs: `docker-compose logs --tail=50`
   - Ask user: "Deployment successful. Monitor logs? [y/n]"

7. **Summary**:
   - Report deployment time
   - List all services started
   - Provide access URLs
