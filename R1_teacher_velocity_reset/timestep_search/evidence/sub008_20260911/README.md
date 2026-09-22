# 8분할(기존 대비32배 Δt) 실패 구간 비교

2026-09-11. **동일 실패 상태에서8분할2step과 후속8step, 총10개 interval 검산 통과.**
격자n=32·선형 반복 한도12·기존 물리/선형 정확도 기준·60Hz 공력 갱신을 유지했다.
기본 구현·동결 plan·장기 실행 스크립트는 변경하지 않았다.

## 비교 조건과 결과

- v3의4분할은195 frame(3.25초)·780개 interval 저장 검산을 완료하고
  frame195/substep3(입력3.2625초)에서 선형 풀이에 실패했다.
  약67분54초 실행했으며 시간 초과가 아니다. [기록 집계와 원본 hash 확인](v3_summary.json).
- 동일 동결 소스·실패 prefix·frame 시작 공력을 사용해4분할 실패를 시도 내역까지 정확히 재현했다.
- 같은 시작 상태에서4분할1step과8분할2step을 비교했다.
  물리 시간 길이는 모두1/240초이며8분할 두 단계 동안 공력을 갱신하지 않는다.
- 4분할은29.329초 후 실패,8분할 두 단계는30.060초에 통과했다.
  실패 실행과의 국소 비교이고 외부 GPU 부하·compile/warm 조건이 달라 전체 가속률로 해석하지 않는다.
- 8분할 끝 상태(3.266667초)를 hi/lo checkpoint로 저장한 뒤 다음 frame196에서
  공력을 갱신하고8개 step을 추가했다. 145.106초에 모두 통과해3.283333초에 도달했다.
- 전체10개 interval에 대해 독립 CPU longdouble 힘으로 운동방정식·위치 갱신·에너지 장부를 검사했고
  요소 기하 상한도 통과했다. 잔차 최대비율0.016947로 기존 허용 한도보다 충분히 작았다.
  상세 최대값과 각 단계는 [summary.json](summary.json), [첫 비교](probe_report.json), [후속 frame](followup_report.json).
- 기존4분할 궤적의 실패 상태에서 갈라진 짧은 진단이다. rest에서 시작한8분할10초 실행,
  16/32분할과의 시간 정확도 비교, 해상도 수렴 완료를 뜻하지 않는다.

## 재현과 다음 선택

- 원본: `experiments/artifacts/runs/teacher_timestep_search/20260911_sub008_probe_v1/`,
  `20260911_sub008_followup_v1/`; hi/lo checkpoint·report·로그 보존.
- 소스: `20260911_precision_segments_v3/runtime/code`를 그대로 사용하고 policy는 동결 plan에서 읽었다.
- Root에서 `PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v3/runtime/code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python`
  뒤에 [probe_substeps.py](probe_substeps.py) 또는 [probe_followup.py](probe_followup.py) 및 새 출력 경로를 지정한다.
  후속 스크립트는 보존된8분할 checkpoint를 입력으로 사용한다.
- [identity.json](identity.json): 입력·소스 manifest·스크립트·결과 hash.
- 다음 분기는8분할·32배를 새 장기 후보로 채택(권장)하거나4분할·64배 풀이 개선을 더 검토하는 것이다.
  사용자 선택 전 새 장기 계획은 만들지 않았다. 남은 v3 본 실행 예산은약2시간13분18초이며
  새 후보는 기존 궤적에 섞지 않고 rest부터 검증해야 한다.
