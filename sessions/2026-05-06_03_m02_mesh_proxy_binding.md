# 2026-05-06 M02 mesh proxy binding start

## Context

Started the first concrete implementation artifact for M2. The goal is to validate the clean `simulation mesh proxy` side before adding `Gaussian binding`.

## Decisions

- Use milestone-tag experiment naming for the active implementation folder: `experiments/M02_mesh_proxy_binding/`.
- Start from a `10x10` square cloth grid before scaling to `50x50`.
- Store the grid as a triangular mesh because later Gaussian binding will attach each Gaussian to a triangle.
- Anchor the left edge, matching a simple flag/cloth setup.
- Provide both data files and a visual inspection tool before generating synthetic Gaussians.
- Added `30x30` and `50x50` mesh resolutions.
- Added sample Gaussian placement with two Gaussians per triangle.
- The viewer now lets the user switch mesh resolution and shows sample Gaussians bound to the deformed mesh.
- Added numeric verification for Gaussian binding invariants under procedural deformation.
- Noted that the Canvas 2D viewer is expected to be slow for dense assets and should be replaced or supplemented by a GPU-backed viewer.
- Confirmed project root `.venv` is available with `numpy`, `moderngl`, and `glfw`.
- Chose a custom minimal GPU debug viewer for M02. The implementation uses `ModernGL + GLFW` because the environment is already prepared for it; this does not make OpenGL a paper-level requirement.
- Added an optional `tkinter` control panel to `viewer_gpu.py` so the GPU viewer exposes the same practical controls as `viewer.html`: asset selection, mesh statistics, display toggles, animation toggle, amplitude/frequency sliders, reset view, and loaded file paths.
- Added per-frame vertex normal shading and distance-based depth cueing to `viewer_gpu.py` after the user noted that depth separation was hard to read.
- Enabled back face culling by default for GPU viewer face rendering and added controls through the Tk UI, `C` key, and `--no-backface-culling`.
- Updated back face culling to be camera-adaptive: the viewer switches front-face winding between `ccw` and `cw` based on the current camera side and flips the shading normal sign accordingly.
- Added full yaw/pitch/roll camera controls. Left drag controls yaw/pitch, right drag or `Shift`+left drag controls roll, the control panel exposes yaw/pitch/roll sliders, and keyboard arrows plus `Z`/`X` adjust rotation.
- Made viewer face surfaces opaque.
- Added selectable deformation modes to both viewers: `sine`, `bend`, `twist`, `edge_flap`, and `compound`. The GPU viewer also supports `--deformation` and `M` key cycling.
- M2 check result before covariance work: Gaussian center transport and local offset preservation were numerically stable across all current synthetic deformation modes.
- Added triangle-local anisotropic frame transport. Each Gaussian preserves canonical frame coefficients in triangle-local coordinates and rebuilds its world-space frame/covariance from the deformed triangle basis.
- Updated sample Gaussian scales to explicit major/minor/normal anisotropy so orientation transport is visible in the debug viewers.
- Added sampled transported GS ellipsoid surfaces to the GPU viewer because axes alone were hard to inspect visually. Ellipsoids are on by default; frame axes are optional.
- Added PLY loading to the M2 GPU viewer so the M1 synthetic leaf `.ply` can be bound to a generated proxy grid and inspected with the existing deformation controls.
- Initial PLY mode used an XY grid over the Gaussian mean bounding box. This was useful for a debug path but left visible mesh outside the current leaf-like asset.
- Replaced the default PLY proxy with a lightweight Gaussian occupancy extraction path after observing that the rectangular proxy left mesh outside the leaf area. The old rectangular proxy remains available as `--ply-proxy-mode bbox`.

## Changed Files

- `experiments/M02_mesh_proxy_binding/README.md`
- `experiments/M02_mesh_proxy_binding/scripts/generate_cloth_grid.py`
- `experiments/M02_mesh_proxy_binding/scripts/generate_sample_gaussians.py`
- `experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py`
- `experiments/M02_mesh_proxy_binding/viewer.html`
- `experiments/M02_mesh_proxy_binding/viewer_gpu.py`
- `experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply`
- `experiments/M02_mesh_proxy_binding/assets/cloth_10x10_cells.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_30x30_cells.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_50x50_cells.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_10x10_cells_gaussians.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_30x30_cells_gaussians.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_50x50_cells_gaussians.*`
- `experiments/M02_mesh_proxy_binding/outputs/binding_numeric_report.md`
- `experiments/M02_mesh_proxy_binding/outputs/binding_numeric_report.json`
- `ideas/implementation_checklist.md`
- `ideas/implementation_checklist.tex`
- `requirements.txt`
- `.gitignore`

## Verification

- Ran `python3 experiments/M02_mesh_proxy_binding/scripts/generate_cloth_grid.py`.
- Generated counts:
  - vertices: `121`
  - faces: `200`
  - edges: `320`
  - anchors: `11`
- Verified JSON mesh counts and endpoints.
- Verified NPZ bundle entries and NPY headers with Python stdlib.
- Rebuilt `ideas/implementation_checklist.pdf` after checklist updates.
- Ran `python3 experiments/M02_mesh_proxy_binding/scripts/generate_cloth_grid.py --cells 10 30 50`.
- Ran `python3 experiments/M02_mesh_proxy_binding/scripts/generate_sample_gaussians.py --cells 10 30 50 --samples-per-face 2 --surface-offset 0.004`.
- Verified generated counts:
  - `10x10`: `121` vertices, `200` faces, `320` edges, `11` anchors, `400` Gaussians.
  - `30x30`: `961` vertices, `1800` faces, `2760` edges, `31` anchors, `3600` Gaussians.
  - `50x50`: `2601` vertices, `5000` faces, `7600` edges, `51` anchors, `10000` Gaussians.
- Verified Gaussian `triangle_id` ranges and barycentric coordinate sums.
- Verified mesh and Gaussian NPZ bundle headers.
- Ran `python3 experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py --cells 10 30 50 --frames 33 --amplitude 0.08 --frequency 1.6`.
- Numeric binding verification passed for all three resolutions.
- Checked local Python viewer-related packages. Project root `.venv` has `numpy`, `moderngl`, and `glfw`; `OpenGL`, `pyglet`, `vispy`, `PySide6`, and `PyQt6` are not installed.
- Ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py`.
- Ran GPU viewer smoke tests without opening a window:
  - `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 10`
  - `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 30`
  - `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50`
- Smoke tests passed for all three resolutions.
- Tried a standalone ModernGL context check, but the current shell cannot open a display: `(standalone) XOpenDisplay: cannot open display`. The viewer should be run from a GUI-capable WSLg/X session.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the GPU viewer decision.
- User hit `libGL.so: cannot open shared object file` when launching `viewer_gpu.py`. Local package check shows `libGL.so.1` is installed but `libgl-dev` is missing, so the README now records the Ubuntu/WSL system dependency command.
- Checked `tkinter`; it is not currently installed in this shell, so the viewer falls back to keyboard/mouse controls until `python3-tk` is installed.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding the optional control panel.
- Re-ran smoke tests for `10x10`, `30x30`, and `50x50` after adding the optional control panel.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the GPU viewer control panel status.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding shading/depth cue code.
- Re-ran smoke tests for `10x10`, `30x30`, and `50x50` after adding shading/depth cue code.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the shading/depth cue update.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding back face culling controls.
- Re-ran smoke tests for `10x10`, `30x30`, and `50x50` after adding back face culling controls.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the back face culling update.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after making culling camera-adaptive.
- Re-ran smoke tests for `10x10`, `30x30`, and `50x50` after making culling camera-adaptive.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the camera-adaptive culling update.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding yaw/pitch/roll camera controls.
- Re-ran smoke tests for `10x10`, `30x30`, and `50x50` after adding yaw/pitch/roll camera controls.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the yaw/pitch/roll camera controls.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding selectable deformation modes and opaque faces.
- Re-ran GPU viewer smoke tests for all five deformation modes on `50x50`, plus `compound` on `10x10`.
- Rebuilt `ideas/implementation_checklist.pdf` after recording opaque faces and selectable deformation modes.
- Extended `verify_gaussian_binding.py` to support `--deformation` and `--all-deformations`.
- Ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py`.
- Ran `.venv/bin/python experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py --cells 10 30 50 --frames 33 --amplitude 0.08 --frequency 1.6 --all-deformations`.
- Numeric verification passed for all `15` combinations: `10x10`, `30x30`, and `50x50` assets under `sine`, `bend`, `twist`, `edge_flap`, and `compound`.
- Re-ran GPU viewer smoke tests for all five deformation modes on `50x50`.
- Regenerated `cloth_*_cells_gaussians.*` assets after changing the scale rule to anisotropic major/minor/normal axes.
- Extended `verify_gaussian_binding.py` to check transported GS frame determinant, triangle-local coefficient preservation, covariance symmetry, covariance axis error, and positive covariance axis variance.
- Re-ran `.venv/bin/python experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py --cells 10 30 50 --frames 33 --amplitude 0.08 --frequency 1.6 --all-deformations`; all `15` combinations passed with max GS frame determinant error <= `8.881784e-16` and max covariance axis error <= `1.517883e-18`.
- Re-ran `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --deformation ...` for all five deformation modes; all passed with finite transported frames and covariance matrices.
- Added `--no-gaussian-ellipsoids`, `--gaussian-ellipsoid-scale`, and `--max-ellipsoid-debug-gaussians` to `viewer_gpu.py`.
- Changed GPU viewer startup behavior so ellipsoid surfaces are visible by default and frame axes are off unless enabled with UI, `O`, or `--show-gaussian-frames`.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py`.
- Re-ran GPU viewer smoke tests for all five deformation modes on `50x50`; all passed after ellipsoid mesh generation was added.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding PLY loading.
- Ran `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply --deformation compound`.
  - Result: passed with `1812` Gaussians bound to the generated `50x50` proxy.
  - Max transported GS frame determinant error: `3.576e-07`.
  - Max covariance symmetry error: `1.091e-11`.
- Ran a focused canonical PLY binding check for `50x50`.
  - Gaussian count: `1812`.
  - Proxy faces: `5000`.
  - Max reconstructed center error against the original PLY means: `0.000e+00`.
  - Max barycentric sum error: `0.000e+00`.
  - Max frame determinant error: `3.576e-07`.
- Ran PLY smoke tests for `10x10` under `sine` and `30x30` under `twist`; both passed.
- Re-ran the existing built-in sample GS smoke test with `--cells 50 --deformation compound`; it still passed.
- Rebuilt `ideas/implementation_checklist.pdf` after recording the PLY loader path.
- Re-ran `.venv/bin/python -m py_compile experiments/M02_mesh_proxy_binding/viewer_gpu.py` after adding occupancy proxy extraction.
- Ran `.venv/bin/python experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply --deformation compound`.
  - Result: passed with an occupancy proxy of `2085` vertices, `3968` faces, `6052` edges, and `36` anchors.
  - This is reduced from the rectangular `50x50` bbox proxy's `2601` vertices and `5000` faces.
  - Max transported GS frame determinant error: `4.768e-07`.
  - Max covariance symmetry error: `1.091e-11`.
- Ran the old rectangular path with `--ply-proxy-mode bbox`; it still passed.
- Ran occupancy PLY smoke tests for `10x10` under `sine` and `30x30` under `twist`; both passed.
- Ran a focused canonical occupancy proxy binding check for `50x50`.
  - Max reconstructed center error against original PLY means: `6.008e-08`.
  - Max barycentric sum error: `0.000e+00`.
  - Max frame determinant error: `5.960e-07`.

## Next

- Open `experiments/M02_mesh_proxy_binding/viewer.html` and visually inspect `10x10`, `30x30`, and `50x50` assets.
- Run `python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --cells 50` from the project `.venv` in a GUI-capable session.
- Run `python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --cells 50 --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply` to inspect proxy binding for the M1 leaf asset.
- If `libGL.so` is missing, install `libgl-dev` and retry the GPU viewer.
- If the control panel does not appear, install `python3-tk` and retry the GPU viewer.
- Add a small debug readout for selected Gaussian binding values if visual inspection is not enough.
- Add captured before/after frames or short videos from the debug viewer.
- Connect the same covariance transport path to a real 3DGS rasterizer path once M1 is available.
