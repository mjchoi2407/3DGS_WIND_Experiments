# 2026-06-24 04 GOF Playroom 3DGS Smoke

## Context

The user approved downloading the previously selected official 3DGS T&T+DB COLMAP dataset and requested generating a 3DGS model first, before mesh extraction.

## Data

- Downloaded official 3DGS T&T+DB COLMAP archive:
  - `experiments/M04_mesh_extraction/downloads/tandt_db.zip`
  - Size: about 652 MiB on disk
- Extracted scenes:
  - `raw/db/drjohnson`
  - `raw/db/playroom`
  - `raw/tandt/train`
  - `raw/tandt/truck`
- Chosen first smoke scene: `raw/db/playroom`
  - 225 images
  - about 151 MiB extracted

## Command

```bash
cd external/gaussian-opacity-fields
MPLCONFIGDIR=/tmp/mpl-gof ../miniforge3/bin/conda run -n gof python train.py \
  -s ../../experiments/M04_mesh_extraction/raw/db/playroom \
  -m ../../experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8 \
  -r 8 \
  --iterations 1000 \
  --test_iterations 1000 \
  --save_iterations 1000 \
  --data_device cpu
```

## Outcome

- Initial sandboxed training failed because GOF imports `network_gui.py`, which creates a TCP socket during import:
  - `PermissionError: [Errno 1] Operation not permitted`
- Re-running with escalated permissions succeeded.
- Training completed at 1000 iterations.
- Reported train metric at iteration 1000:
  - `L1 0.03587201423943043`
  - `PSNR 25.656330490112307`
- Generated Gaussian PLY:
  - `experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/point_cloud/iteration_1000/point_cloud.ply`
  - Header: `format binary_little_endian 1.0`
  - Vertex count: `123060`
  - Size: about 30 MiB

## Next

- Render a small set of views from the generated model for visual confirmation.
- Then run `extract_mesh.py` on `iteration_1000` as a first pipeline smoke test.
- Later, repeat with 7000 or 30000 iterations for quality-oriented extraction.
