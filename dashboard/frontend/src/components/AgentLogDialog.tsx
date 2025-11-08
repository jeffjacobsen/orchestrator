/**
 * Agent Log Dialog Component
 *
 * Modal dialog for viewing agent execution logs:
 * - Prompt tab: Shows the initial prompt sent to the agent
 * - Output tab: Shows the agent's text response
 * - Copy/download functionality for each log
 */
import { useState } from 'react';
import { X, Copy, Download, Check } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../services/api';
import type { Agent } from '../types';

interface AgentLogDialogProps {
  agent: Agent | null;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'prompt' | 'output';

export function AgentLogDialog({ agent, isOpen, onClose }: AgentLogDialogProps) {
  const [activeTab, setActiveTab] = useState<TabType>('output');
  const [copiedTab, setCopiedTab] = useState<TabType | null>(null);

  // Fetch agent logs
  const { data: logs, isLoading } = useQuery({
    queryKey: ['agent-logs', agent?.id],
    queryFn: () => agentApi.getLogs(agent!.id),
    enabled: isOpen && agent !== null,
  });

  if (!isOpen || !agent) return null;

  const handleCopy = async (text: string, tab: TabType) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedTab(tab);
      setTimeout(() => setCopiedTab(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = (text: string, filename: string) => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const currentLog = activeTab === 'prompt' ? logs?.prompt : logs?.output;
  const currentFilename = activeTab === 'prompt'
    ? `${agent.id}_prompt.txt`
    : `${agent.id}_output.txt`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-background border border-border rounded-lg shadow-lg w-full max-w-4xl max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="text-lg font-semibold">Agent Logs</h2>
            <p className="text-sm text-muted-foreground">
              {agent.role} - {agent.id.substring(0, 8)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-md transition-colors"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('output')}
            className={`px-4 py-2 text-sm font-medium transition-colors relative ${
              activeTab === 'output'
                ? 'text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Output
            {activeTab === 'output' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('prompt')}
            className={`px-4 py-2 text-sm font-medium transition-colors relative ${
              activeTab === 'prompt'
                ? 'text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Prompt
            {activeTab === 'prompt' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
        </div>

        {/* Actions Bar */}
        <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b border-border">
          <div className="text-xs text-muted-foreground">
            {isLoading ? 'Loading...' : `${currentLog?.length || 0} characters`}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => currentLog && handleCopy(currentLog, activeTab)}
              className="flex items-center gap-1 px-2 py-1 text-xs hover:bg-muted rounded transition-colors"
              disabled={!currentLog || isLoading}
            >
              {copiedTab === activeTab ? (
                <>
                  <Check className="h-3 w-3" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  Copy
                </>
              )}
            </button>
            <button
              onClick={() => currentLog && handleDownload(currentLog, currentFilename)}
              className="flex items-center gap-1 px-2 py-1 text-xs hover:bg-muted rounded transition-colors"
              disabled={!currentLog || isLoading}
            >
              <Download className="h-3 w-3" />
              Download
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-muted-foreground">Loading logs...</div>
            </div>
          ) : currentLog ? (
            <pre className="text-xs font-mono whitespace-pre-wrap break-words leading-relaxed">
              {currentLog}
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-muted-foreground">No log data available</div>
            </div>
          )}
        </div>

        {/* Footer with agent metrics */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/30">
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>
              <span className="font-medium">Tokens:</span>{' '}
              {(agent.total_input_tokens + agent.total_output_tokens).toLocaleString()}
            </span>
            <span>
              <span className="font-medium">Cost:</span>{' '}
              {agent.total_cost && !isNaN(parseFloat(agent.total_cost))
                ? `$${parseFloat(agent.total_cost).toFixed(4)}`
                : '$0.0000'}
            </span>
            <span>
              <span className="font-medium">Status:</span>{' '}
              <span className={`uppercase ${
                agent.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                agent.status === 'failed' ? 'text-red-600 dark:text-red-400' :
                'text-blue-600 dark:text-blue-400'
              }`}>
                {agent.status}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
