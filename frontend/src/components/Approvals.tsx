import { useState } from 'react'
import type { Approval } from '../api'
import { money } from '../agents'

function describe(a: Approval) {
  if (a.kind === 'purchase_order') return `Purchase order · ${a.qty} × ${a.sku} ${a.size}`
  if (a.ref_type === 'invoice') return `Pay invoice ${a.ref_id}`
  if (a.ref_type === 'lease') return `Pay rent · lease ${a.ref_id}`
  return 'Payment'
}

export function Approvals({
  items,
  onApprove,
  onReject,
}: {
  items: Approval[]
  onApprove: (id: number) => Promise<void>
  onReject: (id: number) => Promise<void>
}) {
  const [busy, setBusy] = useState<number | null>(null)
  const act = async (id: number, fn: (id: number) => Promise<void>) => {
    setBusy(id)
    try {
      await fn(id)
    } finally {
      setBusy(null)
    }
  }

  if (!items.length) return <p className="muted small approvals-empty">Nothing is waiting for you.</p>

  return (
    <ul className="approvals">
      {items.map((a) => (
        <li key={a.id} className="approval">
          <div className="approval-top">
            <span className="approval-amount">{money(a.amount)}</span>
            <span className="muted small">
              #{a.id}
              {a.ticket_id ? ` · ticket ${a.ticket_id}` : ''}
            </span>
          </div>
          <strong className="approval-what">{describe(a)}</strong>
          <p className="muted small approval-reason">{a.reason}</p>
          <div className="approval-actions">
            <button className="btn btn-approve" disabled={busy === a.id} onClick={() => act(a.id, onApprove)}>
              {busy === a.id ? 'Working…' : 'Approve'}
            </button>
            <button className="btn btn-text" disabled={busy === a.id} onClick={() => act(a.id, onReject)}>
              Reject
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
