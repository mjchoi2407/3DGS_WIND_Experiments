# Wind3DGS Experiments

Wind3DGS 프로젝트의 실험 기록, asset, output, report와 얇은 wrapper를 관리한다.

<!-- td00:legacy-status-not-inherited -->

## 현재 방향

현재 방법과 R0--R7 개발 계약은 [ideas index](../ideas/README.md)에서 찾는다. 기존 TD##/M## 실험은 legacy/support이며 현행 R-stage 완료 근거로 자동 승계하지 않는다.

## 현재 Teacher 개발 검증

- [10초 시간 간격 탐색](R1_teacher_velocity_reset/timestep_search/README.md): 기존60 Hz 공력을 유지하는 Δt 최대256배 자동 탐색과 사용자 실행 안내.

- [최신 실험 요약](sessions/README.md): 완료·진행·보류와 다음 선택.
- [약한 바람 검증](R1_teacher_velocity_reset/p3_shell_random/README.md), [4배 바람 검증](R1_teacher_velocity_reset/p3_shell_random/scale4/README.md): 각각의 적용 조건과 정량 판정.
- [GPU 성능·실패 원인](R1_teacher_velocity_reset/p3_shell_random/profiling/README.md): 정확도·속도·채택 여부.
- [실험 근거 목록](teacher_evidence_index.md): 선행 비교·실패·개발 sample의 원본 진입점.

추가 학습데이터 발행은 보류 상태이며 개발 검증을 R1 전체 채택으로 간주하지 않는다.
수식·계약과 논문 claim 경계는 [R1](../ideas/development/r1_teacher_probe_oracle.tex)을 따른다.

## Legacy와 support 목록

| Directory | 현재 역할 | Mainline 상태 |
| --- | --- | --- |
| `M01_static_3dgs_io/` | Static GS I/O와 renderer baseline, TD01 fixture 후보 | 재사용 전 재검증 |
| `M02_mesh_proxy_binding/` | Synthetic cloth asset, transport check, legacy mesh-proxy 비교 | Target runtime 아님 |
| `M03_procedural_wind/` | Prescribed-wind 정성 deformation fixture | Physics solver/teacher 아님 |
| `M04_mesh_extraction/` | Offline GS reconstruction/mesh preprocessing과 mesh baseline support | Training/evaluation only |
| `exp001_baseline_3dgs/`--`exp003_wind_prior/` | 비활성 초기 placeholder | 현재 완료 증거 없음 |

과거 명령과 output은 재현성을 위해 원래 폴더에 보존한다. 기존 milestone 상태는 TD00--TD14에 승계하지 않는다.

## Project 내부 분리

- `../code`: 재사용 구현과 code-side session 기록
- `../ideas`: idea sketch, 참고문헌, checklist와 idea-side session 기록
- `../experiments`: 실험 README, asset, output, report와 experiment-side session 기록

## 작업 기록

- 각 실험 폴더의 `README.md`에 재현 가능한 setup, 명령, metric과 관찰을 기록한다.
- 결정·재발 방지·근거 링크는 `sessions/`에 짧게 기록한다. 중간 보고 원문은 기록하지 않는다.
- 재사용 구현은 `../code`에 둔다.
- 연구 framing과 milestone checklist는 `../ideas`에 둔다.

새 TD 실험은 [`EXPERIMENT_TEMPLATE.md`](EXPERIMENT_TEMPLATE.md)의 goal/falsification, privilege, exact command, artifact, completion gate, failure/decision 항목을 채운다. 첫 실험은 [`TD00_contracts/`](TD00_contracts/)이며 실제 working run은 Git에서 제외된 `artifacts/`에 저장한다.

## Artifact와 evidence 경계

- 새 TD 실험의 dataset, object package, model/checkpoint, complete run, per-frame render와 video는 Git에서 제외된 `artifacts/` 아래에 둔다.
- 실험 디렉터리에는 README, secret-free config, 작은 deterministic fixture, run manifest, compact report, completion marker와 의도적으로 고른 대표 figure만 version-controlled evidence로 둔다.
- 기존 M01--M04의 추적된 asset/output은 legacy 재현 기록으로 보존하지만 새 TD artifact 추적 정책이나 완료 상태로 승계하지 않는다.
- Git ignored artifact는 삭제 가능한 임시 파일이라는 뜻이 아니다. provenance, 최종 derivative, hash와 retrieval rule을 확인하고 명시적 승인을 받기 전에는 삭제하거나 덮어쓰지 않는다.
