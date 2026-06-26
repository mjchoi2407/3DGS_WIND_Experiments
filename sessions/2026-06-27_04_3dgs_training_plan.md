# 2026-06-27 3DGS training plan for extracted datasets

## Context

The M04 data folder now contains:

- Mip-NeRF 360 scenes: `bonsai`, `garden`, `stump`, `flowers`, `treehill`
- CO3D object categories: `broccoli`, `frisbee`, `kite`, `plant`, `teddybear`, `toyplane`, `umbrella`

The next required step is to train or derive 3D Gaussian Splatting assets before mesh extraction and wind-deformation tests.

## Findings

### Mip-NeRF 360

The extracted Mip-NeRF 360 scenes already match the COLMAP-style layout expected by Graphdeco 3DGS and GOF:

```text
<scene>/
  images/
  images_2/
  images_4/
  images_8/
  sparse/0/{cameras.bin,images.bin,points3D.bin}
```

GOF's `scripts/run_mipnerf360.py` uses these image folders directly. Recommended first training factors:

- `bonsai`: `images_2` for quality, `images_4` for smoke
- `flowers`: `images_4`
- `garden`: `images_4`
- `stump`: `images_4`
- `treehill`: `images_4`

### CO3D

CO3D sequences do not directly match the COLMAP layout. Each sequence contains:

```text
images/
masks/
depths/
depth_masks/
pointcloud.ply
```

and category-level `frame_annotations.jgz` provides per-frame `viewpoint` fields:

- `R`
- `T`
- `focal_length`
- `principal_point`

This means a CO3D-to-COLMAP conversion is feasible, but it needs a dedicated converter and projection validation before 3DGS training.

## Recommended order

1. Use Mip-NeRF 360 with GOF first.
   - Fastest path because the data is already COLMAP-compatible.
   - Produces a GOF-compatible Gaussian model and mesh extraction target.

2. Run a short smoke training first, then a full 30k training.
   - Smoke: `1000` iterations on `bonsai` or `flowers`, preferably `images_4`.
   - Full: `30000` iterations with official Mip-NeRF 360 image factor.

3. Convert one CO3D sequence only after the GOF path is stable.
   - First target: `kite/414_56867_109917`.
   - Output derived COLMAP-like dataset under `derived/co3d_colmap/...`.
   - Validate camera projection before training.

## Command template

GOF smoke:

```bash
cd external/gaussian-opacity-fields
MPLCONFIGDIR=/tmp/mpl-gof OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=0 \
/home/choi/conda-envs/wind3dgs/gof/bin/python train.py \
  -s ../../experiments/M04_mesh_extraction/raw/mipnerf360/bonsai \
  -m ../../experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i1000_img4 \
  --eval \
  -i images_4 \
  --iterations 1000 \
  --test_iterations 1000 \
  --save_iterations 1000 \
  --data_device cpu
```

GOF mesh extraction after smoke:

```bash
cd external/gaussian-opacity-fields
MPLCONFIGDIR=/tmp/mpl-gof CUDA_VISIBLE_DEVICES=0 \
/home/choi/conda-envs/wind3dgs/gof/bin/python extract_mesh.py \
  -m ../../experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i1000_img4 \
  --iteration 1000
```

Expected mesh output:

```text
experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i1000_img4/test/ours_1000/fusion/mesh_binary_search_7.ply
```

## Notes

- `nvidia-smi` is blocked from the Codex sandbox by NVML access restrictions, so GPU memory should be checked from the user's terminal before long training.
- Use GOF training as the primary path for mesh extraction. Vanilla Graphdeco 3DGS remains useful for viewer checks, but GOF's own training and `extract_mesh.py` are the intended main path for this milestone.
