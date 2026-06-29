import { motion } from 'framer-motion'

const HISTORICAL_SEASONS = [2025, 2024, 2023, 2022, 2021]

export default function Header({ season, onSeasonChange }) {
  return (
    <header className="flex-shrink-0 flex items-center justify-between px-5 h-10 border-b border-rim bg-base/90 backdrop-blur-sm z-20">
      {/* Left — live pulse + season selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <motion.span
            className="block w-1.5 h-1.5 rounded-full bg-accent"
            animate={{ opacity: [1, 0.25, 1] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
          />
          <span className="font-mono text-[10px] tracking-widest text-sub uppercase">
            Live
          </span>
        </div>

        <select
          value={String(season)}
          onChange={e => {
            const v = e.target.value
            onSeasonChange(v === 'upcoming' ? 'upcoming' : Number(v))
          }}
          className="bg-card border border-rim text-text text-[11px] font-mono rounded px-2 py-1 focus:outline-none focus:border-accent/40 cursor-pointer appearance-none"
        >
          <option value="upcoming">Upcoming 2026/27</option>
          {HISTORICAL_SEASONS.map(s => (
            <option key={s} value={String(s)}>
              {s}/{String(s + 1).slice(2)}
            </option>
          ))}
        </select>
      </div>

      {/* Right — minimal competition label */}
      <div className="flex items-center gap-3">
        <span className="font-mono text-[11px] tracking-[0.18em] text-sub uppercase select-none">
          EN · PL
        </span>
        <span className="w-px h-3 bg-rim" />
        <span className="font-mono text-[10px] tracking-widest text-sub/50 uppercase select-none">
          xG Model
        </span>
      </div>
    </header>
  )
}
