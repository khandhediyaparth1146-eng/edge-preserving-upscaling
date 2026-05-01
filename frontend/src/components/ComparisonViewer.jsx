import React, { useState } from 'react'
import ReactCompareImage from 'react-compare-image'
import { motion, AnimatePresence } from 'framer-motion'
import { Maximize2, Zap, Activity } from 'lucide-react'

export default function ComparisonViewer({ sourceUrl, upscaledUrl, heatmapUrl, processing, analyzing }) {
  const [showHeatmap, setShowHeatmap] = useState(false)

  if (processing) {
    return (
      <div className="w-full aspect-video bg-white/[0.02] border border-white/5 rounded-[2.5rem] flex flex-col items-center justify-center max-w-4xl mx-auto overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-20" />
        <div className="w-10 h-10 border-2 border-white/5 border-t-white rounded-full animate-spin mb-4 relative z-10" />
        <p className="text-[10px] text-white/50 font-black uppercase tracking-[0.4em] relative z-10">Reconstructing Edge Gradients</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pt-4">
      <div className="flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <Activity className="w-4 h-4 text-white/40" />
          <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.5em]">Neural Benchmarking</h3>
        </div>

        {upscaledUrl && heatmapUrl && (
          <button 
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full border transition-all ${
              showHeatmap 
                ? 'bg-white text-black border-white' 
                : 'bg-white/5 text-white/40 border-white/10 hover:border-white/30'
            }`}
          >
            <Zap className={`w-3 h-3 ${showHeatmap ? 'fill-black' : ''}`} />
            <span className="text-[9px] font-black uppercase tracking-widest">
              {showHeatmap ? 'Hide Edge Map' : 'Show Edge Map'}
            </span>
          </button>
        )}
      </div>

      <div className="pro-card p-3 bg-white/[0.01] border-white/5 rounded-[2.5rem] overflow-hidden relative">
        <div className="rounded-[2rem] overflow-hidden relative">
          <AnimatePresence mode="wait">
            {showHeatmap && heatmapUrl ? (
              <motion.div
                key="heatmap"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="w-full"
              >
                <img src={heatmapUrl} alt="Edge Heatmap" className="w-full h-auto rounded-[2rem]" />
                <div className="absolute bottom-6 left-6 px-4 py-2 bg-black/80 backdrop-blur-md rounded-xl border border-white/10">
                  <p className="text-[9px] font-black text-white uppercase tracking-widest">X-Ray: Edge Intensity Map</p>
                </div>
              </motion.div>
            ) : upscaledUrl ? (
              <motion.div
                key="compare"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-full"
              >
                <ReactCompareImage
                  leftImage={sourceUrl}
                  rightImage={upscaledUrl}
                  leftImageLabel="BEFORE"
                  rightImageLabel="AFTER"
                  sliderLineColor="white"
                  handleSize={40}
                  sliderLineWidth={2}
                />
              </motion.div>
            ) : sourceUrl ? (
              <motion.div
                key="preview"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-full flex items-center justify-center p-4"
              >
                <img 
                  src={sourceUrl} 
                  alt="Source Preview" 
                  className="max-w-full h-auto rounded-2xl shadow-2xl border border-white/10" 
                />
                <div className="absolute top-6 right-6 px-4 py-2 bg-white/10 backdrop-blur-xl rounded-full border border-white/20">
                  <p className="text-[10px] font-black text-white uppercase tracking-widest">Ready for Reconstruction</p>
                </div>
              </motion.div>
            ) : (
              <div className="w-full aspect-video bg-white/[0.01] flex items-center justify-center border border-dashed border-white/5 rounded-[2rem]">
                <div className="flex flex-col items-center gap-4">
                  <Maximize2 className="w-6 h-6 text-white/5" />
                  <div className="text-white/10 font-black uppercase tracking-[0.5em] text-[10px]">Processing Core Idle</div>
                </div>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
