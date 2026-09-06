/**
 * Safely extracts a human-readable string from any API error shape.
 *
 * Real, confirmed bug this fixes: FastAPI's own validation errors
 * (HTTP 422) return `detail` as an ARRAY of objects
 * (e.g. [{type, loc, msg, input}]), not a string — confirmed by
 * directly testing a real FastAPI app and inspecting the actual
 * response shape, not assumed. Every place in this app that did
 * `err.response?.data?.detail || 'fallback message'` would pass that
 * raw array straight into a toast's message, and React cannot render
 * an array of objects as JSX children — it throws "Objects are not
 * valid as a React child" and crashes the component. This produces
 * exactly a silent "flash and revert, no visible error" symptom,
 * since the crash happens after the click handler's own try/catch
 * already ran, inside the render that followed.
 */
export function getErrorMessage(err, fallback = 'Something went wrong. Please try again.') {
  if (err?.code === 'ECONNABORTED') {
    return 'The request timed out — the server may be slow or stuck right now. Try again in a moment.'
  }

  const detail = err?.response?.data?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    // Real shape of a FastAPI/Pydantic 422 validation error.
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        const field = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : null
        return field ? `${field}: ${item?.msg ?? 'invalid value'}` : (item?.msg ?? 'Invalid input')
      })
      .join('; ')
  }

  if (typeof err?.message === 'string' && err.message.trim()) {
    return fallback !== undefined ? fallback : err.message
  }

  return fallback
}
