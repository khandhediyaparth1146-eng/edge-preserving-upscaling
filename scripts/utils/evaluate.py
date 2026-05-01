"""
Performance evaluation suite.
Compares edge-preserving adaptive vs standard bicubic on PSNR, SSIM, and timing.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.cpu_numpy_fallback import (
    edge_preserving_upscale_numpy,
    standard_bicubic_upscale_numpy,
)
from backend.metrics import compute_psnr, compute_ssim


def evaluate_image(image_path: str, scale: int = 2, edge_threshold: float = 30.0):
    img = Image.open(image_path).convert("RGB")
    image = np.array(img)

    print(f"\nEvaluating: {image_path}")
    print(f"  Input size: {image.shape[1]}x{image.shape[0]}")
    print(f"  Scale factor: {scale}x")
    print(f"  Edge threshold: {edge_threshold}")

    # downsample first to create ground truth comparison
    src_h, src_w = image.shape[:2]
    small_w, small_h = src_w // scale, src_h // scale
    small = np.array(img.resize((small_w, small_h), Image.BILINEAR))

    # upscale back
    adaptive = edge_preserving_upscale_numpy(small, scale, edge_threshold)
    standard = standard_bicubic_upscale_numpy(small, scale)

    # crop to common size
    h = min(image.shape[0], adaptive["image"].shape[0], standard["image"].shape[0])
    w = min(image.shape[1], adaptive["image"].shape[1], standard["image"].shape[1])
    gt = image[:h, :w]
    ad = adaptive["image"][:h, :w]
    st = standard["image"][:h, :w]

    psnr_adaptive = compute_psnr(gt, ad)
    psnr_standard = compute_psnr(gt, st)
    ssim_adaptive = compute_ssim(gt, ad)
    ssim_standard = compute_ssim(gt, st)

    results = {
        "image": image_path,
        "input_size": f"{small_w}x{small_h}",
        "output_size": f"{w}x{h}",
        "scale": scale,
        "adaptive": {
            "psnr_db": round(psnr_adaptive, 2),
            "ssim": round(ssim_adaptive, 4),
            "time_ms": round(adaptive["elapsed_ms"], 1),
        },
        "standard": {
            "psnr_db": round(psnr_standard, 2),
            "ssim": round(ssim_standard, 4),
            "time_ms": round(standard["elapsed_ms"], 1),
        },
        "improvement": {
            "psnr_db": round(psnr_adaptive - psnr_standard, 2),
            "ssim": round(ssim_adaptive - ssim_standard, 4),
        },
    }

    print(f"\n  {'Metric':<12} {'Standard':>12} {'Adaptive':>12} {'Delta':>10}")
    print(f"  {'─'*48}")
    print(f"  {'PSNR (dB)':<12} {psnr_standard:>12.2f} {psnr_adaptive:>12.2f} {psnr_adaptive-psnr_standard:>+10.2f}")
    print(f"  {'SSIM':<12} {ssim_standard:>12.4f} {ssim_adaptive:>12.4f} {ssim_adaptive-ssim_standard:>+10.4f}")
    print(f"  {'Time (ms)':<12} {standard['elapsed_ms']:>12.1f} {adaptive['elapsed_ms']:>12.1f}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate upscaling quality")
    parser.add_argument("images", nargs="+", help="Image file paths")
    parser.add_argument("--scale", type=int, default=2, choices=[2, 4])
    parser.add_argument("--threshold", type=float, default=30.0)
    parser.add_argument("--output", type=str, default=None, help="JSON output file")
    args = parser.parse_args()

    all_results = []
    for path in args.images:
        r = evaluate_image(path, args.scale, args.threshold)
        all_results.append(r)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
