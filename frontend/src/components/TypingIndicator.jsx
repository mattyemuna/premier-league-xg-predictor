import { motion } from 'framer-motion'

export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        style={{
          background: '#1C1F26',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '18px 18px 18px 4px',
          padding: '10px 14px',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        {[0, 0.18, 0.36].map((delay, i) => (
          <motion.span
            key={i}
            style={{
              display: 'block',
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#10E0A0',
            }}
            animate={{ y: [0, -4, 0], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.1, repeat: Infinity, delay, ease: 'easeInOut' }}
          />
        ))}
      </motion.div>
    </div>
  )
}
