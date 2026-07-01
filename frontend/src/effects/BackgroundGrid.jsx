import { useRef, useEffect } from 'react'

const SPACING  = 24
const R_BASE   = 1.0
const R_PEAK   = 2.2
const GLOW_R   = 180
const TWO_PI   = Math.PI * 2

// Base dot: rgba(38,42,51,0.9)  →  Accent: #10E0A0
const BASE = { r: 38,  g: 42,  b: 51  }
const PEAK = { r: 16,  g: 224, b: 160 }

export default function BackgroundGrid() {
  const canvasRef = useRef(null)
  const mouseRef  = useRef({ x: -9999, y: -9999 })
  const dimsRef   = useRef({ w: 0, h: 0 })
  const rafRef    = useRef(null)

  useEffect(() => {
    const mq      = window.matchMedia('(prefers-reduced-motion: reduce)')
    const reduced = mq.matches

    const canvas = canvasRef.current
    const ctx    = canvas.getContext('2d')
    const dpr    = window.devicePixelRatio || 1

    const resize = () => {
      const w = window.innerWidth
      const h = window.innerHeight
      dimsRef.current = { w, h }
      // Assigning width/height resets the canvas context (including transform),
      // so we always re-apply the DPR scale immediately after.
      canvas.width         = w * dpr
      canvas.height        = h * dpr
      canvas.style.width   = w + 'px'
      canvas.style.height  = h + 'px'
      ctx.scale(dpr, dpr)
    }
    resize()

    const onMouse = (e) => { mouseRef.current = { x: e.clientX, y: e.clientY } }
    if (!reduced) window.addEventListener('mousemove', onMouse, { passive: true })
    window.addEventListener('resize', resize)

    const GR_SQ = GLOW_R * GLOW_R

    const draw = () => {
      const { w, h } = dimsRef.current
      ctx.clearRect(0, 0, w, h)

      // Pass 1 — all dots at base size/color in one batch
      ctx.fillStyle = `rgba(${BASE.r},${BASE.g},${BASE.b},0.9)`
      for (let gx = SPACING; gx < w; gx += SPACING) {
        for (let gy = SPACING; gy < h; gy += SPACING) {
          ctx.beginPath()
          ctx.arc(gx, gy, R_BASE, 0, TWO_PI)
          ctx.fill()
        }
      }

      // Pass 2 — overdraw only the dots inside the glow radius with accent color
      if (!reduced) {
        const { x: mx, y: my } = mouseRef.current
        const xs = Math.ceil(Math.max(SPACING, mx - GLOW_R) / SPACING) * SPACING
        const xe = Math.floor(Math.min(w - 1, mx + GLOW_R) / SPACING) * SPACING
        const ys = Math.ceil(Math.max(SPACING, my - GLOW_R) / SPACING) * SPACING
        const ye = Math.floor(Math.min(h - 1, my + GLOW_R) / SPACING) * SPACING

        for (let gx = xs; gx <= xe; gx += SPACING) {
          for (let gy = ys; gy <= ye; gy += SPACING) {
            const dx  = gx - mx
            const dy  = gy - my
            const dSq = dx * dx + dy * dy
            if (dSq >= GR_SQ) continue

            const t  = 1 - Math.sqrt(dSq) / GLOW_R
            const t2 = t * t   // quadratic falloff — sharper centre, soft edge
            const r  = Math.round(BASE.r + (PEAK.r - BASE.r) * t2)
            const g  = Math.round(BASE.g + (PEAK.g - BASE.g) * t2)
            const b  = Math.round(BASE.b + (PEAK.b - BASE.b) * t2)
            ctx.beginPath()
            ctx.arc(gx, gy, R_BASE + (R_PEAK - R_BASE) * t2, 0, TWO_PI)
            ctx.fillStyle = `rgba(${r},${g},${b},0.9)`
            ctx.fill()
          }
        }
      }

      rafRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(rafRef.current)
      if (!reduced) window.removeEventListener('mousemove', onMouse)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
      <canvas ref={canvasRef} className="absolute inset-0" />

      {/* Radial vignette — fades dots toward edges so content stays readable */}
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
      <Corner style={{ top: 20, left: 20 }}     rotate={0}   />
      <Corner style={{ top: 20, right: 20 }}    rotate={90}  />
      <Corner style={{ bottom: 20, right: 20 }} rotate={180} />
      <Corner style={{ bottom: 20, left: 20 }}  rotate={270} />
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
      <path d="M1 8 L1 1 L8 1" stroke="currentColor" strokeWidth="0.9" />
      <line x1="1" y1="10" x2="1" y2="12" stroke="currentColor" strokeWidth="0.6" />
      <line x1="10" y1="1" x2="12" y2="1" stroke="currentColor" strokeWidth="0.6" />
    </svg>
  )
}
