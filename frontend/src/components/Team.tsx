import type { AgentEvent, AgentName } from '../api'
import { AGENTS, AGENT_ORDER, summaryOf } from '../agents'
import { AgentMark } from './Shape'

type Status = 'idle' | 'working' | 'done'

/** One row per agent: shape, live status, and what it did on this run. */
export function Team({ events }: { events: AgentEvent[] }) {
  const info = (name: AgentName) => {
    const mine = events.filter((e) => e.agent === name)
    const starts = mine.filter((e) => e.step === 'start').length
    const ends = mine.filter((e) => e.step === 'end').length
    const status: Status = starts === 0 ? 'idle' : starts > ends ? 'working' : 'done'
    const summaries = mine.filter((e) => e.step === 'end').map(summaryOf).filter((s): s is string => !!s)
    const tools = new Set(mine.filter((e) => e.tool && e.tool !== 'final_result' && e.tool !== 'ask_agent').map((e) => e.tool!))
    const asked = new Set(
      mine
        .filter((e) => e.tool === 'ask_agent' && e.step !== 'delegation_refused')
        .map((e) => (e.args?.match(/"agent":"(\w+)"/)?.[1] ?? '') as AgentName)
        .filter(Boolean),
    )
    return { status, summaries, tools: [...tools], asked: [...asked] }
  }

  return (
    <ul className="team">
      {AGENT_ORDER.map((name) => {
        const a = AGENTS[name]
        const { status, summaries, tools, asked } = info(name)
        return (
          <li key={name} className={`agent status-${status}`}>
            <div className="agent-head">
              <span className="agent-mark">
                <AgentMark agent={name} size={22} />
              </span>
              <div>
                <strong>{a.label}</strong>
                <span className="muted small">{a.role}</span>
              </div>
              <span className="agent-status">{status === 'idle' ? 'Not needed' : status === 'working' ? 'Working' : 'Done'}</span>
            </div>
            {summaries.length > 0 && (
              <div className="agent-summary">
                {summaries.map((s, i) => (
                  <p key={i}>{s}</p>
                ))}
                {(asked.length > 0 || tools.length > 0) && (
                  <p className="agent-meta">
                    {asked.length > 0 && (
                      <span>
                        Asked{' '}
                        {asked.map((n) => (
                          <span key={n} className="chip">
                            <AgentMark agent={n} size={9} /> {AGENTS[n]?.label ?? n}
                          </span>
                        ))}
                      </span>
                    )}
                    {tools.length > 0 && (
                      <span>
                        Used{' '}
                        {tools.map((t) => (
                          <code key={t}>{t}</code>
                        ))}
                      </span>
                    )}
                  </p>
                )}
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}
