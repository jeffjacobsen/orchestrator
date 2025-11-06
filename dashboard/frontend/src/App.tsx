import { useState } from 'react'
import { AgentList } from './components/AgentList'
import { Activity } from 'lucide-react'

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

            <button
              onClick={toggleDarkMode}
              className="px-4 py-2 rounded border hover:bg-accent transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <AgentList />
      </main>

      {/* Footer */}
      <footer className="border-t mt-12">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          Claude Multi-Agent Orchestrator Dashboard • Phase 1 Core Dashboard
        </div>
      </footer>
    </div>
  )
}

export default App
