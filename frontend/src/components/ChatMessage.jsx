import { motion } from 'framer-motion'
import PredictionCard from './PredictionCard'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.15 }}
        className="flex justify-end"
      >
        <div className="max-w-[72%] px-4 py-2.5 rounded-xl rounded-br-sm bg-card border border-rim text-[13px] text-text leading-relaxed">
          {message.content}
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex gap-2.5"
    >
      {/* Accent dot — subtle indicator, no persona name */}
      <div className="shrink-0 mt-1">
        <span className="block w-1.5 h-1.5 rounded-full bg-accent/70 mt-1" />
      </div>

      <div className="flex-1 min-w-0 space-y-3">
        <p className="text-[13px] text-[#C8CDD5] leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {message.prediction && (
          <PredictionCard prediction={message.prediction} />
        )}
      </div>
    </motion.div>
  )
}
