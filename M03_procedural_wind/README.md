# M03 Procedural Wind Deformation

## Goal

Replace hand-authored M02 deformation modes with a lightweight one-way procedural wind field, then verify that mesh-bound Gaussians remain stable under wind-like motion.

This milestone is intentionally not a two-way coupled fluid simulation. Wind is an external controllable signal: global direction and strength, plus procedural spatial gusts over the proxy surface.

## Input

- Reusable implementation:
  - `code/wind3dgs/m03_procedural_wind/wind_field.py`
  - `code/wind3dgs/m02_mesh_proxy_binding/viewer_gpu.py`
- Built-in M02 cloth proxy assets: `10x10`, `30x30`, `50x50`
- Optional M1 synthetic Inria-style 3DGS PLY:
  - `experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply`

## Command

Run procedural wind on the built-in sample Gaussians:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu \
  --cells 50 \
  --deformation wind \
  --wind-direction 35 \
  --wind-spatial-scale 2.4 \
  --wind-turbulence 0.55
```

Run the same path in non-window smoke-test mode:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu \
  --smoke-test \
  --cells 50 \
  --deformation wind
```

Compare Gaussian transport modes:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu \
  --smoke-test \
  --cells 50 \
  --deformation wind \
  --transport-mode full

PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu \
  --smoke-test \
  --cells 50 \
  --deformation wind \
  --transport-mode position_only
```

Verify the synthetic leaf PLY occupancy proxy under wind:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu \
  --smoke-test \
  --cells 50 \
  --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply \
  --deformation wind \
  --wind-direction 35 \
  --wind-spatial-scale 2.4 \
  --wind-turbulence 0.55
```

Render headless qualitative GIF previews for multiple wind settings:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m03_procedural_wind.render_wind_preview \
  --cells 50 \
  --preset all \
  --frames 36 \
  --fps 12 \
  --width 720 \
  --height 540 \
  --max-gaussians 1800
```

Render the same presets for the M1 synthetic leaf PLY occupancy proxy:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m03_procedural_wind.render_wind_preview \
  --cells 50 \
  --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply \
  --preset all \
  --frames 36 \
  --fps 12 \
  --width 720 \
  --height 540 \
  --max-gaussians 1800
```

## Output

- Viewer UI exposes `procedural wind` as a deformation mode.
- Viewer UI exposes:
  - wind direction
  - amplitude as wind strength
  - frequency as gust frequency
  - wind spatial scale
  - turbulence
  - Gaussian transport mode: `position + frame/covariance` or `position only`
- Smoke tests print bounding boxes and covariance/frame invariants.
- Headless preview renderer writes GIF, poster PNG, and JSON reports under `experiments/M03_procedural_wind/outputs/`.

Generated qualitative previews:

- `cloth_50x50_cells_calm_full.gif`
- `cloth_50x50_cells_crosswind_full.gif`
- `cloth_50x50_cells_gusty_full.gif`
- `synthetic_leaf_3dgs_50x50_occupancy_PLY_proxy_calm_full.gif`
- `synthetic_leaf_3dgs_50x50_occupancy_PLY_proxy_crosswind_full.gif`
- `synthetic_leaf_3dgs_50x50_occupancy_PLY_proxy_gusty_full.gif`

## Metrics

- Anchored vertices remain fixed.
- Free vertices move under procedural wind.
- Gaussian centers stay finite.
- Transported anisotropic frames remain near-orthonormal.
- Gaussian covariances remain symmetric with positive axis variance.
- `full` and `position_only` transport modes both run, so visual comparison can focus on covariance/frame transport rather than center binding.

## Notes

- M3 uses global wind plus procedural spatial gusts, not a voxel wind grid.
- Two-way coupling is out of scope for the current idea sketch.
- M4 is the next step if we want topology-aware dynamics through a small mass-spring or XPBD-style mesh simulator.
