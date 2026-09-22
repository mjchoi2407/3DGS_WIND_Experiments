# 명시적 고정밀 API 및 실패 구간 재검증

2026-09-11. 사용자 선택으로 저장·복원 정확 일치와 수치적 재시작 기준을 채택했다.
이어 계산의 위치 차이≤1e-16m·속도 차이≤1e-12m/s 및 기존 물리식 검산을 함께 요구한다.
물리·Newton 허용오차는 유지하며 장기 재시작은 별도 검증한다.

## 구현과 확인 범위

- `P3ShellWarpPrecisionStepper`가 상태 생성·갱신·속도 reset의 longdouble을 보존한다.
  Sparse 풀이만 float64로 전달하며 전역 함수 교체를 사용하지 않는다.
- `p3_shell_precision_state`가 hi/lo checkpoint를 명시적 별도 schema로 저장한다.
  비정규 표현, 손실 복원, 비유한 값, shape/dtype 오류, 기존 파일 덮어쓰기를 거부한다.
  모델·외력·solver 설정은 실행 manifest 소유이며 이 checkpoint 하나만으로 임의 실행을 복원하지 않는다.
- 기존 sub016 추가 실패 지점에서8개 step(2.66875–2.67708333초)을 수행하여
  독립 CPU 고정밀 운동방정식·위치 갱신·기하 상한·에너지 장부 검산을 모두 통과했다.
- 같은 프로세스 및 별도 프로세스의 checkpoint 저장·재시작은 u/v/time 정확 일치다.
  별도 CPU 고정밀 원식 잔차 비율0.0122266, 공력의 최대 성분 차이4.2471e-20N을 확인했다.
  [별도 프로세스 검산](replay_checkpoint.json).
- 별도로 기존 sub004/016/064 실패 위치에서 각2개 step, 합계6개를 같은 독립 기준으로 통과했다.
- sub001은 완료0개, `linear_solve` 실패1개다. 480회 반복 후 선형 잔차2.1445e-8N이
  한도8.7465e-9N을 넘었다. 고정밀 위치 보존만으로 해결되는 문제는 아니다.
- 이 짧은 재시험은 새 rest 시작10초 궤적의 성공·실패 판정이 아니다.
  현재 새10초 실행과 공간 해상도 수렴 검증은 미완료다.

## 근거와 재현

- [report.json](report.json): 8 step 전체, 소스 hash, 정책과 비용.
  `environment`는 기준 HVP 경로 생성 시 수집했으며 실제 시험 클래스와 정밀도는 `scope` 및 위 구현 설명을 따른다.
- [summary.json](summary.json): 최대 검산 오차.
- [restart_check.json](restart_check.json): 같은 프로세스의 checkpoint 재시작.
- [candidates.json](candidates.json): 기존4개 간격의 실패 위치 재시험, 실패 분모와 실제 풀이 시간.
- [probe_state.py](probe_state.py), [probe_candidates.py](probe_candidates.py): Root에서
  `PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python <script> <새 output>`.
- [replay_checkpoint.py](replay_checkpoint.py): 같은 환경 변수와 Python으로 별도 프로세스 재시작·공력 검산.
- 원본: `experiments/artifacts/runs/teacher_timestep_search/20260911_gpu_precision_api_v1/`,
  `20260911_gpu_precision_candidates_v1/`. 각 상태·로그·source.zip과 JSON을 보존한다.
- [선행 GPU 기하 시험](../gpu_precision_20260911/README.md): 채택한 재현성 기준과 이전 완전 일치 실패 근거.

실패 부근의 풀이 시간은 외부 GPU 부하·상태의 영향을 받으므로 전체10초 소요 시간으로 확정하지 않는다.
진단 비용에 CPU 독립 검산이 포함된 시간과 solver만의 시간도 구별한다.

사용자는 **4분할부터 새10초 검증 준비**를 선택했다.
`--precision`은 별도 탐색 schema와 hi/lo frame을 사용하며 최소4분할을 지킨다.
`--first-candidate-only`는 첫 후보만 완료한 뒤 멈춘다. 이후 옵션 없이 실행하면 저장 후보를 재사용한다.
사용자는 합계4시간 한도와 **2.5초씩 성공 후 이어가기**를 선택했다.
[동결 실행 계획](segmented_plan.json), [준비·검증 기록](segmented_preparation.json).
`run_precision_segments.sh`는60Hz 바람·n=32·4분할(기존 대비64배)을 유지하고
150/300/450/600 frame에서 구간을 마친다. 앞 구간을 검산한 저장 상태에서 다음 구간을 시작한다.
바람·시간을 구간마다 초기화하지 않는다. 4시간은 네 구간 합계의 활성 worker 예산이다.
풀이/검산 실패 또는 예산 도달 시 멈추며 더 작은 간격으로 자동 전환하지 않는다.
10초 통과 전 해당 prefix만 검증된 것으로 보고, 시간 정확도·해상도 수렴 완료로 처리하지 않는다.

Root에서 `bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_segments.sh`로 실행한다.
`--status-only`로 상태 확인, Ctrl+C로 worker 종료·완료 frame 보존, 같은 명령으로 중단 후 재개한다.
시간 한도나 수치 실패 판정 이후의 재개는 자동 보완하지 않고 원인·추가 예산을 검토한다.
현재는 `--prepare-only`만 수행했으며 장시간 실행은 시작하지 않았다.
이번 구간 설정 후 기존 탐색10개·고정밀 탐색4개 검사와 바람 원본 일치·동결 hash 검사를 통과했다.

## 실행기 검증

- 상태 codec2개, dynamics5개, 실행 경로2개, 고정밀 GPU3개,
  기존 탐색10개, 고정밀 CUDA 탐색3개: 총25개 검사 통과.
- 고정밀 CUDA 탐색 검사는6 frame 중2 frame 저장 후 재개한 결과와 연속6 frame을 대조했다.
  모든 구간에서 위치≤1e-16m·속도≤1e-12m/s를 확인했고 해시 보존·비교 API·후보 하한도 검사했다.
- 실제 동결 controller/worker smoke: `20260911_precision_search_smoke_v1`, n=4,0.1초,
  sub4만6 frame 완료 후 `candidate_complete` 종료, 추천 없음·학습 부적격 유지.
  명령은 `bash code/scripts/run_teacher_timestep_search.sh --output experiments/artifacts/runs/teacher_timestep_search/20260911_precision_search_smoke_v1 --smoke --precision --first-candidate-only --budget-hours 0.05 --trial-timeout 120 --step-timeout 60`.
- 작은 smoke의 통과는 n=32의10초 안정성·시간 정확도·해상도 수렴을 대체하지 않는다.
