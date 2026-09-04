import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './styles.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("React Error Boundary caught error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px',
          fontFamily: 'sans-serif',
          color: '#f8fafc',
          background: '#090d16',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <h2 style={{ color: '#ef4444' }}>⚠️ Platform Interface Error</h2>
          <p style={{ color: '#9ca3af', marginBottom: '12px' }}>An unexpected rendering error occurred.</p>
          <pre style={{
            background: '#1e293b',
            padding: '16px',
            borderRadius: '8px',
            maxWidth: '600px',
            overflowX: 'auto',
            color: '#fca5a5',
            fontSize: '13px'
          }}>
            {this.state.error?.toString()}
          </pre>
          <button
            onClick={() => {
              localStorage.clear()
              window.location.href = '/login'
            }}
            style={{
              marginTop: '16px',
              padding: '10px 20px',
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            Reset Session &amp; Return to Login
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)
