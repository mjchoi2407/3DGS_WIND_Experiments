# 2026-05-06 M03 procedural wind start

## Context

Started M3 after M1 static I/O and M2 mesh-proxy binding were usable enough for synthetic cloth and the synthetic leaf PLY occupancy proxy. The goal was to add a one-way procedural wind deformation before moving to a full topology-aware simulator.

## Decisions

- Implement M3 wind as global direction + strength + procedural spatial gusts, not a voxel wind grid.
- Keep two-way coupling out of scope for this milestone.
- Reuse the M2 GPU viewer and binding pipeline so wind can be compared against earlier `sine`, `bend`, `twist`, `edge_flap`, and `compound` modes.
- Add a transport comparison switch:
  - `full`: Gaussian centers plus anisotropic frame/covariance transport.
  - `position_only`: Gaussian centers follow the mesh, but canonical anisotropic frames are retained.
- Keep optional local-frame appearance correction for M9 rather than mixing it into M3.
- Add a headless Pillow-based qualitative preview renderer so M3 wind videos can be generated without opening the OpenGL viewer.

## Changed Files

- `code/wind3dgs/m03_procedural_wind/__init__.py`
- `code/wind3dgs/m03_procedural_wind/render_wind_preview.py`
- `code/wind3dgs/m03_procedural_wind/wind_field.py`
- `code/wind3dgs/m02_mesh_proxy_binding/viewer_gpu.py`
- `code/README.md`
- `experiments/M02_mesh_proxy_binding/README.md`
- `experiments/M03_procedural_wind/README.md`
- `ideas/implementation_checklist.md`
- `ideas/implementation_checklist.tex`
- `ideas/implementation_checklist.pdf`

## Verification

- Ran `PYTHONPATH=code .venv/bin/python -m py_compile code/wind3dgs/m03_procedural_wind/__init__.py code/wind3dgs/m03_procedural_wind/wind_field.py code/wind3dgs/m02_mesh_proxy_binding/viewer_gpu.py`.
- Ran `PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu --smoke-test --cells 50 --deformation wind`.
  - Result: passed for built-in `50x50` cloth sample Gaussians with `transport=full`.
- Ran `PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu --smoke-test --cells 50 --deformation wind --transport-mode position_only`.
  - Result: passed for built-in `50x50` cloth sample Gaussians with `transport=position_only`.
- Ran `PYTHONPATH=code .venv/bin/python -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu --smoke-test --cells 50 --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply --deformation wind --wind-direction 35 --wind-spatial-scale 2.4 --wind-turbulence 0.55`.
  - Result: passed for the synthetic leaf PLY occupancy proxy with `1812` Gaussians, `2085` proxy vertices, and `3968` faces.
- Ran `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --deformation wind`.
  - Result: experiment wrapper still works.
- Ran a focused anchor/free-vertex check for M3 wind deformation.
  - Result: anchored vertex max error was `0.000e+00`; free vertices had nonzero displacement.
- Rebuilt `ideas/implementation_checklist.pdf` with `xelatex`.
- Ran `PYTHONPATH=code .venv/bin/python -m py_compile code/wind3dgs/m03_procedural_wind/render_wind_preview.py`.
- Ran `PYTHONPATH=code .venv/bin/python -m wind3dgs.m03_procedural_wind.render_wind_preview --cells 10 --preset calm --frames 6 --fps 6 --width 480 --height 360 --max-gaussians 200 --wire`.
  - Result: smoke GIF and report were written under `experiments/M03_procedural_wind/outputs/`.
- Ran `PYTHONPATH=code .venv/bin/python -m wind3dgs.m03_procedural_wind.render_wind_preview --cells 50 --preset all --frames 36 --fps 12 --width 720 --height 540 --max-gaussians 1800`.
  - Result: generated `calm`, `crosswind`, and `gusty` GIF previews for the built-in `50x50` cloth sample GS asset.
- Ran `PYTHONPATH=code .venv/bin/python -m wind3dgs.m03_procedural_wind.render_wind_preview --cells 50 --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply --preset all --frames 36 --fps 12 --width 720 --height 540 --max-gaussians 1800`.
  - Result: generated `calm`, `crosswind`, and `gusty` GIF previews for the M1 synthetic leaf PLY occupancy proxy.

## Next

- Open the GPU viewer in a GUI-capable session and visually inspect `--deformation wind`.
- If the interactive behavior looks right, move toward M4: a lightweight mass-spring or XPBD-style mesh simulator.
