# Newmark 고정 dt / 수렴 실패 시 절반 dt — 세 씬씩 비교

## 현행 재시도 변경

사용자 후속 선택으로 `run_newmark_dt_retry.sh`는 이제 [Gauss6차8분할 재시도](newmark_gauss_retry.md)를 실행한다. 아래 half-dt 설명은 선행 비교 기록이다.

## 실행 — half-dt 비교 당시

두 스크립트 모두 이 컴퓨터의 로컬 GPU에서 직사각형→손수건→삼각형을 순차 실행한다.
서브컴 전용 옵션/원격 실행은 없다. 같은 GPU에서 두 스크립트를 동시에 돌리면 성능 비교가 왜곡된다.

```bash
# 1. 세 씬 모두 고정 dt
bash experiments/R1_teacher_velocity_reset/timestep_search/run_newmark_dt_fixed.sh

# 2. 세 씬 모두 수렴 실패 시 해당 substep만 절반 dt 두 단계로 재시도
PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_newmark_dt_suite --mode retry --out experiments/artifacts/runs/teacher_timestep_search/newmark_half_dt_reproduction_v1
```

각 스크립트에 `--prepare-only`, `--status-only`, `--out <새 경로>`를 붙일 수 있다.
`--smoke --out <별도 경로>`는 단계별1프레임의 짧은 구동 확인이다. 본 실행과 섞지 않는다.
완료된 단계는 재계산하지 않으며 interrupted/실패 실행은 자동 재개하지 않는다.
실패한 씬은 실패로 남기고 다음 씬을 실행한다. Ctrl+C는 전체 suite와 현재 소유 worker를 종료한다.

## 공통 조건

- Newmark·FP64 hi/lo, 기본 dt=1/3840초,60Hz·기본64substep.
- 굽힘1/500, 원래 저해상도 메시/면내 강성/면밀도/고정 조건.
- 중력2초(120프레임) 후 같은 처짐 checkpoint에서 무풍4초와 바람4초를 각각 계산한다.
  각 씬 총600프레임이며 단일 연속10초 궤적은 아니다.
- 원래 중력/바람1초 smooth ramp, 속도 reset/추가 댐핑 없음.
- 기존 국소 기하·힘·위치·에너지·고정점·비유한 검산을 유지한다. 기하 경고는 dt 전환 조건이 아니다.
- 정상 구간에는128분할 오차 추정이나 Gauss 재계산이 없다.
- 두 방식의 물리 입력은 동일하지만 재시도 이후 궤적과 처짐 checkpoint는 달라질 수 있다.

재시도는 수렴 실패(code1/2/3, 유한 통계 및 정상 prefix 검산)에만 적용한다.
실패 직전 상태를 복원하여 dt=1/7680초 두 단계로 계산하고, 성공하면 다음 구간은 기본 dt로 돌아간다.
절반 dt에서도 실패하면 중단하며1/4dt로 추가 분할하지 않는다. 정확도 기준은 완화하지 않는다.
세부 캐시/상태 계약은 [구현 문서](../../../../code/docs/newmark_dt_retry.md)를 따른다.

## 출력과 비교

기본 출력은 `artifacts/runs/teacher_timestep_search/` 아래 다음 두 폴더다.

- `newmark_dt_fixed_bend500_v1/<shape>/`
- `newmark_dt_retry_bend500_v1/<shape>/`

각 씬은 config/manifest/runtime, 각 phase의 report/log와2초 간격 확정 chunk를 소유한다.
원시 FP64 hi/lo 상태는60Hz, 검산은 모든 채택 substep에서 기록한다.
가변 간격은 `.audit.npz`의 `dt_s`·`time_s`에 명시하며64배로 시간을 추측하지 않는다.
`frame_timings.jsonl`은 프레임 GPU 완료까지의 계산·검산·실패 시도·재시도 비용과 반복 수를 남긴다.
초기화·파일 저장·worker 전체 시간은 report에서 구분하며, suite_report의 `controller_wall_s`는 프로세스 준비/실행/저장을 포함한 씬 전체 벽시계 시간이다. 실패 시도 비용도 비교에 포함한다.

```bash
.venv/bin/python code/scripts/summarize_newmark_dt_suite.py \
  --fixed experiments/artifacts/runs/teacher_timestep_search/newmark_dt_fixed_bend500_v1 \
  --retry experiments/artifacts/runs/teacher_timestep_search/newmark_dt_retry_bend500_v1 \
  --out /tmp/newmark_dt_comparison.json
```

장치가 다르면 절대 시간 차이를 dt 정책의 가속률로 해석하지 않는다. 공통 완료 프레임과 실패 분모,
GPU 종류/부하·setup/cache 조건을 확인한다. 스크립트의 같은 GPU 이름도 동일 부하를 보장하지 않는다.
현재는 개발 성능/안정성 비교이며 시간 수렴·teacher 적격성·셀프컬리전 검증을 대체하지 않는다.

## 준비·검증 완료 — 2026-09-15

본6개 설정은 모두 ready0이며 긴 본 실행은 시작하지 않았다. 두 방식의 세 phase 물리 입력은
byte 일치, 물성/공식 허용오차/선형 풀이 설정 일치를 확인했다.

- 작은 GPU fixture: 정상 고정/재시도 동등성, 중간 substep 복원과 두 half step 시간 기록,
  half 실패 시 추가 분할 금지 및 프레임 시작 상태 보존 통과.
- 원본1/500 wind2초의 실제 실패 프레임: 고정 dt는56단계 후 GMRES 실패,
  retry는 기본 인덱스56/62 두 구간을 half2로 대체해64기본 구간/66채택 단계 검산 완료.
  각각71.580초(미완료)/92.410초(완료)이며 서로 다른 완료 분모로 가속률을 주장하지 않는다.
- 6씬×preload/calm/wind 각1프레임, 총18phase·1152단계의 짧은 생성/검산/저장/분기 통과.
  모든 저장 hash·가변 dt 합·끝 시각·처짐 checkpoint 분기를 확인하고 정상 두 방식의 끝점 차이1e-12 미만을 확인했다.
- CPU 중력 회귀6개 통과. Gauss 독립 테스트1개는 GPU opt-in이 없어 skip이며 이번 Newmark 근거로 세지 않는다.
- suite 제어의 실패 후 다음 씬 진행과 전체 벽시계 시간 기록은 CPU mock 검사 통과.
- 기본 스크립트 두 개의 상태 조회, Python 구문·shell 구문, 관련 diff 검증 통과.

[선별 검증 근거](newmark_dt_suite_validation.json). 원본은
`artifacts/runs/teacher_timestep_search/newmark_dt_suite_validation_v1/`의 명령/로그/검산/구현 사본이다.
실제 긴 궤적의 성공률·속도·늘어남/순간속도 정확도는 본 실행 후 확인해야 한다.
R1에 별도 개발 시험 범위를 반영하고 canonical PDF/bundle을 빌드했다. R0/master/sketch/Gate는 변경하지 않았다.
code/experiments/ideas의 관련 worktree만 수정했으며 stage/commit/push 및 외부 fetch/download는 하지 않았다.

## 저장 결과 뷰어 — 2026-09-15

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_newmark_dt_fixed.sh handkerchief wind
bash experiments/R1_teacher_velocity_reset/timestep_search/view_newmark_dt_retry.sh reference_rectangle wind
```

씬은 `reference_rectangle`, `handkerchief`, `triangular_flag`, 단계는 `preload`, `calm`, `wind`다.
인자 생략 시 fixed는 손수건 wind, retry는 직사각형 wind를 연다.
`--out <세 씬을 포함하는 suite 경로>`, `--prepare-only`, `--time 1.0` 등도 지원한다.
동결된 기하 코드/입력/hash를 사용하고 현행 표시 reader만 별도로 연결한다. solver는 실행하지 않는다.
표시 캐시는 `playback_newmark/<phase>/<report hash>/`에 두므로 다른 저장 prefix를 덮어쓰지 않는다.

현재 확인된 고정 dt 바람 결과: 손수건4초 완료, 삼각형은 실패 전 확정2초, 직사각형은 확정0초다.
직사각형은 preload/calm을 선택해야 한다. 실패하거나 report가 running인 실행도 확정 chunk만 재생하며
미저장 상태를 완료 데이터처럼 추가하지 않는다.
로컬 retry 기본 경로는 아직 ready0이다. 따라서 `--out` 미지정 시 저장 결과가 있는
`artifacts/runs/sub_pc/20260915T030822Z-1738c19337474a3ca5634380f6f55049/simulation`을 대체 경로로 확인한다.
이 공유 사본은 직사각형 preload/calm 완료, wind2초 저장/report running이며 나머지 두 씬은 ready0이다.
이는 조회한 파일 상태로, 실제 원격 프로세스가 실행 중이라는 판정이 아니다. 원격 fetch/download는 하지 않았다.
완료 결과가 다른 위치에 있으면 `--out`으로 해당 suite를 지정한다.

검증: 손수건 완료4초/삼각형 확정2초/재시도 직사각형 확정2초 캐시 생성과 hash 확인, 두 스크립트의 OpenGL smoke 각2프레임 렌더링·종료 통과. 기존 뷰어 회귀5개 및 Python/shell 구문 검사 통과. 물리 재계산/원본 report 변경 없음.
