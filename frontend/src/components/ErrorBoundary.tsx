import { Component } from 'react'
import type { ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  handleReset = () => {
    this.setState({ error: null })
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 p-8 text-center">
          <AlertTriangle size={40} className="text-gold" />
          <div>
            <h2 className="text-lg font-semibold text-navy dark:text-white mb-1">
              Something went wrong
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md">
              {this.state.error.message || 'An unexpected error occurred.'}
            </p>
          </div>
          <button onClick={this.handleReset} className="btn-primary text-sm">
            Try again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
