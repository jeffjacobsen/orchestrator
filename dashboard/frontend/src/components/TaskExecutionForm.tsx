/**
 * Task Execution Form Component
 *
 * Allows users to submit new tasks with:
 * - Task description
 * - Task type selection
 * - Automatic complexity estimation
 * - Workflow preview
 * - ANALYST inclusion toggle
 */
import { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { taskApi } from '../services/api';
import { Play, Loader2, CheckCircle2, XCircle, Info, FolderOpen } from 'lucide-react';
import type { TaskType } from '../types/api';

interface TaskExecutionFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const TASK_TYPES: { value: TaskType; label: string; description: string }[] = [
  {
    value: 'feature_implementation',
    label: 'Feature Implementation',
    description: 'Add new functionality or features to the codebase'
  },
  {
    value: 'bug_fix',
    label: 'Bug Fix',
    description: 'Fix existing bugs or issues in the code'
  },
  {
    value: 'refactoring',
    label: 'Refactoring',
    description: 'Improve code structure without changing functionality'
  },
  {
    value: 'documentation',
    label: 'Documentation',
    description: 'Write or update documentation'
  },
  {
    value: 'testing',
    label: 'Testing',
    description: 'Write or improve tests'
  }
];

/**
 * Estimate task complexity based on description keywords
 */
function estimateComplexity(description: string): 'simple' | 'complex' {
  const descLower = description.toLowerCase();

  // Complex indicators
  const complexKeywords = [
    'integrate', 'system', 'architecture', 'multiple', 'refactor',
    'migrate', 'redesign', 'overhaul', 'infrastructure', 'authentication',
    'authorization', 'payment', 'security', 'optimize', 'performance',
    'scale', 'distributed', 'microservice', 'api design'
  ];

  // Simple indicators
  const simpleKeywords = [
    'simple', 'quick', 'small', 'minor', 'typo', 'comment',
    'rename', 'update text', 'change color', 'add log'
  ];

  // Check for complexity
  if (complexKeywords.some(keyword => descLower.includes(keyword))) {
    return 'complex';
  }

  if (simpleKeywords.some(keyword => descLower.includes(keyword))) {
    return 'simple';
  }

  // Default to simple for short descriptions, complex for long ones
  return description.split(' ').length < 10 ? 'simple' : 'complex';
}

/**
 * Detect task type based on description keywords
 */
function detectTaskType(description: string): TaskType | null {
  const descLower = description.toLowerCase();

  // Feature implementation keywords
  const featureKeywords = [
    'add', 'implement', 'create', 'build', 'develop', 'feature',
    'functionality', 'capability', 'new', 'enhancement'
  ];

  // Bug fix keywords
  const bugFixKeywords = [
    'fix', 'bug', 'error', 'issue', 'problem', 'broken', 'crash',
    'not working', 'doesn\'t work', 'fails', 'repair', 'resolve'
  ];

  // Refactoring keywords
  const refactorKeywords = [
    'refactor', 'restructure', 'reorganize', 'clean up', 'cleanup',
    'improve code', 'simplify', 'modularize', 'extract', 'consolidate'
  ];

  // Documentation keywords
  const docKeywords = [
    'document', 'documentation', 'readme', 'docs', 'comment',
    'explain', 'describe', 'write guide', 'api docs', 'jsdoc'
  ];

  // Testing keywords
  const testKeywords = [
    'test', 'testing', 'unit test', 'integration test', 'e2e',
    'spec', 'coverage', 'jest', 'pytest', 'test case'
  ];

  // Count matches for each type
  const scores = {
    feature_implementation: featureKeywords.filter(k => descLower.includes(k)).length,
    bug_fix: bugFixKeywords.filter(k => descLower.includes(k)).length,
    refactoring: refactorKeywords.filter(k => descLower.includes(k)).length,
    documentation: docKeywords.filter(k => descLower.includes(k)).length,
    testing: testKeywords.filter(k => descLower.includes(k)).length,
  };

  // Find type with highest score
  const maxScore = Math.max(...Object.values(scores));

  // Only suggest if we have a clear match (at least 1 keyword)
  if (maxScore === 0) return null;

  // Return the type with highest score
  const detectedType = Object.entries(scores).find(([_, score]) => score === maxScore)?.[0];
  return detectedType as TaskType || null;
}

/**
 * Get expected workflow based on task type and complexity
 * Note: Actual workflow is determined by the orchestrator - this is just a preview
 */
function getExpectedWorkflow(taskType: TaskType, complexity: 'simple' | 'complex', includeAnalyst: string): string[] {
  const workflow: string[] = [];

  // Add analyst if requested or auto for complex tasks
  if (includeAnalyst === 'yes' || (includeAnalyst === 'auto' && complexity === 'complex')) {
    workflow.push('ANALYST');
  }

  // Task-type specific workflows
  switch (taskType) {
    case 'feature_implementation':
      if (complexity === 'simple') {
        workflow.push('BUILDER', 'TESTER');
      } else {
        workflow.push('PLANNER', 'BUILDER', 'TESTER', 'REVIEWER');
      }
      break;

    case 'bug_fix':
      if (complexity === 'simple') {
        workflow.push('BUILDER', 'TESTER');
      } else {
        workflow.push('PLANNER', 'BUILDER', 'TESTER');
      }
      break;

    case 'refactoring':
      if (complexity === 'simple') {
        workflow.push('BUILDER', 'REVIEWER');
      } else {
        workflow.push('PLANNER', 'BUILDER', 'TESTER', 'REVIEWER');
      }
      break;

    case 'documentation':
      // Documentation tasks don't need testing
      if (complexity === 'simple') {
        workflow.push('BUILDER');
      } else {
        workflow.push('PLANNER', 'BUILDER', 'REVIEWER');
      }
      break;

    case 'testing':
      // Testing tasks
      if (complexity === 'simple') {
        workflow.push('BUILDER');
      } else {
        workflow.push('PLANNER', 'BUILDER', 'REVIEWER');
      }
      break;

    default:
      // Default workflow
      workflow.push('PLANNER', 'BUILDER');
  }

  return workflow;
}

export function TaskExecutionForm({ onSuccess, onCancel }: TaskExecutionFormProps) {
  const [description, setDescription] = useState('');
  const [taskType, setTaskType] = useState<TaskType>('feature_implementation');
  const [includeAnalyst, setIncludeAnalyst] = useState<'auto' | 'yes' | 'no'>('auto');
  const [workingDirectory, setWorkingDirectory] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isTaskTypeManual, setIsTaskTypeManual] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const handleBrowseDirectory = () => {
    fileInputRef.current?.click();
  };

  const handleDirectorySelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Get the directory path from the first file
      const file = files[0];
      // Extract directory path (remove filename)
      const path = file.webkitRelativePath || file.name;
      const dirPath = path.substring(0, path.lastIndexOf('/'));
      setWorkingDirectory(dirPath || path);
    }
  };

  // Real-time complexity estimation
  const complexity = estimateComplexity(description);
  const expectedWorkflow = getExpectedWorkflow(taskType, complexity, includeAnalyst);

  // Auto-detect task type based on description (only if user hasn't manually selected)
  useEffect(() => {
    if (!isTaskTypeManual && description.trim().length > 10) {
      const detected = detectTaskType(description);
      if (detected) {
        setTaskType(detected);
      }
    }
  }, [description, isTaskTypeManual]);

  const createTaskMutation = useMutation({
    mutationFn: taskApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setDescription('');
      setTaskType('feature_implementation');
      setIncludeAnalyst('auto');
      setWorkingDirectory('');
      setIsTaskTypeManual(false);
      onSuccess?.();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || !workingDirectory.trim()) return;

    createTaskMutation.mutate({
      description: description.trim(),
      task_type: taskType,
      include_analyst: includeAnalyst,
      working_directory: workingDirectory.trim(),
    });
  };

  return (
    <div className="bg-card border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Execute New Task</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Submit a task for the multi-agent orchestrator to execute
          </p>
        </div>
        {onCancel && (
          <button
            onClick={onCancel}
            className="text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Working Directory */}
        <div>
          <label htmlFor="workingDirectory" className="block text-sm font-medium mb-2">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4" />
              Working Directory *
            </div>
          </label>
          <input
            id="workingDirectory"
            type="text"
            value={workingDirectory}
            onChange={(e) => setWorkingDirectory(e.target.value)}
            placeholder="/absolute/path/to/your/project"
            className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
          <p className="text-xs text-muted-foreground mt-2">
            <strong>Important:</strong> Enter the absolute path to your project directory. This prevents accidentally creating code in the orchestrator root.
            <br />
            <span className="text-xs">Example: <code className="bg-muted px-1 rounded">/Users/yourname/projects/myapp</code> or <code className="bg-muted px-1 rounded">/home/user/workspace/project</code></span>
          </p>
        </div>

        {/* Task Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium mb-2">
            Task Description *
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what you want to accomplish... (e.g., 'Add user authentication with JWT tokens')"
            className="w-full px-3 py-2 border rounded-md bg-background min-h-[100px] resize-y focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
          <div className="flex items-center gap-2 mt-2">
            <div className={`text-xs px-2 py-1 rounded ${
              complexity === 'simple'
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
            }`}>
              {complexity === 'simple' ? 'Simple Task' : 'Complex Task'}
            </div>
            <span className="text-xs text-muted-foreground">
              Estimated automatically based on description
            </span>
          </div>
        </div>

        {/* Task Type */}
        <div>
          <label htmlFor="taskType" className="block text-sm font-medium mb-2">
            Task Type *
          </label>
          <select
            id="taskType"
            value={taskType}
            onChange={(e) => {
              setTaskType(e.target.value as TaskType);
              setIsTaskTypeManual(true);
            }}
            className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {TASK_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-muted-foreground flex-1">
              {TASK_TYPES.find(t => t.value === taskType)?.description}
            </p>
            {!isTaskTypeManual && description.trim().length > 10 && (
              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                Auto-detected
              </span>
            )}
          </div>
        </div>

        {/* Workflow Preview */}
        <div className="border rounded-lg p-4 bg-muted/30">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-medium">Expected Workflow (Preview)</h3>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {expectedWorkflow.map((agent, index) => (
              <div key={index} className="flex items-center gap-2">
                <div className="px-3 py-1 bg-primary/10 text-primary rounded-md text-sm font-medium">
                  {agent}
                </div>
                {index < expectedWorkflow.length - 1 && (
                  <span className="text-muted-foreground">→</span>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            <strong>Note:</strong> This is an estimated workflow. The actual orchestrator workflow may differ based on task requirements.
          </p>
        </div>

        {/* Advanced Options */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
          >
            {showAdvanced ? '▼' : '▶'} Advanced Options
          </button>

          {showAdvanced && (
            <div className="mt-4 p-4 border rounded-lg space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  ANALYST Inclusion
                </label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="includeAnalyst"
                      value="auto"
                      checked={includeAnalyst === 'auto'}
                      onChange={(e) => setIncludeAnalyst(e.target.value as 'auto')}
                      className="text-primary focus:ring-primary"
                    />
                    <span className="text-sm">Auto (recommended) - Include for complex tasks</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="includeAnalyst"
                      value="yes"
                      checked={includeAnalyst === 'yes'}
                      onChange={(e) => setIncludeAnalyst(e.target.value as 'yes')}
                      className="text-primary focus:ring-primary"
                    />
                    <span className="text-sm">Always include ANALYST</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="includeAnalyst"
                      value="no"
                      checked={includeAnalyst === 'no'}
                      onChange={(e) => setIncludeAnalyst(e.target.value as 'no')}
                      className="text-primary focus:ring-primary"
                    />
                    <span className="text-sm">Never include ANALYST</span>
                  </label>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  The ANALYST agent performs research and analysis before planning
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={!workingDirectory.trim() || !description.trim() || createTaskMutation.isPending}
            className="flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {createTaskMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating Task...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Execute Task
              </>
            )}
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-2 border rounded-md hover:bg-accent transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        {/* Status Messages */}
        {createTaskMutation.isError && (
          <div className="flex items-center gap-2 p-3 border border-destructive rounded-md bg-destructive/10">
            <XCircle className="h-4 w-4 text-destructive" />
            <p className="text-sm text-destructive">
              {(createTaskMutation.error as Error).message || 'Failed to create task'}
            </p>
          </div>
        )}

        {createTaskMutation.isSuccess && (
          <div className="flex items-center gap-2 p-3 border border-green-500 rounded-md bg-green-500/10">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <p className="text-sm text-green-500">
              Task created successfully! Agents will begin execution.
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
