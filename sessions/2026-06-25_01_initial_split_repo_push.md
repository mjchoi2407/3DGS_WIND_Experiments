# 2026-06-25 01 initial split repo push

## Context

The user asked to review today's session history, summarize the work, and push the split Git repositories.

## Reviewed Sessions

- `sessions/2026-06-24_01_project_internal_split_cleanup.md`
- `sessions/2026-06-24_02_session_numbering_rules.md`
- `sessions/2026-06-24_03_mesh_extraction_data_prep.md`
- `sessions/2026-06-24_04_gof_playroom_3dgs_smoke.md`
- `sessions/2026-06-24_05_gof_render_preview.md`

## Summary

- The Wind3DGS workspace now keeps experiment records and reproducible outputs in the independent `experiments/` repository.
- The experiments repository remote is `git@github.com:mjchoi2407/3DGS_WIND_Experiments.git`.
- Experiment-side session notes were moved under `experiments/sessions/` and renamed into the numbered `YYYY-MM-DD_NN_short_topic.md` convention.
- `M04_mesh_extraction` records the GOF/SuGaR data strategy, the official 3DGS T&T+DB dataset candidate, and the approved GOF playroom smoke run.
- GOF playroom smoke training generated a 1000-iteration model locally, and GOF rendering produced a recognizable preview, but downloaded datasets, trained models, and heavy M04 outputs are ignored.

## Push Scope

- Initial experiments repository files.
- Experiment READMEs, reusable small assets, scripts, selected reports/previews, and experiment-side session records.
- Heavy public datasets, trained model checkpoints, and M04 generated outputs remain ignored.

## Next

- Commit this repository and push `main` to `origin`.
- Keep future experiment-side work history in `experiments/sessions/`.
