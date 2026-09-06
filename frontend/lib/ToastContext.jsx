'use client'

import { createContext, useCallback, useContext, useState } from 'react'

const ToastContext = createContext(null)

let idCounter = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismissToast = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id))
  }, [])

  const showToast = useCallback((message, type = 'info', durationMs = 4000) => {
    const id = ++idCounter
    setToasts((current) => [...current, { id, message, type }])
    if (durationMs > 0) {
      setTimeout(() => dismissToast(id), durationMs)
    }
    return id
  }, [dismissToast])

  return (
    <ToastContext.Provider value={{ showToast, dismissToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-[999] flex flex-col gap-2 max-w-[360px]">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`rounded-lg shadow-lg border px-4 py-3 text-[13.5px] flex items-start gap-2.5 animate-toast-in ${
              t.type === 'success'
                ? 'bg-[#f0faf4] border-[#bfe8cf] text-[#1e6f4c]'
                : t.type === 'error'
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-white border-border text-ink'
            }`}
          >
            <span className="mt-0.5">
              {t.type === 'success' ? '✓' : t.type === 'error' ? '⚠' : 'ℹ'}
            </span>
            <span className="flex-1">{t.message}</span>
            <button
              onClick={() => dismissToast(t.id)}
              className="text-ink-faint hover:text-ink -mt-0.5"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return ctx
}
