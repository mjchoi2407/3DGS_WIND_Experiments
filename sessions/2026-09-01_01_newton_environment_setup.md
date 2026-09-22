# 2026-09-01 01 Newton 환경 설정과 GPU smoke test

## 목적과 범위

Wind3DGS의 향후 simulation data 생성 도구 후보인 Newton을 기존 root `.venv`와 분리해 설치하고,
CPU/GPU rigid-body, GPU deformable cloth와 USD 시계열 저장까지 실제로 구동한다.

이번 작업은 **tooling preflight**다. Newton을 canonical R1 teacher로 확정하거나 teacher physics,
wind traction, spatial/temporal convergence 또는 R1 Gate를 통과한 근거로 사용하지 않는다.

## 공식 기준 확인

- 조회일: 2026-09-01
- 최신 안정판: `newton==1.5.1`
- 공식 최소 조건: Python 3.10+, Linux x86-64, NVIDIA driver 545+, CUDA 12/13
- Newton이 상속하는 Warp CUDA 12 경로의 최소 GPU는 compute capability 5.2 이상이다.
- 이 호스트의 GTX 1080 Ti는 compute capability 6.1이므로 CUDA 12 Warp 경로를 사용했다.
- 공식 문서와 GitHub release를 네트워크로 조회했고, PyPI package를 실제 다운로드했다.
  Git source clone/fetch는 수행하지 않았다.

## 설치 환경

- OS: Ubuntu 24.04.4 LTS on WSL2
- Python: 3.12.3
- 전용 venv: `artifacts/environments/newton-1.5.1-py312/`
- GPU: NVIDIA GeForce GTX 1080 Ti, 11 GiB, `sm_61`
- Driver: 582.28 (`nvidia-smi` CUDA compatibility 13.0)
- Warp runtime: CUDA Toolkit 12.9, NVRTC 12.9, driver 13.0
- 설치 크기: 약 2.7 GiB
- kernel cache: `artifacts/caches/warp-newton-1.17.0/`

주요 설치 package:

- `newton==1.5.1`
- `warp-lang==1.17.0`
- `mujoco==3.11.0`
- `mujoco-warp==3.11.0`
- `open3d==0.19.0`
- `usd-core==26.3`
- `newton-usd-schemas==0.5.0`
- `numpy==2.5.2`

## 설치 명령

`experiments/`에서 다음을 실행했다.

```bash
python3 -m venv artifacts/environments/newton-1.5.1-py312
artifacts/environments/newton-1.5.1-py312/bin/python -m pip install --upgrade pip
artifacts/environments/newton-1.5.1-py312/bin/python -m pip install 'newton[examples]==1.5.1'
```

관리 실행 환경에서는 기본 user cache가 read-only이므로 모든 Newton 명령에 다음 cache를 주입했다.
일반 shell에서도 같은 값을 쓰면 kernel cache를 프로젝트 artifact 경계에 유지할 수 있다.

```bash
export WARP_CACHE_PATH="$PWD/artifacts/caches/warp-newton-1.17.0"
```

## 검증 결과

### Package와 example discovery

- `python -m pip check`: `No broken requirements found.`
- import version: Newton 1.5.1, Warp 1.17.0
- `python -m newton.examples --list`: rigid, cloth, softbody, MPM, differentiable simulation 예제 목록 정상 출력

### 공식 rigid-body smoke

```bash
python -m newton.examples basic_pendulum --viewer null --test --device cpu
python -m newton.examples basic_pendulum --viewer null --test --device cuda:0
```

- CPU: 종료 코드 0
- GPU: 종료 코드 0
- GPU 실행에서 Warp가 CUDA 12.9 runtime과 GTX 1080 Ti `sm_61`을 인식했고 XPBD kernel을 실제 compile/launch했다.
- 제한 sandbox의 CPU 실행은 숨겨진 CUDA driver에 대한 warning을 출력했지만 명시적 CPU test 자체는 통과했다.

### GPU deformable cloth smoke

```bash
python -m newton.examples cloth_hanging \
  --viewer null --test --device cuda:0 --solver vbd \
  --num-frames 100
```

- 기본 64 x 32 cloth, 2,048 particle, frame당 10 substep을 100 frame 실행했다.
- VBD deformable/contact kernel이 GTX 1080 Ti에서 compile/launch됐다.
- Newton 공식 `test_final()`의 지면 관통 및 bounded-volume 검사가 통과했고 종료 코드 0이었다.

### USD simulation data 저장 smoke

```bash
python -m newton.examples cloth_hanging \
  --viewer usd \
  --output-path artifacts/runs/newton-install-smoke-20260901/cloth_hanging_vbd.usda \
  --test --device cuda:0 --solver vbd \
  --num-frames 10 --width 16 --height 8
```

- output: `artifacts/runs/newton-install-smoke-20260901/cloth_hanging_vbd.usda`
- size: 142,779 bytes
- SHA-256: `507370669287c65159c7ec991f807e232ee907bf00207d77248b364a44383313`
- `pxr.Usd.Stage.Open()` 성공
- time code: start 0, end 10, 60 time-codes/sec
- traversed prim count: 16

전용 venv, kernel cache와 run output은 모두 기존 `artifacts/` ignore 정책 안에 있으며 다른 Python 환경을
수정하지 않았다.

## 주의와 다음 단계

- Root `.venv`의 PyTorch CUDA 13 build는 GTX 1080 Ti `sm_61` kernel을 포함하지 않으므로 Newton 실행에 쓰지 않는다.
- Newton wheel의 Warp CUDA 12.9 runtime은 local `nvcc` 없이 동작한다. 설치된 CUDA Toolkit 12.6이나
  `CUDA_HOME` 설정은 이번 smoke의 전제 조건이 아니다.
- 현재 PyPI 설치는 Newton top-level version을 1.5.1로 고정했지만 transitive dependency 전체 lock은 아니다.
  엄격한 장기 재현이 필요하면 공식 v1.5.1 release branch의 `uv.lock`을 별도 검토한다.
- Wind3DGS용 다음 작업은 별도의 승인을 거쳐 solver/material/attachment/traction schema와 wind force 적용,
  trajectory field 및 unit, refinement/convergence contract를 설계해야 한다.
