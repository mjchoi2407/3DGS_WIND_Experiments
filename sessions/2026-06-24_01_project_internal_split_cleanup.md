# 2026-06-24 project internal split cleanup

## Context

The split repository setup was corrected so the three Git repositories live inside the original project directory instead of as sibling folders outside it.

## Decisions

- Use `experiments/` as the independent experiments Git repository inside `Wind_Deformable_3DGS/`.
- Keep experiment-side session history in `experiments/sessions/`.
- Configure `experiments/` with `origin` set to `git@github.com:mjchoi2407/3DGS_WIND_Experiments.git`.
- Leave commit and push for later review.

## Changed Files

- `AGENTS.md`
- `.gitignore`
- `README.md`
- `sessions/`

## Verification

- `git -C experiments remote -v` shows the expected SSH remote.
- `find experiments -maxdepth 2 -type d -name sessions` shows `experiments/sessions`.

## Next

- Review, then run `git -C experiments add -A && git -C experiments commit -m "Initial experiments repository"` when ready.
