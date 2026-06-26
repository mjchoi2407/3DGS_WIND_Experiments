# 2026-06-26 01 WSL migration runtime test

## Context

Runtime validation after moving Wind3DGS from `/mnt/h/...` into the WSL-native
workspace at `/home/choi/projects/2026_paper_work/Wind_Deformable_3DGS`.

## Verification

- M01 static 3DGS:
  - Existing synthetic leaf asset loaded successfully.
  - Render smoke wrote canonical outputs to `/tmp/wind3dgs_m01_smoke_gpucheck`.
  - Backend used `cpu_debug` as expected on the local GTX 1080 Ti.
- M02 mesh proxy binding:
  - Built-in `50x50` viewer smoke tests passed for sine, wind/full, and
    wind/position-only.
  - Synthetic leaf PLY occupancy proxy smoke tests passed for sine and wind.
  - Numeric verification logic passed for cells `10` and `50` across all five
    pre-wind deformation modes.
- M03 procedural wind:
  - Headless preview smoke rendered three short GIFs and a JSON report under
    `/tmp/wind3dgs_m03_smoke`.
- M04 mesh extraction utility:
  - SIBR-compatible viewer-safe PLY filtering passed on the GOF playroom
    `iteration_1000` PLY.
  - Result matched the previous expected counts: `123060` input vertices,
    `122612` output vertices, `448` dropped vertices.

## Notes

- No persistent experiment outputs were intentionally regenerated; smoke outputs
  were written under `/tmp`.
- A temporary `codex_smoke_leaf` M01 asset was generated to test the generator and
  then removed.
- The desktop OpenGL viewer launched briefly without immediate exception, but
  `glxinfo` reports WSLg llvmpipe software rendering.

## Next

- Confirm the interactive viewer visually from the user session.
- Keep using CPU/debug paths on this GTX 1080 Ti for local development; use a
  CC >= 7.0 GPU for `gsplat` CUDA rendering.
