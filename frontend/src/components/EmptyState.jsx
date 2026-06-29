const SUGGESTIONS = [
  'Arsenal vs Manchester City',
  'Liverpool vs Chelsea',
  'Tottenham vs Newcastle United',
  'Brighton vs Aston Villa',
]

export default function EmptyState({ onSuggestion }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 text-center select-none">
      {/* Crosshair — consistent with blueprint grid aesthetic */}
      <div className="mb-5 opacity-25">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <circle cx="14" cy="14" r="4"  stroke="#F4F5F7" strokeWidth="0.9"/>
          <line x1="14" y1="1"  x2="14" y2="9"  stroke="#F4F5F7" strokeWidth="0.9"/>
          <line x1="14" y1="19" x2="14" y2="27" stroke="#F4F5F7" strokeWidth="0.9"/>
          <line x1="1"  y1="14" x2="9"  y2="14" stroke="#F4F5F7" strokeWidth="0.9"/>
          <line x1="19" y1="14" x2="27" y2="14" stroke="#F4F5F7" strokeWidth="0.9"/>
        </svg>
      </div>

      <p className="text-[12px] text-sub leading-relaxed max-w-[230px]">
        Select a fixture to load its xG projection, or type any matchup below.
      </p>

      <div className="mt-5 flex flex-col gap-1.5 w-full max-w-[290px]">
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => onSuggestion(s)}
            className="text-left px-3.5 py-2.5 rounded-lg bg-card border border-rim text-[11px] text-sub hover:border-accent/30 hover:text-text transition-colors duration-150 cursor-pointer font-mono"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
