import { useEffect, useRef } from 'react'
import { AGENTS, type FeedItem } from '../agents'
import { AgentMark } from './Shape'

export function Feed({ items, live }: { items: FeedItem[]; live: boolean }) {
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (live) end.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [items.length, live])

  if (!items.length) {
    return (
      <div className="feed-empty">
        <div className="feed-empty-shapes" aria-hidden="true">
          <AgentMark agent="boss" size={22} />
          <AgentMark agent="inventory" size={22} />
          <AgentMark agent="accounting" size={22} />
          <AgentMark agent="facilities" size={22} />
          <AgentMark agent="customer_service" size={22} />
        </div>
        <p>The team is quiet. Run the team and their conversation will appear here, step by step.</p>
      </div>
    )
  }

  return (
    <ol className="feed">
      {items.map((it) => (
        <li key={it.key} className={`feed-item kind-${it.kind}${it.depth > 0 ? ' nested' : ''}`} style={{ '--depth': it.depth } as React.CSSProperties}>
          <span className="feed-mark">
            <AgentMark agent={it.agent} size={14} />
          </span>
          <div className="feed-text">
            <div className="feed-line">
              <strong style={{ color: AGENTS[it.agent]?.color }}>{AGENTS[it.agent]?.label ?? it.agent}</strong>
              {it.kind === 'handoff' && it.to ? (
                <span className="handoff">
                  <span className="arrow">→</span>
                  <AgentMark agent={it.to} size={12} />
                  <strong style={{ color: AGENTS[it.to]?.color }}>{AGENTS[it.to]?.label ?? it.to}</strong>
                </span>
              ) : (
                <span className="feed-title">{it.title}</span>
              )}
              <time>{new Date(it.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</time>
            </div>
            {it.detail && <p className="feed-detail">{it.detail}</p>}
          </div>
        </li>
      ))}
      <div ref={end} />
    </ol>
  )
}
