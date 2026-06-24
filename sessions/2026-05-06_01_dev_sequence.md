# 2026-05-06 development sequence

## Context

The implementation is about to begin for the wind-driven deformable 3DGS project. Current project direction is a hybrid pipeline: trained 3DGS input, lightweight simulation mesh proxy, Gaussian-to-mesh binding, wind-driven mesh dynamics, Gaussian attribute transport, and optional SH residual appearance correction.

## Decisions

- Start from a small synthetic mesh-to-Gaussian prototype before using real 3DGS assets.
- Validate the representation bridge first: proxy mesh, barycentric binding, local frames, covariance transport, and rendering sanity checks.
- Add wind physics and exposure only after the static binding/deformation path is reliable.
- Treat SH residual prediction as a later fidelity module, not the first implementation target.
- Added an implementation checklist under `ideas/` to track milestone-level progress.
- Converted the checklist into a LaTeX source for easier PDF viewing.
- Rewrote the checklist in Korean for day-to-day progress tracking while keeping paper terms and proper nouns in English.
- Updated the experiment naming convention to use development milestone tags such as `M02_mesh_proxy_binding` instead of sequential `expNNN` prefixes for new implementation work.
- Started `experiments/M02_mesh_proxy_binding/` with a generated 10x10 triangular cloth mesh and a simple HTML viewer.
- Extended M02 assets to `10x10`, `30x30`, and `50x50`, and added sample Gaussian placement plus viewer resolution switching.
- Added numeric Gaussian binding verification under procedural deformation.
- Recorded the need for a future GPU-backed viewer because the current Canvas 2D viewer is slow for dense assets.
- Confirmed project root `.venv` with `numpy`, `moderngl`, and `glfw`, and added `requirements.txt`.
- Added `viewer_gpu.py` as the M02 GPU-backed desktop debug viewer and kept `viewer.html` as the zero-setup fallback.
- Added an optional `tkinter` control panel to `viewer_gpu.py` so the GPU viewer exposes the same controls as `viewer.html`.
- Added per-frame vertex normal shading and distance-based depth cueing to improve depth readability in the GPU viewer.
- Enabled back face culling by default in the GPU viewer and added UI, keyboard, and CLI toggles.
- Updated GPU viewer back face culling to be camera-adaptive by switching front-face winding based on the current camera side.
- Added yaw/pitch/roll camera controls to the GPU viewer, including roll by right drag or `Shift`+left drag.
- Made viewer faces opaque and added selectable deformation modes: `sine`, `bend`, `twist`, `edge_flap`, and `compound`.

## Changed Files

- `ideas/implementation_checklist.md`
- `ideas/implementation_checklist.tex`
- `experiments/M02_mesh_proxy_binding/README.md`
- `experiments/M02_mesh_proxy_binding/scripts/generate_cloth_grid.py`
- `experiments/M02_mesh_proxy_binding/scripts/generate_sample_gaussians.py`
- `experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py`
- `experiments/M02_mesh_proxy_binding/viewer.html`
- `experiments/M02_mesh_proxy_binding/viewer_gpu.py`
- `experiments/M02_mesh_proxy_binding/assets/cloth_10x10_cells.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_30x30_cells.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_50x50_cells.*`
- `experiments/M02_mesh_proxy_binding/assets/cloth_*_gaussians.*`
- `experiments/M02_mesh_proxy_binding/outputs/binding_numeric_report.*`
- `requirements.txt`
- `.gitignore`
- `sessions/2026-05-06_dev_sequence.md`
- `sessions/2026-05-06_m02_mesh_proxy_binding.md`

## Next

- Create the first implementation milestone under `code/` for synthetic mesh proxy binding.
- Add or update an experiment README for the active prototype before implementation.
- Run the GPU viewer from a GUI-capable session: `python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --cells 50`.
- Install `python3-tk` if the GPU viewer control panel does not appear.
- Continue M02 with covariance or anisotropic-frame transport.

## Build Notes

- Built `ideas/implementation_checklist.pdf` successfully from `ideas/implementation_checklist.tex`.
- Build command: `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=ideas ideas/implementation_checklist.tex`
- Note: LaTeX reported one small overfull table warning, but the PDF was generated successfully.
- Built the Korean `ideas/implementation_checklist.pdf` successfully with `xelatex`.
- Build command: `latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=ideas ideas/implementation_checklist.tex`
- Rebuilt `ideas/implementation_checklist.pdf` after adding the milestone-tag experiment naming convention.
- Rebuilt `ideas/implementation_checklist.pdf` after marking M0 complete and M2 in progress.
- Rebuilt `ideas/implementation_checklist.pdf` after adding the M02 GPU viewer status and renderer decision.
- Rebuilt `ideas/implementation_checklist.pdf` after adding the GPU viewer control panel status.
- Rebuilt `ideas/implementation_checklist.pdf` after adding the GPU viewer shading/depth cue status.
- Rebuilt `ideas/implementation_checklist.pdf` after adding the GPU viewer back face culling status.
- Rebuilt `ideas/implementation_checklist.pdf` after making GPU viewer culling camera-adaptive.
- Rebuilt `ideas/implementation_checklist.pdf` after adding yaw/pitch/roll camera control status.
- Rebuilt `ideas/implementation_checklist.pdf` after adding opaque faces and selectable deformation mode status.
