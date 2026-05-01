"""Image quality metrics: PSNR and SSIM."""

import numpy as np


def compute_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    if img1.shape != img2.shape:
        raise ValueError("Images must have the same dimensions")

    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")

    return 10.0 * np.log10(255.0**2 / mse)


def compute_ssim(
    img1: np.ndarray, img2: np.ndarray, window_size: int = 11
) -> float:
    if img1.shape != img2.shape:
        raise ValueError("Images must have the same dimensions")

    if img1.ndim == 3:
        channels = img1.shape[2]
        ssim_vals = [
            _ssim_channel(img1[:, :, c], img2[:, :, c], window_size)
            for c in range(channels)
        ]
        return float(np.mean(ssim_vals))

    return _ssim_channel(img1, img2, window_size)


def _ssim_channel(
    img1: np.ndarray, img2: np.ndarray, window_size: int
) -> float:
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    from scipy.ndimage import uniform_filter

    mu1 = uniform_filter(img1, window_size)
    mu2 = uniform_filter(img2, window_size)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = uniform_filter(img1 ** 2, window_size) - mu1_sq
    sigma2_sq = uniform_filter(img2 ** 2, window_size) - mu2_sq
    sigma12 = uniform_filter(img1 * img2, window_size) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
    )

    return float(np.mean(ssim_map))
