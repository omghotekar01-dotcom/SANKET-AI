const configured = import.meta.env.VITE_API_BASE as string | undefined
export const API_BASE = configured || 'http://127.0.0.1:8000'
export const WS_BASE = (import.meta.env.VITE_WS_BASE as string | undefined) || API_BASE.replace(/^http/, 'ws')

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
