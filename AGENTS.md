# Wind3DGS Experiments Instructions

This is the experiments-focused repository inside the Wind3DGS project workspace.

Project-specific topic: CG + AI research on wind-driven deformable 3D Gaussian Splatting.

Project tag for conversation/session tracking: `Wind3DGS`.

## 기록 언어 규칙

- 2026-06-27부터 새로 작성하거나 갱신하는 실험-side 기록은 한국어를 기본 언어로 쓴다.
- 적용 대상은 실험 `README.md`, `sessions/` 기록, 실험 보고서, 산출물 설명, 작업 로그, 스크립트가 직접 남기는 설명성 로그와 상태 메시지를 포함한다.
- 명령어, 파일 경로, 코드 식별자, API 이름, 논문/데이터셋/방법론의 공식 영문 명칭은 원문을 유지한다.
- 외부 도구가 출력한 에러 메시지, 학습 로그, 라이브러리 로그처럼 원문 보존이 필요한 출력은 번역하지 않아도 된다. 다만 사람이 덧붙이는 요약과 해석은 한국어로 쓴다.
- 사용자가 명시적으로 영어 기록이나 논문 제출용 영문 문구를 요청한 경우에만 영어를 사용한다.
- 기존 영문 기록은 별도 요청이 없는 한 소급 번역하지 않는다.

Sibling work folders:

- `../code`: reusable implementation, configs, scripts, dependencies, and code-side session notes
- `../ideas`: idea sketches, checklists, bibliography, research direction changelog, and idea-side session notes
- `../experiments`: experiment READMEs, assets, outputs, reports, wrappers, and experiment-side session notes

## Startup Protocol

At the start of every meaningful task:

1. Read `../RESEARCH_PROJECT_GUIDE.md` if available from the workspace root.
2. Read this `AGENTS.md`.
3. Check the active experiment README before changing experiment files.
4. If the work depends on a milestone or research direction, check `../ideas/implementation_checklist.md` or `../ideas/idea_sketch.tex`.

## Working Loop

1. Keep experiment-specific notes, assets, outputs, reports, and thin wrappers in this folder.
2. Keep reusable implementation in `../code/wind3dgs/`.
3. Keep research framing and milestone checklists in `../ideas/`.
4. Record experiment-side work history in `sessions/`.

## Editing Rules

- Preserve existing user files unless explicitly asked to reorganize them.
- Do not put new reusable implementation directly in this folder; add or update a module under `../code/wind3dgs/` and document how the experiment uses it.
- When adding a new experiment, create or update a short `README.md` under the experiment directory.
- Keep generated outputs with the experiment that produced them.
- After meaningful experiment work, record commands, verification, outputs, blockers, and next steps in `sessions/`.

## Session Tracking

- Start substantial new conversations with a prefix like `[Wind3DGS | expNNN]` or `[Wind3DGS | code | expNNN]`.
- At the end of meaningful experiment work, create or update a note under `sessions/`.
- Name new session notes as `YYYY-MM-DD_NN_short_topic.md`, where `NN` is the next two-digit sequence for that date inside `experiments/sessions/`.
- Keep numbering independent from `../code/sessions/` and `../ideas/sessions/`.
- Do not rename legacy unnumbered notes unless the user explicitly asks for a migration.
- Use experiment READMEs for reproducible experiment records; use `sessions/` for conversation and task history.
