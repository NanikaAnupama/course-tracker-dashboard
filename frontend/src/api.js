const BASE = import.meta.env.VITE_API_URL || ''

export async function fetchJson(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body.detail) detail = body.detail
    } catch { /* keep default */ }
    throw new Error(detail)
  }
  return res.json()
}

export async function refreshData() {
  const res = await fetch(`${BASE}/api/refresh`, { method: 'POST' })
  if (!res.ok) throw new Error('Refresh failed')
  return res.json()
}
