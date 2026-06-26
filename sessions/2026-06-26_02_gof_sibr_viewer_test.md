# 2026-06-26 02 GOF SIBR viewer test

## Context

Smoke-tested the interactive SIBR Gaussian viewer for the GOF playroom model
after moving the Wind3DGS workspace and Conda environments into WSL-native
storage.

## Verification

Command:

```bash
env SIBR_DEFAULT_ITERATION=sibr_safe SIBR_RENDER_WIDTH=960 SIBR_RENDER_HEIGHT=540 \
  timeout 12 code/scripts/run_sibr_gaussian_viewer.sh
```

Result:

- SIBR initialized GLFW/OpenGL.
- The playroom source dataset loaded `225` input images/cameras.
- The SfM point cloud loaded with `37005` vertices.
- The SIBR-compatible GOF point cloud loaded `122612` Gaussian splats.
- CUDA rasterizer frame stats were printed repeatedly, indicating active
  rendering before `timeout` terminated the viewer.

## Notes

- Use `SIBR_DEFAULT_ITERATION=sibr_safe`; the original GOF `iteration_1000` PLY
  contains the extra `filter_3D` property and is not the SIBR-safe copy.
- The code-side launch script was updated to prefer the restored sibr env at
  `/home/choi/conda-envs/wind3dgs/sibr`.
- Some WSLg/Mesa EGL warnings remain, but they did not block rendering in the
  smoke test.

## Next

- User should visually confirm the interactive window with:

```bash
SIBR_DEFAULT_ITERATION=sibr_safe code/scripts/run_sibr_gaussian_viewer.sh
```
