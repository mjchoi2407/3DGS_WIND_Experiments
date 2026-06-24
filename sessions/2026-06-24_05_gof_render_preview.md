# 2026-06-24 05 GOF Render Preview

## Context

The user asked whether there is a renderer for visual inspection of the generated GOF/3DGS model.

## Decision

- Use GOF's own `render.py` for this checkpoint because it reads the saved GOF/3DGS model, `cfg_args`, source cameras, and Gaussian representation directly.
- The older Wind3DGS M01 renderer is useful for synthetic/minimal assets, and the M2 viewer is useful for proxy-binding/debug visualization, but neither is the right first renderer for this trained GOF model.

## Command

Initial sandboxed rendering failed because CUDA was hidden from the sandbox:

```text
RuntimeError: Found no NVIDIA driver on your system.
```

Rendering succeeded with escalated GPU access:

```bash
cd external/gaussian-opacity-fields
MPLCONFIGDIR=/tmp/mpl-gof ../miniforge3/bin/conda run -n gof python render.py \
  -m ../../experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8 \
  --iteration 1000 \
  --skip_test
```

## Outputs

- Render root:
  - `experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/train/ours_1000`
- Prediction images:
  - `test_preds_8`
  - 225 PNGs
- GT images:
  - `gt_8`
  - 225 PNGs
- Preview folder:
  - `experiments/M04_mesh_extraction/outputs/gof_playroom_i1000_r8_preview`
- Contact sheet:
  - `contact_sheet_gt_vs_pred.jpg`
  - size: `464 x 1464`

## Visual Check

The `1000` iteration model reconstructs the playroom scene recognizably. Some views are blurry or incomplete, which is expected for this short smoke run. The result is sufficient to confirm that the downloaded COLMAP scene, GOF training, saved Gaussian model, and GOF renderer are connected correctly.

## Next

- Run GOF `extract_mesh.py --iteration 1000` for the first mesh extraction smoke test.
- Later repeat with `7000` or `30000` iterations for quality-oriented extraction.
