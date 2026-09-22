# 32격자 Teacher 병목 진단 — 2026-09-10

## 목적과 범위

사용자가 긴 검증 재개나 전체 GPU 이식에 앞서 대표 구간 병목 진단을 승인했다.
물리식·solver·허용오차·기존 원본은 변경하지 않았다. 학습데이터 생성과 GPU 이식은 수행하지 않았다.
완료된 `20260909_scale4_natural_m32_s256_v1`의 manifest 전체와 현행 producer source를 대조했다.
진행 이력은 [기존 session](../../../sessions/2026-09-09_02_teacher_velocity_reset.md)의 병목 진단 절에 보존한다.

## 방법

32격자/sub256의 저장된 상태에서 각각 4 substep을 재생했다. 전 frame의 step 기록에서
연속 4 substep의 HVP 호출 합이 최소/최대인 구간과, frame72 이후 최대인 구간을 선택했다.
최소 구간은 아직 외력이 없는 정지 시작 상태이므로 활성 변형 구간의 대표 속도로 해석하지 않는다.
각 구간에서 1 step 워밍업 후 비계측 재생과 cProfile 계측 재생을 실행했다.
프레임 시작 공력을 원본에서 그대로 읽으므로 이번 측정은 공력 생성·파일 저장·전체 검산 비용을 포함하지 않는다.
초기 설정은 약 19.78초이며 아래 시간에서 제외했다. 결과는 [원본 계측 보고서](report_v1.json)에 있다.

| 구간 (0-based frame/substep) | 비계측 4 step | 계측 4 step | CPU 희소 풀이 자체 시간 | GPU 동기화 자체 시간 | HVP 호출 |
|---|---:|---:|---:|---:|---:|
| 정지 시작 0/0 | 0.151초 | 0.171초 | 0.035초 | 0.066초 | 0 |
| 무거운 구간 39/236 | 2.787초 | 2.959초 | 1.159초 (39.2%) | 0.837초 (28.3%) | 160 |
| 바람 종료 79/144 | 2.713초 | 2.972초 | 1.122초 (37.8%) | 0.858초 (28.9%) | 155 |

세 구간 모두 원본 끝 상태의 위치·속도 최대 절대 차이가 0이었다. 계측/비계측 결과도 정확히 같고
HVP 호출 수가 원본과 일치했다. 긴 수렴 검증을 대체하는 결과는 아니다.

## 해석과 다음 우선순위

- 무거운 구간에서 CPU SuperLU solve 168회에 1.159초가 걸렸다. 질량 풀이와 선형 반복을 돕는
  전처리 풀이가 포함된다. CPU 희소 풀이가 실제 비용의 큰 부분임을 확인했다.
- 같은 구간에서 구조 평가 181회, GPU 동기화 181회, Warp copy 1,810회, launch 1,991회가 관측됐다.
  Copy 함수 자체 시간은 0.201초(6.8%)다. 이것은 양방향 순수 전송시간의 직접 측정이 아니며
  함수 내 처리·대기를 포함한다. Launch와 동기화 횟수는 profiler 관측 함수 호출 수다.
- GMRES의 하위 호출 포함 시간은 2.631초이나 여기에 GPU 평가와 CPU 풀이가 중첩된다.
  이를 위 항목과 합산하면 안 된다. 보고서 groups는 중첩되지 않는 자체 시간으로만 합산한다.
- 우선 검토할 최적화는 HVP 반복에서 불필요한 force/energy/diagnostic 생성·회수를 분리하는 것과
  CPU 희소 전처리/질량 풀이를 포함한 반복 데이터를 GPU에 유지하는 것이다.
  GPU 전처리 선택에 따라 수렴과 반복 수가 달라질 수 있어 현재 진단만으로 속도 향상을 보장하지 않는다.
- 후속 구현은 별도 범위 합의 후 수행한다. 정확도 기준이나 float64를 낮추는 방식은 이번 진단에 포함하지 않았다.

## 한계와 장애 처리

일반 sandbox에서는 NVML 접근이 차단됐지만 승인된 실행 환경에서 CUDA 진단을 완료했다.
보이는 프로세스 목록에는 이전 Teacher 작업이 없었다. 진단 시작 전에도 GPU 사용률 66%가
관측됐고 실행 중 관측값은 96%였다. GPU 전체 사용률로 이 프로세스의 사용률을 분리할 수 없으며
다른 부하 간섭을 배제할 수 없다. 사용자 관측 20%의 원인을 직접 재현한 것은 아니다.

cProfile은 CPU wall-time 계측이다. GPU 동기화에는 실제 커널 실행 대기와 다른 작업의 대기가
포함될 수 있다. GPU 장치 이벤트 기반 커널/전송 타임라인은 측정하지 않았으며, 동기화 28%를
제거 가능한 낭비로 해석하지 않는다. 계측 시간은 비계측보다 약 6–14% 길었다.
결과는 각 구간 1회의 짧은 측정이며 전체 run 평균이나 독점 GPU 성능 벤치마크가 아니다.

## 재현

Workspace root에서 새 output 경로를 지정한다. 기존 output은 덮어쓰지 않는다.

```bash
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/p3_shell_random/profiling/profile_replay.py --parent experiments/artifacts/runs/teacher_p3_shell_random/20260909_scale4_natural_m32_s256_v1 --output experiments/artifacts/runs/teacher_p3_shell_profile/new_diagnostic
```

원본·source SHA는 report에, 사용한 진단 스크립트 SHA도 같은 report에 기록했다.


## 승인된 1–4단계 구현 — 후속 진행 중

사용자는 (1) HVP 전용 연산, (2) GPU 반복 풀이, (3) 동기화/호출 정리,
(4) 저장·검산 비용 분리를 승인했다. CuPy 추가와 이후 직접 반복 제어도 각각 선택했다.
현재 기존 실행기는 변경하지 않았고 새 backend는 명시적으로 선택하는 개발 경로다.

- `p3_shell_warp_fast.py` / `_fast_kernels.py`: 기존 dual derivative를 그대로 사용하며 HVP에서
  에너지·힘 출력과 조립을 생략한다. 기하 guard와 유한성 검사는 유지한다. 선택적 CUDA graph는
  입력 buffer 갱신과 잘못된 기하 거부·회복을 실제 GPU에서 확인했다.
- `p3_shell_cupy.py` / `_cupy_linalg.py`: GPU에 큰 벡터와 희소 행렬을 두고, left-preconditioned
  restarted GMRES의 조기 종료를 구현했다. 작은 Hessenberg/Givens 제어 및 초기 LU 분해는 CPU다.
  GPU LU의 구조 분석 계획과 buffers를 재사용한다. CUDA graph는 CuPy/Warp 공유 전용 stream에서 실행한다.
- 선택 의존성은 `code/pyproject.toml`의 `teacher-gpu-solver`다. 실제 설치한 것은
  `cupy-cuda12x==13.6.0`, `fastrlock==0.8.3`이며 `pip check`가 통과했다.
- 새 물리 허용오차를 도입하지 않았다. 초기 비트 일치 검사는 GPU 커널 분리의 미세 차이로 실패했다.
  기존 CPU/GPU 비교 기준을 사용해 확인했으며 bitwise equality를 계약으로 채택하지 않는다.

### 실제 n32 순차 비교

같은 frame39/substep236에서 1 step을 워밍업 후 3회씩 측정했다.
[현재 비교 결과](evidence/backends_v3.json)의 중앙값은 다음과 같다.

| backend | 반복 실행 중앙값 | HVP 호출 | 원본 위치 최대 차이 | 원본 속도 최대 차이 |
|---|---:|---:|---:|---:|
| 기존 CPU 풀이 + Warp | 0.6553초 | 40 | 0 | 0 |
| HVP 전용 + graph + CPU 풀이 | 0.5878초 | 40 | 2.65e−23m | 8.67e−19m/s |
| 직접 GMRES + GPU LU 재사용 + graph | 13.0850초 | 40 | 5.29e−23m | 2.78e−17m/s |

현재 GPU LU 경로는 느리므로 채택하지 않았다. HVP/graph 경로는 이 비교에서 약10.3% 짧지만
한 상태의 세 반복이며 전체 시뮬레이션 속도 보장은 아니다. 이전 예비 비교의 약17%와 구분한다.

### GPU 희소 풀이만 분리한 결과

[LU 분리 계측](evidence/lu_v1.json): 같은 행렬/우변/분석 계획 재사용 조건에서 CPU 6.7–9.7ms,
GPU wall 약176–177ms, CUDA event 약177–178ms다. GPU해의 상대 잔차는1.36e−15,
CPU/GPU 해의 상대 차이는6.25e−16이다. 현재 카드·행렬·cuSPARSE 구현의 성능 결과이며
GPU 희소 풀이 전체가 언제나 느리다는 일반화는 하지 않는다.

사용자에게 CPU 희소 풀이 유지와 GPU 친화적인 다른 전처리 개발의 장단점을 제시하고 답을 기다린다.
후자는 추가 수렴/성능 검증이 필요한 별도 결정이다.

### 저장·검산 분리

[기존 완결 frame39 I/O·검산](evidence/io_audit_v1.json): 읽기/hash0.354초,
압축 저장2.214초, CUDA 원식+3 NumPy 상태/공력+기하 검산12.813초.
256 interval 검산과 저장 배열의 정확한 왕복을 통과했다. 새 GPU backend의 검산 통과로
승계하지 않는다. 검산 기능을 삭제하거나 판정 기준을 낮추지 않았다.

### 실패와 수정 이력

- CuPy 기본 GMRES는 작은 격자에서 HVP8–10회를126회로 늘렸다. n32 warmup은 수 분 뒤 중단했다.
  중단 stack은 `spSM_analysis`였다. [V1](evidence/backends_v1.json)은 미완료로 보존한다.
- 조기 종료와 계획 재사용 후 null stream graph capture가 실패했다.
  공유 비기본 stream으로 수정했다. [V2](evidence/backends_v2.json)는 실패 기록이다.
- 직접 GMRES의 항등 연산자 시험에서 buffer aliasing을 발견해 작업 벡터를 복사하도록 고쳤다.
  이후 선형 풀이·초기화·물리 검사를 함께 통과했다.
- `compare_backends` 검산 인수의 list/dict 계약 오류는 해당 실행 경로에 도달하기 전 발견해 고쳤다.
  별도 I/O 검산 wrapper에서 검산을 실제 실행했다.

사용한 wrapper는 `compare_backends.py`, `profile_lu.py`, `profile_io_audit.py`,
`validate_accelerated.py`다. 모두 새 output 경로를 요구하며 원본은 읽기만 한다.
`validate_accelerated.py --backend fast`의 실제 전체 frame 검증은 완료했다.
[원식 검산 결과](evidence/fast_validation_v1.json): frame39/79의 총512 interval, frame마다
3 CPU 상태와 공력 대조·Bernstein 기하 검산을 통과했다. 위치 최대 차이는각각5.55e−16/5.83e−16m,
속도 최대 차이는9.29e−11/1.01e−10m/s였다. 최대 force/허용치 비는0.98864/0.69880이다.
Frame39의 계산/압축 저장/검산은130.168/2.069/14.281초,
frame79 계산/검산은103.110/10.825초다. 같은 조건의 기준 전체 frame wall-time을 새로 재지 않았으므로
이 수치로 전체 frame 배속을 주장하지 않는다.

Frame42의 실제 변형 상태에서 속도를0으로 만든 뒤4 step도 기준과 비교했다.
제거 운동에너지는두 경로 모두0.0014712900753203473J, 최종 위치/속도 최대 차이는
4.53e−20m/1.39e−15m/s였다. 전체 random/reset 공간·시간 수렴 묶음의 재검증을 대체하지 않는다.

CUDA 단위 검사는 HVP/graph3개, CuPy 물리1개, 선형 풀이2개를 통과했다.
기존 원본과 실행기·수식·물리 허용오차는 유지하며, 긴 검증 재개와 학습데이터 생성은 하지 않았다.
현재1번 HVP분리,3번 선택적 graph,4번 저장·검산 분리 측정은 구현·검증됐고,
2번 GPU 반복 풀이 시제품은 수치 검사에 통과했지만 성능 때문에 미채택이다.
CPU 희소 풀이 유지 또는 새로운 GPU 친화적 전처리 중 사용자 결정을 기다린다.

비교 당시 source는 `evidence/backend_v3_source.zip`에 보고서의 SHA와 정확히 대조해 보존했다.
폐기하지 않은 첫 시제품 source는 `evidence/optimization_prototype_v1.zip`이다.
추후 반복 결과는 새 output 경로로 남기며 기존 실패 결과를 덮어쓰지 않는다.
