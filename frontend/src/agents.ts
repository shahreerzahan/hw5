// How each agent looks, and how raw audit events read as plain sentences.
import type { AgentEvent, AgentName } from './api'

export type ShapeKind = 'circle' | 'square' | 'triangle' | 'half' | 'rounded'

export const AGENTS: Record<AgentName, { label: string; role: string; shape: ShapeKind; color: string }> = {
  boss: { label: 'Boss', role: 'Reads the ticket, makes the call', shape: 'circle', color: 'var(--c-boss)' },
  inventory: { label: 'Inventory', role: 'Stock, shortfalls, restock', shape: 'square', color: 'var(--c-inventory)' },
  accounting: { label: 'Accounting', role: 'Cash, invoices, margins', shape: 'triangle', color: 'var(--c-accounting)' },
  facilities: { label: 'Facilities', role: 'Lease and rent', shape: 'half', color: 'var(--c-facilities)' },
  customer_service: {
    label: 'Customer Service',
    role: 'Drafts replies, never sends',
    shape: 'rounded',
    color: 'var(--c-customer)',
  },
}

export const AGENT_ORDER: AgentName[] = ['boss', 'inventory', 'accounting', 'facilities', 'customer_service']

export const TICKET_TYPE: Record<string, string> = {
  customer_order: 'Customer order',
  rent_notice: 'Rent notice',
  price_override: 'Price override',
}

export const money = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: n % 1 ? 2 : 0 })

// Audit args/results are JSON cut to 300 characters, so parse when we can and
// fall back to pulling single fields out of the text.
function parse(text: string | null): Record<string, any> | null {
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function field(text: string | null, key: string): string | undefined {
  if (!text) return undefined
  const m = text.match(new RegExp(`"${key}":("((?:[^"\\\\]|\\\\.)*)"?|-?[\\d.]+|true|false|null)`))
  if (!m) return undefined
  return m[2] !== undefined ? m[2].replace(/\\"/g, '"').replace(/\\n/g, ' ') : m[1]
}

const TOOL_VERB: Record<string, string> = {
  get_desk_date: 'Checked the desk date',
  list_tickets: 'Listed tickets',
  get_ticket: 'Read the ticket',
  check_stock: 'Checked stock',
  list_vendors: 'Looked up vendors',
  get_vendor_invoices: 'Checked vendor invoices',
  get_invoice: 'Opened an invoice',
  get_lease: 'Read the lease',
  get_cash_balance: 'Checked cash',
  list_pending_approvals: 'Checked pending approvals',
  prepare_payment: 'Prepared a payment',
  prepare_purchase_order: 'Prepared a purchase order',
  save_customer_draft: 'Saved a customer draft',
  resolve_ticket: 'Resolved the ticket',
}

function toolDetail(tool: string, args: string | null, result: string | null): string {
  const r = parse(result)
  const a = parse(args)
  if (r && (r.ok === false || r.found === false)) return r.error ?? 'Not found'
  switch (tool) {
    case 'get_desk_date':
      return `Today is ${r?.date_today ?? field(result, 'date_today')}`
    case 'get_ticket':
      return `“${r?.subject ?? field(result, 'subject')}” from ${r?.requester ?? field(result, 'requester')}`
    case 'check_stock': {
      const sku = a?.sku ?? field(args, 'sku')
      const size = a?.size ?? field(args, 'size')
      const qty = r?.qty_in_stock ?? field(result, 'qty_in_stock')
      return `${sku} size ${size}: ${qty} in stock · cost ${money(Number(r?.unit_cost ?? field(result, 'unit_cost')))} · list ${money(Number(r?.list_price ?? field(result, 'list_price')))}`
    }
    case 'list_vendors':
      return r ? r.vendors.map((v: any) => `${v.name} (${v.lead_days}d)`).join(' · ') : 'Vendor list'
    case 'get_vendor_invoices': {
      const name = r?.vendor?.name ?? field(result, 'name')
      const lead = r?.vendor?.lead_days ?? field(result, 'lead_days')
      const n = r?.open_invoices?.length
      const total = r?.open_invoice_total
      return `${name}, ${lead}-day lead${n !== undefined ? ` · ${n} open invoice${n === 1 ? '' : 's'}${n ? ` (${money(total)})` : ''}` : ''}`
    }
    case 'get_invoice':
      return `Invoice ${r?.id ?? field(result, 'id')}: ${money(Number(r?.amount ?? field(result, 'amount')))}, due ${r?.due_date ?? field(result, 'due_date')}, ${r?.status ?? field(result, 'status')}`
    case 'get_lease':
      return `${r?.landlord ?? field(result, 'landlord')} · ${money(Number(r?.monthly_rent ?? field(result, 'monthly_rent')))} due ${r?.next_due ?? field(result, 'next_due')}`
    case 'get_cash_balance':
      return `Checking ${money(Number(r?.balance ?? field(result, 'balance')))} · ${money(Number(r?.available_after_pending ?? field(result, 'available_after_pending')))} free after pending`
    case 'list_pending_approvals':
      return `${r?.count ?? field(result, 'count')} waiting for approval`
    case 'prepare_payment':
      return `${money(Number(a?.amount ?? field(args, 'amount')))} for ${a?.ref_type ?? field(args, 'ref_type')} ${a?.ref_id ?? field(args, 'ref_id')}, waiting for approval (request #${r?.request_id ?? field(result, 'request_id')})`
    case 'prepare_purchase_order':
      return `${a?.qty ?? field(args, 'qty')} × ${a?.sku ?? field(args, 'sku')} ${a?.size ?? field(args, 'size')} = ${money(Number(r?.amount ?? field(result, 'amount')))}, waiting for approval (request #${r?.request_id ?? field(result, 'request_id')})`
    case 'save_customer_draft':
      return `To ${a?.recipient ?? field(args, 'recipient')}: “${a?.subject ?? field(args, 'subject')}” (draft #${r?.draft_id ?? field(result, 'draft_id')}, not sent)`
    case 'resolve_ticket':
      return a?.resolution ?? field(args, 'resolution') ?? 'Marked resolved'
    default:
      return ''
  }
}

export interface FeedItem {
  key: number
  agent: AgentName
  depth: number
  kind: 'start' | 'tool' | 'handoff' | 'reply' | 'finish' | 'refused' | 'stopped'
  title: string
  detail: string
  to?: AgentName
  time: string
}

/** An agent's own words at the end of its run (older trail entries have no summary field). */
export const summaryOf = (e: AgentEvent) => e.summary ?? field(e.result, 'summary') ?? field(e.result, 'decision')

const clean = (s: string | null | undefined) => (s ?? '').replace(/^Request from \w+ about ticket \d+:\s*/, '').trim()

/** Turn one audit event into a feed line, or null to hide it. */
export function toFeedItem(e: AgentEvent, liveHandoffs: boolean): FeedItem | null {
  const base = { key: e.index, agent: e.agent, depth: e.depth, time: e.time }
  if (e.step === 'start') {
    return e.called_by && e.called_by !== 'user'
      ? { ...base, kind: 'start', title: `Picked up a request from ${AGENTS[e.called_by as AgentName]?.label ?? e.called_by}`, detail: '' }
      : { ...base, kind: 'start', title: `Picked up ticket ${e.ticket_id}`, detail: '' }
  }
  if (e.step === 'end') {
    if (e.stop_reason === 'completed')
      return { ...base, kind: 'finish', title: 'Done', detail: summaryOf(e) ?? '' }
    return { ...base, kind: 'stopped', title: `Stopped (${e.stop_reason})`, detail: e.result ?? '' }
  }
  if (e.step === 'delegation_refused') {
    return { ...base, kind: 'refused', title: 'Handoff refused by a guardrail', detail: e.result ?? '' }
  }
  if (!e.tool || e.tool === 'final_result') return null
  if (e.tool === 'ask_agent') {
    const a = parse(e.args)
    const to = (a?.agent ?? field(e.args, 'agent')) as AgentName
    // Newer trails log the handoff when it starts; the tool result is then just the reply.
    if (liveHandoffs && e.step !== 'handoff')
      return { ...base, kind: 'reply', title: `Heard back from ${AGENTS[to]?.label ?? to}`, detail: '' }
    return {
      ...base,
      kind: 'handoff',
      to,
      title: `Asked ${AGENTS[to]?.label ?? to}`,
      detail: clean(a?.request ?? field(e.args, 'request')),
    }
  }
  const retry = e.stop_reason === 'tool_error_retry'
  return {
    ...base,
    kind: 'tool',
    title: (TOOL_VERB[e.tool] ?? e.tool) + (retry ? ' (retrying)' : ''),
    detail: retry ? e.result ?? '' : toolDetail(e.tool, e.args, e.result),
  }
}
