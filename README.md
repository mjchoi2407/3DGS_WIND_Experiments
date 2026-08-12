# Wind3DGS Experiments

Wind3DGS 프로젝트의 실험 기록, asset, output, report와 얇은 wrapper를 관리한다.

<!-- td00:legacy-status-not-inherited -->

## 현재 방향

현재 방법은 `../ideas/README.md`에서 찾는다. 새 실험은 `TD##` namespace를 사용한다. TD00은 Global--Local solver milestone을 완료 처리하기 전에 계약, manifest, artifact 소유권과 regression test를 고정한다.

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
- 이 experiments 폴더에 속한 대화와 작업 이력은 `sessions/`에 둔다.
- 재사용 구현은 `../code`에 둔다.
- 연구 framing과 milestone checklist는 `../ideas`에 둔다.

새 TD 실험은 [`EXPERIMENT_TEMPLATE.md`](EXPERIMENT_TEMPLATE.md)의 goal/falsification, privilege, exact command, artifact, completion gate, failure/decision 항목을 채운다. 첫 실험은 [`TD00_contracts/`](TD00_contracts/)이며 실제 working run은 Git에서 제외된 `artifacts/`에 저장한다.
