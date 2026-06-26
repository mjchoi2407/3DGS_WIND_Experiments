# 2026-06-26 04 - CO3D batch download and umbrella assembly recovery

## Context

- Target categories: `broccoli`, `frisbee`, `plant`, `teddybear`, `toyplane`, `umbrella`.
- `broccoli`, `frisbee`, `plant`, `teddybear`, and `toyplane` completed as regular zip downloads.
- `umbrella.zip` single-connection download was slow, so it was converted to HTTP range parts under:
  - `experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip.parts/`

## Current umbrella state

- All range parts `part_001` through `part_012` were downloaded with expected sizes.
- `part_000` was moved into the beginning of the final `umbrella.zip` during an earlier assembly attempt.
- Final zip path:
  - `experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip`
- Last observed final zip size:
  - `6,203,795,719 bytes`
- Expected final zip size:
  - `41,944,422,600 bytes`

## Fixes added

- Added resumable assembler:
  - `experiments/M04_mesh_extraction/scripts/assemble_parts_resume.py`
- Added visible user-facing wrapper:
  - `experiments/M04_mesh_extraction/scripts/run_umbrella_assemble_visible.sh`
- Updated `parallel_range_download.sh` to use the Python resumable assembler instead of shell append/dd assembly.

## How to continue manually

Run from project root:

```bash
./experiments/M04_mesh_extraction/scripts/run_umbrella_assemble_visible.sh
```

The wrapper prints progress to stdout and also writes:

```text
experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella_assemble_latest.log
```

After the output size reaches `41,944,422,600 bytes`, run:

```bash
unzip -tq experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip
```
