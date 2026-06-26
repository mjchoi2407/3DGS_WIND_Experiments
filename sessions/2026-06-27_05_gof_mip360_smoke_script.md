# 2026-06-27 GOF Mip-NeRF 360 smoke script

## Context

The user wants to directly run a small 3DGS smoke test on the currently usable Mip-NeRF 360 data before spending time on higher-quality training.

## Added

Created:

```text
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
```

The script trains a GOF/3DGS model from a ready Mip-NeRF 360 scene. Defaults:

- Scene: `bonsai`
- Images: `images_4`
- Iterations: `1000`
- Output: `experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i1000_images_4`
- Logs: `experiments/M04_mesh_extraction/outputs/logs`

It supports:

- `--dry-run`
- `--scene`
- `--iterations`
- `--images`
- `--model-dir`
- `--gpu`
- `--run-render`
- `--run-mesh`
- `--skip-train-if-ready`
- `--backup-existing`

## Verification

Checked script syntax:

```bash
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
```

Checked help output:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --help
```

Checked path-level dry run:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --dry-run
```

Dry run resolved:

```text
scene: bonsai
source: experiments/M04_mesh_extraction/raw/mipnerf360/bonsai
images: images_4
iterations: 1000
model: experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i1000_images_4
python: /home/choi/conda-envs/wind3dgs/gof/bin/python
```

Also checked dry-run command printing for optional render and mesh steps:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --dry-run --run-render --run-mesh
```

Actual GPU training was intentionally not started. The user will run the script directly from their terminal.

## Recommended first command

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --dry-run
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
```

After the smoke model is confirmed, increase iterations and use the official image factor for quality experiments.
