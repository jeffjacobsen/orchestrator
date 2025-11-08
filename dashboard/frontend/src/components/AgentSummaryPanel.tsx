/**
 * Agent Summary Panel Component
 *
 * Displays aggregate statistics about all agents:
 * - Total agents
 * - Status breakdown (active/idle/completed/failed)
 * - Total tokens (prompt, completion, cache)
 * - Total cost
 */
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../services/api';
import { Activity, CheckCircle2, XCircle, Clock, DollarSign, Zap } from 'lucide-react';
import type { Agent } from '../types/api';

export function AgentSummaryPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentApi.list(),
  });

  if (isLoading || !data) {
    return null; // Don't show until data loads
  }

  const agents = data.agents;

  // Calculate aggregate statistics
  const stats = agents.reduce(
    (acc, agent: Agent) => {
      // Count by status
      acc.byStatus[agent.status] = (acc.byStatus[agent.status] || 0) + 1;

      // Sum tokens
      acc.totalPromptTokens += agent.tokens?.prompt_tokens || 0;
      acc.totalCompletionTokens += agent.tokens?.completion_tokens || 0;
      acc.totalCacheReadTokens += agent.tokens?.cache_read_tokens || 0;
      acc.totalCacheCreationTokens += agent.tokens?.cache_creation_tokens || 0;

      // Sum cost
      acc.totalCost += agent.cost || 0;

      return acc;
    },
    {
      byStatus: {} as Record<string, number>,
      totalPromptTokens: 0,
      totalCompletionTokens: 0,
      totalCacheReadTokens: 0,
      totalCacheCreationTokens: 0,
      totalCost: 0,
    }
  );

  const totalTokens =
    stats.totalPromptTokens +
    stats.totalCompletionTokens +
    stats.totalCacheReadTokens +
    stats.totalCacheCreationTokens;

  const statusCards = [
    {
      label: 'Active',
      count: stats.byStatus.active || 0,
      icon: Activity,
      color: 'text-blue-500',
      bg: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Idle',
      count: stats.byStatus.idle || 0,
      icon: Clock,
      color: 'text-yellow-500',
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    },
    {
      label: 'Completed',
      count: stats.byStatus.completed || 0,
      icon: CheckCircle2,
      color: 'text-green-500',
      bg: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'Failed',
      count: stats.byStatus.failed || 0,
      icon: XCircle,
      color: 'text-red-500',
      bg: 'bg-red-100 dark:bg-red-900/30',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Agent Overview</h2>
        <div className="text-sm text-muted-foreground">
          {agents.length} {agents.length === 1 ? 'agent' : 'agents'} total
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statusCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className={`${card.bg} rounded-lg p-4 border border-border`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">{card.label}</span>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
              <div className={`text-2xl font-bold ${card.color}`}>
                {card.count}
              </div>
            </div>
          );
        })}
      </div>

      {/* Aggregate Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Total Tokens */}
        <div className="border rounded-lg p-4 bg-card">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Total Tokens</h3>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Total:</span>
              <span className="font-medium">{totalTokens.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Prompt:</span>
              <span>{stats.totalPromptTokens.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Completion:</span>
              <span>{stats.totalCompletionTokens.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Cache Read:</span>
              <span className="text-blue-600 dark:text-blue-400">
                {stats.totalCacheReadTokens.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Cache Creation:</span>
              <span className="text-orange-600 dark:text-orange-400">
                {stats.totalCacheCreationTokens.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Total Cost */}
        <div className="border rounded-lg p-4 bg-card">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="h-4 w-4 text-green-600 dark:text-green-400" />
            <h3 className="font-semibold">Total Cost</h3>
          </div>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">
              ${stats.totalCost.toFixed(4)}
            </div>
            {agents.length > 0 && (
              <div className="text-xs text-muted-foreground">
                Average: ${(stats.totalCost / agents.length).toFixed(4)} per agent
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
