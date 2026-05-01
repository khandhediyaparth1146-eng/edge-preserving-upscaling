# Real-Time Edge-Preserving Image Upscaling Engine

**Author:** Khandhediya Parth  
**Date:** April 2026  
**Subject:** GPU-Accelerated Hybrid Image Processing

---

## Abstract
Image upscaling is a fundamental task in computer vision. Traditional interpolation methods often suffer from blurring across edges and ringing artifacts. In this paper, we propose a hybrid, real-time edge-preserving framework that combines **Iterative Back-Projection (IBP)** with **Anisotropic Gradient Refinement**. By integrating multi-stage cascaded upscaling and luminance-isolated processing in the LAB color space, the proposed algorithm significantly improves structural similarity (SSIM) and perceptual sharpness compared to standard bicubic methods.

---

## I. Introduction
With the rising demand for high-resolution displays, efficient image upscaling techniques are essential. While deep learning methods provide state-of-the-art results, they are computationally heavy. This research focuses on a hybrid mathematical model that achieves high accuracy with deterministic real-time performance.

---

## II. Methodology

### A. Cascaded Iterative Upscaling (1x → 2x → 4x)
To prevent the loss of structural integrity common in single-step 4x magnification, we implement a **dual-stage cascaded pipeline**. Each stage performs a 2x upscale followed by an intermediate **Bilateral Filter** to suppress artifacts before the subsequent magnification stage.

### B. Luminance-Isolated Refinement (LAB Space)
To avoid chromatic aberration and "color-bleeding" during sharpening, the image is transformed into the **CIE LAB color space**. Adaptive sharpening and **CLAHE (Contrast Limited Adaptive Histogram Equalization)** are applied exclusively to the **L-channel** (Lightness), ensuring that color information (A and B channels) remains untouched.

### C. Iterative Back-Projection (IBP) for Error Correction
We propose a "self-correcting" loop using **Iterative Back-Projection**. After the upscale ($I_{up}$), the image is downsampled ($I_{down}$) and compared to the original input ($I_{orig}$). The residual error is upscaled and added back to $I_{up}$ to ensure mathematical consistency:
$$I_{t+1} = I_t + \eta \cdot \text{Upscale}(I_{orig} - \text{Downscale}(I_t))$$

### D. Direction-Aware Anisotropic Sharpening
We employ **Scharr operators** for high-precision gradient calculation. A **Sigmoid-weighted mask** is used to blend a directional Laplacian sharpening filter with the upscaled base, ensuring sharp edges while maintaining smooth backgrounds.

---

## III. System Architecture
The system is implemented as a full-stack, dual-architecture solution:
1.  **CUDA Engine:** A per-pixel directional suppression algorithm for NVIDIA GPUs.
2.  **Advanced CPU Pipeline:** An iterative IBP-based fallback using NumPy vectorization and OpenCV's C-compiled backends.
3.  **FastAPI/React Stack:** A live dashboard for real-time comparative analysis.

---

## IV. Experimental Results
Tested on a high-contrast test pattern at 4x scale.

| Metric | Standard Bicubic | **Proposed Hybrid Method** |
| :--- | :---: | :---: |
| **PSNR (dB)** | 26.45 | **29.82** |
| **SSIM** | 0.9214 | **0.9658** |
| **Execution Time** | 0.8 ms | **24.2 ms** |

---

## V. Conclusion
The proposed hybrid framework successfully combines deterministic interpolation with iterative error correction. By fusing **Iterative Back-Projection** with **Luminance-isolated adaptive sharpening**, we achieve a "self-correcting" upscaler that provides superior accuracy (SSIM) and perceptual sharpness without neural network overhead.

---
**References**
1. Keys, R., "Cubic convolution interpolation," IEEE Trans. ASSP, 1981.
2. Irani, M. and Peleg, S., "Improving resolution by image registration," CVGIP, 1991. (IBP Foundation)
