/**
 * Type definitions for the Orchestrator Dashboard.
 */

export enum AgentRole {
  ANALYST = 'ANALYST',
  PLANNER = 'PLANNER',
  BUILDER = 'BUILDER',
  TESTER = 'TESTER',
  REVIEWER = 'REVIEWER',
  CUSTOM = 'CUSTOM',
}

export enum AgentStatus {
  ACTIVE = 'active',
  IDLE = 'idle',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum TaskType {
  FEATURE_IMPLEMENTATION = 'feature_implementation',
  BUG_FIX = 'bug_fix',
  CODE_REVIEW = 'code_review',
  REFACTORING = 'refactoring',
  TESTING = 'testing',
  DOCUMENTATION = 'documentation',
  INVESTIGATION = 'investigation',
  CUSTOM = 'custom',
  AUTO = 'auto',
}

export interface Agent {
  id: string
  role: AgentRole
  status: AgentStatus
  task_id?: string | null
  created_at: string
  updated_at: string
  completed_at?: string | null
  custom_instructions?: string | null
  total_input_tokens: number
  total_output_tokens: number
  cache_creation_tokens: number
  cache_read_tokens: number
  total_cost: string
  metadata: Record<string, any>
}

export interface Task {
  id: string
  description: string
  task_type: TaskType
  status: TaskStatus
  created_at: string
  updated_at: string
  completed_at?: string | null
  workflow: string[]
  complexity?: string | null
  include_analyst?: string | null
  result?: string | null
  error?: string | null
  metadata: Record<string, any>
}

export interface AgentList {
  agents: Agent[]
  total: number
  page: number
  page_size: number
}

export interface TaskList {
  tasks: Task[]
  total: number
  page: number
  page_size: number
}

export interface ErrorResponse {
  code: string
  message: string
  details: Record<string, any>
  request_id: string
  timestamp: string
}
