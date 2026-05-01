"""
Upscale engine — tries CUDA first, falls back to NumPy-vectorized CPU.
"""

import ctypes
import os
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger("upscale_engine")

_cuda_lib = None


class UpscaleParams(ctypes.Structure):
    _fields_ = [
        ("src_width", ctypes.c_int),
        ("src_height", ctypes.c_int),
        ("dst_width", ctypes.c_int),
        ("dst_height", ctypes.c_int),
        ("channels", ctypes.c_int),
        ("scale_factor", ctypes.c_int),
        ("edge_threshold", ctypes.c_float),
        ("elapsed_ms", ctypes.c_float),
    ]


def _load_cuda():
    global _cuda_lib
    if _cuda_lib is not None:
        return _cuda_lib

    so_path = Path(__file__).resolve().parent.parent / "cuda" / "libedge_bicubic.so"
    if not so_path.exists():
        logger.info("CUDA shared library not found at %s", so_path)
        return None

    try:
        lib = ctypes.CDLL(str(so_path))
        lib.edge_preserving_upscale.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(UpscaleParams),
        ]
        lib.edge_preserving_upscale.restype = ctypes.c_int
        lib.standard_bicubic_upscale.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(UpscaleParams),
        ]
        lib.standard_bicubic_upscale.restype = ctypes.c_int
        _cuda_lib = lib
        logger.info("CUDA library loaded successfully")
        return lib
    except OSError as e:
        logger.warning("Failed to load CUDA library: %s", e)
        return None


def upscale_image(
    image: np.ndarray,
    scale_factor: int = 2,
    edge_threshold: float = 30.0,
    method: str = "adaptive",
) -> dict:
    """
    Upscale image using edge-preserving adaptive bicubic interpolation.

    Returns dict with keys: image, elapsed_ms, method, src_size, dst_size, backend
    """
    if image.dtype != np.uint8:
        image = image.astype(np.uint8)

    lib = _load_cuda()

    if lib is not None:
        return _gpu_upscale(lib, image, scale_factor, edge_threshold, method)

    logger.info("Falling back to CPU (NumPy) implementation")
    return _cpu_upscale(image, scale_factor, edge_threshold, method)


def _gpu_upscale(lib, image, scale_factor, edge_threshold, method):
    src_h, src_w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    dst_w, dst_h = src_w * scale_factor, src_h * scale_factor

    flat_in = np.ascontiguousarray(image).flatten()
    flat_out = np.zeros(dst_w * dst_h * channels, dtype=np.uint8)

    params = UpscaleParams()
    params.src_width = src_w
    params.src_height = src_h
    params.channels = channels
    params.scale_factor = scale_factor
    params.edge_threshold = edge_threshold

    in_ptr = flat_in.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
    out_ptr = flat_out.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

    if method == "standard":
        ret = lib.standard_bicubic_upscale(in_ptr, out_ptr, ctypes.byref(params))
    else:
        ret = lib.edge_preserving_upscale(in_ptr, out_ptr, ctypes.byref(params))

    if ret != 0:
        raise RuntimeError("CUDA kernel execution failed")

    if channels == 1:
        result_image = flat_out.reshape(dst_h, dst_w)
    else:
        result_image = flat_out.reshape(dst_h, dst_w, channels)

    return {
        "image": result_image,
        "elapsed_ms": params.elapsed_ms,
        "method": method,
        "src_size": (src_w, src_h),
        "dst_size": (dst_w, dst_h),
        "backend": "cuda",
    }


def _cpu_upscale(image, scale_factor, edge_threshold, method):
    from .cpu_numpy_fallback import (
        edge_preserving_upscale_numpy,
        standard_bicubic_upscale_numpy,
    )

    if method == "standard":
        result = standard_bicubic_upscale_numpy(image, scale_factor)
    else:
        result = edge_preserving_upscale_numpy(image, scale_factor, edge_threshold)

    result["backend"] = "cpu"
    return result


def get_backend_info() -> dict:
    lib = _load_cuda()
    return {
        "cuda_available": lib is not None,
        "backend": "cuda" if lib is not None else "cpu",
    }
