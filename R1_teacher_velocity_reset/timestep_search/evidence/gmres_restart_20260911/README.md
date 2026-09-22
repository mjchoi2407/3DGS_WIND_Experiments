# 64배 Δt를 유지한 GMRES 재시작 간격 검토

2026-09-11. 사용자 결정: 시간 간격을32배로 낮추는 대신64배 풀이를 개선하고,64배 검증 후256배로 진행한다.

## 조건과 첫 결과

- v3의 frame195/substep3 실패 상태(3.2625초), n=32, Δt=1/240초, frame195 시작 상태에서 계산한 공력을 그대로 사용했다.
- 기존 restart60×12주기 실패와 비교하여 restart120×6, restart240×3을 시험했다. 각 선형 풀이의 최대 반복 수720과 모든 허용오차는 유지했다.
- restart120과240 모두 실패 단계를 통과했고 독립 CPU longdouble 운동방정식·위치 갱신·에너지 장부·기하 검사를 통과했다.
- 120:34.228초·HVP2086회,240:29.991초·HVP1726회. 외부 부하와 warm 상태가 있는 국소 진단이며 전체 가속률이 아니다.
- 240의 최대 Newton 선형 반복 수445, 최종 독립 잔차/허용한도0.495234 미만. 선형 잔차 검사도 유지했다.
- 더 긴 탐색 방향 묶음을 보존하면 주기마다 잃는 정보를 줄일 수 있다. 대가로 Krylov 벡터 메모리와 직교화 비용이 늘어난다. 실제 전체 비용은 장기 실행에서 확인해야 한다.
- [단계별 결과](probe_report.json). 기존 실패 재현은 [선행 비교](../sub008_20260911/probe_report.json)에 보존했다.

## 재현과 범위

동결 소스 `experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v3/runtime/code`를 PYTHONPATH로 지정하고,
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python` 뒤에 [probe_restart.py](probe_restart.py)와 새 출력 경로를 지정한다.
시험 프로세스 안에서 GMRES의 restart/maxiter만 바꾼다. report의 policy는 동결 기반 설정이며 실제 덮어쓴 값은 각 trial의 restart/max_cycles다.
원본은 `experiments/artifacts/runs/teacher_timestep_search/20260911_gmres_restart_probe_v1`에 보존한다.
[probe_followup.py](probe_followup.py)는240 설정 checkpoint에서 frame196 공력을 갱신하여 다음4개 단계를 검사한다.
후속4단계도132.306초에 모두 통과해3.283333초에 도달했다.240 설정 총5개 interval의 독립 잔차/허용한도 최대0.589558 미만이다.
[후속 결과](followup_report.json), [집계](summary.json).64배10초·시간 정확도·해상도 수렴·256배는 아직 미검증이다.

## v4 실행 준비

실행기에 명시적 `linear_restart`를 연결했다. 기본60과 기존 동결 plan은 유지한다.
새 v4는240×3,64배 Δt,2.5/5/7.5/10초 구간, 원래 합계4시간에서 남은7998초로 준비했다.
이전 실패 상태를 장기 성공 궤적에 섞지 않고 rest부터 검증한다. 단기 진단 비용은 별도로 기록하며 본 실행 예산에 합산하지 않았다.
원본은 `experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v4`이고,
설정·runtime manifest 사본은 [plan.json](plan.json), [runtime_manifest.json](runtime_manifest.json)에 보존한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_segments.sh
```

이는 새 본 실행을 시작하는 명령이다. v3 재실행 명령으로 해석하지 않는다. 남은 예산 내10초 완주는 보장하지 않는다.
64배 장기 검증 통과 후256배를 별도 후보로 진행한다. 현재 wrapper는64배만 실행한다.


검증: 시간 탐색16개·dynamics5개 검사와 n=4 CUDA0.1초/6frame 동결 smoke 통과. [검증 범위](validation.json). v4 runtime hash·계약·v3와 바람 배열 정확 일치 확인. `experiments/`는 실험·wrapper·기록, `code/`는 옵션·검사·사용법·기록을 변경했다. 기존 dirty 상태 보존, commit/push/fetch 없음.
