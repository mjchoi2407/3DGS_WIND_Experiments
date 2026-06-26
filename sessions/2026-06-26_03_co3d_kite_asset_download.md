# 2026-06-26 03 CO3D Kite Asset Download

## Goal

Find and prepare a public 3DGS-ready source asset that is more appropriate for wind/aerodynamics testing than the indoor GOF playroom smoke scene.

## Input

- Link manifest provided by user: `/mnt/h/co3d_links.txt`
- Chosen category: `kite`
- Reason: `plant` and `teddybear` are closer to the original search wording but are about `49 GiB` each; `kite` is about `11.60 GiB` and is directly wind-relevant.

## Commands

```bash
wget -c --progress=dot:giga \
  -O experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip \
  https://dl.fbaipublicfiles.com/co3d/kite.zip

unzip -tq experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip

unzip -q -n \
  experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip \
  -d experiments/M04_mesh_extraction/raw/co3d
```

## Result

- Download completed successfully.
- Archive path: `experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip`
- Archive size: `12,453,472,106` bytes (`12G` on disk)
- Integrity check: `No errors detected in compressed data`
- Extracted path: `experiments/M04_mesh_extraction/raw/co3d/kite`
- Extracted size: `12G`
- Category-level files: `LICENSE`, `sequence_annotations.jgz`, `frame_annotations.jgz`, `set_lists.json`, `eval_batches_multisequence.json`, `eval_batches_singlesequence.json`
- Sequence count: `163`
- Frame annotation count: `16,358`
- Extracted file count: `65,600`

## Candidate Selection

Generated a preview sheet at:

```text
experiments/M04_mesh_extraction/outputs/co3d_kite_candidate_preview/kite_top_sequence_contact_sheet.jpg
```

Recommended first GOF mesh extraction candidate:

- Sequence: `414_56867_109917`
- Path: `experiments/M04_mesh_extraction/raw/co3d/kite/414_56867_109917`
- Size: `168M`
- Files: `409`
- Frames: `102`
- Valid mask frames: `102 / 102`
- CO3D point cloud: `840,238` points
- Point-cloud quality score: `-0.535`
- Viewpoint quality score: `1.499`
- Visual rationale: wide triangular kite, better aerodynamic proxy than the indoor playroom and more directly wind-relevant than rigid object categories.

Backup candidates:

- `402_52522_102936`: `82M`, `102` valid-mask frames, `338,343` point-cloud points.
- `398_50636_99350`: `55M`, `102` valid-mask frames, `641,671` point-cloud points.

## Next Steps

1. Convert or adapt the selected CO3D sequence into the camera/image format expected by GOF training.
2. Run a short GOF training pass on `414_56867_109917`.
3. Run `extract_mesh.py` on the resulting GOF model and inspect the extracted mesh.
