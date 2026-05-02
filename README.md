# EDGE GEN: Edge-Preserving Image Reconstruction Platform 🔬🎨

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/khandhediyaparth1146-eng/edge-preserving-upscaling)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/khandhediyaparth1146-eng/edge-preserving-upscaling&root-directory=frontend&env=VITE_API_URL)

**EDGE GEN** is a high-precision, research-grade image upscaling engine featuring a Golden Standard Laplacian Pyramid synthesis model. It implements advanced structural preservation techniques, including Fast Guided Filtering and Iterative Back-Projection (IBP).

## 🚀 One-Click Deployment
1. **Backend:** Click the **Deploy to Render** button above.
2. **Frontend:** Click the **Deploy with Vercel** button above.

---

## 📂 Project Structure

```bash
├── backend/            # FastAPI Server & Python Core
│   ├── core/           # Golden Standard Upscale Engine
│   └── main.py         # API Endpoints
├── frontend/           # React + Vite Dashboard
│   ├── src/components/ # Dashboard UI Components
│   └── src/hooks/      # Upscale & Auth Hooks
├── cuda/               # High-Performance C++ Kernels
├── docs/               # Academic Research & Documentation
│   └── RESEARCH_PAPER.md
├── docker/             # Containerization Config
├── scripts/            # Evaluation & Testing Utilities
└── render.yaml         # Deployment Manifest
```

---

## 📊 Research & Methodology

The **Golden Standard** engine utilizes a Multi-Scale Laplacian Pyramid approach combined with Fast Guided Filtering and Iterative Back-Projection (IBP). For a deep dive into the mathematical formulations (PSNR, SSIM, MSE), please refer to the full **[Research Paper](docs/RESEARCH_PAPER.md)**.

---

## 🛠️ Local Development

### 1. Backend
```bash
cd backend && pip install -r requirements.txt && python main.py
```

### 2. Frontend
```bash
cd frontend && npm install && npm run dev
```

### 3. Docker
```bash
docker compose -f docker/docker-compose.yml up --build
```

---

## 📊 Evaluation Results

The adaptive engine consistently outperforms standard bicubic interpolation in both perceptual quality and objective metrics (PSNR/SSIM), especially on high-contrast edges and complex textures.

---
*Developed as part of a High-Performance Computing Research Project.*
