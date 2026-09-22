# Wind3DGS Experiments Instructions

Wind3DGS의 experiments 독립 저장소다. 공통 지침은 [`../AGENTS.md`](../AGENTS.md)를 적용한다.
상위 지침이 자동 로드되지 않은 하위 저장소 단독 실행에서도 직접 확인한다. 이미 확인한 내용은 반복 출력하지 않는다.
공통 언어·기록·Git·보안·LaTeX 규칙을 이 파일에 복제하지 않는다.

## Startup Protocol

- 공통 시작 절차에 따라 `README.md`, `sessions/README.md`의 최신 요약을 확인한다.
- 실행·수정 전에 active experiment README를 읽고 연구 계약이 필요한 경우 해당 R 절만 확인한다.
- 시뮬레이션 상태·결과·계산 시간 검토에는 `artifacts/runs/sub_pc/<run ID>/`도 포함한다. 서브컴은 공유 코드를 읽고 자체 CPU/GPU로 계산한다. 각 run의 설정·manifest·로그로 실험을 식별하고 메인컴과 비교할 때 조건·계산 구간·장치 차이를 확인한다. 별도 요청 없이 실행을 중단하거나 기존 결과를 수정·삭제하지 않는다.
- Dataset/model/run/external/environment/artifact 작업은 `../manifests/`의 관련 기록을 확인한다.

## Editing Rules

- Preserve existing user files unless explicitly asked to reorganize them.
- Do not put new reusable implementation directly in this folder; add or update a module under `../code/wind3dgs/` and document how the experiment uses it.
- When adding a new experiment, create or update a short `README.md` under the experiment directory.
- 새 TD 작업의 dataset, object package, checkpoint/model, complete run, per-frame render, video와 다른 heavy working output은 `artifacts/datasets/`, `artifacts/packages/`, `artifacts/models/` 또는 `artifacts/runs/`에 둔다. 이 경로들은 Git에서 제외한다.
- 실험을 이해하거나 재현하는 데 필요한 compact evidence만 추적한다. 여기에는 README, secret 없는 config, 작은 deterministic fixture, run manifest, compact report, completion marker와 의도적으로 선택한 대표 figure가 포함된다.
- 기존 tracked M01--M04 asset과 output은 legacy evidence로 보존한다. 이를 모든 새 TD output을 추적하는 선례로 삼거나 TD milestone 완료 근거로 사용하지 않는다.
- Ignored artifact는 disposable file이 아니다. Git에서 제외된다는 이유로 삭제하거나 덮어쓰지 말고 provenance, final derivative, hash, retrieval rule, 정확한 대상과 명시적 삭제 허가를 먼저 확인한다.
- Config, report, log, manifest 또는 environment 파일에 credential이나 token을 넣지 않는다. `.env`와 `.env.*`는 제외하고 secret이 없는 `.env.example`만 추적할 수 있다.
- 실행 명령·설정·상세 수치는 해당 experiment report/manifest에, 판정·재발 방지·다음 작업은 session에 기록한다.

## Session Tracking

- 공통 기록 기준을 따른다. 이 저장소의 고유 결정·변경·근거만 `sessions/`에 기록하고 다른 저장소의 상세 결과는 링크한다.
- `sessions/README.md`는 짧은 최신 진입점, 과거 목록은 `sessions/history.md`다. 중간 보고 원문은 기록하지 않는다.
