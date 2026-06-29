import { cn } from '../lib/utils'
import { getAbbr, getHue, formatDate } from '../lib/teams'

export default function FixtureRow({ fixture, isActive, onClick }) {
  const { home_team, away_team, date } = fixture

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left flex flex-col px-4 py-3 border-b border-[#1C1F26] border-l-2 transition-colors duration-150 cursor-pointer group',
        isActive
          ? 'border-l-accent bg-card'
          : 'border-l-transparent hover:bg-card/60'
      )}
    >
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

        {/* vs */}
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

      {/* Date */}
      <span className="font-mono text-[10px] text-sub/50 mt-1 pl-7">
        {formatDate(date)}
      </span>
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
