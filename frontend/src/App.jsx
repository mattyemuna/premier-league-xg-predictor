import { useState } from 'react'
import BackgroundGrid from './effects/BackgroundGrid'
import Header from './components/Header'
import FixturesPanel from './components/FixturesPanel'
import ChatPanel from './components/ChatPanel'

const API_BASE = 'http://localhost:8000'

export default function App() {
  // 'upcoming' | 2021 | 2022 | 2023 | 2024 | 2025
  const [season, setSeason]                 = useState('upcoming')
  const [pendingFixture, setPendingFixture] = useState(null)

  return (
    <div className="relative flex flex-col h-full bg-base overflow-hidden">
      <BackgroundGrid />

      <div className="relative z-10 flex flex-col h-full">
        <Header season={season} onSeasonChange={setSeason} />

        <div className="flex flex-1 overflow-hidden">
          {/* Left — Fixtures 38% */}
          <div className="w-[38%] flex flex-col border-r border-rim overflow-hidden bg-panel/50">
            <FixturesPanel
              apiBase={API_BASE}
              season={season}
              onFixtureSelect={setPendingFixture}
            />
          </div>

          {/* Right — Chat 62% */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <ChatPanel
              apiBase={API_BASE}
              pendingFixture={pendingFixture}
              onFixtureConsumed={() => setPendingFixture(null)}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
