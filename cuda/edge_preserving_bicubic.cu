/*
 * Edge-Preserving Adaptive Bicubic Interpolation — CUDA Implementation
 *
 * Sobel-based gradient detection drives per-pixel kernel adaptation:
 * smooth regions get standard bicubic; edge regions get direction-aware
 * modified kernels that interpolate along (not across) edges.
 */

#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BLOCK_SIZE 16
#define TILE_SIZE (BLOCK_SIZE + 4) // extra halo for bicubic (2 pixels each side)
#define EDGE_THRESHOLD 30.0f
#define PI 3.14159265358979323846f

// ---------- host-side helpers ----------

#define CUDA_CHECK(call)                                                      \
    do {                                                                      \
        cudaError_t err = call;                                               \
        if (err != cudaSuccess) {                                             \
            fprintf(stderr, "CUDA error at %s:%d — %s\n", __FILE__,          \
                    __LINE__, cudaGetErrorString(err));                        \
            return -1;                                                        \
        }                                                                     \
    } while (0)

// ---------- device helpers ----------

__device__ __forceinline__ float bicubic_weight(float t, float a) {
    float abs_t = fabsf(t);
    if (abs_t <= 1.0f)
        return (a + 2.0f) * abs_t * abs_t * abs_t -
               (a + 3.0f) * abs_t * abs_t + 1.0f;
    if (abs_t < 2.0f)
        return a * abs_t * abs_t * abs_t -
               5.0f * a * abs_t * abs_t +
               8.0f * a * abs_t - 4.0f * a;
    return 0.0f;
}

__device__ __forceinline__ float clamp_pixel(float v) {
    return fminf(255.0f, fmaxf(0.0f, v));
}

__device__ __forceinline__ int mirror_index(int idx, int limit) {
    if (idx < 0) return -idx;
    if (idx >= limit) return 2 * limit - idx - 2;
    return idx;
}

// ---------- Sobel gradient kernel ----------

__global__ void sobel_gradient_kernel(
    const unsigned char* __restrict__ input,
    float* __restrict__ grad_mag,
    float* __restrict__ grad_dir,
    int width, int height, int channels)
{
    __shared__ float tile[TILE_SIZE][TILE_SIZE];

    int tx = threadIdx.x;
    int ty = threadIdx.y;
    int gx = blockIdx.x * BLOCK_SIZE + tx;
    int gy = blockIdx.y * BLOCK_SIZE + ty;

    // load tile with 2-pixel halo — convert to luminance
    for (int dy = ty; dy < TILE_SIZE; dy += BLOCK_SIZE) {
        for (int dx = tx; dx < TILE_SIZE; dx += BLOCK_SIZE) {
            int sx = blockIdx.x * BLOCK_SIZE + dx - 2;
            int sy = blockIdx.y * BLOCK_SIZE + dy - 2;
            sx = mirror_index(sx, width);
            sy = mirror_index(sy, height);
            int idx = (sy * width + sx) * channels;
            if (channels >= 3)
                tile[dy][dx] = 0.299f * input[idx] +
                               0.587f * input[idx + 1] +
                               0.114f * input[idx + 2];
            else
                tile[dy][dx] = (float)input[idx];
        }
    }
    __syncthreads();

    if (gx >= width || gy >= height) return;

    int lx = tx + 2;
    int ly = ty + 2;

    float gx_val =
        -tile[ly - 1][lx - 1] + tile[ly - 1][lx + 1] +
        -2.0f * tile[ly][lx - 1] + 2.0f * tile[ly][lx + 1] +
        -tile[ly + 1][lx - 1] + tile[ly + 1][lx + 1];

    float gy_val =
        -tile[ly - 1][lx - 1] - 2.0f * tile[ly - 1][lx] - tile[ly - 1][lx + 1] +
         tile[ly + 1][lx - 1] + 2.0f * tile[ly + 1][lx] + tile[ly + 1][lx + 1];

    int out_idx = gy * width + gx;
    grad_mag[out_idx] = sqrtf(gx_val * gx_val + gy_val * gy_val);
    grad_dir[out_idx] = atan2f(gy_val, gx_val);
}

// ---------- adaptive bicubic upscale kernel ----------

__global__ void adaptive_bicubic_kernel(
    const unsigned char* __restrict__ input,
    unsigned char* __restrict__ output,
    const float* __restrict__ grad_mag,
    const float* __restrict__ grad_dir,
    int src_w, int src_h,
    int dst_w, int dst_h,
    int channels, int scale_factor,
    float edge_threshold)
{
    int dst_x = blockIdx.x * blockDim.x + threadIdx.x;
    int dst_y = blockIdx.y * blockDim.y + threadIdx.y;

    if (dst_x >= dst_w || dst_y >= dst_h) return;

    float src_xf = (dst_x + 0.5f) / scale_factor - 0.5f;
    float src_yf = (dst_y + 0.5f) / scale_factor - 0.5f;
    int src_xi = (int)floorf(src_xf);
    int src_yi = (int)floorf(src_yf);
    float dx = src_xf - src_xi;
    float dy = src_yf - src_yi;

    // sample gradient at nearest source pixel
    int near_x = min(max(src_xi, 0), src_w - 1);
    int near_y = min(max(src_yi, 0), src_h - 1);
    float mag = grad_mag[near_y * src_w + near_x];
    float dir = grad_dir[near_y * src_w + near_x];

    bool is_edge = mag > edge_threshold;

    // bicubic parameter: sharper on edges
    float a = is_edge ? -0.75f : -0.5f;

    // precompute weights
    float wx[4], wy[4];
    for (int i = 0; i < 4; i++) {
        wx[i] = bicubic_weight(dx - (i - 1), a);
        wy[i] = bicubic_weight(dy - (i - 1), a);
    }

    // direction-aware weight modification for edges
    if (is_edge) {
        float cos_d = cosf(dir);
        float sin_d = sinf(dir);
        float abs_cos = fabsf(cos_d);
        float abs_sin = fabsf(sin_d);

        // suppress weights perpendicular to edge
        for (int i = 0; i < 4; i++) {
            float offset_x = (float)(i - 1) - dx;
            float offset_y = (float)(i - 1) - dy;
            float perp_x = fabsf(offset_x * cos_d);
            float perp_y = fabsf(offset_y * sin_d);
            float perp_factor_x = expf(-perp_x * 0.5f);
            float perp_factor_y = expf(-perp_y * 0.5f);
            wx[i] *= (0.3f + 0.7f * perp_factor_x);
            wy[i] *= (0.3f + 0.7f * perp_factor_y);
        }
    }

    // normalise
    float sum_wx = wx[0] + wx[1] + wx[2] + wx[3];
    float sum_wy = wy[0] + wy[1] + wy[2] + wy[3];
    for (int i = 0; i < 4; i++) {
        wx[i] /= sum_wx;
        wy[i] /= sum_wy;
    }

    // interpolate each channel
    for (int c = 0; c < channels; c++) {
        float val = 0.0f;
        for (int j = 0; j < 4; j++) {
            float row_val = 0.0f;
            for (int i = 0; i < 4; i++) {
                int sx = mirror_index(src_xi + i - 1, src_w);
                int sy = mirror_index(src_yi + j - 1, src_h);
                row_val += wx[i] * (float)input[(sy * src_w + sx) * channels + c];
            }
            val += wy[j] * row_val;
        }
        int dst_idx = (dst_y * dst_w + dst_x) * channels + c;
        output[dst_idx] = (unsigned char)clamp_pixel(val);
    }
}

// ---------- standard bicubic (for comparison) ----------

__global__ void standard_bicubic_kernel(
    const unsigned char* __restrict__ input,
    unsigned char* __restrict__ output,
    int src_w, int src_h,
    int dst_w, int dst_h,
    int channels, int scale_factor)
{
    int dst_x = blockIdx.x * blockDim.x + threadIdx.x;
    int dst_y = blockIdx.y * blockDim.y + threadIdx.y;

    if (dst_x >= dst_w || dst_y >= dst_h) return;

    float src_xf = (dst_x + 0.5f) / scale_factor - 0.5f;
    float src_yf = (dst_y + 0.5f) / scale_factor - 0.5f;
    int src_xi = (int)floorf(src_xf);
    int src_yi = (int)floorf(src_yf);
    float dx = src_xf - src_xi;
    float dy = src_yf - src_yi;

    float a = -0.5f;
    float wx[4], wy[4];
    for (int i = 0; i < 4; i++) {
        wx[i] = bicubic_weight(dx - (i - 1), a);
        wy[i] = bicubic_weight(dy - (i - 1), a);
    }

    for (int c = 0; c < channels; c++) {
        float val = 0.0f;
        for (int j = 0; j < 4; j++) {
            float row_val = 0.0f;
            for (int i = 0; i < 4; i++) {
                int sx = mirror_index(src_xi + i - 1, src_w);
                int sy = mirror_index(src_yi + j - 1, src_h);
                row_val += wx[i] * (float)input[(sy * src_w + sx) * channels + c];
            }
            val += wy[j] * row_val;
        }
        int dst_idx = (dst_y * dst_w + dst_x) * channels + c;
        output[dst_idx] = (unsigned char)clamp_pixel(val);
    }
}

// ---------- public C interface ----------

extern "C" {

typedef struct {
    int src_width;
    int src_height;
    int dst_width;
    int dst_height;
    int channels;
    int scale_factor;
    float edge_threshold;
    float elapsed_ms;
} UpscaleParams;

int edge_preserving_upscale(
    const unsigned char* h_input,
    unsigned char* h_output,
    UpscaleParams* params)
{
    int src_w = params->src_width;
    int src_h = params->src_height;
    int channels = params->channels;
    int scale = params->scale_factor;
    int dst_w = src_w * scale;
    int dst_h = src_h * scale;
    float edge_thresh = params->edge_threshold > 0 ? params->edge_threshold : EDGE_THRESHOLD;

    params->dst_width = dst_w;
    params->dst_height = dst_h;

    size_t src_size = (size_t)src_w * src_h * channels;
    size_t dst_size = (size_t)dst_w * dst_h * channels;
    size_t grad_size = (size_t)src_w * src_h * sizeof(float);

    unsigned char *d_input = NULL, *d_output = NULL;
    float *d_grad_mag = NULL, *d_grad_dir = NULL;

    CUDA_CHECK(cudaMalloc(&d_input, src_size));
    CUDA_CHECK(cudaMalloc(&d_output, dst_size));
    CUDA_CHECK(cudaMalloc(&d_grad_mag, grad_size));
    CUDA_CHECK(cudaMalloc(&d_grad_dir, grad_size));
    CUDA_CHECK(cudaMemcpy(d_input, h_input, src_size, cudaMemcpyHostToDevice));

    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));
    CUDA_CHECK(cudaEventRecord(start));

    // --- pass 1: Sobel gradient ---
    dim3 block1(BLOCK_SIZE, BLOCK_SIZE);
    dim3 grid1((src_w + BLOCK_SIZE - 1) / BLOCK_SIZE,
               (src_h + BLOCK_SIZE - 1) / BLOCK_SIZE);
    sobel_gradient_kernel<<<grid1, block1>>>(
        d_input, d_grad_mag, d_grad_dir, src_w, src_h, channels);

    // --- pass 2: adaptive bicubic ---
    dim3 block2(BLOCK_SIZE, BLOCK_SIZE);
    dim3 grid2((dst_w + BLOCK_SIZE - 1) / BLOCK_SIZE,
               (dst_h + BLOCK_SIZE - 1) / BLOCK_SIZE);
    adaptive_bicubic_kernel<<<grid2, block2>>>(
        d_input, d_output, d_grad_mag, d_grad_dir,
        src_w, src_h, dst_w, dst_h, channels, scale, edge_thresh);

    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float ms = 0;
    CUDA_CHECK(cudaEventElapsedTime(&ms, start, stop));
    params->elapsed_ms = ms;

    CUDA_CHECK(cudaMemcpy(h_output, d_output, dst_size, cudaMemcpyDeviceToHost));

    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_grad_mag);
    cudaFree(d_grad_dir);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    return 0;
}

int standard_bicubic_upscale(
    const unsigned char* h_input,
    unsigned char* h_output,
    UpscaleParams* params)
{
    int src_w = params->src_width;
    int src_h = params->src_height;
    int channels = params->channels;
    int scale = params->scale_factor;
    int dst_w = src_w * scale;
    int dst_h = src_h * scale;

    params->dst_width = dst_w;
    params->dst_height = dst_h;

    size_t src_size = (size_t)src_w * src_h * channels;
    size_t dst_size = (size_t)dst_w * dst_h * channels;

    unsigned char *d_input = NULL, *d_output = NULL;

    CUDA_CHECK(cudaMalloc(&d_input, src_size));
    CUDA_CHECK(cudaMalloc(&d_output, dst_size));
    CUDA_CHECK(cudaMemcpy(d_input, h_input, src_size, cudaMemcpyHostToDevice));

    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));
    CUDA_CHECK(cudaEventRecord(start));

    dim3 block(BLOCK_SIZE, BLOCK_SIZE);
    dim3 grid((dst_w + BLOCK_SIZE - 1) / BLOCK_SIZE,
              (dst_h + BLOCK_SIZE - 1) / BLOCK_SIZE);
    standard_bicubic_kernel<<<grid, block>>>(
        d_input, d_output, src_w, src_h, dst_w, dst_h, channels, scale);

    CUDA_CHECK(cudaEventRecord(stop));
    CUDA_CHECK(cudaEventSynchronize(stop));

    float ms = 0;
    CUDA_CHECK(cudaEventElapsedTime(&ms, start, stop));
    params->elapsed_ms = ms;

    CUDA_CHECK(cudaMemcpy(h_output, d_output, dst_size, cudaMemcpyDeviceToHost));

    cudaFree(d_input);
    cudaFree(d_output);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    return 0;
}

} // extern "C"
