import React from 'react'
import { Github, ExternalLink } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-500">EdgeBicubic</span>
          <span>|</span>
          <span>Real-Time Edge-Preserving Bicubic Interpolation</span>
        </div>
        <div className="flex items-center gap-4">
          <span>CUDA-Accelerated</span>
          <span className="w-1 h-1 rounded-full bg-slate-700" />
          <span>Research-Grade Implementation</span>
        </div>
      </div>
    </footer>
  )
}
