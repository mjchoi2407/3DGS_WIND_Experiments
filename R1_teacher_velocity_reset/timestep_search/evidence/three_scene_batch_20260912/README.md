# 세 씬 10초 순차 실행 준비

## 현재 상태

**후속 복구 v3:** 사용자 요청으로 첫 씬도 시간 한도를 임시 제거하고 Python 빌드 문자열 검사를 보완했다. 기존364프레임을 보존해 이어간다. 현재 wrapper는 [복구 설정과 검증](../three_scene_recovery_20260912/README.md)을 사용한다. 아래 v2 설정·준비 결과는 이전 기록이다.

2026-09-12 동결 준비 완료. 본 실행은 세 씬 모두 ready, 0프레임이며 시작하지 않았다.
최종 목적은 메시별 10초 궤적의 총 비용·잔차 초과·느린 구간을 확보하는 것이다.
사용자 변경 요청을 반영한 v2: 첫 직사각형만4시간 한도를 유지하고 삼각 깃발·손수건은 시간 한도를 제거했다.
추가 두 씬은 수치 실패나 사용자 중단이 없으면10초까지 계산한다. 전체 실행 시간 상한은 없다.
이전 전체4시간 제한 v1과 그 plan/manifest는 별도 보존했다.

대상: 기존 reference_rectangle n32, 저장된 triangular_flag와 handkerchief NPZ.
별도 rectangular_flag 샘플은 이번 대상이 아니다. 동일 원본 60Hz 바람, 기존 재료·면밀도,
4배 dt=1/(60×64), 내부 힘 목표30%·EW 상한1e-4, rest/current 전환32·재구축4회를 사용한다.
각 프레임에서 보조 풀이 이력을 초기화한다. [계획](plan.json), [동결 원본](runtime_manifest.json).

## 실행

Workspace root에서:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_three_scenes.sh
```

상태 조회:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_three_scenes.sh --status-only
```

출력: `experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v2`.
직사각형 → 삼각 깃발 → 손수건 순서로 GPU 프로세스를 하나씩 실행한다.
10초=600프레임이며 2.5초마다 수동 확인을 기다리지 않는다. 프레임마다 검산·확정 저장한다.
첫 씬만 누적 프로세스 활성 시간14,400초. 추가 두 씬의 `scene_budget_s`는 null(시간 제한 없음)이다.
초기화·원본 확인·계산·검산·저장·정상 종료가 프로세스 시간에 포함된다.
과거 개발·시험 시간은 이 본 실행 한도에서 차감하지 않는다.
본 묶음 재실행 시 정상 완료·실패·한도 종료 씬은 건너뛰고 정상 중단된 씬만 확정 frame에서 재개한다.
실패·한도 종료를 해결해 다시 이어갈 때는 별도 검토가 필요하며 같은 명령으로 예산을 초기화하지 않는다.

## 기록과 실패 처리

- 전체 `summary.md/json`: 씬별 총 프로세스 시간, 완료 물리 시간, 최대 잔차, 느린 frame 10개·step 20개.
- `<shape>/report.json`: 확정 프레임별 풀이·공력·검산·저장·전체 frame 시간 및 원본 hash.
- `<shape>/frames/NNN.json`: 모든 step의 잔차·Newton/선형 반복·HVP·보조 풀이 전환 및 시간.
- `NNN.steps.jsonl`: 프레임 확정 전에도 완료 step의 진단을 남긴다. 한도 종료 때에도 보존한다.
- `NNN.npz`: hi/lo 전체 substep 위치·속도·시간·바람·외력을 보존한다.
- `failure.json`/`controller_failure.json`: 수치·검산 실패와 시간 한도/프로세스 오류를 구분하고 마지막 위치를 남긴다.
- `failure_prefix.npz`/`last_valid_state.npz`: worker가 처리한 실패의 유효 prefix와 상태.
  외부 강제 종료는 확정 프레임·단계 로그를 보존하며 미완료 상태 복원을 보장하지 않는다.

공식 force 기준1.0 초과, 위치 갱신2e-14m 초과, 에너지 장부 불일치, 기하 충분조건 미확정 등은
해당 씬을 중단하고 다음 씬으로 진행한다. 내부30% 목표 초과는 별도로 표시하며 공식 기준과 혼동하지 않는다.
단순히 오차를 무시한 상태를 정상 궤적으로 이어가지 않는다. 기하 충분조건 실패는 실제 충돌의 증명은 아니다.
정상 Ctrl+C는 자식 프로세스를 종료하고 사용 시간을 기록한다. 중복 controller/worker 실행은 lock으로 거부한다.
controller 비정상 종료 흔적은 중복 실행·예산 누락 방지를 위해 자동 재개하지 않고 보존한다.

## 검산 범위와 비용

장기는 기존 본 실행처럼 고정밀 GPU 힘을 다시 평가하고 운동방정식·위치·에너지 장부를 재구성한다.
매 step마다 CPU longdouble 물리 함수를 다시 계산하는 느린 개발 probe와 같은 검산 backend는 아니다.
새 GPU 실행의 초기 전체 경로는 앞서 CPU longdouble 검산을 통과한 세 메시의 경로와 정확히 일치했다.
[경로 대조](cpu_audited_trace_comparison.json). 이는 초기 구간 검증이며 긴 구간의 독립 CPU 검증을 대신하지 않는다.
에너지 장부 일치는 에너지 보존 오차의 인증이 아니다. 비정규 메시의 기하 상한은 개발용 수치 추정이다.
더 작은 dt의 시간 정확도와 해상도 수렴은 별도 미완료이며, 학습 적격성/R1 완료를 선언하지 않는다.
초기화·기록 overhead와 실패한 미확정 frame 비용은 프로세스 총시간에 포함되지만 확정 frame의 비용 합과는 다를 수 있다.

## 검증

- 동결 GPU 연속3프레임: 세 씬 모두 공식 검산 통과. 총 프로세스 시간 약65.4/33.8/33.1초.
  초기 작은 바람 시험이며 10초 비용 외삽에 쓰지 않는다. [원본 요약](continuous_summary.json).
- 각 씬 2프레임 뒤 별도 프로세스로 재개해3프레임까지 완료: 연속 궤적과 모든 trace 배열 정확 일치.
  [재시작 결과](restart_checks.json), [검증 코드](verify_restart.py).
- 단계 로그192행·미완료 파일 보존·재시작 후 trace 일치 검사 통과.
  [결과](journal_checks.json), [코드](verify_journal.py).
- CPU4개 검사: 원본 변조 거부, 실패 후 다음 씬 진행, controller 비정상 종료 보호, 비유한 실패값 보존.
  [로그](tests.log). Wrapper shell 문법과 최종 동결 hash/라이브러리 버전·ready 상태 확인 완료.
- 마지막 동결본에는 검증 후 진단 출력 보완(시간 한도 위치·라이브러리 버전 검사)을 포함한다.
  수치 풀이·재개 상태 경로는 검증본과 동일하며 source hash는 각각 보존했다.

[검증 산출물 hash](validation_identity.json). 준비 및 검증은 로컬에서 수행했고 fetch·다운로드·commit·push는 하지 않았다.

## 추가 씬 시간 제한 제거 검증

CPU5개 검사 통과. 누적20,000초 이상에서 첫 씬은 시간 한도로 종료하고, 추가 두 씬은
15초 상태 조회 주기를 넘겨도 계속 계산하는지 가상 시계·프로세스로 검증했다.
[검사 로그](budget_tests.log). 수치 풀이 변경은 없으며 GPU 재시험은 하지 않았다.
새 v2는 동결 hash·ready/0frame을 확인했고 본 계산은 시작하지 않았다.
