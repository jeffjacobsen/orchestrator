import { useQuery } from '@tanstack/react-query'
import { agentApi } from '../services/api'
import { AgentCard } from './AgentCard'
import { Loader2 } from 'lucide-react'

export function AgentList() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentApi.list(),
    // No polling needed - WebSocket provides real-time updates
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="border border-destructive rounded-lg p-4 bg-destructive/10">
        <h3 className="font-semibold text-destructive mb-2">Error loading agents</h3>
        <p className="text-sm text-muted-foreground mb-4">{(error as Error).message}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!data || data.agents.length === 0) {
    return (
      <div className="border rounded-lg p-8 text-center">
        <p className="text-muted-foreground">No agents found</p>
        <p className="text-sm text-muted-foreground mt-2">
          Agents will appear here once created
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          Agents
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({data.total})
          </span>
        </h2>
        <button
          onClick={() => refetch()}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}
