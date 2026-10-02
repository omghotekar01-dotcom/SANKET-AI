const configuredApi = import.meta.env.VITE_API_BASE as string | undefined
const configuredWs = import.meta.env.VITE_WS_BASE as string | undefined

const runtimeHost =
  typeof window !== 'undefined' && window.location.hostname
    ? window.location.hostname
    : '127.0.0.1'

export const API_BASE = (configuredApi || `http://${runtimeHost}:8000`).replace(/\/$/, '')
export const WS_BASE = (configuredWs || API_BASE.replace(/^http/, 'ws')).replace(/\/$/, '')

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {'Content-Type':'application/json', ...(init?.headers || {})},
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export async function apiHealth(timeoutMs = 1800): Promise<any> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await api('/api/health', {signal: controller.signal})
  } finally {
    window.clearTimeout(timer)
  }
}
