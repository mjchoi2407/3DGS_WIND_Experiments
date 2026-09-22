# 선형 반복 한도 비교: 8 → 12

2026-09-11. **반복 한도만12로 늘린 별도 시험이 실패 step과 다음4개 step을 통과했다.**
사용자가64배 간격+반복 한도12를 채택했다. 일반 기본 policy는8을 유지하고 새 v3의 명시적 선택에12를 반영했다. 장기 재실행은 아직 시작하지 않았다.

## 기존 v2 결과와 실패 원인

- 첫2.5초 구간 통과, 총161 frame(2.683333초)·644 interval의 저장/검산을 완료했다.
  실패 prefix의 추가3개 step은 완료 frame 분모에 포함하지 않는다.
- Frame161/substep3, 입력 시각2.695833초에서 `linear_solve` 실패.
  실행 시간2309.808초(38분30초)이며 시간 초과가 아니다.
- 힘 잔차2.72127e-12N은 허용 한도1.06185e-10N 안이었다.
  직전 위치 수정이 아직 크므로 작은 최종 수정량 확인을 위한 선형 풀이가 필요했다.
  마지막 선형 잔차2.99386e-22N이 한도2.72127e-22N의약1.10배여서 종료했다.
- 동결 소스·모든 완료 frame hash와 metadata 연결을 확인했다.
  [prefix 요약](prefix_summary.json)은 저장된 검산 판정 집계이며 전체 물리식을 다시 계산한 결과는 아니다.

## 한도 비교와 독립 검산

- 동일 실패 상태·소스·외력·Δt에서8 한도의 실패를 시도 내역까지 동일하게 재현했다.
- 한도12: 마지막 선형 풀이506회에서 잔차4.18487e-23N으로 통과했다.
  실패한8 한도의 마지막471회보다35회 추가했다. 전체 선형 반복 합은1728→1763이다.
- 한도8/12의 한 step 실측은 각각29.84/28.59초였다. GPU 부하·초기 compile/warm 상태가 달라
  속도 개선을 뜻하지 않는다. 최대 반복 예산은480→720이며 실제로는 수렴하면 먼저 종료한다.
- 한도12로2.7초 상태를 저장한 뒤 다음 frame162의4개 step도 같은 한도로 통과했다.
  전체5개 interval은2.695833–2.716667초의 짧은 개발 검증이다.
- 각 통과 결과를 별도 CPU longdouble 힘 식으로 검사했다.
  잔차 최대비율0.112808, 위치 갱신 차이최대5.42101e-20m,
  에너지 장부 차이최대8.02310e-18J, 기하 gradient 상한최대0.136621<1로 모두 통과했다.
- 모든 물리/Newton/선형 정확도 허용오차와64배 Δt는 유지했다.12가 통과하여16은 실행하지 않았다.
  5초/10초 성공, 시간 정확도와 공간 해상도 수렴은 미확정이다.

## 근거와 재현

[한도 비교](probe_report.json), [다음 frame](followup_report.json), [요약](summary.json), [identity](identity.json).
원본은 `experiments/artifacts/runs/teacher_timestep_search/20260911_linear_cycles_probe_v1/`와
`20260911_linear_cycles_followup_v1/`에 report·hi/lo checkpoint·로그로 보존한다.
소스는 기존 `20260911_precision_segments_v2/runtime/code`를 그대로 사용한다.
실험 프로세스에서만 `dataclasses.replace(policy, linear_cycles=12)`를 적용했다.

Root에서 `PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v2/runtime/code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python`
뒤에 [probe_cycles.py](probe_cycles.py) 또는 [probe_followup.py](probe_followup.py)와 새 출력 경로를 지정한다.
후속 스크립트는 보존된 한도12 checkpoint를 입력으로 사용한다.

## 채택과 새 실행 준비

사용자가64배 간격 유지+한도12를 선택했다. `--linear-cycles 12`를 별도 고정밀 탐색에서
선택할 수 있게 연결했으며 다른 물리·선형 정확도 기준은 그대로다. 일반 기본 한도는8이다.
새 동결 v3는 rest부터 다시 검증하며 기존 v1/v2 결과를 그대로 보존한다.
[채택 계획](adopted_plan.json), [준비 근거](adoption.json), [동결 CUDA smoke](adoption_smoke.json).

- 실제 solver에12 전달·정확도 완화 거부·저장 재개 비교 등15개 검사 통과.
- 별도 n=4/0.1초 CUDA 동결 실행은 sub4만6 frame 완료 후 정지했다.
- 같은60Hz 바람·n=32·4분할·2.5/5/7.5/10초 구간이다.
- 이전 본 실행의18+2310초를 차감하여12072초(3시간21분12초)의 활성 worker 예산을 동결했다.
  개발 진단의 wall time과 본 실행 후보 예산은 구별한다.
- Root에서 `bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_segments.sh`.
  현재 스크립트는 `20260911_precision_segments_v3`를 선택한다.
- 현재 `--prepare-only`만 실행했다. 새10초·시간 정확도·해상도 수렴은 미완료다.
