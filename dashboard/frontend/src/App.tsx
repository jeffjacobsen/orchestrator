import { useState } from 'react'
import { TaskList } from './components/TaskList'
import { TaskExecutionForm } from './components/TaskExecutionForm'
import { Activity, Wifi, WifiOff, Plus } from 'lucide-react'
import { useWebSocket } from './hooks/useWebSocket'

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    // Check system preference or localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('darkMode')
      if (stored !== null) {
        return stored === 'true'
      }
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return false
  })

  const [wsConnected, setWsConnected] = useState(false)
  const [showTaskForm, setShowTaskForm] = useState(false)

  // Initialize WebSocket connection for real-time updates
  useWebSocket({
    enabled: true,
    onConnectionChange: setWsConnected,
  })

  // Apply dark mode class to document
  if (typeof document !== 'undefined') {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      const newValue = !prev
      localStorage.setItem('darkMode', String(newValue))
      return newValue
    })
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold">Orchestrator Dashboard</h1>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                v0.1.0
              </span>
            </div>

            <div className="flex items-center gap-3">
              {/* WebSocket connection status */}
              <div className="flex items-center gap-1.5 text-sm">
                {wsConnected ? (
                  <>
                    <Wifi className="h-4 w-4 text-green-500" />
                    <span className="text-muted-foreground">Live</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Connecting...</span>
                  </>
                )}
              </div>

              <button
                onClick={toggleDarkMode}
                className="px-4 py-2 rounded border hover:bg-accent transition-colors"
                aria-label="Toggle dark mode"
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Task Execution Section */}
        <section>
          {showTaskForm ? (
            <TaskExecutionForm
              onSuccess={() => setShowTaskForm(false)}
              onCancel={() => setShowTaskForm(false)}
            />
          ) : (
            <button
              onClick={() => setShowTaskForm(true)}
              className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
            >
              <Plus className="h-5 w-5" />
              New Task
            </button>
          )}
        </section>

        {/* Tasks Section */}
        <section>
          <TaskList />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t mt-12">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          Claude Multi-Agent Orchestrator Dashboard • Phase 2: Real-Time Updates
        </div>
      </footer>
    </div>
  )
}

export default App
