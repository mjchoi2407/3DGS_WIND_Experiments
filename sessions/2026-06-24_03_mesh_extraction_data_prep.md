# 2026-06-24 03 Mesh Extraction Data Prep

## Context

The next implementation target is mesh extraction adapter development for GOF as the main extractor and SuGaR/TSDF as comparison paths. Before implementation, public test data candidates were checked.

## Findings

- Existing local assets are only synthetic leaf PLY and M2 cloth proxy files; they are useful for Wind3DGS-internal viewer tests but not sufficient for external GOF/SuGaR mesh extraction pipelines.
- GOF official README states that custom datasets follow the 3DGS data format and shows training/extraction with a Tanks and Temples scene.
- SuGaR full pipeline documentation uses a COLMAP dataset path as the main input.
- Official 3DGS T&T+DB COLMAP archive is reachable and about 651 MiB:
  - `https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip`
  - HEAD `Content-Length`: `682628995`
- GOF official TNT_GOF dataset is reachable but about 8 GB:
  - `https://huggingface.co/datasets/ZehaoYu/gaussian-opacity-fields/tree/main`
  - HEAD `Content-Length`: `8004621817`
- Official 3DGS pre-trained models are reachable but about 13.6 GB:
  - HEAD `Content-Length`: `14660630999`

## Changes

- Added `experiments/M04_mesh_extraction/README.md` with the data strategy and candidate analysis.
- Added `experiments/M04_mesh_extraction/scripts/download_official_3dgs_tandt_db.sh`.
- Updated `experiments/.gitignore` so downloaded archives, raw data, model outputs, and extraction outputs are not accidentally tracked.

## Recommendation

Use a two-stage data plan:

1. Generate a tiny local synthetic COLMAP-style fixture for adapter smoke tests.
2. Download the official 3DGS T&T+DB COLMAP dataset when the user approves a 651 MiB public data download.

The larger GOF TNT_GOF archive should be deferred until the adapter is stable.
