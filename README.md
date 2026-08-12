# Wind3DGS Experiments

Experiment notes, assets, outputs, reports, and thin wrappers for the Wind3DGS project.

## Current Direction

The active method is indexed by `../ideas/README.md`. New experiments use the `TD##` namespace. TD00 establishes contracts, manifests, artifact ownership, and regression tests before any Global--Local solver milestone is marked complete.

## Legacy and Support Index

| Directory | Current role | Mainline status |
| --- | --- | --- |
| `M01_static_3dgs_io/` | Static GS I/O and renderer baseline; candidate TD01 fixture | Revalidate before reuse |
| `M02_mesh_proxy_binding/` | Synthetic cloth assets, transport checks, and legacy mesh-proxy comparison | Not the target runtime |
| `M03_procedural_wind/` | Qualitative prescribed-wind deformation fixture | Not a physical solver or teacher |
| `M04_mesh_extraction/` | Offline GS reconstruction/mesh preprocessing and mesh baseline support | Training/evaluation only |
| `exp001_baseline_3dgs/`--`exp003_wind_prior/` | Inactive early placeholders | No current completion evidence |

Historical commands and outputs remain in their original directories for reproducibility. Their old milestone status is not inherited by TD00--TD14.

## Project-Internal Split

- `../code`: reusable implementation and code-side session notes
- `../ideas`: idea sketches, bibliography, checklists, and idea-side session notes
- `../experiments`: experiment READMEs, assets, outputs, reports, and experiment-side session notes

## Working Notes

- Use each experiment directory's `README.md` for reproducible setup, commands, metrics, and observations.
- Use `sessions/` for conversation and task history local to this experiments folder.
- Keep reusable implementation in `../code`.
- Keep research framing and milestone checklists in `../ideas`.
