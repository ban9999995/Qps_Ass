const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${base}${path}`, { headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) }, ...options })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(payload.detail || `请求失败（HTTP ${response.status}）`)
    return payload as T
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`无法连接后端：${base}。请确认后端服务正在运行。`)
    }
    throw error
  }
}
