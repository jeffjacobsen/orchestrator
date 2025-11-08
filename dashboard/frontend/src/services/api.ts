/**
 * API client for the Orchestrator Dashboard backend.
 */

import type { AgentList, TaskList, Agent, Task } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-api-key-change-in-production'

/**
 * Make an authenticated API request.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
    ...options.headers,
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      code: 'UNKNOWN_ERROR',
      message: 'An unknown error occurred',
    }))
    throw new Error(error.message || 'Request failed')
  }

  return response.json()
}

/**
 * Agent API endpoints.
 */
export const agentApi = {
  /**
   * List all agents.
   */
  list: async (params?: {
    page?: number
    page_size?: number
    status?: string
    task_id?: string
  }): Promise<AgentList> => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', params.page.toString())
    if (params?.page_size) query.set('page_size', params.page_size.toString())
    if (params?.status) query.set('status', params.status)
    if (params?.task_id) query.set('task_id', params.task_id)

    const queryString = query.toString()
    return apiRequest(`/api/v1/agents${queryString ? `?${queryString}` : ''}`)
  },

  /**
   * Get agent by ID.
   */
  get: async (agentId: string): Promise<Agent> => {
    return apiRequest(`/api/v1/agents/${agentId}`)
  },

  /**
   * Create a new agent.
   */
  create: async (data: {
    role: string
    custom_instructions?: string
    task_id?: string
  }): Promise<Agent> => {
    return apiRequest('/api/v1/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * Delete an agent.
   */
  delete: async (agentId: string): Promise<void> => {
    await apiRequest(`/api/v1/agents/${agentId}`, {
      method: 'DELETE',
    })
  },

  /**
   * Get agent logs (prompt and output).
   */
  getLogs: async (agentId: string): Promise<{ prompt: string; output: string }> => {
    return apiRequest(`/api/v1/agents/${agentId}/logs`)
  },
}

/**
 * Task API endpoints.
 */
export const taskApi = {
  /**
   * List all tasks.
   */
  list: async (params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<TaskList> => {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', params.page.toString())
    if (params?.page_size) query.set('page_size', params.page_size.toString())
    if (params?.status) query.set('status', params.status)

    const queryString = query.toString()
    return apiRequest(`/api/v1/tasks${queryString ? `?${queryString}` : ''}`)
  },

  /**
   * Get task by ID.
   */
  get: async (taskId: string): Promise<Task> => {
    return apiRequest(`/api/v1/tasks/${taskId}`)
  },

  /**
   * Create a new task.
   */
  create: async (data: {
    description: string
    task_type: string
    include_analyst?: string
    working_directory?: string
    metadata?: Record<string, any>
  }): Promise<Task> => {
    return apiRequest('/api/v1/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * Delete a task.
   */
  delete: async (taskId: string): Promise<void> => {
    await apiRequest(`/api/v1/tasks/${taskId}`, {
      method: 'DELETE',
    })
  },

  /**
   * Get workflow planner logs for a task.
   */
  getPlannerLogs: async (taskId: string): Promise<{ prompt: string; output: string }> => {
    return apiRequest(`/api/v1/tasks/${taskId}/planner-logs`)
  },
}
