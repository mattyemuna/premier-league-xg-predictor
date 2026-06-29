import { useState, useRef, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'

// Aceternity-inspired spotlight card: radial gradient spotlight follows the cursor,
// creating a subtle glare that reveals the card surface without being decorative noise.
export default function PredictionCard({ prediction }) {
  const { home_team, away_team, home_xg, away_xg } = prediction
  const [mouse, setMouse]     = useState({ x: 0, y: 0 })
  const [hovered, setHovered] = useState(false)
  const cardRef               = useRef(null)

  const handleMouseMove = useCallback((e) => {
    const rect = cardRef.current?.getBoundingClientRect()
    if (rect) setMouse({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }, [])

  const maxXG    = Math.max(home_xg, away_xg, 0.5)
  const homePct  = Math.min((home_xg / maxXG) * 100, 100)
  const awayPct  = Math.min((away_xg / maxXG) * 100, 100)
  const diff     = Math.abs(home_xg - away_xg)
  const favored  = diff < 0.05 ? null : home_xg > away_xg ? 'home' : 'away'

  const spotlightBg = hovered
    ? `radial-gradient(320px circle at ${mouse.x}px ${mouse.y}px, rgba(16,224,160,0.05) 0%, transparent 55%), #1C1F26`
    : '#1C1F26'

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      initial={{ opacity: 0, scale: 0.98, y: 6 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="relative overflow-hidden rounded-xl border border-rim"
      style={{ background: spotlightBg }}
    >
      {/* Glare border overlay */}
      {hovered && (
        <div
          className="pointer-events-none absolute inset-0 rounded-xl"
          style={{
            background: `radial-gradient(280px circle at ${mouse.x}px ${mouse.y}px, rgba(16,224,160,0.12) 0%, transparent 45%)`,
          }}
        />
      )}

      <div className="relative z-10 p-4">
        {/* Header row */}
        <div className="flex items-center justify-between mb-4">
          <span className="font-mono text-[9px] tracking-[0.2em] text-sub/60 uppercase">
            xG Projection
          </span>
          <span className="font-mono text-[9px] text-sub/40">
            Elo-weighted · 5 seasons
          </span>
        </div>

        {/* Home */}
        <XGRow
          label={home_team}
          xg={home_xg}
          pct={homePct}
          isFavored={favored === 'home'}
          delay={0.08}
        />

        <div className="my-2.5" />

        {/* Away */}
        <XGRow
          label={away_team}
          xg={away_xg}
          pct={awayPct}
          isFavored={favored === 'away'}
          delay={0.24}
        />

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-rim flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            {favored ? (
              <>
                <span className="block w-1.5 h-1.5 rounded-full bg-accent" />
                <span className="font-mono text-[10px] text-accent">
                  {favored === 'home' ? home_team : away_team} favored
                </span>
              </>
            ) : (
              <span className="font-mono text-[10px] text-sub/60">Evenly matched</span>
            )}
          </div>
          <span className="font-mono text-[10px] text-sub/50 tabular-nums">
            Δ {diff.toFixed(2)} xG
          </span>
        </div>
      </div>
    </motion.div>
  )
}

function XGRow({ label, xg, pct, isFavored, delay }) {
  const [barWidth, setBarWidth] = useState(0)

  // Trigger bar animation after mount
  useEffect(() => {
    const t = setTimeout(() => setBarWidth(pct), delay * 1000 + 80)
    return () => clearTimeout(t)
  }, [pct, delay])

  return (
    <div className="flex items-center gap-3">
      <span
        className={cn(
          'text-[12px] font-medium w-36 truncate shrink-0 transition-colors duration-150',
          isFavored ? 'text-text' : 'text-sub'
        )}
      >
        {label}
      </span>

      <div className="flex-1 h-[5px] bg-rim rounded-full overflow-hidden">
        <div
          className="xg-bar"
          style={{
            width: `${barWidth}%`,
            background: isFavored ? '#10E0A0' : '#363C47',
          }}
        />
      </div>

      <span
        className={cn(
          'font-mono text-[13px] tabular-nums w-10 text-right shrink-0 transition-colors duration-150',
          isFavored ? 'text-accent' : 'text-sub'
        )}
      >
        {xg.toFixed(2)}
      </span>
    </div>
  )
}
