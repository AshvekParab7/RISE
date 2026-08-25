const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '')
let refreshPromise = null

export class ApiError extends Error {
  constructor(status, message, data = null) { super(message); this.status = status; this.data = data }
}

const friendlyMessage = status => ({ 400: 'Please check the information you entered.', 401: 'Your session has expired. Please sign in again.', 403: 'You do not have permission to do that.', 404: 'That RISE record could not be found.', 409: 'This record already exists.', 429: 'RISE is busy right now. Please try again shortly.', 500: 'RISE had trouble processing that request.' }[status] || 'RISE could not complete that request.')

async function refreshAccessToken() {
  if (refreshPromise) return refreshPromise
  const refresh = localStorage.getItem('rise_refresh_token')
  if (!refresh) return false
  refreshPromise = (async () => {
    const response = await fetch(`${API_URL}/token/refresh/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh }) })
    if (!response.ok) return false
    const data = await response.json()
    localStorage.setItem('rise_access_token', data.access)
    return true
  })().finally(() => { refreshPromise = null })
  return refreshPromise
}

export async function request(path, options = {}, retried = false) {
  const token = localStorage.getItem('rise_access_token')
  const hadSession = Boolean(token || localStorage.getItem('rise_refresh_token'))
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response
  try { response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: 'include' }) } catch { throw new ApiError(0, "RISE can't reach the server right now. Please try again.") }
  if (response.status === 401 && !retried && await refreshAccessToken()) return request(path, options, true)
  if (response.status === 401 && !retried) {
    localStorage.removeItem('rise_access_token')
    localStorage.removeItem('rise_refresh_token')
    if (hadSession) window.dispatchEvent(new CustomEvent('rise:auth-expired'))
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new ApiError(response.status, data?.detail || friendlyMessage(response.status), data)
  }
  return response.status === 204 ? null : response.json()
}

export const api = { request, url: API_URL }
export const hasSession = () => Boolean(localStorage.getItem('rise_access_token') || localStorage.getItem('rise_refresh_token'))
export const get = path => request(path)
export const post = (path, body) => request(path, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body) })
export const patch = (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) })
export const remove = path => request(path, { method: 'DELETE' })
