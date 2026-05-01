import React from 'react'
import { motion } from 'framer-motion'

export default function ProcessingOverlay({ progress }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="glass-panel p-6"
    >
      <div className="flex items-center gap-4">
        {/* Animated spinner */}
        <div className="relative w-10 h-10">
          <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
            <circle
              cx="18" cy="18" r="15"
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="3"
            />
            <motion.circle
              cx="18" cy="18" r="15"
              fill="none"
              stroke="url(#progress-grad)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray="94.2"
              animate={{ strokeDashoffset: 94.2 - (94.2 * progress) / 100 }}
              transition={{ duration: 0.3 }}
            />
            <defs>
              <linearGradient id="progress-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#a78bfa" />
              </linearGradient>
            </defs>
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-semibold text-indigo-400">
            {Math.round(progress)}
          </span>
        </div>

        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Processing image...</span>
            <span className="text-xs text-slate-500 font-mono">
              {Math.round(progress)}%
            </span>
          </div>

          {/* Progress bar */}
          <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
            <motion.div
              className="h-full rounded-full progress-bar-fill"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          <div className="mt-2 flex gap-4 text-xs text-slate-600">
            <motion.span
              animate={{ opacity: progress > 5 ? 1 : 0.3 }}
            >
              Gradient detection
            </motion.span>
            <motion.span
              animate={{ opacity: progress > 30 ? 1 : 0.3 }}
            >
              Edge classification
            </motion.span>
            <motion.span
              animate={{ opacity: progress > 60 ? 1 : 0.3 }}
            >
              Adaptive interpolation
            </motion.span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
