# 4배 보조 풀이 전환 검증

## 현재 판정

2026-09-11 사용자 승인 범위인 초기 비용 비교와 필요한 구간의 전환 시험을 완료했다.
초기0.1초에서 같은 전환 방식의1배보다 순수 계산3.687배 빨랐고, 전체 수치 보간의
변위·속도 상대 상한 각각1%를 통과했다. [결과](prefix_comparison.json), [판정](summary.json).
실제GPU 저장·재개 위치·속도·시간 차이0. [재개 결과](gpu_restart_comparison.json).
2.5초·10초·해상도 수렴은 미완료이며 새 본 실행은 준비만 했다.

## 방법과 한계

`AdaptivePreconditionerStepper`는 매frame을rest 보조 풀이로 시작한다.
성공한step에서 선형 반복 최대가32 이상이면 다음step부터current 보조 행렬을 쓴다.
current는4회 선형 풀이마다 재구축한다. rest 선형 실패만 같은 입력 상태/힘/dt로current 재시도한다.
Newton·선형 참 잔차·물리 허용오차는 그대로이며 비선형 실패는 숨기지 않는다.
전환 기준32는 개발 설정이며 최적값 또는 모든 변형에서의 가속 보장이 아니다.
실패 재시도 시간은 step 비용에 포함하지만 HVP 수는 성공 재시도만 포함하므로 총횟수 해석에 주의한다.
frame 경계에서 전환 이력을 초기화하며 과거 상태를 별도로 저장하지 않는다.

초기 작은 변형의1/960초 시험: rest1.776초, current재사용5.409초,
전환 방식1.339초. current의 복원/분해가4.367초로 약81%를 차지했다.
두 고정 방식 모두 선형 반복2회 수준이라 초기에는 비싼 행렬의 이득이 없었다.
같은 시작의전환 방식은4단계 모두rest, 독립 힘·기하·갱신·에너지 장부 검산 통과.
[rest](initial_rest_report.json), [current](initial_current_report.json), [전환](initial_auto_report.json).

이전3.2666667초 어려운 상태에서는rest→current→current→current로 전환했고
4단계10.890초 및 독립 검산 통과. [어려운 상태](difficult_auto_report.json).
이전 같은 상태의rest12.897초/current재사용9.264초와 비교하면 전환 비용이 남는다.
서로 다른 개발 시행의 시간이며 보조 풀이가 모든 구간에서 항상 가장 빠르다는 주장은 아니다.

## 같은 초기0.1초의 실행 비교

| 방식 | 계산 | 준비·검산·저장 포함 기록 합계 |
| --- | ---: | ---: |
| 전환4배 | 71.907초 | 115.465초 |
| 같은 전환1배 | 265.115초 | 400.249초 |

같은GPU에서 순차 실행. 기록 합계는 프로세스 시작 등 모든 wall overhead를 포함한 값은 아니다.
전체 수치 보간의1배 대비 변위 차이 상한0.003408%, 속도0.141521%로1% 통과.
이는 초기0.1초의 Newmark 경로 비교이며 참해 오차나 전체 궤적 정확도 인증이 아니다.
1배보다 더 세밀한 초기 구간 참조 수렴은 이번 시험에서 하지 않았다.
이전 상수current4배 초기0.1초 계산454.013초 대비 새4배 계산은 약6.31배 빠르다.
상수current와 전환4배 저장 경로의 최대 차이는 위치2.315e-17m,속도1.153e-12m/s다.
이는 서로 다른 보조 풀이 경로 비교이며 동일 방식의 저장·재시작 검증과 별개다.
GPU 재시작은 동일 전환 정책으로 마지막frame을 다시 계산해 차이0을 확인했다.

## 재현과 원본

모든 명령은 workspace에서 `PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python`을 사용한다.
- `probe_initial.py 새_출력 rest|current|adaptive`: 저장된frame0 끝에서4단계.
- `probe_difficult.py 새_출력 adaptive`: 이전 어려운 상태에서4단계.
- `compare_prefix.py`: 동결 `20260911_adaptive4_prefix_v1`의sub64/sub256 처음6frame 비교.
- `check_prefix_restart.py`: 별도 복제본 `20260911_adaptive4_restart_v1`에서5frame 뒤 재개.

초기0.1초 worker 명령은 해당동결 출력에 `--frozen --worker --substeps 64 --target 6`,
같은1배는 `--substeps 256 --target 6`을 사용한다. PYTHONPATH는 출력의runtime/code다.
비교용계획의controller는 실행하지 않았다. 직접worker를 통한 개발 검증이며 본 실행 예산을 늘린 것이 아니다.
NPZ·report·실행 당시source는 `experiments/artifacts/runs/teacher_timestep_search/20260911_adaptive4_*`에 보존한다.
probe 초기버전과 최종버전 차이는 각 출력의probe.py/source.zip으로 재현하며 현재 파일만 소급 적용하지 않는다.
고정밀 탐색12개+전환 wrapper4개 unittest 통과. source AST·JSON·diff 점검 완료.

## 새 본 실행 준비

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_adaptive4_segments.sh
```

처음부터 새 출력 `20260911_adaptive4_segments_v1`에서 계산한다.
이전 실행의629.682725초를 차감한 잔여7368.317275초만 사용한다.
2.5초마다 정지하며 정확도·비용 판정 전에 다음 구간으로 자동 진행하지 않는다.
기존run_acceleration4_segments.sh는상수current 시험이므로새전환 설정에는위명령을 사용한다.
이번 작업에서는 `--prepare-only`만 실행했고 본 실행은 재개하지 않았다.
본 실행의예산상태와 이전 실패·원본은 보존했다. 외부fetch·다운로드·commit·push는 하지 않았다.
