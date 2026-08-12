# TD00 실험 scaffold 정리

## 목적

물리 실험 전에 provenance와 artifact 규칙 자체를 반증 가능한 첫 TD 실험으로 만든다.

## 추가한 항목

- 공통 `EXPERIMENT_TEMPLATE.md`
- `TD00_contracts/README.md`
- M01--M04 재사용 후보 감사 보고서
- compact reference evidence 폴더와 완결성 marker 계약
- 실제 run을 `artifacts/runs/`에 보관하는 Git ignore 정책

## TD00 성공 조건

- 네 source repository가 clean인 상태에서 실행된다.
- config/source/output hash와 재현성 key가 자동 검증된다.
- legacy 완료 상태를 TD milestone로 승격하지 않는다.
- reference manifest/report/marker 세 파일이 서로 일치한다.

## 명시적 미검증

Physics E0, teacher/object package, learned model, GPU/render, force/torque 보존, rollout 정확도는 TD01 이후 항목이다.

## 실행 결과

- Reference run: `td00-contracts-smoke-20260812t184509388327z-abde7ba`
- Python 3.12 unit test: 38/38 통과
- TD00 report: 15개 check 통과, 12개 TD01+ 검증 항목 명시적 보류
- Source commits: root `37dea4d`, code `abde7ba`, ideas `5a8ad16`, experiments `4e34842`
- Working run은 ignored `artifacts/runs/`에 보존하고 compact JSON 세 파일만 version control 대상으로 승격했다.
