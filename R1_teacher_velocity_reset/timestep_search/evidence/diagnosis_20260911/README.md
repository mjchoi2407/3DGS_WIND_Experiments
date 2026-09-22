# 저장 실패 상태의 단일 step 진단

## 현재 상태

2026-09-11. sub004/016/064의 `line_search` 실패를 동결 CUDA 경로로 재현했다.
세 실행 모두 마지막 Newton 시도 기록이 저장 실패와 정확히 일치했다.
진단만 수행했으며 허용오차·물리식·원본 실행·추천 판정은 변경하지 않았다.

| 분할 수 | 실패 시작 물리 시간(s) | 마지막 잔차(N) | 허용치(N) | 위치 수정량(m) |
|---|---:|---:|---:|---:|
| 4 | 2.625000 | 1.10180e-10 | 1.09218e-10 | 4.61222e-16 |
| 16 | 2.633333 | 1.09217e-10 | 1.08815e-10 | 4.54754e-16 |
| 64 | 2.647656 | 1.10343e-10 | 1.07400e-10 | 4.41686e-16 |

같은 최선 상태에서 CPU로 힘을 재계산해도 잔차가 유지됐다. CPU/GPU 힘 차이의
자유도 norm은 1.18–1.28e-14 N이며 GPU 힘 평가 3회는 정확히 일치했다.
GPU 비결정적 실행 또는 HVP graph만의 문제라는 근거는 없다.

sub064 최선 상태의 정규화된 임의 방향(seed 13)에서 중앙 차분으로 힘의 미분과 HVP를 비교했다.
수정 norm 1e-5/1e-7 m에서는 상대 차이가 각각 4.31e-9/6.44e-9였으나,
1e-13 m에서는 0.00667, 1e-15 m에서는 0.556으로 증가했다.
이는 매우 작은 수정에서 힘 차분의 정밀도가 떨어짐을 보여준다. 실제 Newton 방향에 대한
고정밀 오차 분해나 모든 HVP 방향의 정확성 증명은 아니다.
현재 가장 강한 설명은 **공통 float64 힘/상태 계산의 정밀도 부근에서 잔차 감소가 정체되는 것**이다.
어느 연산의 상쇄가 지배적인지는 아직 확정하지 않았다.

sub001은 별도 문제다. 저장된 첫 Newton 시도에서 GMRES가 480회/8 cycle 한도에 도달했고,
선형 잔차 2.14353e-8 N이 허용치 8.74650e-9 N을 넘었다. 이 후보는 이번에 재실행하지 않았다.
sub256은 82 frame 뒤 운영 시간 한도로 끝나 안정성 미확정이다.

## 검증 범위와 재현

- 동결 manifest 170항목(plan/wind 포함)의 size/hash를 확인했다.
- 다섯 후보의 마지막 확정 frame NPZ/JSON hash와 네 실패 prefix의 이전 frame 연결을 확인했다.
  실패 prefix 배열은 유한하다. 마지막 frame의 원식/기하 통과는 저장 검산 결과이며 재계산하지 않았다.
- 단일 step 재현은 실패 prefix 마지막 상태와 그 frame 시작 상태로 계산한 고정 외력을 사용했다.
  허용오차는 기존 `ShellSolvePolicy` 그대로다. 실패 궤적에 결과를 추가하지 않았다.
- CPU/GPU 자원 공유 중 수행한 시간은 성능 벤치마크가 아니다. 전체 NPZ chain/물리 재검산은 미실행이다.

Workspace root에서 아래 명령을 실행한다. 재현 스크립트는 JSON을 표준 출력으로 내보낸다.
`probe_precision.py`는 추가로 `/tmp/wind3dgs_precision_probe.json`에 임시 결과를 쓴다.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
WARP_CACHE_PATH=code/outputs/warp-cache \
PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/ten_second_v1/runtime/code \
.venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/diagnosis_20260911/replay_failure.py

PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
WARP_CACHE_PATH=code/outputs/warp-cache \
PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/ten_second_v1/runtime/code \
.venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/diagnosis_20260911/probe_precision.py
```

[실패 재현 요약](replay_results.json), [정밀도 원본 결과](precision_result.json),
[동결 입력 identity](source_identity.json)를 보존한다. Source revision은 현재 worktree가 아니라
연결된 runtime manifest의 파일 hash가 소유한다.

## 다음 진단

허용오차 완화나 장시간 재실행 전에 실제 Newton 수정 방향의 표현 오차와 요소별 힘 상쇄를
분해하고, 수식을 유지하는 계산 안정화로 기존 잔차 기준을 만족할 수 있는지 확인한다.
sub001의 반복 한도 문제는 별도로 다룬다. 이번 결과로 10초 안정성·시간 정확도를 채택하지 않는다.
