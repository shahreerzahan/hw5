// Client for the FastAPI backend (backend/main.py).
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type AgentName = 'boss' | 'inventory' | 'accounting' | 'facilities' | 'customer_service'

export interface RunState {
  state: 'running' | 'done' | 'failed'
  started_at: string
  finished_at: string | null
  decision: Decision | null
  error?: string
}

export interface Ticket {
  id: number
  type: string
  requester: string
  subject: string
  status: 'open' | 'resolved'
  created_at: string
  run: RunState | null
}

export interface Decision {
  ticket_id: number
  decision: string
  reasoning: string
  agents_consulted: AgentName[]
  actions_taken: { tool: string; detail: string }[]
  needs_human_approval: string[]
  customer_draft_id: number | null
  ticket_status: 'open' | 'resolved'
}

export interface AgentEvent {
  index: number
  time: string
  run_id: string
  ticket_id: number
  agent: AgentName
  depth: number
  step: number | 'start' | 'end' | 'handoff' | 'delegation_refused'
  tool: string | null
  args: string | null
  result: string | null
  stop_reason: string | null
  called_by?: string
  summary?: string
}

export interface Cash {
  balance: number
  as_of: string
  pending_approval_total: number
  available_after_pending: number
}

export interface Approval {
  id: number
  kind: 'payment' | 'purchase_order'
  ticket_id: number | null
  ref_type: 'invoice' | 'lease' | null
  ref_id: number | null
  vendor_id: number | null
  sku: string | null
  size: string | null
  qty: number | null
  amount: number
  reason: string
  requested_by: string
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.detail ?? `${res.status} ${res.statusText}`)
  return body as T
}

export const api = {
  tickets: () => call<{ tickets: Ticket[] }>('/api/tickets').then((r) => r.tickets),
  runTicket: (id: number) => call<RunState>(`/api/tickets/${id}/run`, { method: 'POST' }),
  events: (ticketId: number, after?: number) =>
    call<{ total: number; events: AgentEvent[] }>(
      `/api/events?ticket_id=${ticketId}&limit=500${after !== undefined ? `&after=${after}` : ''}`,
    ),
  cash: () => call<Cash>('/api/cash'),
  approvals: () => call<{ items: Approval[] }>('/api/approvals').then((r) => r.items),
  approve: (id: number) =>
    call<{ balance_after: number }>(`/api/approvals/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved_by: 'desk' }),
    }),
  reject: (id: number) =>
    call(`/api/approvals/${id}/reject`, { method: 'POST', body: JSON.stringify({ approved_by: 'desk' }) }),
  reset: () => call('/api/reset', { method: 'POST' }),
}
