import numpy as np
from PIL import Image, ImageDraw
import sys, json
from pathlib import Path

sys.path.insert(0, ".")
from backend.cpu_numpy_fallback import edge_preserving_upscale_numpy, standard_bicubic_upscale_numpy
from backend.metrics import compute_psnr, compute_ssim

def make_photo_like(name, w=256, h=256):
    """Create a photo-realistic test image with gradients + edges."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # sky gradient
    for row in range(h//2):
        t = row / (h//2)
        img[row, :] = [int(30+100*t), int(60+120*t), int(180+50*t)]
    # ground
    for row in range(h//2, h):
        t = (row - h//2) / (h//2)
        img[row, :] = [int(60+80*t), int(100+50*t), int(40+20*t)]
    # add a sharp building silhouette
    img[40:180, 80:100] = [20, 20, 30]
    img[80:180, 100:130] = [20, 20, 30]
    img[60:180, 155:175] = [20, 20, 30]
    # windows (bright inside dark)
    for wy in range(90, 170, 20):
        for wx in range(83, 97, 8):
            img[wy:wy+10, wx:wx+6] = [255, 220, 100]
    # Save
    pil_img = Image.fromarray(img)
    pil_img.save(name)
    return img

def evaluate(img_arr, scale, threshold):
    src_h, src_w = img_arr.shape[:2]
    small_w, small_h = src_w // scale, src_h // scale
    small = np.array(Image.fromarray(img_arr).resize((small_w, small_h), Image.BILINEAR))

    adaptive = edge_preserving_upscale_numpy(small, scale, threshold)
    standard = standard_bicubic_upscale_numpy(small, scale)

    h = min(img_arr.shape[0], adaptive["image"].shape[0])
    w = min(img_arr.shape[1], adaptive["image"].shape[1])
    gt = img_arr[:h, :w]
    ad = adaptive["image"][:h, :w]
    st = standard["image"][:h, :w]

    return {
        "psnr_adaptive": round(compute_psnr(gt, ad), 2),
        "psnr_standard": round(compute_psnr(gt, st), 2),
        "ssim_adaptive": round(compute_ssim(gt, ad), 4),
        "ssim_standard": round(compute_ssim(gt, st), 4),
        "time_adaptive_ms": round(adaptive["elapsed_ms"], 1),
        "time_standard_ms": round(standard["elapsed_ms"], 1),
        "adaptive_img": ad,
        "standard_img": st,
        "original": gt,
        "input_small": small,
    }

# Test 1: Photo-like (building scene)
photo = make_photo_like("test_photo.png")
r2 = evaluate(photo, 2, 30.0)
r4 = evaluate(photo, 4, 30.0)

# Save visual outputs
Image.fromarray(r2["input_small"]).save("output_input_2x.png")
Image.fromarray(r2["standard_img"]).save("output_standard_2x.png")
Image.fromarray(r2["adaptive_img"]).save("output_adaptive_2x.png")
Image.fromarray(r4["input_small"]).save("output_input_4x.png")
Image.fromarray(r4["standard_img"]).save("output_standard_4x.png")
Image.fromarray(r4["adaptive_img"]).save("output_adaptive_4x.png")

print("\n====== EVALUATION RESULTS ======")
print("\n--- 2x Upscale ---")
print(f"  {'Metric':<14} {'Standard':>12} {'Adaptive':>12} {'Delta':>10}")
print(f"  {'─'*50}")
print(f"  {'PSNR (dB)':<14} {r2['psnr_standard']:>12.2f} {r2['psnr_adaptive']:>12.2f} {r2['psnr_adaptive']-r2['psnr_standard']:>+10.2f}")
print(f"  {'SSIM':<14} {r2['ssim_standard']:>12.4f} {r2['ssim_adaptive']:>12.4f} {r2['ssim_adaptive']-r2['ssim_standard']:>+10.4f}")
print(f"  {'Time (ms)':<14} {r2['time_standard_ms']:>12.1f} {r2['time_adaptive_ms']:>12.1f}")

print("\n--- 4x Upscale ---")
print(f"  {'Metric':<14} {'Standard':>12} {'Adaptive':>12} {'Delta':>10}")
print(f"  {'─'*50}")
print(f"  {'PSNR (dB)':<14} {r4['psnr_standard']:>12.2f} {r4['psnr_adaptive']:>12.2f} {r4['psnr_adaptive']-r4['psnr_standard']:>+10.2f}")
print(f"  {'SSIM':<14} {r4['ssim_standard']:>12.4f} {r4['ssim_adaptive']:>12.4f} {r4['ssim_adaptive']-r4['ssim_standard']:>+10.4f}")
print(f"  {'Time (ms)':<14} {r4['time_standard_ms']:>12.1f} {r4['time_adaptive_ms']:>12.1f}")
