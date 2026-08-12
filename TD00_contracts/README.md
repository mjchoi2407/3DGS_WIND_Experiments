# TD00 Contracts and Reproducibility Smoke

## 목표와 반증 질문

TD00의 목표는 새 방법의 source commit, config hash, seed, device, dataset/object-package 상태와 output hash를 자동 기록하고, 기존 M01--M04 완료 상태가 새 TD 방법으로 승격되지 않았음을 검증하는 것이다.

빈 CPU smoke가 이 provenance를 자동 생성·검증하지 못하거나, mainline import가 legacy M module/RSH runtime에 의존하면 TD00은 실패다.

## 입력 privilege와 runtime 제한

- Dataset, target mesh, teacher trajectory, checkpoint, learned network, renderer를 사용하지 않는다.
- `dataset_id`와 `object_package_id`는 빈 값이나 가짜 hash 대신 TD00 전용 `not_applicable` sentinel로 기록한다.
- GPU/MPM/FEM/CFD/LBM/RSH를 호출하지 않는다.
- TD00 통과는 TD01 physics contract, M01--M04 재검증 또는 14-stage solver 완료를 의미하지 않는다.

## 소유권과 저장 경로

- Config/schema/generator/test: `../code/`
- Working run: `artifacts/runs/<run_id>/` (Git 제외, 자동 삭제 금지)
- Compact reference evidence: `TD00_contracts/reports/reference_smoke/`
- Reuse audit: `TD00_contracts/reports/reuse_candidate_audit.md`

## 재현 명령

입력 코드와 이 README를 먼저 커밋하여 네 source repo가 clean인 상태에서 project root에서 실행한다.

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.runtime.td00_smoke \
  --config code/configs/td00_contracts_smoke.json \
  --publish-dir experiments/TD00_contracts/reports/reference_smoke
```

TD00 core unit test:

```bash
cd code
PYTHONPATH=. ../.venv/bin/python -m unittest discover -s tests -v
```

## 검증 항목

- run manifest schema와 packaged schema resource
- 네 저장소의 full commit과 dirty 상태
- config SHA-256, seed, CPU device, dataset/package sentinel
- output의 상대경로 containment, regular-file 여부, size와 SHA-256
- 논리 Module 번호와 다른 실제 실행 순서 `1→2→3→4→5→6→7→10→9→8→11→12→13→14`
- Local analytic aero, learned missing aero, learned missing structural channel 분리
- predictor-consumed cross load와 corrector structural delta 분리
- TD mainline의 legacy M/RSH import 부재
- publication file당 1 MiB 상한과 absolute/private path 부재
- `reference_complete.json` marker를 통한 manifest/report pair 완결성

질량/감쇠/강성의 PSD, Global--Local 직교성, force/torque 보존, zero-wind rest, affine transport, rollout 정확도와 JSON Schema--Python validator parity는 `not_evaluated`다. 이는 TD01 이후 검증한다.

## 완료 gate

- [x] Python 3.12 unit test 38개가 통과한다.
- [x] Clean-source TD00 smoke가 통과한다.
- [x] ignored working run에 `run_manifest.json`, `td00_smoke_report.json`이 존재한다.
- [x] compact reference JSON의 hash와 working run이 일치한다.
- [x] reuse audit가 M01--M04를 새 완료 상태로 승격하지 않는다.
- [x] Python 3.10/3.11 미검증, GPU/physics 미검증 상태가 숨겨지지 않는다.

검증된 reference run은 `td00-contracts-smoke-20260812t184509388327z-abde7ba`다.
`reference_complete.json`이 manifest와 report의 SHA-256을 고정하며,
독립 verifier에서 15개 check가 `pass`, 12개 TD01+ 항목이 `not_evaluated`로 확인됐다.

## 실패 사례와 결정

| 사례 | 처리 |
| --- | --- |
| Source repo dirty | Reference 발행을 중단하고 입력 변경을 먼저 검토·커밋한다. |
| 기존 reference와 다른 JSON | 자동 overwrite하지 않고 source/config 차이를 먼저 확인한다. |
| Schema 또는 output hash 불일치 | TD01로 진행하지 않고 generator/manifest 계약을 수정한다. |
| Legacy/RSH mainline import 발견 | TD package boundary에서 import를 제거하거나 명시적 evaluation-only 경로로 옮긴다. |
