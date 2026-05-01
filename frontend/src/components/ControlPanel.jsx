import React from 'react'
import { motion } from 'framer-motion'
import { Zap, RotateCcw, Download } from 'lucide-react'

export default function ControlPanel({
  onUpscale,
  onClear,
  processing,
  hasResult,
  upscaledUrl,
  metadata,
}) {
  const handleDownload = () => {
    if (!upscaledUrl) return
    const a = document.createElement('a')
    a.href = upscaledUrl
    a.download = `reconstructed_4x.png`
    a.click()
  }

  return (
    <div className="pro-card p-4 mt-8 flex flex-col md:flex-row items-center justify-between gap-4 max-w-4xl mx-auto border-white/5 bg-white/[0.02]">
      <div className="flex items-center gap-6 px-2">
        <div className="flex items-center gap-3">
          <div className={`w-1.5 h-1.5 rounded-full ${hasResult ? 'bg-white' : 'bg-white/20'}`} />
          <span className="text-[11px] font-bold text-white/40 uppercase tracking-widest">
            {hasResult ? 'Upscale Complete' : 'System Ready'}
          </span>
        </div>
        
        {metadata && (
          <div className="flex items-center gap-6 border-l border-white/10 pl-6">
            <div className="flex flex-col">
              <span className="text-[8px] text-white/30 uppercase font-black tracking-widest">PSNR</span>
              <span className="text-xs font-bold text-white/90">{metadata.psnr} dB</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[8px] text-white/30 uppercase font-black tracking-widest">SSIM</span>
              <span className="text-xs font-bold text-white/90">{metadata.ssim}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[8px] text-white/30 uppercase font-black tracking-widest">Latency</span>
              <span className="text-xs font-bold text-white/90">{parseFloat(metadata.processingTime).toFixed(0)}ms</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onClear}
          className="p-3 text-white/30 hover:text-white transition-colors"
          title="Reset"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {hasResult ? (
          <button
            onClick={handleDownload}
            className="bg-white text-black text-[11px] font-black px-8 py-2.5 rounded-lg hover:bg-gray-200 transition-all uppercase tracking-tight"
          >
            <Download className="w-3.5 h-3.5 inline mr-2" />
            Download 4X
          </button>
        ) : (
          <button
            onClick={onUpscale}
            disabled={processing}
            className="bg-white/10 border border-white/20 text-white text-[11px] font-black px-10 py-2.5 rounded-lg hover:bg-white/20 transition-all uppercase tracking-tight disabled:opacity-30"
          >
            {processing ? 'Processing...' : 'Run Engine'}
          </button>
        )}
      </div>
    </div>
  )
}
