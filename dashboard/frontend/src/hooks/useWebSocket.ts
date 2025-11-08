/**
 * WebSocket hook for real-time updates from the orchestrator backend.
 *
 * This hook replaces the 5-second polling mechanism with true real-time updates
 * via WebSocket connections. It automatically handles:
 * - Connection management (connect, reconnect, disconnect)
 * - Message routing to appropriate handlers
 * - React Query cache updates for seamless UI updates
 * - Error handling and connection status tracking
 */
import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Agent, Task } from '@/types/api';

interface WebSocketMessage {
  type: 'agent_update' | 'agent_deleted' | 'task_update' | 'task_deleted';
  data: Agent | Task | { id: string };
}

interface UseWebSocketOptions {
  enabled?: boolean;
  url?: string;
  onConnectionChange?: (connected: boolean) => void;
}

const DEFAULT_WS_URL = 'ws://localhost:8000/api/v1/ws';
const RECONNECT_INTERVAL = 3000; // 3 seconds

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    enabled = true,
    url = DEFAULT_WS_URL,
    onConnectionChange,
  } = options;

  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectedRef = useRef(false);

  /**
   * Handle incoming WebSocket messages and update React Query cache.
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'agent_update': {
            const agent = message.data as Agent;

            // Update the agents list cache
            queryClient.setQueryData<{ agents: Agent[]; total: number }>(
              ['agents'],
              (old) => {
                if (!old) return old;

                const existingIndex = old.agents.findIndex(a => a.id === agent.id);
                if (existingIndex >= 0) {
                  // Update existing agent
                  const newAgents = [...old.agents];
                  newAgents[existingIndex] = agent;
                  return { ...old, agents: newAgents };
                } else {
                  // Add new agent
                  return {
                    agents: [agent, ...old.agents],
                    total: old.total + 1,
                  };
                }
              }
            );

            // Update individual agent cache
            queryClient.setQueryData(['agents', agent.id], agent);
            break;
          }

          case 'agent_deleted': {
            const { id } = message.data as { id: string };

            // Remove from agents list cache
            queryClient.setQueryData<{ agents: Agent[]; total: number }>(
              ['agents'],
              (old) => {
                if (!old) return old;
                return {
                  agents: old.agents.filter(a => a.id !== id),
                  total: old.total - 1,
                };
              }
            );

            // Remove individual agent cache
            queryClient.removeQueries({ queryKey: ['agents', id] });
            break;
          }

          case 'task_update': {
            const task = message.data as Task;

            // Update the tasks list cache
            queryClient.setQueryData<{ tasks: Task[]; total: number }>(
              ['tasks'],
              (old) => {
                if (!old) return old;

                const existingIndex = old.tasks.findIndex(t => t.id === task.id);
                if (existingIndex >= 0) {
                  // Update existing task
                  const newTasks = [...old.tasks];
                  newTasks[existingIndex] = task;
                  return { ...old, tasks: newTasks };
                } else {
                  // Add new task
                  return {
                    tasks: [task, ...old.tasks],
                    total: old.total + 1,
                  };
                }
              }
            );

            // Update individual task cache
            queryClient.setQueryData(['tasks', task.id], task);
            break;
          }

          case 'task_deleted': {
            const { id } = message.data as { id: string };

            // Remove from tasks list cache
            queryClient.setQueryData<{ tasks: Task[]; total: number }>(
              ['tasks'],
              (old) => {
                if (!old) return old;
                return {
                  tasks: old.tasks.filter(t => t.id !== id),
                  total: old.total - 1,
                };
              }
            );

            // Remove individual task cache
            queryClient.removeQueries({ queryKey: ['tasks', id] });
            break;
          }

          default:
            console.warn('Unknown WebSocket message type:', message);
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    },
    [queryClient]
  );

  /**
   * Connect to WebSocket server.
   */
  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnectedRef.current = true;
        onConnectionChange?.(true);

        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          } else {
            clearInterval(pingInterval);
          }
        }, 30000);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        isConnectedRef.current = false;
        onConnectionChange?.(false);

        // Attempt to reconnect after delay
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, RECONNECT_INTERVAL);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }, [enabled, url, handleMessage, onConnectionChange]);

  /**
   * Disconnect from WebSocket server.
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    isConnectedRef.current = false;
    onConnectionChange?.(false);
  }, [onConnectionChange]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected: isConnectedRef.current,
    connect,
    disconnect,
  };
}
