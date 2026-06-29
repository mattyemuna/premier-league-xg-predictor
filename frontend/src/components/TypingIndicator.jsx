import { motion } from 'framer-motion'

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className="flex items-center gap-1.5 py-1"
    >
      {[0, 0.18, 0.36].map((delay, i) => (
        <motion.span
          key={i}
          className="block w-1 h-1 rounded-full bg-sub"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.2, repeat: Infinity, delay, ease: 'easeInOut' }}
        />
      ))}
    </motion.div>
  )
}
