// Aceternity-inspired blueprint grid: subtle dot matrix + hairline frame + corner registration marks
export default function BackgroundGrid() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
      {/* Dot matrix */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(38,42,51,0.9) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* Radial vignette — fades dots at edges so content stays readable */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 75% 65% at 50% 50%, transparent 20%, rgba(13,14,18,0.55) 100%)',
        }}
      />

      {/* Hairline outer frame */}
      <div
        className="absolute"
        style={{
          inset: '20px',
          border: '1px solid rgba(38,42,51,0.45)',
          borderRadius: '2px',
        }}
      />

      {/* Corner registration marks */}
      <Corner style={{ top: 20, left: 20 }} rotate={0}   />
      <Corner style={{ top: 20, right: 20 }} rotate={90} />
      <Corner style={{ bottom: 20, right: 20 }} rotate={180} />
      <Corner style={{ bottom: 20, left: 20 }} rotate={270} />
    </div>
  )
}

function Corner({ style, rotate }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      style={{
        position: 'absolute',
        ...style,
        transform: `rotate(${rotate}deg)`,
        transformOrigin: 'center',
        color: 'rgba(38,42,51,0.85)',
      }}
    >
      {/* L-bracket */}
      <path d="M1 8 L1 1 L8 1" stroke="currentColor" strokeWidth="0.9" />
      {/* Crosshair ticks */}
      <line x1="1" y1="10" x2="1" y2="12" stroke="currentColor" strokeWidth="0.6" />
      <line x1="10" y1="1" x2="12" y2="1" stroke="currentColor" strokeWidth="0.6" />
    </svg>
  )
}
