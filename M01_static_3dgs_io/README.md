# M01 Static 3DGS I/O Baseline

> **현재 역할:** 이 폴더는 새 방법의 mainline milestone이 아니라 static GS I/O와 renderer 회귀 기준선이다. TD01의 `CanonicalGaussianAsset` schema와 좌표계·covariance 계약을 다시 통과한 뒤에만 재사용 완료로 인정한다.

## Goal

본격적인 real/pretrained 3DGS asset을 붙이기 전에, 최소한의 static 3DGS I/O pipeline을 고정한다.

이 실험은 synthetic Inria-style 3DGS `.ply`를 생성하고, Gaussian attributes와 camera를 load한 뒤 canonical views와 turntable preview를 저장한다. `gsplat` CUDA rasterizer 경로를 우선 시도하되, 현재 실행 환경에서 CUDA rasterization이 실패하면 `cpu_debug` renderer로 fallback해서 pipeline output contract를 유지한다.

## Input

- Synthetic 3DGS asset: `assets/synthetic_leaf_3dgs.ply`
- Camera set: `cameras/synthetic_leaf_3dgs_cameras.json`
- Stored Gaussian attributes:
  - `x y z`
  - `scale_0..2`
  - `rot_0..3`
  - `opacity`
  - `f_dc_0..2`
  - `f_rest_0..44`

## Command

Reusable implementation now lives under `code/wind3dgs/m01_static_3dgs_io/`.
The commands below use experiment-local wrappers for backward compatibility.
The equivalent module form is:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m01_static_3dgs_io.render_static_baseline --backend cpu_debug
```

Generate the synthetic asset and camera path:

```bash
.venv/bin/python experiments/M01_static_3dgs_io/scripts/generate_synthetic_asset.py
```

Render canonical frames and a turntable:

```bash
.venv/bin/python experiments/M01_static_3dgs_io/scripts/render_static_baseline.py --backend auto
```

Force `gsplat` after CUDA Toolkit / rasterizer runtime is available:

```bash
.venv/bin/python experiments/M01_static_3dgs_io/scripts/render_static_baseline.py --backend gsplat
```

Use the CPU debug renderer explicitly:

```bash
.venv/bin/python experiments/M01_static_3dgs_io/scripts/render_static_baseline.py --backend cpu_debug
```

## gsplat CUDA Toolkit Check

`torch.cuda.is_available() == True`와 `gsplat.rendering.rasterization` import 성공만으로는 충분하지 않다. `gsplat`이 실제 rendering을 하려면 CUDA extension `_C`가 load되어야 하며, 현재 Python 3.12 / PyTorch 조합에서는 first run 때 CUDA Toolkit의 `nvcc`로 JIT build가 필요할 수 있다.

Check:

```bash
which nvcc
nvcc --version
.venv/bin/python -c "import torch; from torch.utils.cpp_extension import CUDA_HOME; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), CUDA_HOME)"
.venv/bin/python experiments/M01_static_3dgs_io/scripts/check_gsplat_env.py
```

If `nvcc` is missing on WSL, install CUDA Toolkit without installing a Linux display driver:

```bash
sudo apt-get install -y build-essential ninja-build
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install -y cuda-toolkit-12-6
```

For the current `torch==2.11.0+cu126`, prefer CUDA Toolkit 12.6. Then open a fresh shell or set:

```bash
export CUDA_HOME=/usr/local/cuda-12.6
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}
```

Verify:

```bash
nvcc --version
.venv/bin/python experiments/M01_static_3dgs_io/scripts/render_static_baseline.py --backend gsplat
```

If the build log contains `cooperative_groups has no member labeled_partition` and `compute_61` / `sm_61`, this is likely not a CUDA Toolkit setup issue anymore. `labeled_partition` requires Compute Capability 7.0 or newer, while `compute_61` means the visible GPU is CC 6.1. In that case, use a CC >= 7.0 GPU for `gsplat`, or keep using `--backend cpu_debug` for this legacy baseline.

Current local confirmation:

- GPU: `NVIDIA GeForce GTX 1080 Ti`
- Compute Capability: `6.1`
- Status: `gsplat 1.5.3` CUDA backend is expected to fail on this GPU because `cooperative_groups::labeled_partition` requires CC >= 7.0.
- Script behavior: `--backend auto` prechecks compute capability and falls back to `cpu_debug` before triggering the slow `gsplat` JIT build on CC < 7.0 devices.

Do not force `TORCH_CUDA_ARCH_LIST=7.0` unless the physical GPU really supports CC 7.0 or newer. Forcing a newer arch on a CC 6.1 GPU may compile farther but will not produce a runnable kernel for that GPU.

## Output

- Render report: `outputs/render_report.md`
- Sanity statistics: `outputs/stats.json`
- Canonical frames:
  - `outputs/renders/canonical_front.png`
  - `outputs/renders/canonical_oblique.png`
  - `outputs/renders/canonical_side.png`
- Turntable frames: `outputs/turntable/turntable_*.png`
- Turntable preview: `outputs/turntable.gif`

## Metrics

현재 synthetic/minimal asset에는 ground-truth image가 없기 때문에 PSNR, SSIM, LPIPS는 계산하지 않는다.

대신 다음 sanity statistics를 M1 기준선으로 기록한다.

- Gaussian count
- bounding box
- opacity range
- scale range
- quaternion norm range
- SH coefficient shape
- stored SH degree

## Notes

- `cpu_debug` backend는 실제 3DGS rasterization이 아니라 projection과 alpha circle splat 기반의 debug preview다.
- 사용자 local shell에서 `--backend cpu_debug` render가 성공했다: canonical renders 3장, turntable frames 48장이 생성되었다.
- 논문/실험용 final render 품질 판단은 `gsplat` 또는 다른 CUDA Gaussian rasterizer로 다시 검증해야 한다.
- WSL 내부 CUDA Toolkit / `nvcc` 설치 후에는 `gsplat` JIT build가 시작된다.
- 현재 사용자 local shell에서는 `NVIDIA GeForce GTX 1080 Ti`, Compute Capability `6.1`로 확인되었다.
- `gsplat 1.5.3` CUDA backend는 이 GPU에서 `cooperative_groups::labeled_partition` 때문에 실패할 것으로 예상된다.
- TD contract 재검증 전에는 `cpu_debug`를 legacy I/O smoke에만 사용하고, 논문용 render 검증은 호환되는 CUDA backend/GPU에서 별도로 진행한다.
