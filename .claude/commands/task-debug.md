---
description: Debug failed orchestrator task with log analysis
---

Debug a failed orchestrator task:

1. **Get task ID**:
   - Ask user: "Task ID to debug (or 'latest' for most recent):"
   - If 'latest':
     - Execute: `ls -t agent_logs/ | head -1` for CLI tasks
     - Execute: `sqlite3 dashboard/backend/orchestrator.db "SELECT id FROM tasks ORDER BY created_at DESC LIMIT 1"` for dashboard tasks

2. **Locate logs**:
   - Check CLI logs: `agent_logs/{task_id}/`
   - Check dashboard logs: `dashboard/backend/agent_logs/{task_id}/`
   - Report which location has logs

3. **Analyze task structure**:
   - Read `plan.json` to understand intended workflow
   - List all agent subdirectories
   - Check which agents completed vs. failed

4. **For each agent**:
   - Read `prompt.txt` to see task given to agent
   - Read `text.txt` for agent's thinking and output
   - Read `tools.jsonl` for tool calls made
   - Identify where failure occurred

5. **Common failure patterns**:
   - Check for context window overflow: `grep "context.*limit" */text.txt`
   - Check for tool errors: `grep -i "error\|exception\|failed" */tools.jsonl`
   - Check for timeout: `grep -i "timeout\|timed out" */text.txt`
   - Check for file access issues: `grep -i "permission\|not found" */text.txt`

6. **Cost and performance analysis**:
   - Calculate total tokens used from all agents
   - Calculate total execution time
   - Identify most expensive agent
   - Identify slowest agent

7. **Root cause identification**:
   - Pinpoint exact failure point (agent, line, error)
   - Explain why failure occurred
   - Check if issue is prompt-related, tool-related, or data-related

8. **Recommendations**:
   - Suggest prompt improvements
   - Suggest workflow changes
   - Suggest tool usage improvements
   - Provide example fixed prompt if applicable

9. **Summary report**:
   ```
   Task: {task_id}
   Status: FAILED
   Failed at: BUILDER agent (step 3/5)
   Root cause: File not found error
   Cost: $0.42 (3 agents completed)
   Duration: 145s

   Fix: Update PLANNER prompt to verify file paths exist before BUILDER
   ```
