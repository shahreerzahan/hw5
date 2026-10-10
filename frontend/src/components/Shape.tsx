import type { AgentName } from '../api'
import { AGENTS, type ShapeKind } from '../agents'

const PATHS: Record<ShapeKind, React.ReactNode> = {
  circle: <circle cx="12" cy="12" r="11" />,
  square: <rect x="1.5" y="1.5" width="21" height="21" />,
  triangle: <polygon points="12,1.5 23,22.5 1,22.5" />,
  half: <path d="M1 18 A11 11 0 0 1 23 18 Z" />,
  rounded: <rect x="1.5" y="1.5" width="21" height="21" rx="6.5" />,
}

export function Shape({ kind, color, size = 16 }: { kind: ShapeKind; color: string; size?: number }) {
  return (
    <svg className="shape" width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ fill: color }}>
      {PATHS[kind]}
    </svg>
  )
}

export function AgentMark({ agent, size = 16 }: { agent: AgentName; size?: number }) {
  const a = AGENTS[agent]
  return a ? <Shape kind={a.shape} color={a.color} size={size} /> : null
}
