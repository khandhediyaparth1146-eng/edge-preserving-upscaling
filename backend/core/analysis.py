import cv2
import numpy as np

def generate_edge_heatmap(image_array: np.ndarray, threshold: float = 30.0) -> np.ndarray:
    """
    Generates a high-performance visual heatmap of edges using OpenCV.
    """
    # Convert to grayscale
    if image_array.ndim == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_array

    # Fast Sobel gradients via OpenCV
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    
    # Normalize to 0-255
    mag_norm = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # Apply a high-contrast colormap (JET or INFERNO-like)
    heatmap = cv2.applyColorMap(mag_norm, cv2.COLORMAP_JET)
    
    # Convert BGR (OpenCV) to RGB (PIL/Web)
    return cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

def get_upscale_metrics(original: np.ndarray, upscaled: np.ndarray) -> dict:
    """
    Computes PSNR and SSIM by downscaling the upscaled image back to original size.
    """
    from metrics import compute_psnr, compute_ssim
    from PIL import Image
    
    h, w = original.shape[:2]
    upscaled_pil = Image.fromarray(upscaled)
    downsampled = np.array(upscaled_pil.resize((w, h), Image.Resampling.LANCZOS))
    
    psnr = compute_psnr(original, downsampled)
    ssim = compute_ssim(original, downsampled)
    
    return {"psnr": psnr, "ssim": ssim}
