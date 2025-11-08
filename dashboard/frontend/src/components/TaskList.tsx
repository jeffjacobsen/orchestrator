/**
 * Task List Component
 *
 * Displays a list of tasks with their status, workflow, and execution details.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { taskApi } from '../services/api';
import { Loader2, CheckCircle2, XCircle, Clock, Play, Trash2 } from 'lucide-react';
import { WorkflowProgress } from './WorkflowProgress';
import type { Task } from '../types/api';

const STATUS_CONFIG = {
  pending: {
    icon: Clock,
    color: 'text-yellow-500',
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    label: 'Pending'
  },
  in_progress: {
    icon: Play,
    color: 'text-blue-500',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    label: 'In Progress'
  },
  completed: {
    icon: CheckCircle2,
    color: 'text-green-500',
    bg: 'bg-green-100 dark:bg-green-900/30',
    label: 'Completed'
  },
  failed: {
    icon: XCircle,
    color: 'text-red-500',
    bg: 'bg-red-100 dark:bg-red-900/30',
    label: 'Failed'
  },
};

interface TaskCardProps {
  task: Task;
  onDelete: (taskId: string) => void;
}

function TaskCard({ task, onDelete }: TaskCardProps) {
  const statusConfig = STATUS_CONFIG[task.status as keyof typeof STATUS_CONFIG];
  const StatusIcon = statusConfig?.icon || Clock;

  return (
    <div className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <div className={`${statusConfig?.bg} ${statusConfig?.color} px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1`}>
              <StatusIcon className="h-3 w-3" />
              {statusConfig?.label}
            </div>
            <div className="text-xs text-muted-foreground">
              {task.complexity === 'simple' ? '⚡ Simple' : '🔥 Complex'}
            </div>
          </div>
          <p className="text-sm font-medium line-clamp-2">
            {task.description}
          </p>
        </div>
        <button
          onClick={() => onDelete(task.id)}
          className="ml-2 p-1 hover:bg-destructive/10 rounded text-muted-foreground hover:text-destructive transition-colors"
          title="Delete task"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {/* Task Type & Working Directory */}
      <div className="text-xs text-muted-foreground mb-3 space-y-1">
        <div>
          <span className="font-medium">Type:</span> {task.task_type.replace('_', ' ')}
        </div>
        {task.working_directory && (
          <div>
            <span className="font-medium">Working Directory:</span> {task.working_directory}
          </div>
        )}
      </div>

      {/* Workflow Progress */}
      {task.workflow && task.workflow.length > 0 && (
        <div className="mb-3">
          <WorkflowProgress task={task} />
        </div>
      )}

      {/* Timestamps */}
      <div className="text-xs text-muted-foreground pt-3 border-t flex items-center justify-between">
        <span>
          Created: {new Date(task.created_at).toLocaleString()}
        </span>
        {task.completed_at && (
          <span>
            Completed: {new Date(task.completed_at).toLocaleString()}
          </span>
        )}
      </div>

      {/* Error message if failed */}
      {task.status === 'failed' && task.error && (
        <div className="mt-3 p-2 bg-destructive/10 border border-destructive rounded text-xs text-destructive">
          {task.error}
        </div>
      )}

      {/* Result if completed */}
      {task.status === 'completed' && task.result && (
        <div className="mt-3 p-2 bg-green-500/10 border border-green-500 rounded text-xs text-green-600 dark:text-green-400">
          {task.result}
        </div>
      )}
    </div>
  );
}

export function TaskList() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => taskApi.list(),
    // No polling needed - WebSocket provides real-time updates
  });

  const deleteTaskMutation = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-destructive rounded-lg p-4 bg-destructive/10">
        <h3 className="font-semibold text-destructive mb-2">Error loading tasks</h3>
        <p className="text-sm text-muted-foreground mb-4">{(error as Error).message}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data || data.tasks.length === 0) {
    return (
      <div className="border rounded-lg p-8 text-center">
        <p className="text-muted-foreground">No tasks found</p>
        <p className="text-sm text-muted-foreground mt-2">
          Create a new task to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          Tasks
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

      <div className="grid grid-cols-1 gap-4">
        {data.tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onDelete={(taskId) => deleteTaskMutation.mutate(taskId)}
          />
        ))}
      </div>
    </div>
  );
}
