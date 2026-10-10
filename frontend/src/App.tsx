import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, API_URL, type AgentEvent, type Approval, type Cash, type Ticket } from './api'
import { summaryOf, TICKET_TYPE, toFeedItem } from './agents'
import { Approvals } from './components/Approvals'
import { CashFigure } from './components/CashFigure'
import { Feed } from './components/Feed'
import { AgentMark, Shape } from './components/Shape'
import { Team } from './components/Team'
import { TicketList } from './components/TicketList'

const FAST = 1200 // ms between refreshes while agents are working
const SLOW = 5000

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [error, setError] = useState<string | null>(null)
  const [offline, setOffline] = useState(false)
  const [dropped, setDropped] = useState(false)
  const lastIndex = useRef<number | undefined>(undefined)
  const selectedRef = useRef(selected)
  selectedRef.current = selected

  const anyRunning = tickets.some((t) => t.run?.state === 'running')

  const refresh = useCallback(async () => {
    try {
      const [t, c, a] = await Promise.all([api.tickets(), api.cash(), api.approvals()])
      setTickets(t)
      setCash(c)
      setApprovals(a)
      setOffline(false)
      setSelected((s) => s ?? t[0]?.id ?? null)
      const id = selectedRef.current
      if (id !== null) {
        const r = await api.events(id, lastIndex.current)
        if (selectedRef.current === id && r.events.length) {
          lastIndex.current = Math.max(lastIndex.current ?? -1, r.events[r.events.length - 1].index)
          setEvents((prev) => {
            const seen = new Set(prev.map((e) => e.index))
            return [...prev, ...r.events.filter((e) => !seen.has(e.index))]
          })
        }
      }
    } catch (e) {
      setOffline(e instanceof TypeError) // fetch failed: backend not reachable
      if (!(e instanceof TypeError)) setError(String((e as Error).message))
    }
  }, [])

  // New ticket picked: start its event list from scratch.
  useEffect(() => {
    lastIndex.current = undefined
    setEvents([])
    refresh()
  }, [selected, refresh])

  useEffect(() => {
    const id = setInterval(refresh, anyRunning ? FAST : SLOW)
    return () => clearInterval(id)
  }, [anyRunning, refresh])

  const ticket = tickets.find((t) => t.id === selected) ?? null

  // Show the latest run on this ticket (the audit trail keeps every past run too).
  const runId = events.length ? events[events.length - 1].run_id : null
  const runEvents = useMemo(() => events.filter((e) => e.run_id === runId), [events, runId])
  const feed = useMemo(() => {
    const liveHandoffs = runEvents.some((e) => e.step === 'handoff')
    return runEvents.map((e) => toFeedItem(e, liveHandoffs)).filter((x) => x !== null)
  }, [runEvents])
  const pastRuns = new Set(events.map((e) => e.run_id)).size - (runId ? 1 : 0)
  const bossDone = [...runEvents].reverse().find((e) => e.agent === 'boss' && e.depth === 0 && e.step === 'end')
  const decision = ticket?.run?.decision ?? null
  const running = ticket?.run?.state === 'running'
  const ticketApprovals = approvals.filter((a) => a.ticket_id === selected)
  const otherApprovals = approvals.filter((a) => a.ticket_id !== selected)

  const run = async () => {
    if (!ticket) return
    setError(null)
    try {
      await api.runTicket(ticket.id)
      await refresh()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const approve = async (id: number) => {
    setError(null)
    try {
      await api.approve(id)
      setDropped(true)
      setTimeout(() => setDropped(false), 1600)
      await refresh()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const reject = async (id: number) => {
    try {
      await api.reject(id)
      await refresh()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const reset = async () => {
    if (!confirm('Reset the shop data to the original database? Pending approvals and drafts will be cleared.')) return
    try {
      await api.reset()
      await refresh()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="desk">
      <header className="masthead">
        <div className="brand">
          <div className="brand-shapes" aria-hidden="true">
            <Shape kind="circle" color="var(--c-boss)" size={18} />
            <Shape kind="square" color="var(--c-inventory)" size={18} />
            <Shape kind="triangle" color="var(--c-accounting)" size={18} />
          </div>
          <div>
            <h1>Campus Customs</h1>
            <p className="muted">Agent desk · Chapel Street, New Haven</p>
          </div>
        </div>
        <CashFigure cash={cash} dropped={dropped} />
      </header>

      {offline && (
        <div className="banner">
          Can’t reach the backend at {API_URL}. Start it from <code>backend/</code> with{' '}
          <code>uvicorn main:app --reload --port 8000</code>.
        </div>
      )}
      {error && (
        <div className="banner banner-error" onClick={() => setError(null)}>
          {error}
        </div>
      )}

      <main className="grid">
        <section className="col col-tickets">
          <h2 className="col-title">Tickets</h2>
          <TicketList tickets={tickets} selected={selected} onSelect={setSelected} />
          <button className="btn btn-text reset" onClick={reset} disabled={anyRunning}>
            Reset shop data
          </button>
        </section>

        <section className="col col-floor">
          {ticket && (
            <>
              <div className="floor-head">
                <div>
                  <span className="eyebrow">
                    {TICKET_TYPE[ticket.type] ?? ticket.type} · {ticket.requester}
                  </span>
                  <h2 className="floor-title">
                    <span className="floor-no">{ticket.id}</span> {ticket.subject}
                  </h2>
                </div>
                {ticket.status === 'resolved' ? (
                  <span className="resolved-stamp">Resolved</span>
                ) : (
                  <button className="btn btn-primary" onClick={run} disabled={anyRunning}>
                    {running ? (
                      <span className="working">
                        <AgentMark agent="boss" size={10} />
                        <AgentMark agent="inventory" size={10} />
                        <AgentMark agent="accounting" size={10} />
                        Team working
                      </span>
                    ) : anyRunning ? (
                      'Another ticket is running'
                    ) : (
                      'Run the team'
                    )}
                  </button>
                )}
              </div>

              {(decision || bossDone) && (
                <div className="decision">
                  <span className="decision-mark">
                    <AgentMark agent="boss" size={28} />
                  </span>
                  <div>
                    <span className="eyebrow">The Boss’s call</span>
                    <p className="decision-text">{decision?.decision ?? (bossDone && summaryOf(bossDone))}</p>
                    {decision?.reasoning && <p className="muted small">{decision.reasoning}</p>}
                  </div>
                </div>
              )}

              <div className="floor-sub">
                <h3 className="col-title">Conversation</h3>
                {pastRuns > 0 && (
                  <span className="muted small">
                    Latest run · {pastRuns} earlier run{pastRuns === 1 ? '' : 's'} in the audit trail
                  </span>
                )}
              </div>
              <Feed items={feed} live={running} />
            </>
          )}
        </section>

        <aside className="col col-side">
          <h2 className="col-title">
            Needs you{' '}
            {approvals.length > 0 && <span className="count">{approvals.length}</span>}
          </h2>
          <Approvals items={[...ticketApprovals, ...otherApprovals]} onApprove={approve} onReject={reject} />

          <h2 className="col-title team-title">The team</h2>
          <Team events={runEvents} />
        </aside>
      </main>
    </div>
  )
}
