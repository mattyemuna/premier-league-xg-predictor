import { useState, useEffect, useRef, useCallback } from 'react'
import ChatMessage from './ChatMessage'
import TypingIndicator from './TypingIndicator'
import ChatInput from './ChatInput'
import EmptyState from './EmptyState'

export default function ChatPanel({ apiBase, pendingFixture, onFixtureConsumed }) {
  const [messages, setMessages]   = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef                 = useRef(null)
  const messagesRef               = useRef([])
  const sendRef                   = useRef(null)

  // Keep ref in sync so pendingFixture effect doesn't need sendMessage in deps
  useEffect(() => { messagesRef.current = messages }, [messages])

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: trimmed }])
    setIsLoading(true)

    try {
      const history = messagesRef.current.map(m => ({ role: m.role, content: m.content }))
      const res = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history }),
      })
      if (!res.ok) throw new Error(`${res.status}`)
      const data = await res.json()
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: 'assistant', content: data.reply, prediction: data.prediction ?? null },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: 'assistant', content: `Connection error — ${err.message}. Is the backend running on port 8000?`, prediction: null },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, apiBase])

  // Keep sendRef current so the pending fixture effect always sees the latest sendMessage
  useEffect(() => { sendRef.current = sendMessage }, [sendMessage])

  // Consume fixture clicks from the left panel
  useEffect(() => {
    if (!pendingFixture) return
    const msg = `Predict ${pendingFixture.home_team} vs ${pendingFixture.away_team}`
    sendRef.current?.(msg)
    onFixtureConsumed()
  }, [pendingFixture, onFixtureConsumed])

  const isEmpty = messages.length === 0 && !isLoading

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable message area */}
      <div className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <div className="h-full">
            <EmptyState onSuggestion={sendMessage} />
          </div>
        ) : (
          <div className="px-5 py-5 flex flex-col gap-5">
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
