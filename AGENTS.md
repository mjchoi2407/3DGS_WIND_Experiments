# Wind3DGS Experiments Instructions

Wind3DGS의 experiments 독립 저장소다. 공통 지침은 [`../AGENTS.md`](../AGENTS.md)를 적용한다.
상위 지침이 자동 로드되지 않은 하위 저장소 단독 실행에서도 직접 확인한다. 이미 확인한 내용은 반복 출력하지 않는다.
공통 언어·기록·Git·보안·LaTeX 규칙을 이 파일에 복제하지 않는다.

## Startup Protocol

- 맥락이 충분하면 진행한다. 부족할 때만 [주제별 작업 색인](sessions/README.md#현재-상태) → 해당 note의 현재 상태 → 상세 절 링크 순서로 확인한다.
- 실행·수정 전에는 해당 experiment README의 실행 조건·검증 절을 확인한다. 이미 확인한 계약은 재사용하되 실제 코드·설정·프로세스 상태는 확인한다. 연구 계약이 필요한 경우에만 해당 R 절을 읽는다.
- 서브컴 또는 메인·서브 비교가 요청 범위에 포함되면 `artifacts/runs/sub_pc/<run ID>/`도 확인한다. 서브컴은 공유 코드를 읽고 자체 CPU/GPU로 계산한다. 각 run의 설정·manifest·로그로 실험을 식별하고 메인컴과 비교할 때 조건·계산 구간·장치 차이를 확인한다. 별도 요청 없이 실행을 중단하거나 기존 결과를 수정·삭제하지 않는다.
- Dataset/model/run/environment/artifact 작업은 해당 experiment가 연결한 manifest를 먼저 확인한다. 연결이 없을 때만 `../manifests/`에서 필요한 기록을 찾는다. 외부 의존성 작업에는 [patch 절차](../docs/workflows/external_dependencies.md#external-dependency-및-patch-규칙)를 적용한다.

## Editing Rules

- 기존 사용자 파일은 명시적으로 정리 요청을 받은 범위 외에는 보존한다.
- 새 재사용 구현은 `../code/wind3dgs/`에 두고 실험에서 사용하는 방법만 연결한다.
- 새 실험에는 해당 폴더의 짧은 `README.md`와 상세 설정·결과 위치를 제공한다.
- 새 TD 작업의 dataset, object package, checkpoint/model, complete run, per-frame render, video와 다른 heavy working output은 `artifacts/datasets/`, `artifacts/packages/`, `artifacts/models/` 또는 `artifacts/runs/`에 둔다. 이 경로들은 Git에서 제외한다.
- 실험을 이해하거나 재현하는 데 필요한 compact evidence만 추적한다. 여기에는 README, secret 없는 config, 작은 deterministic fixture, run manifest, compact report, completion marker와 의도적으로 선택한 대표 figure가 포함된다.
- 기존 tracked M01--M04 asset과 output은 legacy evidence로 보존한다. 이를 모든 새 TD output을 추적하는 선례로 삼거나 TD milestone 완료 근거로 사용하지 않는다.
- Ignored artifact는 disposable file이 아니다. Git에서 제외된다는 이유로 삭제하거나 덮어쓰지 말고 provenance, final derivative, hash, retrieval rule, 정확한 대상과 명시적 삭제 허가를 먼저 확인한다.
- Config, report, log, manifest 또는 environment 파일에 credential이나 token을 넣지 않는다. `.env`와 `.env.*`는 제외하고 secret이 없는 `.env.example`만 추적할 수 있다.
- 실행 명령·설정·상세 수치는 해당 experiment report/manifest에, 판정·재발 방지·다음 작업은 session에 기록한다.

## Session Tracking

실험 결과·판정·사용자 결정·중단이 확정되면 [공통 기록 규칙](../AGENTS.md#간결한-작업-기록)에 따라 해당 note를 갱신한다. [주제별 색인](sessions/README.md#현재-상태)은 짧게 유지하고, 과거 근거는 [이전 작업 링크](sessions/README.md#이전-작업-링크--당시-상태)로 연결한다.
