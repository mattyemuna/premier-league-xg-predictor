import { useState, useEffect, useRef } from 'react'
import { cn } from '../lib/utils'
import FixtureRow from './FixtureRow'

export default function FixturesPanel({ apiBase, season, onFixtureSelect }) {
  // matchdays is an object keyed by string: { "1": [{...},...], "2": [...], ... }
  const [matchdays, setMatchdays]   = useState({})
  // selectedMD is always a STRING key
  const [selectedMD, setSelectedMD] = useState(null)
  const [activeKey, setActiveKey]   = useState(null)
  const [isLoading, setIsLoading]   = useState(false)
  const [error, setError]           = useState(null)
  const tabsRef                     = useRef(null)

  useEffect(() => {
    setIsLoading(true)
    setError(null)
    setMatchdays({})
    setSelectedMD(null)

    const url = season === 'upcoming'
      ? `${apiBase}/upcoming-fixtures`
      : `${apiBase}/fixtures?season=${season}`

    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        // /upcoming-fixtures → data.matchdays; /fixtures → data.matchweeks
        const md = data.matchdays ?? data.matchweeks ?? {}
        setMatchdays(md)
        const sorted = Object.keys(md).sort((a, b) => Number(a) - Number(b))
        setSelectedMD(sorted[0] ?? null)
        setActiveKey(null)
      })
      .catch(e => setError(e.message))
      .finally(() => setIsLoading(false))
  }, [apiBase, season])

  const mdKeys   = Object.keys(matchdays).sort((a, b) => Number(a) - Number(b))
  const fixtures = (selectedMD && Array.isArray(matchdays[selectedMD]))
    ? matchdays[selectedMD]
    : []

  const panelLabel = season === 'upcoming'
    ? 'Fixtures · 2026/27'
    : `Fixtures · ${season}`

  const handleSelect = (fixture) => {
    const key = `${fixture.home_team}|${fixture.away_team}`
    setActiveKey(key)
    onFixtureSelect(fixture)
  }

  const handleTabClick = (mdKey) => {
    setSelectedMD(mdKey)
    const el = tabsRef.current?.querySelector(`[data-md="${mdKey}"]`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Panel label */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2.5 border-b border-rim">
        <span className="font-mono text-[10px] tracking-[0.18em] text-sub uppercase">
          {panelLabel}
        </span>
        {mdKeys.length > 0 && (
          <span className="font-mono text-[10px] text-sub/40">
            {mdKeys.length} GW
          </span>
        )}
      </div>

      {/* Matchday tabs — horizontally scrollable */}
      <div
        ref={tabsRef}
        className="flex-shrink-0 flex overflow-x-auto no-scrollbar border-b border-rim bg-base/60"
      >
        {mdKeys.map(mdKey => (
          <button
            key={mdKey}
            data-md={mdKey}
            onClick={() => handleTabClick(mdKey)}
            className={cn(
              'shrink-0 px-3 py-2 font-mono text-[10px] tracking-wider transition-colors duration-150 border-b-2 cursor-pointer whitespace-nowrap',
              selectedMD === mdKey
                ? 'text-accent border-accent'
                : 'text-sub border-transparent hover:text-text'
            )}
          >
            GW{mdKey}
          </button>
        ))}
      </div>

      {/* Fixture list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center h-24">
            <span className="font-mono text-[11px] text-sub/60">Loading…</span>
          </div>
        )}

        {!isLoading && error && (
          <div className="flex items-center justify-center h-24 px-4 text-center">
            <span className="font-mono text-[11px] text-sub/60">
              {error} — is the backend running?
            </span>
          </div>
        )}

        {!isLoading && !error && fixtures.map((f, i) => {
          const rowKey = `${f.home_team}|${f.away_team}`
          return (
            <FixtureRow
              key={i}
              fixture={f}
              isActive={activeKey === rowKey}
              onClick={() => handleSelect(f)}
            />
          )
        })}
      </div>
    </div>
  )
}
