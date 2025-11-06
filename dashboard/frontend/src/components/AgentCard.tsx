import { Agent } from '../types'
import { formatDateTime, formatDuration, getStatusColor, getRoleColor } from '../lib/utils'
import { cn } from '../lib/utils'

interface AgentCardProps {
  agent: Agent
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow bg-card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={cn('px-2 py-1 rounded text-xs font-medium', getRoleColor(agent.role))}>
            {agent.role}
          </span>
          <span className={cn('px-2 py-1 rounded text-xs font-medium', getStatusColor(agent.status))}>
            {agent.status}
          </span>
        </div>
        <span className="text-xs text-muted-foreground">
          {agent.id.slice(0, 8)}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Created:</span>
          <span>{formatDateTime(agent.created_at)}</span>
        </div>

        {agent.status === 'active' && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Running:</span>
            <span>{formatDuration(agent.created_at)}</span>
          </div>
        )}

        {agent.completed_at && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Duration:</span>
            <span>{formatDuration(agent.created_at, agent.completed_at)}</span>
          </div>
        )}

        {agent.task_id && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Task:</span>
            <span className="font-mono text-xs">{agent.task_id.slice(0, 8)}</span>
          </div>
        )}

        <div className="flex justify-between border-t pt-2 mt-2">
          <span className="text-muted-foreground">Tokens:</span>
          <span>
            {agent.total_input_tokens + agent.total_output_tokens}
            {agent.cache_read_tokens > 0 && (
              <span className="text-green-600 ml-1">
                (cached: {agent.cache_read_tokens})
              </span>
            )}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-muted-foreground">Cost:</span>
          <span className="font-medium">{agent.total_cost}</span>
        </div>
      </div>
    </div>
  )
}
