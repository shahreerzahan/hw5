import { useEffect, useRef, useState } from 'react'
import type { Cash } from '../api'
import { money } from '../agents'

/** Eases from the old value to the new one, so a payment visibly "drains" the balance. */
function useTween(target: number, ms = 900) {
  const [value, setValue] = useState(target)
  const from = useRef(target)
  useEffect(() => {
    const start = performance.now()
    const a = from.current
    let raf = 0
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms)
      const eased = 1 - Math.pow(1 - t, 3)
      setValue(a + (target - a) * eased)
      if (t < 1) raf = requestAnimationFrame(tick)
      else from.current = target
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      from.current = target
    }
  }, [target, ms])
  return value
}

export function CashFigure({ cash, dropped }: { cash: Cash | null; dropped: boolean }) {
  const shown = useTween(cash?.balance ?? 0)
  return (
    <div className={`cash${dropped ? ' cash-dropped' : ''}`}>
      <span className="eyebrow">Checking</span>
      <span className="cash-number">{cash ? money(Math.round(shown)) : '—'}</span>
      {cash && (
        <span className="muted small">
          {cash.pending_approval_total > 0
            ? `${money(cash.pending_approval_total)} waiting for approval · ${money(cash.available_after_pending)} free`
            : `as of ${cash.as_of}`}
        </span>
      )}
    </div>
  )
}
