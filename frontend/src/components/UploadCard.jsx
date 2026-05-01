import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { Upload, ArrowUpRight } from 'lucide-react'

export default function UploadCard({ onImageSelected }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles?.[0]) {
      onImageSelected(acceptedFiles[0])
    }
  }, [onImageSelected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    multiple: false
  })

  return (
    <div className="max-w-4xl mx-auto py-12 text-center">

      <h2 className="text-5xl md:text-6xl font-bold text-white mb-8 tracking-tighter leading-tight">
        May these pixels guide <br /> you on your path
      </h2>

      <div {...getRootProps()} className="mb-12 cursor-pointer group">
        <input {...getInputProps()} />
        <div className="flex flex-col md:flex-row items-center justify-center gap-4">
          <button className="bg-[#e5e5e5] hover:bg-white text-black font-bold py-3.5 px-10 rounded-xl transition-all flex items-center gap-2">
            Get started
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
        
        <p className="mt-8 text-xs font-medium text-white/30 group-hover:text-white/60 transition-colors uppercase tracking-[0.2em]">
          Drop an image to start reconstruction
        </p>
      </div>

      <div className="grid grid-cols-3 gap-1 px-8 max-w-xl mx-auto opacity-20">
        <div className="h-[1px] bg-white" />
        <div className="h-[1px] bg-white" />
        <div className="h-[1px] bg-white" />
      </div>
    </div>
  )
}
