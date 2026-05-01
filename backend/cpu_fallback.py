"""
CPU fallback implementation of edge-preserving adaptive bicubic interpolation.
Used when CUDA is unavailable. Mirrors the GPU algorithm exactly.
"""

import numpy as np
from scipy.ndimage import sobel
import time


def _bicubic_weight(t: float, a: float) -> float:
    t = abs(t)
    if t <= 1.0:
        return (a + 2) * t**3 - (a + 3) * t**2 + 1
    if t < 2.0:
        return a * t**3 - 5 * a * t**2 + 8 * a * t - 4 * a
    return 0.0


def _mirror(idx: int, limit: int) -> int:
    if idx < 0:
        return -idx
    if idx >= limit:
        return 2 * limit - idx - 2
    return idx


def compute_gradients(image: np.ndarray):
    if image.ndim == 3:
        gray = (
            0.299 * image[:, :, 0]
            + 0.587 * image[:, :, 1]
            + 0.114 * image[:, :, 2]
        ).astype(np.float32)
    else:
        gray = image.astype(np.float32)

    gx = sobel(gray, axis=1).astype(np.float32)
    gy = sobel(gray, axis=0).astype(np.float32)
    mag = np.sqrt(gx**2 + gy**2)
    direction = np.arctan2(gy, gx)
    return mag, direction


def edge_preserving_upscale_cpu(
    image: np.ndarray,
    scale_factor: int = 2,
    edge_threshold: float = 30.0,
) -> dict:
    start = time.perf_counter()

    src_h, src_w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    dst_w, dst_h = src_w * scale_factor, src_h * scale_factor

    if image.ndim == 2:
        image = image[:, :, np.newaxis]

    mag, direction = compute_gradients(image)
    output = np.zeros((dst_h, dst_w, channels), dtype=np.uint8)

    for dy in range(dst_h):
        src_yf = (dy + 0.5) / scale_factor - 0.5
        src_yi = int(np.floor(src_yf))
        fdy = src_yf - src_yi

        for dx in range(dst_w):
            src_xf = (dx + 0.5) / scale_factor - 0.5
            src_xi = int(np.floor(src_xf))
            fdx = src_xf - src_xi

            near_x = min(max(src_xi, 0), src_w - 1)
            near_y = min(max(src_yi, 0), src_h - 1)
            m = mag[near_y, near_x]
            d = direction[near_y, near_x]
            is_edge = m > edge_threshold

            a = -0.75 if is_edge else -0.5
            wx = [_bicubic_weight(fdx - (i - 1), a) for i in range(4)]
            wy = [_bicubic_weight(fdy - (i - 1), a) for i in range(4)]

            if is_edge:
                cos_d, sin_d = np.cos(d), np.sin(d)
                for i in range(4):
                    ox = abs((i - 1) - fdx) * abs(cos_d)
                    oy = abs((i - 1) - fdy) * abs(sin_d)
                    wx[i] *= 0.3 + 0.7 * np.exp(-ox * 0.5)
                    wy[i] *= 0.3 + 0.7 * np.exp(-oy * 0.5)

            sw = sum(wx)
            sh = sum(wy)
            wx = [w / sw for w in wx]
            wy = [w / sh for w in wy]

            for c in range(channels):
                val = 0.0
                for j in range(4):
                    row = 0.0
                    for i in range(4):
                        sx = _mirror(src_xi + i - 1, src_w)
                        sy = _mirror(src_yi + j - 1, src_h)
                        row += wx[i] * float(image[sy, sx, c])
                    val += wy[j] * row
                output[dy, dx, c] = int(min(255, max(0, round(val))))

    elapsed = (time.perf_counter() - start) * 1000
    if channels == 1:
        output = output[:, :, 0]

    return {
        "image": output,
        "elapsed_ms": elapsed,
        "method": "cpu",
        "src_size": (src_w, src_h),
        "dst_size": (dst_w, dst_h),
    }


def standard_bicubic_upscale_cpu(
    image: np.ndarray, scale_factor: int = 2
) -> dict:
    """Standard bicubic for comparison metrics."""
    start = time.perf_counter()

    src_h, src_w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    dst_w, dst_h = src_w * scale_factor, src_h * scale_factor

    if image.ndim == 2:
        image = image[:, :, np.newaxis]

    output = np.zeros((dst_h, dst_w, channels), dtype=np.uint8)
    a = -0.5

    for dy in range(dst_h):
        src_yf = (dy + 0.5) / scale_factor - 0.5
        src_yi = int(np.floor(src_yf))
        fdy = src_yf - src_yi

        for dx in range(dst_w):
            src_xf = (dx + 0.5) / scale_factor - 0.5
            src_xi = int(np.floor(src_xf))
            fdx = src_xf - src_xi

            wx = [_bicubic_weight(fdx - (i - 1), a) for i in range(4)]
            wy = [_bicubic_weight(fdy - (i - 1), a) for i in range(4)]

            for c in range(channels):
                val = 0.0
                for j in range(4):
                    row = 0.0
                    for i in range(4):
                        sx = _mirror(src_xi + i - 1, src_w)
                        sy = _mirror(src_yi + j - 1, src_h)
                        row += wx[i] * float(image[sy, sx, c])
                    val += wy[j] * row
                output[dy, dx, c] = int(min(255, max(0, round(val))))

    elapsed = (time.perf_counter() - start) * 1000
    if channels == 1:
        output = output[:, :, 0]

    return {
        "image": output,
        "elapsed_ms": elapsed,
        "method": "cpu_standard",
        "src_size": (src_w, src_h),
        "dst_size": (dst_w, dst_h),
    }
