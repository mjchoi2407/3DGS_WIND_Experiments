# 전체 1.5초 자연 응답: baseline 대 HVP/graph 비교

> **2026-09-22 보존 상태:** 성능·검산 판정, config, manifest와 source identity를 유지하고 baseline/fast의
> 180개 frame 배열은 report-only로 정리했다. 아래 수치는 보존 report가 authority다. 궤적이 다시 필요하면
> `full_comparison.py --output 새로운_폴더`로 처음부터 계산하며 과거 wall-clock의 정확 재현은 보장하지 않는다.

## 현재 상태

2026-09-10 16:32 KST 전체 비교 완료. 사용자 재개 후 기존·개선 방식 각90 frame,
양쪽 검산 및 최종 비교5단계가 모두 통과했다. 계산 시간은13.41% 단축됐다.
단일 순차 실행이며 다른 GPU 부하와 기존 방식의 재시작을 포함하므로 성능은 잠정값이다.
R1 전체 완료·학습 적격성 판정은 아니다.

## 후속 실행 방식 결정

2026-09-10 사용자가 이번 개선 수준으로 계속 진행하기로 선택했다.
후속 물리 검증은 CPU 반복 풀이를 유지한 HVP 전용 계산+CUDA graph 경로를 사용한다.
추가 GPU 풀이·전처리 최적화는 보류한다. 이번 결정은 수식·정밀도·통과 기준이나 R1 완료 판정을 바꾸지 않는다.
장시간 계산은 사용자 실행 스크립트로 인계하는 방식을 유지한다.
기존 중단 원본의 동결 source를 덮어쓰거나 구현 변경을 숨긴 채 이어 붙이지 않는다.
일반 실험 실행기의 경로 연결·재시작 provenance를 정리한 뒤 남은4배 바람 검증에 적용한다.

## 완료 결과

| 기록된 시간 | 기존 방식 | HVP/graph 개선 방식 |
| --- | ---: | ---: |
| 계산 | 9,991.43초 (166.52분) | 8,651.35초 (144.19분) |
| 압축 저장 | 180.89초 | 180.77초 |
| 검산 계산 | 1,206.66초 | 1,243.69초 |
| 검산 읽기 | 69.12초 | 85.31초 |
| 준비·워밍업·재시작 준비 포함 합계 | 11,472.26초 (191.20분) | 10,172.67초 (169.54분) |

계산은1.1549배 속도, 소요 시간13.4124% 감소로22분20초 절약됐다.
기록된 전체 비용 합계는11.3281% 감소했다. 사용자 중단 대기와 미저장 frame에 소모된 시간은
합계에 포함되지 않으므로 실제 시작부터 종료까지의 벽시계 시간과 구분한다.
검산기는 양쪽 모두 원래 구현이며 검산 시간이 줄었다는 결과는 아니다.
CPU 반복 풀이를 유지한 개선 방식의 결과이며 CuPy GPU LU의 성능 결과로 사용하지 않는다.

- 양쪽 각각90 frame ×256 interval =23,040 interval 자동 원식·기하 검산 통과.
  매 frame의0/128/256 상태에서 NumPy 대조도 수행했다.
- 변위 상대 차이 상한3.0526e-14, 속도 상대 차이 상한1.2254e-10으로 기존0.01(1%) 기준 통과.
  최대 좌표 성분 차이는3.7002e-15m, 속도 성분 차이는6.1650e-10m/s다.
- 전체 HVP 호출 수는 기존609,554회, 개선609,528회로 완전히 같지는 않다.
  이 차이에도 기존 수치 허용오차와 전체 응답 비교를 통과했다. 반복 횟수를 강제로 같게 만든 벤치마크는 아니다.
- 완료 후180개 NPZ hash, 원 동결 소스 및 재개 실행기 hash, frame/interval 분모와 시간 합계를 확인했다.
  재시작 경계인37번째 마지막 상태와38번째 첫 상태의 모양·속도·시간은 정확히 일치했다.
  물리 계산을 다시 실행한 것이 아니라 저장된 자동 검산 결과와 원본 무결성을 확인한 검토다.

[완료 근거](evidence/completed_pair_v1/)에 config, 단계 상태, 양쪽 계산·검산 보고서,
전체 비교, source identity 및 완료 검토를 보존했다. Raw 경로는 아래 실행 안내와 같다.

## 비교 범위와 기준

- 32격자, sub256, 60fps, 90 frame(1.5초), seed20260909, 기존 4배 바람(목표 knot1–2m/s).
- Baseline은 기존 Warp 물리 연산+CPU 반복 풀이, fast는 HVP 전용+CUDA graph+동일 CPU 반복 풀이다.
- 두 방식 모두 rest에서 독립적으로 시작해 끝까지 계산한다. 기준 실행 뒤 최적화 실행을 순차 수행한다.
- 두 실행이 끝나면 각각 전 frame의 원식·기하 및 frame별3 NumPy 상태/공력 대조를 검산한다.
- 같은 격자의 모든 substep 결과와 Newmark 보간 차이를 비교한다. 기존1% 상대 상한 기준을 사용하고
  최대 위치·속도 성분 차이도 함께 기록한다. Rest-origin이0이라 변위 증분과 변위는 같다.
- 준비, 워밍업, 계산, 압축 저장, 검산 읽기와 검산 시간을 분리한다. Warmup은 별도 합성 상태의1 step이며
  본 물리 시간에 포함하지 않는다. 단일 순차 pair로 순서/시간대 효과를 배제할 수 없다.
- GPU LU 시제품, 새 전처리, 세 velocity-reset 분기와 다른 격자의 전체 재검증은 이번 pair에 포함하지 않는다.
  학습데이터 생성0, R1 전체/학습 적격성은 미완료다.

## 실행과 확인

### 사용자용 연결·이어하기 명령

Workspace root에서 다음 한 줄을 실행한다. 기본 대상은 당시 완료 결과이며 현재는 정리된 요약 조회용이다.
새 궤적은 아래 `full_comparison.py --output` 명령으로 별도 생성한다.

```bash
bash experiments/R1_teacher_velocity_reset/p3_shell_random/profiling/run_full_comparison.sh
```

- 이미 실행 중이면 해당 프로세스에 연결하여 진행도만 표시한다. 기존 시뮬레이션을 중복 시작하거나 중단하지 않는다.
- 실행이 중단돼 프로세스가 없으면 같은 명령이 보고서에 확정된 마지막 frame의 모양·속도·시간에서 이어간다.
  계산 중이던 미저장 frame은 다시 계산한다. 저장 파일은 생겼지만 report에 반영되지 않은 frame은 `recovery/`에 보존한 뒤 다시 계산한다.
- 초기 source snapshot의 hash를 확인하고 동일 물리 구현을 사용한다. 재시작용 실행기만 `runtime/controls/`에 별도 동결한다.
- 계산을 다시 진행한 backend의 기존 검산/비교 완료 결과는 이력으로 옮기고 다시 검산한다.
  검산 자체가 중단됐으면 그 검산 단계는 처음부터 다시 수행한다.
- 기존·개선 방식 각각 계산 frame 수·백분율과 검산 frame 수를 출력한다. 변화가 없어도30초마다 표시하며,
  계산 중에는 마지막 frame 보고 이후 경과 시간도 보여 준다. Frame 내부 substep 진행률은 아직 표시하지 않는다.
- **Ctrl+C는 표시만 종료한다. 계산은 별도 프로세스에서 계속된다.** 같은 명령으로 다시 연결한다.
  PC 종료/재부팅으로 계산까지 중단됐다면 재실행 시 이어하기가 적용된다.
- 실패하면 오류를 알리고 종료 코드1을 반환한다. 무한 자동 재시도는 하지 않는다.
- 전체 완료 시 원식 검산·결과 차이 기준의 통과 여부와 잠정 계산 속도 비율을 표시한다.
  최종 `comparison.json`과 `summary.md`를 검토해야 하며, 성공 종료가 R1 전체 완료나 학습 적격성을 의미하지 않는다.

기본 확인 간격은10초다. 상태만 조회하거나 다른 기존 결과 폴더에 연결할 수도 있다.

```bash
bash experiments/R1_teacher_velocity_reset/p3_shell_random/profiling/run_full_comparison.sh --status-only
bash experiments/R1_teacher_velocity_reset/p3_shell_random/profiling/run_full_comparison.sh --output experiments/artifacts/runs/teacher_p3_shell_profile/기존_폴더 --interval 5
```

최초 실행 로그는 `20260910_full_pair_v1.launch.log`, 재시작 시 상위 로그는 결과 폴더의
`continuation.launch.log`, 단계별 상세 로그와 이전 보고서는 `continuations/<시각>/`에 남긴다.
진행도 표시는 기존 결과에 대한 조회이며 별도 채팅 원문 기록을 만들지 않는다.

### 새 전체 비교 생성용 실행기

실행기는 [`../full_comparison.py`](../full_comparison.py)다. Workspace root에서:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -u experiments/R1_teacher_velocity_reset/p3_shell_random/profiling/full_comparison.py --output experiments/artifacts/runs/teacher_p3_shell_profile/새로운_폴더
```

이번 결과 경로는 `experiments/artifacts/runs/teacher_p3_shell_profile/20260910_full_pair_v1`이다.
같은 parent의 `20260910_full_pair_v1.launch.json`은 시작 PID/명령,
`20260910_full_pair_v1.launch.log`는 전체 로그다. 실행은 별도 process session에서 이어진다.

- `status.json`: 진행 단계·완료 단계·실패 여부. PID가 사라졌는데 실행 중이라면 강제 중단 여부를 확인한다.
- `baseline/report.json`, `fast/report.json`: 완료 frame과 시간 합계.
- 각 `frames/`: NPZ와 진단 JSON. 새 결과이며 기존 원본을 덮어쓰지 않는다.
- 각 `audit.json`: 원식·기하·CPU 대조 결과.
- `gpu_load.jsonl`:10초 간격GPU 전체 부하/메모리/온도/전력. 개별 작업 점유율은 아니다.
- `comparison.json`, `summary.md`: 모든 단계가 끝난 뒤 생성하는 비교·요약.
- `runtime/manifest.json`, `runtime/code/`, `runtime/driver.py`: 시작 시 소스를 복사·동결하며
  각 worker는 해당 복사본에서 실행한다. 이후 원래 작업 파일 수정과 분리한다.

재실행은 새 output 경로를 요구한다. 실패한 결과를 자동 삭제하거나 처음부터 덮어쓰지 않는다.
위 문장은 새 비교 생성용 실행기에 대한 제약이다. 사용자용 스크립트는 기존 결과를 이어가는 별도 제어기다.

## 실행기 검증

n4/sub8/2 frame의 CPU 및 실제 CUDA smoke에서 두 backend 실행, 연속성 검사,
원식·기하·CPU 대조, 전체 비교와 자동 요약까지 완료·통과했다.
[evidence](evidence/)의 smoke 결과는 실행기 검증이며 n32 전체의 정확도·속도 결과가 아니다.

### 이어하기 검증

- CPU n4/sub8/2 frame의 원래 완료 smoke를 별도 `20260910_resume_smoke_v2`로 복사했다.
  초기 smoke에는 아직 없던 schema 표기만 현행 값으로 추가하고, 양 backend의 완료 report를 첫 frame까지로
  제한했다. 두 번째 frame 파일과 기존 완료 검산을 남겨 저장/보고서 갱신 사이 중단 조건도 시험했다.
- 양 backend 모두 두 번째 frame만 이어 계산했다. 첫 frame의 NPZ hash가 보존됐고,
  두 frame의 모든 저장 배열이 원래 연속 실행과 정확히 일치했다. 미보고 frame은 recovery에 보존됐다.
- 후속 양쪽 원식·기하 검산 및 전체 비교가 다시 수행돼 통과했다. Source hash 변조는 실행 전 거부됐다.
- 실제 장시간 CUDA 실행에는 조회만 연결했다. 기존 PID 두 개를 탐지했으며 표시 프로세스에 SIGINT를 보낸 뒤에도
  기존 계산 프로세스가 유지됐다. 실제 n32 CUDA 실행을 강제로 중단하는 시험은 하지 않았다.
  작은 CPU 이어하기 시험은 장시간 실행과 동시에 수행했으므로 해당 시간대 역시 전용 성능 측정 환경이 아니다.
- 재시작의 추가 준비/워밍업 비용은 각 report의 `resume_events`와 새 comparison의
  `resume_setup_warmup_s`에 따로 기록한다. 중단 프레임에서 소모된 미보고 시간은 복구할 수 없으므로
  기록된 계산 시간은 완료 frame 기준이며 전체 벽시계 시간과 다르다. 다른 부하 및 재시작 영향을 포함하는 잠정 성능값이다.
- 초기 v1 시험은 schema 없는 옛 fixture를 거부했으며 fixture 메타데이터를 명시적으로 보완했다.
  기존 물리식·수치 정밀도·허용오차는 변경하지 않았다.

근거: [이어하기 검사](evidence/resume_smoke_v2_verification.json),
[검산·비교 결과](evidence/resume_smoke_v2_comparison.json),
[실행기 및 시험 snapshot identity](evidence/resume_control_manifest.json).

### 사용자 인계 시 종료와 저장점 확인

사용자가 Codex의 지속 모니터링 대신 직접 실행하도록 요청하여, 명령·결과 경로와 독립
process group을 확인한 뒤 해당 실행 관리자와 계산 worker만 SIGTERM으로 종료했다.
종료 전 상태와 이유는 raw의 `user_stop_*.json`에 보존하고 `status.json`은 사용자 중단으로 표시했다.
37개 확정 frame의 NPZ hash와 동결 source hash, 마지막 모양·속도·시간의 유효성을 확인했다.
이는 저장점 확인이며 물리식 전 구간 검산을 대신하지 않는다. 미저장38번째 frame은 재개 시 다시 계산한다.
실제 시뮬레이션은 다시 시작하지 않았다. 사용자 완료 알림 후 최종 보고서를 검토한다.
