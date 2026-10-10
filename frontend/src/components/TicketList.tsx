import type { Ticket } from '../api'
import { TICKET_TYPE } from '../agents'

export function TicketList({
  tickets,
  selected,
  onSelect,
}: {
  tickets: Ticket[]
  selected: number | null
  onSelect: (id: number) => void
}) {
  return (
    <ul className="tickets">
      {tickets.map((t) => {
        const running = t.run?.state === 'running'
        return (
          <li key={t.id}>
            <button
              className={`ticket${selected === t.id ? ' is-selected' : ''}${t.status === 'resolved' ? ' is-resolved' : ''}`}
              onClick={() => onSelect(t.id)}
              aria-pressed={selected === t.id}
            >
              <span className="ticket-no">{t.id}</span>
              <span className="ticket-body">
                <span className="eyebrow">{TICKET_TYPE[t.type] ?? t.type}</span>
                <span className="ticket-subject">{t.subject}</span>
                <span className="muted small">{t.requester}</span>
              </span>
              <span className="ticket-status">
                {t.status === 'resolved' ? (
                  <span className="resolved-mark" title="Resolved">
                    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                      <circle cx="12" cy="12" r="11" />
                      <path d="M7 12.5l3.2 3.2L17 9" />
                    </svg>
                    Resolved
                  </span>
                ) : running ? (
                  <span className="status-running">
                    <i />
                    Working
                  </span>
                ) : (
                  <span className="status-open">Open</span>
                )}
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
