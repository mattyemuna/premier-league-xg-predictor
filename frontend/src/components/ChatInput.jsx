import { useState, useRef, useEffect } from 'react'
import { ArrowUp } from 'lucide-react'

export default function ChatInput({ onSend, isLoading }) {
  const [input, setInput] = useState('')
  const textareaRef       = useRef(null)

  const resize = (el) => {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }

  const handleChange = (e) => {
    setInput(e.target.value)
    resize(e.target)
  }

  const submit = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  // Re-focus after send
  useEffect(() => {
    if (!isLoading) textareaRef.current?.focus()
  }, [isLoading])

  const canSend = input.trim().length > 0 && !isLoading

  return (
    <div className="flex-shrink-0 border-t border-rim bg-base/90 backdrop-blur-sm p-3">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Type a matchup…"
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-card border border-rim rounded-xl px-4 py-2.5 text-[13px] text-text placeholder-sub/40 resize-none focus:outline-none focus:border-accent/40 transition-colors duration-150 disabled:opacity-50 leading-relaxed font-sans"
          style={{ minHeight: '40px', maxHeight: '120px' }}
        />
        <button
          onClick={submit}
          disabled={!canSend}
          aria-label="Send"
          className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150 cursor-pointer disabled:opacity-25 disabled:cursor-not-allowed bg-accent hover:bg-[#0DC98A] active:scale-95"
        >
          <ArrowUp size={15} className="text-base stroke-[2.5]" />
        </button>
      </div>

      <p className="text-center font-mono text-[10px] text-sub/30 mt-2 tracking-wide">
        xG · Elo · 5 seasons
      </p>
    </div>
  )
}
