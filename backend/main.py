"""
FastAPI backend for Edge-Preserving Bicubic Interpolation.
"""

import io
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image

from core.upscale_engine import upscale_image, get_backend_info
from core import auth_utils
from core.database import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api")

MAX_INPUT_SIZE = 4096 * 4096
MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/bmp", "image/tiff"}

app = FastAPI(
    title="Edge-Preserving Bicubic Upscaler",
    description="GPU-accelerated adaptive bicubic image upscaling with edge preservation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    info = get_backend_info()
    return {"status": "ok", **info}


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    edge_threshold: float = Query(30.0, ge=1.0, le=255.0),
):
    """Generates an edge-awareness heatmap for the input image."""
    raw = await file.read()
    try:
        img = Image.open(io.BytesIO(raw))
        if img.mode != "RGB":
            img = img.convert("RGB")
        image_array = np.array(img)
    except Exception:
        raise HTTPException(400, "Could not decode image")

    from core.analysis import generate_edge_heatmap
    heatmap_array = generate_edge_heatmap(image_array, edge_threshold)
    
    heatmap_img = Image.fromarray(heatmap_array)
    buf = io.BytesIO()
    heatmap_img.save(buf, format="PNG")
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")


@app.post("/upscale")
async def upscale(
    file: UploadFile = File(...),
    scale: int = Query(2, ge=2, le=4),
    method: str = Query("adaptive", regex="^(adaptive|standard)$"),
    edge_threshold: float = Query(30.0, ge=1.0, le=255.0),
    output_format: str = Query("png", regex="^(png|jpeg|webp)$"),
):
    request_id = uuid.uuid4().hex[:8]
    logger.info("[%s] Upscale request: scale=%d method=%s fmt=%s", request_id, scale, method, output_format)

    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported image type: {file.content_type}")

    raw = await file.read()
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(400, f"File too large ({len(raw)} bytes, max {MAX_FILE_BYTES})")

    try:
        img = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(400, "Could not decode image")

    if img.mode == "RGBA":
        img = img.convert("RGB")
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    w, h = img.size
    if w * h > MAX_INPUT_SIZE:
        raise HTTPException(400, f"Image too large ({w}x{h}), max {MAX_INPUT_SIZE} pixels")

    image_array = np.array(img)
    logger.info("[%s] Input: %dx%d %s", request_id, w, h, img.mode)

    t0 = time.perf_counter()
    try:
        result = upscale_image(
            image_array,
            scale_factor=scale,
            edge_threshold=edge_threshold,
            method=method,
        )
    except Exception as e:
        logger.exception("[%s] Upscale failed", request_id)
        raise HTTPException(500, f"Processing failed: {str(e)}")

    # Also run standard bicubic for metrics comparison
    from core.cpu_numpy_fallback import standard_bicubic_upscale_numpy
    standard_result = standard_bicubic_upscale_numpy(
        image_array,
        scale_factor=scale
    )

    # Efficient metrics comparison
    from metrics import compute_psnr, compute_ssim
    import cv2
    
    # For large images, use a downsampled version for metrics to save time
    if result["image"].shape[0] > 1024 or result["image"].shape[1] > 1024:
        # Downsample to ~1024px for metrics
        scale_down = 1024 / max(result["image"].shape[:2])
        m_h, m_w = int(result["image"].shape[0] * scale_down), int(result["image"].shape[1] * scale_down)
        m_standard = cv2.resize(standard_result["image"], (m_w, m_h), interpolation=cv2.INTER_AREA)
        m_adaptive = cv2.resize(result["image"], (m_w, m_h), interpolation=cv2.INTER_AREA)
        psnr_val = compute_psnr(m_standard, m_adaptive)
        ssim_val = compute_ssim(m_standard, m_adaptive)
    else:
        psnr_val = compute_psnr(standard_result["image"], result["image"])
        ssim_val = compute_ssim(standard_result["image"], result["image"])

    total_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "[%s] Done: %dx%d → %dx%d in %.1fms (kernel %.1fms, backend=%s, PSNR=%.2f)",
        request_id,
        *result["src_size"],
        *result["dst_size"],
        total_ms,
        result["elapsed_ms"],
        result.get("backend", "unknown"),
        psnr_val
    )

    out_img = Image.fromarray(result["image"])
    buf = io.BytesIO()

    fmt_map = {"png": "PNG", "jpeg": "JPEG", "webp": "WEBP"}
    pil_fmt = fmt_map[output_format]
    save_kwargs = {}
    if output_format == "jpeg":
        save_kwargs["quality"] = 95
    elif output_format == "webp":
        save_kwargs["quality"] = 95

    out_img.save(buf, format=pil_fmt, **save_kwargs)
    buf.seek(0)

    mime = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}
    return StreamingResponse(
        buf,
        media_type=mime[output_format],
        headers={
            "X-Processing-Time-Ms": f"{total_ms:.1f}",
            "X-Kernel-Time-Ms": f"{result['elapsed_ms']:.1f}",
            "X-Backend": result.get("backend", "unknown"),
            "X-Method": result["method"],
            "X-Source-Size": f"{result['src_size'][0]}x{result['src_size'][1]}",
            "X-Output-Size": f"{result['dst_size'][0]}x{result['dst_size'][1]}",
            "X-PSNR": f"{psnr_val:.2f}",
            "X-SSIM": f"{ssim_val:.4f}",
            "X-Request-Id": request_id,
            "Content-Disposition": f'inline; filename="upscaled_{request_id}.{output_format}"',
        },
    )


@app.post("/compare")
async def compare(
    file: UploadFile = File(...),
    scale: int = Query(2, ge=2, le=4),
    edge_threshold: float = Query(30.0, ge=1.0, le=255.0),
):
    """Run both adaptive and standard bicubic, return metrics comparison."""
    request_id = uuid.uuid4().hex[:8]

    raw = await file.read()
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(400, "File too large")

    try:
        img = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(400, "Could not decode image")

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    image_array = np.array(img)

    adaptive = upscale_image(image_array, scale, edge_threshold, "adaptive")
    standard = upscale_image(image_array, scale, edge_threshold, "standard")

    # compute PSNR and SSIM between the two
    from metrics import compute_psnr, compute_ssim

    psnr_val = compute_psnr(standard["image"], adaptive["image"])
    ssim_val = compute_ssim(standard["image"], adaptive["image"])

    return JSONResponse({
        "request_id": request_id,
        "scale": scale,
        "src_size": list(adaptive["src_size"]),
        "dst_size": list(adaptive["dst_size"]),
        "adaptive": {
            "elapsed_ms": adaptive["elapsed_ms"],
            "backend": adaptive.get("backend"),
        },
        "standard": {
            "elapsed_ms": standard["elapsed_ms"],
            "backend": standard.get("backend"),
        },
        "comparison": {
            "psnr_db": round(psnr_val, 2),
            "ssim": round(ssim_val, 4),
        },
    })


@app.post("/api/signup")
async def signup(payload: dict):
    db = get_db()
    # Check if user exists
    existing_user = await db.users.find_one({"email": payload["email"]})
    if existing_user:
        raise HTTPException(400, "Email already registered")
    
    hashed_password = auth_utils.get_password_hash(payload["password"])
    new_user = {
        "full_name": payload.get("full_name", "Research User"),
        "email": payload["email"],
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(new_user)
    
    token = auth_utils.create_access_token(data={"sub": new_user["email"]})
    return {"access_token": token, "token_type": "bearer", "user": {"name": new_user["full_name"], "email": new_user["email"]}}

@app.post("/api/login")
async def login(payload: dict):
    db = get_db()
    user = await db.users.find_one({"email": payload["email"]})
    if not user or not auth_utils.verify_password(payload["password"], user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")
    
    token = auth_utils.create_access_token(data={"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer", "user": {"name": user["full_name"], "email": user["email"]}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
