# 삼각 깃발 실패의 정적 원인 분석

## 현재 상태 — 2026-09-12

**10초 실행 준비 완료:** 검증된 새 입력·동결 코드를 별도10초 묶음으로 복사했다. 삼각 깃발만 rest·0초부터600프레임, 시간 한도 없음. ready·0프레임 확인, 본 계산 미시작. [실행 명령](#새-삼각-깃발-10초-실행-준비).

**후속 수정·단기 검증 완료:** 사용자 승인으로 고른576면 입력을 별도 동결하고 rest에서0.1초·6프레임·384단계를 계산했다. 전체 GPU 단계 검산과 대표3단계 CPU 독립 원식 검산 통과. 기존 실패 시각을 넘겼으며 시간/공간 수렴·10초·학습 적격성은 미완료다. [후속 검증](#고른-삼각-격자-01초-검증). 아래 정적 진단의 미실행 표기는 당시 범위다.

동결 v4의 옛 삼각 깃발 입력에서 **rest 굽힘 강성의 음의 방향**을 확인했다.
현행 생성기로 같은 폭1.2m·높이0.75m를 고르게 나눈 후보는 rest 굽힘 Cholesky 검사를 통과했다.
CPU 정적 진단이며 GPU 재실행·시간/공간 수렴·후보 채택은 하지 않았다. 기존 실행·동결 입력은 보존했다.

## 직접 실패와 구조적 원인

- 확정3프레임 뒤 frame3/substep44에서 `line_search` 실패. 마지막 유효 상태는0.0614583333초다.
- 실패 시 선형 풀이3회 모두 참 잔차 기준 통과. 세 번째 Newton 수정의 전체 벡터 norm은0.169257m로 커졌고, 12회 축소 탐색(최소1/2048)에서도 잔차70.9504N보다 낮아지지 않았다.
- 직전 substep30→43에서 초기 힘 잔차가0.1442→53.2358N으로 증가했다. 이를 선형 반복 한도나 VS Code 종료 문제로 해석하지 않는다.
- 실제 동결 입력은752면, 끝부분의 가느다란 삼각형 때문에 품질 최솟값0.06088이다. 정삼각형1·퇴화0 기준이다.
- 마지막 유효 변형의 전체 탄성 에너지는 약-2.1253e-7J다. 양의 내부 굽힘 에너지보다 음의 면 연결 에너지가 커졌다. 변형을1/100로 줄여도 약-2.1239e-11J이며 선형 에너지와 일치한다. 큰 변형이나 충돌이 있어야만 발생하는 문제가 아니다.
- rest 강성의 자유 Y방향 부분행렬에서 음의 고유값 약-2.0926e8을 확인했다. 물리 고유진동수 계산이 아니라 강성의 부호 검사다. 저장된 변형 방향 자체도 음의 에너지를 보여 이 결함과 실제 실패 상태가 연결된다.
- 현행 생성기는 끝으로 갈수록 정점 행을 줄이는 삼각 격자를 사용하지만, v4는 옛 저장 NPZ를 읽는다. 후보576면의 품질 최솟값은0.83724이며 rest 굽힘 Cholesky 재구성 상대오차는 약1.8e-16이다.

확정한 것은 **옛 입력과 현재 이산 굽힘 연산자의 조합이 rest 안정성을 잃는다는 것**이다.
면 연결 penalty의 크기·길이 척도·법선/경계 조립 중 개별 원인의 완전한 분리는 후속 감사다.
예비 메모리상 penalty2배·4배 비교에서도 음의 최소 고유값이 남았다. 단일 배수를 최종 해결책으로 채택하지 않는다.
새 메시의 정적 양정성은 올바른 시간 응답·GPU 미분·해상도 수렴의 증거가 아니다.

## 권장 해결 순서

1. 기존 원본은 유지하고 현행 생성기의 고른 삼각 격자로 별도 입력을 만든다. 물리적 외곽·단위·고정변·재료·바람·시간 간격·오차 기준을 유지한다.
2. 변경된 공간 자유도에 기존 변위·속도를 그대로 복사하지 않는다. 별도 실행에서 초기 상태부터 실패 시각을 넘는 짧은 구간을 확인한다.
3. CPU/GPU 힘·미분과 원식 검산, 새 메시 해상도 비교를 통과하면10초 검증을 검토한다. 형상별 국소 penalty 선택/경계 항 감사도 필요하다.
4. 반복 횟수 확대·작은dt·추가 감쇠만으로 음의 강성을 해결했다고 판정하지 않는다. 안정적인 공간 모델에서 남는 비선형 실패에 한해 line search 보완을 검토한다.

일반적인 C0 interior penalty의 안정화 계수는 삼각분할 기하에 의존한다.
[Bringmann·Carstensen·Streitberger의 원문 초록](https://arxiv.org/abs/2209.05221)을 웹에서 확인했다.
해당 선형 biharmonic 결과를 현재 비선형 셸의 안정성 증명으로 자동 승계하지 않는다.

## 재현

원본·동결 manifest·실패 상태 SHA256과 상세 진단은 [report.json](report.json), 검사 코드는 [audit.py](audit.py)다.
동결 manifest의 원본 hash/버전을 검증한 뒤 CPU1스레드로 실행한다. 후보 메시와 행렬은 메모리에만 생성한다.

```bash
PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4/runtime/code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/triangle_failure_20260912/audit.py
```

예비 penalty 배수 검사는 상세 재현 스크립트 범위 밖이며 채택 근거로 쓰지 않는다.
외부 메시 다운로드·fetch 없음. 원문 웹 조회만 수행했다. 코드·물리 설정·본 실행 변경과 commit·push는 하지 않았다.

## 고른 삼각 격자 0.1초 검증

- 새 입력은 기존 생성기의 고른 삼각 격자다. 외곽 좌표 범위와 고정변 양 끝 일치 검사 통과. 공간 삼각분할만 변경했으며 기존 바람·물성·dt·허용오차·재구축64회를 유지했다.
- 별도 출력: `experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_01s_v1`. 기존 v4 세 씬 및 기존 입력은 보존했다. 새 실행은 rest에서 시작하며 기존 실패 궤적을 전송하지 않았다.
- 실제 GPU 실행6프레임·384단계 완료, 모든 단계의 공식 검산 통과. 최대 힘 잔차/허용치0.299843, 내부30% 목표 초과0. 확정18파일 hash 검증 통과.
- 대표 CPU longdouble 검산은 첫 비영 바람 단계, 기존 실패 frame3/substep44, 마지막 frame5/substep63이다. 세 단계 모두 공식 힘/위치 기준·고정점 보존 통과, CPU 최대 잔차 비0.005542 미만. 대표 시점의 탄성 에너지는 양수다. 전체384단계 CPU 재계산은 하지 않았다.
- 총 프로세스 시간 약73.8초, 풀이36.9초·GPU검산9.0초. 다른 GPU 작업이 관측됐고 커널 컴파일이 포함되어 속도 비교나10초 비용 외삽 근거가 아니다.
- 기존 failure 시각을 넘는 단기 검증 완료이며 새 메시의 시간·공간 수렴, 장기10초와 학습 적격성은 미완료다. 기존 공통10초 wrapper는 v4를 유지하고, 별도 단기 wrapper만 추가했다.

[입력 변경·source hash](regular_input_change.json), [동결 계획](regular_plan.json), [검산 결과](regular_checks.json).
기존 동결 runtime을 그대로 복사하여 새 manifest로 봉인했다. 물리 코드 수정·허용오차 완화·자동dt 변경은 없다.

Workspace root에서 실행한 명령:

```bash
PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4/runtime/code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/triangle_failure_20260912/prepare_regular.py
bash experiments/R1_teacher_velocity_reset/timestep_search/run_triangle_regular_check.sh
PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_01s_v1/runtime/code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/triangle_failure_20260912/verify_regular.py
```

준비 스크립트는 기존 출력 덮어쓰기를 거부하며 완료 실행의 wrapper 재호출은 계산을 반복하지 않는다.
이번 수정에서는 외부fetch·다운로드·commit·push를 하지 않았다.

## 새 삼각 깃발 10초 실행 준비

출력은 `experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_10s_v1`이다.
단기 검증과 입력·동결 Python 코드·물성·바람·dt·공식 및 내부 허용오차가 동일하다.
계획에서 총프레임만6→600으로 변경했다. 삼각 깃발의 기존 시간 한도 없음 정책을 유지한다.
초기 rest·0초부터 계산하며0.1초 검증 궤적은 복사하지 않았다. 직사각형·손수건은 다시 계산하지 않는다.
기존 `run_three_scenes.sh`는 옛 v4를 가리키므로 새 삼각 깃발은 아래 전용 명령을 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_triangle_regular_10s.sh
```

상태 조회:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_triangle_regular_10s.sh --status-only
```

실행 터미널은 초기화 후 약15초 간격으로 상태를 표시한다. 상세 프레임 로그는 새 출력 아래
`triangular_flag/worker.log`에 누적된다. 정상 중단은 실행 터미널에서 Ctrl+C를 사용한다.
완료·수치 실패는 재호출로 초기화하지 않으며, controller 소실 흔적은 기존처럼 수동 복구 대상이다.

[동결 계획](regular_10s_plan.json), [준비 근거](regular_10s_preparation.json), [준비 코드](prepare_regular_10s.py).
준비 반복 호출의 비초기화, 입력·원본 복사 hash/버전,600프레임 바람 길이, shell 문법,
ready·0프레임을 확인했다. GPU 계산은 시작하지 않았다.10초 성공·수렴은 미검증이다.
