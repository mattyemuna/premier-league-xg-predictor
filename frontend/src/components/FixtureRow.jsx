import { useState, useEffect, useRef } from 'react'
import { cn } from '../lib/utils'
import { getAbbr, getHue, formatDate } from '../lib/teams'

const GLOW_HOLD_MS  = 3000   // how long the glow stays at full intensity
const GLOW_FADE_MS  = 700    // CSS transition duration for the fade-out

export default function FixtureRow({ fixture, isActive, onClick }) {
  const { home_team, away_team, date } = fixture

  // glowOn drives the boxShadow value; glowFade drives whether the change is
  // instant (snap to full) or animated (fade to nothing).
  const [glowOn,   setGlowOn]   = useState(false)
  const [glowFade, setGlowFade] = useState(false) // false = instant, true = animated
  const timerRef = useRef(null)

  useEffect(() => {
    clearTimeout(timerRef.current)

    if (isActive) {
      // Snap to full intensity immediately — no transition
      setGlowFade(false)
      setGlowOn(true)

      // After the hold period, switch to animated and remove the glow
      timerRef.current = setTimeout(() => {
        setGlowFade(true)
        setGlowOn(false)
      }, GLOW_HOLD_MS)
    } else {
      // Another row was selected — start an animated fade-out right away
      setGlowFade(true)
      setGlowOn(false)
    }

    return () => clearTimeout(timerRef.current)
  }, [isActive])

  const shadow = glowOn ? 'inset 4px 0 16px -4px rgba(16,224,160,0.3)' : 'none'
  const transition = glowFade
    ? `box-shadow ${GLOW_FADE_MS}ms ease`
    : 'box-shadow 0ms'

  return (
    <button
      onClick={onClick}
      className={cn(
        'relative w-full text-left border-b border-[#1C1F26] border-l-2 transition-colors duration-150 cursor-pointer group overflow-hidden',
        isActive
          ? 'border-l-accent bg-card'
          : 'border-l-transparent hover:bg-card/60'
      )}
      style={{ boxShadow: shadow, transition }}
    >
      <div className="flex flex-col px-4 py-3">
        <div className="flex items-center gap-2 w-full">
          {/* Home */}
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <TeamBadge team={home_team} />
            <span
              className={cn(
                'text-[12px] font-medium truncate transition-colors duration-150',
                isActive ? 'text-text' : 'text-[#C8CDD5] group-hover:text-text'
              )}
            >
              {home_team}
            </span>
          </div>

          <span className="shrink-0 font-mono text-[10px] text-sub/50 px-1">—</span>

          {/* Away */}
          <div className="flex items-center gap-2 flex-1 min-w-0 justify-end">
            <span
              className={cn(
                'text-[12px] font-medium truncate text-right transition-colors duration-150',
                isActive ? 'text-text' : 'text-[#C8CDD5] group-hover:text-text'
              )}
            >
              {away_team}
            </span>
            <TeamBadge team={away_team} />
          </div>
        </div>

        <span className="font-mono text-[10px] text-sub/50 mt-1 pl-7">
          {formatDate(date)}
        </span>
      </div>
    </button>
  )
}

function TeamBadge({ team }) {
  const abbr  = getAbbr(team)
  const color = getHue(team)

  return (
    <span
      className="shrink-0 w-[22px] h-[22px] rounded-full flex items-center justify-center font-mono text-[9px] font-semibold"
      style={{
        background: color + '22',
        border: `1px solid ${color}55`,
        color,
      }}
    >
      {abbr.slice(0, 2)}
    </span>
  )
}
