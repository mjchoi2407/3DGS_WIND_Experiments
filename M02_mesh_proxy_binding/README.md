# M02 Mesh Proxy Binding

## Goal

Build clean `simulation mesh proxy` test assets for M2 and verify `Gaussian binding`, triangle-local frame transport, and covariance transport before using real 3DGS assets.

The current assets are `10x10`, `30x30`, and `50x50` square cloth grids stored as triangulated meshes. Each mesh has synthetic sample Gaussians bound to triangles through `triangle_id`, `barycentric coordinates`, `triangle local frame`, `local offset`, and anisotropic Gaussian scales.

## Input

- Procedural grid parameters in `scripts/generate_cloth_grid.py`
  - `cells = 10, 30, 50`
  - `size = 1.0`
  - plane: `z = 0`
  - anchor rule: left edge vertices are anchored
  - triangulation: two consistently wound triangles per quad
- Gaussian sampling parameters in `scripts/generate_sample_gaussians.py`
  - `samples_per_face = 2`
  - `surface_offset = 0.004`
  - scale rule: `major = size / cells * 0.30`, `minor = size / cells * 0.14`, `normal = size / cells * 0.065`

## Command

Reusable implementation now lives under `code/wind3dgs/m02_mesh_proxy_binding/`.
The commands below use experiment-local wrappers for backward compatibility.
The equivalent module form is:

```bash
PYTHONPATH=code python3 -m wind3dgs.m02_mesh_proxy_binding.viewer_gpu --smoke-test --cells 50
```

Use the project root virtual environment for GPU-viewer-related work:

```bash
source .venv/bin/activate
```

The GPU viewer also needs the system OpenGL development loader. On Ubuntu/WSL,
install:

```bash
sudo apt update
sudo apt install -y libgl-dev mesa-utils python3-tk
```

If a later GLFW/X11-related loader error appears, also install:

```bash
sudo apt install -y libegl-dev libx11-6 libxrandr2 libxinerama1 libxcursor1 libxi6
```

Generate assets:

```bash
python3 experiments/M02_mesh_proxy_binding/scripts/generate_cloth_grid.py --cells 10 30 50
python3 experiments/M02_mesh_proxy_binding/scripts/generate_sample_gaussians.py --cells 10 30 50 --samples-per-face 2 --surface-offset 0.004
```

Verify binding numerically:

```bash
python3 experiments/M02_mesh_proxy_binding/scripts/verify_gaussian_binding.py --cells 10 30 50 --frames 33 --amplitude 0.08 --frequency 1.6 --all-deformations
```

Open the viewer:

```text
experiments/M02_mesh_proxy_binding/viewer.html
```

The viewer is a dependency-free HTML file. It loads `assets/cloth_10x10_cells.js`, so it can be opened directly in a browser.
Use the asset selector in the right panel to switch between `10x10`, `30x30`, and `50x50`.

Run the GPU-backed desktop viewer:

```bash
python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --cells 50
```

Load an Inria-style 3DGS `.ply` into the M02 proxy-binding viewer:

```bash
python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py \
  --cells 50 \
  --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply
```

In PLY mode, `--cells` controls the generated proxy mesh resolution. By default,
the viewer extracts a lightweight occupancy proxy: it rasterizes Gaussian means
onto the proxy grid, keeps only Gaussian-supported cells with a one-cell
dilation, estimates proxy vertex height from nearby Gaussian means, and binds
each Gaussian to a remaining triangle with `triangle_id`, `barycentric
coordinates`, and `local offset`. It then transports the loaded Gaussian
anisotropic frame from the PLY quaternion through the deformed triangle-local
basis. The Tk control panel also has `load PLY...` and `use sample GS` buttons
for switching between a loaded PLY and the built-in synthetic sample Gaussians.
Use `--ply-proxy-mode bbox` if you need the old rectangular bounding-box proxy
for debugging.

By default, the GPU viewer opens a small control panel that mirrors the HTML
viewer controls:

- asset selector for `10x10`, `30x30`, and `50x50`
- mesh statistics: vertices, triangles, edges, anchors, Gaussians, and GS/tri
- display toggles: faces, wireframe, vertices, anchors, sample Gaussians, transported GS ellipsoids, transported GS anisotropic frames, back face culling, and depth cue
- deformation controls: mode selector, Gaussian transport selector, flutter preview, amplitude slider, frequency slider, wind direction, wind spatial scale, and turbulence sliders
- camera controls: yaw, pitch, roll sliders and reset view button
- loaded mesh and Gaussian file paths

The cloth surface uses per-frame vertex normals for directional shading, and
the mesh, vertices, anchors, and sample Gaussians use distance-based depth cueing
so the animated surface has clearer front/back separation.
Back face culling is on by default for the cloth surface. The viewer switches
front-face winding between `ccw` and `cw` from the current camera side, so
orbiting to the back side keeps the camera-facing cloth surface visible. Disable
it when debugging winding, flips, or two-sided visibility.

Keyboard and mouse controls remain available:

- left mouse drag: yaw/pitch orbit
- right mouse drag or `Shift` + left mouse drag: roll around the view axis
- mouse wheel: zoom
- `1` / `2` / `3`: load `10x10`, `30x30`, or `50x50`
- `Space`: play or pause flutter preview
- `M`: cycle deformation mode
- `T`: cycle Gaussian transport mode
- `F` / `W` / `G`: toggle faces, wireframe, or sample Gaussians
- `E`: toggle transported GS ellipsoid surfaces
- `O`: toggle transported GS anisotropic frame axes
- `A` / `V`: toggle anchors or mesh vertices
- `C`: toggle back face culling
- `D`: toggle depth cue
- arrow keys: yaw/pitch orbit
- `Z` / `X`: roll around the view axis
- `+` / `-`: adjust amplitude
- `[` / `]`: adjust frequency
- `--no-ui`: run without the optional Tk control panel
- `--deformation {sine,bend,twist,edge_flap,compound,wind}`: choose the initial deformation mode
- `--transport-mode {full,position_only}`: compare full position + frame/covariance transport against position-only Gaussian transport
- `--wind-direction`: set procedural wind direction in mesh XY degrees
- `--wind-spatial-scale`: set procedural gust phase variation over the proxy surface
- `--wind-turbulence`: set lateral flutter amount
- `--no-gaussian-ellipsoids`: hide transported GS ellipsoid surfaces
- `--gaussian-ellipsoid-scale`: scale displayed GS ellipsoid surfaces
- `--max-ellipsoid-debug-gaussians`: cap the number of displayed GS ellipsoid surfaces
- `--show-gaussian-frames`: show transported GS anisotropic frame axes at startup
- `--gaussian-frame-scale`: scale the displayed GS covariance axes
- `--max-frame-debug-gaussians`: cap the number of displayed GS frame-axis triplets
- `--no-backface-culling`: run with two-sided face rendering
- `--no-depth-cue`: run without distance-based depth cueing
- `--ply path/to/asset.ply`: load and bind an Inria-style 3DGS PLY to the generated proxy mesh
- `--ply-proxy-mode {occupancy,bbox}`: choose occupancy-extracted proxy or rectangular bounding-box proxy
- `--ply-occupancy-dilate`: adjust the occupancy proxy dilation radius in grid cells

Available deformation modes:

- `sine`: anchored sine-wave flutter
- `bend`: smooth one-sided bending from the anchored edge
- `twist`: twist around the cloth's local length direction
- `edge_flap`: stronger motion near the free edge
- `compound`: sine, bend, and twist combined
- `wind`: global wind direction plus spatial gust phase, anchor falloff, drag, bending, and lateral turbulence

Run a non-window smoke test:

```bash
python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50
python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --ply experiments/M01_static_3dgs_io/assets/synthetic_leaf_3dgs.ply
python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --deformation wind --transport-mode full
python3 experiments/M02_mesh_proxy_binding/viewer_gpu.py --smoke-test --cells 50 --deformation wind --transport-mode position_only
```

## Output

Generated files:

- `assets/cloth_*x*_cells.json`: human-readable mesh data
- `assets/cloth_*x*_cells.js`: browser-loadable mesh data for the viewer
- `assets/cloth_*x*_cells.obj`: debug mesh for Blender/MeshLab
- `assets/cloth_*x*_cells.npz`: compact mesh array bundle written without NumPy
- `assets/cloth_*x*_cells_summary.txt`: quick mesh sanity summary
- `assets/cloth_*x*_cells_gaussians.json`: human-readable sample Gaussian data
- `assets/cloth_*x*_cells_gaussians.js`: browser-loadable sample Gaussian data
- `assets/cloth_*x*_cells_gaussians.npz`: compact Gaussian array bundle written without NumPy
- `assets/cloth_*x*_cells_gaussians_summary.txt`: quick Gaussian sanity summary
- `outputs/binding_numeric_report.md`: human-readable numeric binding verification
- `outputs/binding_numeric_report.json`: machine-readable numeric binding verification
- `viewer.html`: zero-dependency Canvas 2D fallback viewer
- `viewer_gpu.py`: compatibility wrapper for the Python GPU-backed desktop debug viewer

Reusable code modules:

- `code/wind3dgs/m02_mesh_proxy_binding/generate_cloth_grid.py`
- `code/wind3dgs/m02_mesh_proxy_binding/generate_sample_gaussians.py`
- `code/wind3dgs/m02_mesh_proxy_binding/verify_gaussian_binding.py`
- `code/wind3dgs/m02_mesh_proxy_binding/viewer_gpu.py`

Expected counts:

| Mesh | Vertices | Faces | Edges | Anchors | Sample Gaussians |
| --- | ---: | ---: | ---: | ---: | ---: |
| `10x10` | `121` | `200` | `320` | `11` | `400` |
| `30x30` | `961` | `1800` | `2760` | `31` | `3600` |
| `50x50` | `2601` | `5000` | `7600` | `51` | `10000` |

## Metrics

For this first mesh-only step, use structural sanity checks:

- vertex count matches `(cells + 1)^2`
- face count matches `2 * cells^2`
- all face indices are valid
- face winding produces `+z` normals in the canonical pose
- anchor mask marks exactly the left edge
- Gaussian count matches `faces * samples_per_face`
- each Gaussian has a valid `triangle_id`
- each Gaussian has barycentric coordinates that sum to `1`
- viewer shows a square cloth, visible anchored edge, and sample Gaussians following the selected deformation mode
- GPU viewer loads `10x10`, `30x30`, and `50x50` assets and renders the dense `50x50` sample Gaussian set interactively
- GPU viewer shows depth separation through per-frame normal shading and distance-based depth cueing
- GPU viewer uses camera-adaptive back face culling by default and exposes a UI/keyboard/CLI toggle for two-sided debugging
- GPU viewer can load an Inria-style 3DGS `.ply`, extract a Gaussian occupancy proxy, and bind the loaded Gaussians to that proxy for deformation inspection
- GPU viewer can run procedural wind deformation with global direction, strength, gust frequency, spatial scale, turbulence, and anchored boundary controls
- GPU viewer can compare position-only Gaussian transport against full position + anisotropic frame/covariance transport
- numeric verification passes for barycentric recovery, local offset preservation, triangle frame determinant, transported GS frame determinant, covariance symmetry, covariance axis variance, and triangle area ratio under `sine`, `bend`, `twist`, `edge_flap`, and `compound` deformation
  - M3 smoke tests additionally verify procedural `wind` deformation for built-in cloth sample Gaussians and the M1 synthetic leaf PLY occupancy proxy

## Notes

- This step does not perform `3DGS-to-mesh extraction`.
- The current viewer is a debug visualization, not a real 3DGS renderer.
- Gaussian covariance is transported by preserving each Gaussian's canonical anisotropic frame coefficients in triangle-local coordinates, then rebuilding the frame in the deformed triangle basis.
- Numeric verification validates Gaussian center transport, local offset preservation, transported anisotropic frames, and covariance invariants. It does not yet validate real 3DGS rasterization, SH appearance, or rendered image quality.
- `viewer.html` remains the zero-setup fallback. `viewer_gpu.py` is the dense-inspection path.
- The GPU viewer currently uses Python `moderngl + glfw` because those dependencies are already in the project `.venv` and are sufficient for this debug renderer. This is an implementation choice for M02, not a paper-level dependency on OpenGL.
- The GPU viewer uses optional `tkinter` for the control panel. If `python3-tk` is not installed, it falls back to keyboard and mouse controls.
- PLY mode currently uses an XY-projected Gaussian occupancy proxy. This is appropriate for the current synthetic leaf asset; arbitrary real assets may need a manually provided proxy, multi-view/depth-based extraction, or a stronger 3DGS-to-mesh extraction path in M5/M6.
- M3 procedural wind is one-way and artist-controllable. It is not two-way fluid coupling and does not feed Gaussian or mesh motion back into a simulated wind field.
- Project root `.venv` currently has `numpy`, `moderngl`, and `glfw` installed. Use `requirements.txt` to reproduce this minimal environment.
- A stale `code/venv` directory may exist from earlier setup attempts; do not use it for this experiment.

## Run Log

### 2026-05-06

- Generated `cloth_10x10_cells` using `scripts/generate_cloth_grid.py`.
- Verified structural counts:
  - vertices: `121`
  - faces: `200`
  - edges: `320`
  - anchors: `11`
- Verified canonical face winding is `+z`.
- Added `viewer.html` for visual inspection with face, wireframe, vertex, anchor, and flutter preview controls.
- Extended generation to `10x10`, `30x30`, and `50x50`.
- Added `scripts/generate_sample_gaussians.py`.
- Generated sample Gaussians:
  - `10x10`: `400`
  - `30x30`: `3600`
  - `50x50`: `10000`
- Updated `viewer.html` to switch mesh resolution and show sample Gaussians bound to the deformed mesh.
- Added `scripts/verify_gaussian_binding.py`.
- Verified binding numerically over `33` frames at amplitude `0.08` and frequency `1.6`.
- Viewer performance note: Canvas 2D remains a fallback for quick checks; use the GPU-backed viewer for dense covariance/frame inspection.
- Set up project root `.venv` with `numpy`, `moderngl`, and `glfw`.
- Added `viewer_gpu.py`, a GPU-backed desktop debug viewer for dense mesh and sample Gaussian inspection.
- Verified `viewer_gpu.py --smoke-test` for `10x10`, `30x30`, and `50x50` assets.
- Added an optional Tk control panel to `viewer_gpu.py` with feature parity for the HTML viewer controls.
- Added per-frame normal shading and distance-based depth cueing to `viewer_gpu.py`.
- Enabled camera-adaptive back face culling by default in `viewer_gpu.py` and added UI, keyboard, and CLI toggles.
- Made viewer faces opaque in both `viewer_gpu.py` and `viewer.html`.
- Added selectable deformation modes: `sine`, `bend`, `twist`, `edge_flap`, and `compound`.
- Extended `verify_gaussian_binding.py` with `--deformation` and `--all-deformations`.
- Verified `10x10`, `30x30`, and `50x50` assets over all five deformation modes for `33` frames.
- Updated sample Gaussian scales to explicit anisotropic axes: major, minor, and normal.
- Added triangle-local anisotropic frame transport and covariance reconstruction.
- Added transported GS ellipsoid surface visualization and optional frame-axis visualization to `viewer_gpu.py`.
- Added anisotropic ellipse/frame display to `viewer.html`.
- Extended numeric verification to cover transported GS frame determinant, covariance symmetry, covariance axis variance, and triangle-local coefficient preservation.
- Re-verified all `10x10`, `30x30`, and `50x50` assets over all five deformation modes for `33` frames after covariance transport was added.
- Changed the GPU viewer default from axes-only inspection to sampled ellipsoid surfaces. Use `E` to toggle ellipsoids and `O` to toggle axes.
- Added PLY loading to `viewer_gpu.py`. The viewer can now load the M1 synthetic leaf `.ply`, extract an occupancy proxy from PLY Gaussian means, bind each Gaussian to a proxy triangle, and inspect deformation transport with existing M2 controls.
- Changed PLY mode's default proxy from rectangular bounding-box grid to occupancy-extracted silhouette proxy. The old rectangular proxy remains available through `--ply-proxy-mode bbox`.
