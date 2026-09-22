# GPU 고정밀 기하 시험

2026-09-11. **단기 8/8 step과 독립 CPU 고정밀 잔차 검사 통과.**
격자는 n=32, Δt=1/(60×16)초, 기존 Newton 허용오차를 유지했다.
기존 sub016 추가 실패 직전 상태에서 frame160의 substep2–9를 실행했다
(2.66875–2.67708333초). 해상도 수렴이나 시간 간격 탐색의 완료 판정은 아니다.

## 구현과 판정

- 상태는 CPU `longdouble`(이 환경 가수64bit), GPU로 보낼 때 float64 hi/lo로 분리한다.
- 위치 차이·형상 미분을 보정 연산으로 누적하고, 구성식·힘 조립·HVP는 기존 float64를 사용한다.
- 별도 실행 프로세스에서 상태 생성과 sparse solve dtype 연결을 교체한 시험본이다. 기본 factory·저장 schema는 미변경이며 일반 실행에 채택하지 않았다.
- 8개 모두 Newton 수정3회, CPU 고정밀 원식 잔차는 허용 한도의 최대1.258%다. 위치 갱신 오차 최대2.711e-20m.
- float64 내보내기 후 기존 식 검산은 8/8 기준 미달(비율1.00247–1.45883). hi/lo 저장의 작은 항을 버리면 안 된다.
- 저장된 CPU 기준 상태3개에서 힘 차이 norm은 9.13e-13–9.25e-13N이었다. 같은 상태를 기존 GPU에서 평가하면 최대1.07e-10N이었다.
- 힘 평가3회 평균: 기존 GPU3.993ms, 시험 GPU10.310ms, CPU 고정밀559.293ms.
  시험 GPU는 기존 대비약2.58배 비용, CPU 고정밀 대비약54.25배 빠르다.
  warmed 경로별 순차 측정이며 외부 GPU 부하는 통제하지 않았다. 전체 시뮬레이션 가속률로 해석하지 않는다.
- 공력은 기존 frame 시작 상태의 float64 고정 힘을 동일하게 재사용했다. 일반 고정밀 공력/ledger·장기 안정성·정식 저장 API 검증은 남았다.

## 재시작과 회귀 검사

Hi/lo 분리 후 복원은 원래 longdouble 상태와 정확히 일치했다.
추가로 전체9개 상태의 재분리 값·dtype·유한성을 확인했다([저장 무결성](storage_check.json)).
그러나 별도 프로세스의 index4→5 재계산은 u/v 완전 일치 검사에 실패했다.
최대 차이는 위치1.605e-18m, 속도3.079e-15m/s이며 시간은 같았다.
같은 프로세스에서 같은 입력을 두 번 계산하면 u/v가 정확히 일치한다.
추가 시험에서 초기 상태부터 재계산한 앞4개 구간은 정확히 일치하고 5번째에서 같은 차이가 발생했다.
따라서 저장 손실이나 중간 재시작에만 국한된 문제로 볼 수 없다. 차이를 유발한 계산 위치는 아직 미확정이다.
재계산/저장 결과를 독립 CPU 고정밀 식으로 검산한 잔차 비율은 각각0.0122318/0.0124582로 모두 통과했다.
[연속 재계산](replay_history.json), [양쪽 원식 검산](replay_audit.json); 실행 스크립트는 같은 이름의 `.py`다.
사용자는 저장 복원 정확 일치를 유지하고 계산은 수치적 재현성으로 검증하는 방안을 채택했다.
위치 차이≤1e-16m·속도 차이≤1e-12m/s와 기존 물리식 검산 통과를 함께 요구한다.
위의 한 step 재계산은 채택 기준을 통과하며 장기 재시작은 별도 검증한다.
이는 기존 물리 허용오차의 변경이 아니다. 계산 완전 일치 실패 원본도 유지한다.
작은 차이라는 이유로 정확 일치 기준을 통과 처리하지 않았다.
[restart_check.json](restart_check.json); 최초 실패 로그와 차이 진단 로그는 모두 보존했다.

기존 dynamics5개, execution2개(CPU), fast HVP3개(CUDA), 새 보정 산술·입력2개(CUDA),
총12개 회귀/단위 검사를 통과했다. 재시작 실패1건은 별도 분모이며 이 통과 수에 포함하지 않는다.
단위 검사는 `PYTHONPATH=code .venv/bin/python -m unittest discover -s code/tests -p '<test file>'`로 실행했다.
GPU 검사는 `WIND3DGS_P3_SHELL_DEVICE=cuda:0`을 지정한다.
파일은 `test_teacher_p3_shell_{dynamics,execution,warp_fast,warp_precision}.py`다.

## 재현과 근거

Root에서 `PYTHONPATH=code .venv/bin/python` 뒤에 다음 스크립트를 지정한다.

- [probe_state.py](probe_state.py): 인수로 **새** output directory 지정; 기존 결과를 덮어쓰지 않는다.
- [compare_force.py](compare_force.py): 기존 CPU 고정밀 저장 상태3개의 힘 비교.
- [replay_state.py](replay_state.py): 저장 index4부터 한 step 재시작하여 index5와 u/v/time 정확히 비교.
- [report.json](report.json): 환경, 정책, 모든 step의 독립 검산, 입력 hash와 소스 hash.
- [summary.json](summary.json): 간단한 기계 판독 결과.
- 원본은 `experiments/artifacts/runs/teacher_timestep_search/20260911_gpu_precision_v1/`의
  `states_hi_lo.npz`, `source.zip`, `report.json`, `replay.log`다.
- 입력/CPU 기준: [고정밀 상태 선행 시험](../highprecision_state_20260911/README.md).

Two-Sum과 분할 곱의 설계 근거는 [QD 원 논문](https://www.davidhbailey.com/dhbpapers/qd.pdf)이다.
보정 연산의 재결합을 막기 위해 Warp 모듈에서 fast_math/fuse_fp를 끈다.
이 구현은 전체 double-double 연산자가 아니며 극단적인 overflow/underflow 범위까지 보증하지 않는다.

다음은 시험 프로세스의 dtype 교체를 정식 opt-in 상태·저장·재시작 API로 옮기고
재시작 정확 일치의 원인을 확인하고 공력·기하·에너지 ledger까지 검산하는 작업이다. 그 뒤 장기 시간 간격 탐색을 준비한다.
