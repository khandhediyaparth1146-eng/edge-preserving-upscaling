import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster, toast } from 'react-hot-toast'
import Header from './components/Header'
import UploadCard from './components/UploadCard'
import ControlPanel from './components/ControlPanel'
import ComparisonViewer from './components/ComparisonViewer'
import ProcessingOverlay from './components/ProcessingOverlay'
import LightRays from './components/LightRays'
import LandingPage from './components/LandingPage'
import Footer from './components/Footer'
import { useUpscale } from './hooks/useUpscale'

export default function App() {
  const [user, setUser] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [sourceUrl, setSourceUrl] = useState(null)
  const { 
    processImage, 
    upscaledUrl, 
    heatmapUrl,
    processing, 
    analyzing,
    progress, 
    metadata, 
    reset 
  } = useUpscale()

  const handleImageSelected = (file) => {
    setSelectedImage(file)
    const url = URL.createObjectURL(file)
    setSourceUrl(url)
  }

  const handleUpscale = () => {
    if (selectedImage) {
      processImage(selectedImage, 4)
    }
  }

  const handleClear = () => {
    reset()
    setSelectedImage(null)
    setSourceUrl(null)
  }

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    if (savedUser && token) {
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const handleAuthSuccess = (userData, token) => {
    setUser(userData)
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('token', token)
    toast.success('Successfully authenticated!')
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    handleClear()
    toast.success('Logged out')
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <Toaster 
        position="top-right"
        toastOptions={{
          style: { background: '#121212', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }
        }}
      />

      <AnimatePresence mode="wait">
        {!user ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <LandingPage onAuthSuccess={handleAuthSuccess} />
          </motion.div>
        ) : (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, scale: 1.05 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="min-h-screen flex flex-col relative overflow-hidden"
          >
            {/* Background Layer */}
            <div className="noise-overlay" />
            <div className="fixed inset-0 pointer-events-none z-0">
              <div className="absolute inset-0 z-0">
                <LightRays
                  raysOrigin="top-center"
                  raysColor="#ffffff"
                  raysSpeed={0.5}
                  lightSpread={1.0}
                  rayLength={1.5}
                  pulsating={true}
                  followMouse={true}
                  mouseInfluence={0.1}
                  noiseAmount={0.1}
                  distortion={0.05}
                />
              </div>
              <div className="neon-ring !border-white/5 opacity-10" />
            </div>

            <div className="relative z-10 flex flex-col min-h-screen">
              <Header 
                user={user} 
                onLogout={handleLogout} 
              />

              <main className="flex-grow container mx-auto px-8 max-w-6xl py-8">
                <AnimatePresence mode="wait">
                  {!selectedImage ? (
                    <motion.div
                      key="upload"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                    >
                      <UploadCard onImageSelected={handleImageSelected} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="workspace"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-8"
                    >
                      <ComparisonViewer 
                        sourceUrl={sourceUrl}
                        upscaledUrl={upscaledUrl}
                        heatmapUrl={heatmapUrl}
                        processing={processing}
                        analyzing={analyzing}
                      />
                      
                      <ControlPanel 
                        onUpscale={handleUpscale}
                        onClear={handleClear}
                        processing={processing}
                        analyzing={analyzing}
                        hasResult={!!upscaledUrl}
                        upscaledUrl={upscaledUrl}
                        metadata={metadata}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </main>

              <Footer />
            </div>

            {processing && <ProcessingOverlay progress={progress} />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
