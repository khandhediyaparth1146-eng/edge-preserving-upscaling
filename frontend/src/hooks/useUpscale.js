import { useState, useCallback, useRef } from 'react'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export function useUpscale() {
  const [upscaledUrl, setUpscaledUrl] = useState(null)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [metadata, setMetadata] = useState(null)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const [heatmapUrl, setHeatmapUrl] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  const reset = useCallback(() => {
    if (upscaledUrl) URL.revokeObjectURL(upscaledUrl)
    if (heatmapUrl) URL.revokeObjectURL(heatmapUrl)
    setUpscaledUrl(null)
    setHeatmapUrl(null)
    setProcessing(false)
    setAnalyzing(false)
    setProgress(0)
    setMetadata(null)
    setError(null)
  }, [upscaledUrl, heatmapUrl])

  const analyzeImage = useCallback(async (file) => {
    setAnalyzing(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        body: formData
      })
      if (!res.ok) throw new Error('Analysis failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setHeatmapUrl(url)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setAnalyzing(false)
    }
  }, [])

  const processImage = useCallback(async (file, scale) => {
    reset()
    setProcessing(true)
    setProgress(0)
    setError(null)
    
    // Automatically trigger analysis too
    analyzeImage(file)

    // simulate progress snappily
    let p = 0
    intervalRef.current = setInterval(() => {
      p += Math.random() * 15 + 5
      if (p > 95) p = 95
      setProgress(p)
    }, 50)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(
        `${API_BASE}/upscale?scale=${scale}&method=adaptive&output_format=png`,
        { method: 'POST', body: formData }
      )

      clearInterval(intervalRef.current)

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Server error (${res.status})`)
      }

      setProgress(95)

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)

      const meta = {
        processingTime: res.headers.get('X-Processing-Time-Ms'),
        kernelTime: res.headers.get('X-Kernel-Time-Ms'),
        backend: res.headers.get('X-Backend'),
        method: res.headers.get('X-Method'),
        sourceSize: res.headers.get('X-Source-Size'),
        outputSize: res.headers.get('X-Output-Size'),
        psnr: res.headers.get('X-PSNR'),
        ssim: res.headers.get('X-SSIM'),
      }

      setUpscaledUrl(url)
      setMetadata(meta)
      setProgress(100)
      toast.success(
        `Upscaled to ${meta.outputSize} in ${parseFloat(meta.processingTime).toFixed(0)}ms`
      )
    } catch (err) {
      clearInterval(intervalRef.current)
      setError(err.message)
      toast.error(`Upscale failed: ${err.message}`)
    } finally {
      setProcessing(false)
    }
  }, [reset])

  return {
    upscaledUrl,
    heatmapUrl,
    processing,
    analyzing,
    progress,
    metadata,
    error,
    processImage,
    analyzeImage,
    reset,
  }
}
