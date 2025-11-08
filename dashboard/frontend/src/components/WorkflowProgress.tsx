/**
 * Workflow Progress Component
 *
 * Displays workflow steps with visual progress indicators showing:
 * - Completed steps (checkmark)
 * - Current step (spinning loader)
 * - Pending steps (empty circle)
 * - Agent metrics (tokens, cost) inline with each step
 * - Clickable agent names to view logs
 */
import { useState } from 'react';
import { Check, Loader2, Circle, FileText } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { agentApi, taskApi } from '../services/api';
import { AgentLogDialog } from './AgentLogDialog';
import type { Task, Agent } from '../types';

interface WorkflowProgressProps {
  task: Task;
}

export function WorkflowProgress({ task }: WorkflowProgressProps) {
  const { workflow, current_step, status } = task;
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showPlannerLogs, setShowPlannerLogs] = useState(false);

  // Fetch agents for this task
  const { data: agentData } = useQuery({
    queryKey: ['agents', { task_id: task.id }],
    queryFn: () => agentApi.list({ task_id: task.id, page_size: 100 }),
    refetchInterval: 2000, // Refresh every 2 seconds for real-time updates
  });

  // Fetch planner logs when dialog is open
  const { data: plannerLogs } = useQuery({
    queryKey: ['planner-logs', task.id],
    queryFn: () => taskApi.getPlannerLogs(task.id),
    enabled: showPlannerLogs,
  });

  const handleAgentClick = (agent: Agent | undefined) => {
    if (agent && (agent.status === 'completed' || agent.status === 'failed')) {
      setSelectedAgent(agent);
      setIsDialogOpen(true);
    }
  };

  const handlePlannerClick = () => {
    setShowPlannerLogs(true);
  };

  const handleClosePlannerDialog = () => {
    setShowPlannerLogs(false);
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setSelectedAgent(null);
  };

  // Don't render if no workflow
  if (!workflow || workflow.length === 0) {
    return null;
  }

  // Map agent roles to their data
  const agentsByRole = new Map<string, Agent>();
  agentData?.agents.forEach(agent => {
    agentsByRole.set(agent.role, agent);
  });

  // Determine step status
  const getStepStatus = (index: number): 'completed' | 'current' | 'pending' | 'failed' => {
    if (status === 'failed' && current_step !== null && current_step !== undefined && index === current_step) {
      return 'failed';
    }
    if (status === 'completed') {
      return 'completed';
    }
    if (current_step === null || current_step === undefined) {
      return 'pending';
    }
    if (index < current_step) {
      return 'completed';
    }
    if (index === current_step) {
      return 'current';
    }
    return 'pending';
  };

  // Format numbers for display
  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
  };

  const formatCost = (cost: string): string => {
    const numCost = parseFloat(cost);
    if (numCost === 0) return '$0';
    if (numCost < 0.01) return '<$0.01';
    return `$${numCost.toFixed(2)}`;
  };

  return (
    <div className="workflow-progress">
      {/* Header */}
      <div className="text-xs text-muted-foreground mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span>Workflow Progress</span>
          <button
            onClick={handlePlannerClick}
            className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            title="View workflow planner logs"
          >
            <FileText className="h-3 w-3" />
            Planner
          </button>
        </div>
        {current_step !== null && current_step !== undefined && status === 'in_progress' && (
          <span className="text-blue-600 dark:text-blue-400">
            Step {current_step + 1} of {workflow.length}
          </span>
        )}
      </div>

      {/* Progress Steps */}
      <div className="space-y-3">
        {workflow.map((agentRole, index) => {
          const stepStatus = getStepStatus(index);
          const agent = agentsByRole.get(agentRole);
          const totalTokens = agent
            ? agent.total_input_tokens + agent.total_output_tokens
            : 0;

          return (
            <div key={index} className="flex items-start gap-3">
              {/* Step Indicator */}
              <div className="relative mt-1">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all ${
                    stepStatus === 'completed'
                      ? 'bg-green-100 dark:bg-green-900/30 border-green-500'
                      : stepStatus === 'current'
                      ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-500'
                      : stepStatus === 'failed'
                      ? 'bg-red-100 dark:bg-red-900/30 border-red-500'
                      : 'bg-muted border-border'
                  }`}
                >
                  {stepStatus === 'completed' ? (
                    <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                  ) : stepStatus === 'current' ? (
                    <Loader2 className="h-4 w-4 text-blue-600 dark:text-blue-400 animate-spin" />
                  ) : stepStatus === 'failed' ? (
                    <span className="text-red-600 dark:text-red-400 text-xs font-bold">✕</span>
                  ) : (
                    <Circle className="h-3 w-3 text-muted-foreground" />
                  )}
                </div>

                {/* Connector Line */}
                {index < workflow.length - 1 && (
                  <div className="absolute left-1/2 top-8 w-0.5 h-6 -translate-x-1/2 bg-border" />
                )}
              </div>

              {/* Agent Details */}
              <div className="flex-1 min-w-0 pt-1">
                {/* Agent Name - Clickable for completed/failed agents */}
                {agent && (stepStatus === 'completed' || stepStatus === 'failed') ? (
                  <button
                    onClick={() => handleAgentClick(agent)}
                    className={`text-sm font-medium hover:underline cursor-pointer text-left ${
                      stepStatus === 'completed'
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                    title="Click to view agent logs"
                  >
                    {agentRole}
                  </button>
                ) : (
                  <div
                    className={`text-sm font-medium ${
                      stepStatus === 'current'
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-muted-foreground'
                    }`}
                  >
                    {agentRole}
                  </div>
                )}

                {/* Agent Metrics */}
                {agent && (stepStatus === 'completed' || stepStatus === 'current' || stepStatus === 'failed') && (
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    {totalTokens > 0 && (
                      <span className="flex items-center gap-1">
                        <span className="font-mono">{formatTokens(totalTokens)}</span>
                        <span className="text-[10px]">tokens</span>
                      </span>
                    )}
                    {parseFloat(agent.total_cost) > 0 && (
                      <span className="flex items-center gap-1">
                        <span className="font-mono">{formatCost(agent.total_cost)}</span>
                      </span>
                    )}
                    {agent.status && (
                      <span className="text-[10px] uppercase tracking-wide">
                        {agent.status}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Agent Log Dialog */}
      <AgentLogDialog
        agent={selectedAgent}
        isOpen={isDialogOpen}
        onClose={handleCloseDialog}
      />

      {/* Planner Log Dialog */}
      {showPlannerLogs && plannerLogs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={handleClosePlannerDialog}>
          <div
            className="bg-background border border-border rounded-lg shadow-lg w-full max-w-4xl max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold">Workflow Planner Logs</h2>
                <p className="text-sm text-muted-foreground">Task: {task.id.substring(0, 8)}</p>
              </div>
              <button
                onClick={handleClosePlannerDialog}
                className="p-2 hover:bg-muted rounded-md transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <pre className="text-xs font-mono whitespace-pre-wrap break-words leading-relaxed">
                {plannerLogs.output || 'No planner output available'}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
