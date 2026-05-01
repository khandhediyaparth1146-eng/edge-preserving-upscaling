# Real-Time Edge-Preserving Image Upscaling Engine

A high-performance image reconstruction system featuring a custom **CUDA kernel** and an optimized **NumPy-vectorized CPU fallback**. This project provides research-grade adaptive upscaling (up to 4x) that preserves sharp edges and enhances micro-textures, delivering superior visual fidelity compared to standard interpolation methods.

---

## 🚀 Key Features

This project implements several advanced Computer Vision techniques to achieve state-of-the-art upscaling quality:

1.  **Lanczos4 Upscaling Engine:** Beyond standard bicubic, we utilize a high-order Lanczos4 kernel (64-pixel window) to achieve superior initial sharpness and significantly reduced aliasing.
2.  **Scharr Gradient Intelligence:** High-precision edge detection using Scharr operators for superior derivative approximation, allowing the system to adaptively sharpen diagonal lines and fine details.
3.  **Bilateral Noise Suppression:** Intelligent "edge-aware" noise filtering that cleans up grainy regions while strictly maintaining the integrity of sharp boundaries.
4.  **CLAHE Detail Enhancement:** Integrated Contrast Limited Adaptive Histogram Equalization to pop micro-textures and local contrast, providing a high-definition perceptual output.
5.  **Sigmoid-based Blending Logic:** Advanced blending using a mathematical Sigmoid transition to eliminate "halo" artifacts and ensure smooth transitions between edges and backgrounds.
6.  **Full-Stack Comparison Dashboard:** A live React/FastAPI interface for real-time testing, side-by-side evaluation, and performance metrics (PSNR/SSIM).

---

## 🛠️ Architecture

- **Frontend:** Premium UI built with **React**, **Tailwind CSS**, and **Framer Motion**.
- **Backend:** High-throughput **FastAPI** server with asynchronous image processing.
- **Engine:** Hybrid backend that detects hardware capabilities:
    - **CUDA:** Per-pixel adaptive kernel for NVIDIA GPUs.
    - **CPU Fallback:** Optimized NumPy/OpenCV pipeline for cross-platform support.

---

## ⚡ Setup & Installation

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Docker Deployment
```bash
# To run the full stack via Docker
docker compose -f docker/docker-compose.yml up --build
```

---

## 📊 Evaluation Results

The adaptive engine consistently outperforms standard bicubic interpolation in both perceptual quality and objective metrics (PSNR/SSIM), especially on high-contrast edges and complex textures.

---
*Developed as part of a High-Performance Computing Research Project.*
