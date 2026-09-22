# wind120 완료 상태에서 200까지 복원

2026-09-18 사용자 승인으로 직사각형의 중단된 바람 실행을 **별도 출력**에 재생할 스크립트를 준비했다.
원본 실행을 덮어쓰거나 자동 재개하지 않는다. 실제 장시간 계산은 사용자가 시작한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_wind_from120.sh
```

- 시작: 저장된 **120번째 프레임 완료 상태**, 바람 phase time2.0초. 첫 계산/출력은121번째다.
- 종료: **200번째 프레임 완료**. 요청한182–200 구간의 비교 입력 확보가 목적이며240까지 확대하지 않는다.
- 기존 동결된 `Newmark → Gauss6차8분할`, GTX1080Ti M1·256/256/256, FP64 hi/lo 상태와 기존 독립 검산 유지.
- dt1/3840초·64substeps·굽힘1/500·물성/고정점/중력·바람은 원본 그대로다.
- forcing을 자르지 않고 전체 원본 배열의 index120부터 읽는다. GPU 정책의 frame index도120부터다.
- 원본GPU/driver API와 다르면 중단한다. RTX5070 환경 복구/이식 실행용 스크립트가 아니다.
- 물리 상태만 저장돼 있으므로 솔버/전처리기/Graph는 새로 초기화한다. 재생성 상태가 유실된 원본과 bitwise 동일하다고 주장하지 않는다.

기본 출력:
`experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_wind120_to200_reference_v1/`.
원본: `gpu_gtx1080ti_auto_bend500_v1/reference_rectangle/`.

## 저장과 중단

각 `frames/000121/` 같은 폴더의 `state.npz`는 **시작/끝 raw hi/lo·held·모든 채택 단계 검산·dt·method·Gauss 검산**을 보존한다.
`record.json`에는 실패 시도를 포함한 반복/계산+검산 시간, 저장 hash와 상태 연결 hash를 남긴다.
임시 폴더에서 파일을 완성한 뒤 프레임 폴더를 rename한다. 부분 저장 폴더는 재개 대상으로 쓰지 않는다.
완전한 프레임 저장 후 report 갱신 직전에 중단돼도 hash/프레임/시작-끝 상태 연결을 검증해 마지막 승인 프레임을 찾는다.

Ctrl+C/SIGTERM은 worker에 전달하되 현재 프레임 검산·저장까지 기다린다. 고비용 프레임에서는 수분이 걸릴 수 있다.
SIGKILL/전원 종료 시 미확정 프레임은 재개하지 않는다. 확정된 매 프레임 파일은 보존한다.

```bash
# 조회: 계산하지 않음
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_wind_from120.sh --status-only
# 사용자가 명시적으로 중단 이후 이어갈 때
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_wind_from120.sh --resume
```

`--out <새 경로>`는 독립 재생을 준비한다. 중단된 경로는 `--resume` 없이 이어가지 않는다.
`--prepare-only`는 입력/코드 복사와 hash 확인만 수행한다.
`--limit-frames N`은 별도 검증용으로 N프레임을 저장하고 중단한다. 본 비교 구간을 바꾸는 기본 옵션이 아니다.

`attempts/`에는 실제 명령·프로세스 로그·외부 process wall을 남긴다. 계산+검산 시간에 전송/저장을 중복 합산하지 않는다.
프레임 총 wall은 report, 스냅샷 전송/저장 시간은 각 record에 분리한다. 종료·저장을 외부 process wall 밖으로 숨기지 않는다.
부모 launcher에서 Warp/CUDA를 초기화하지 않으며 GPU 조회/초기화는 worker가 한다.

## 완료 후 비교

복원이 끝나도 비교 계산을 자동으로 실행하지 않는다. 요청한182–200번째, 즉0기반181–199의 시작 상태19개를 추출한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_wind_from120.sh --prepare-comparison
```

`comparison/`의 두 후보 모두 **같은 저장 시작 상태와 원본 forcing index**에서 새 solver/전처리기로 시작한다.
이전 프레임에서 누적된 궤적 차이와 해당 프레임 재시도 정책 차이를 분리한다.
A는 Newmark→Gauss8, B는 Newmark→R64 half2→Gauss8이다.
완료된 연속 재생 시간과 새 초기화 비교 시간을 직접 섞지 않는다.

그 다음 비교 실행 명령(이번 준비 작업에서는 실행하지 않음):

```bash
OUT=experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_wind120_to200_reference_v1
PYTHONPATH=code .venv/bin/python -u "$OUT/comparison/compare_cascade_retry.py" \
  --out "$OUT/comparison" --prepared --repeats 1
PYTHONPATH=code .venv/bin/python "$OUT/comparison/analyze_cascade_retry.py" \
  "$OUT/comparison" --mass-metrics
```

원시 `frames.csv`, `attempts.csv`, `pairs.csv`와각 result.json/NPZ를 이용해 시간·수렴·위치/속도·에너지 장부를 대조한다.
1회씩의 초기 비교이며 반복 측정 확장은 별도 결정이다. 비교 자체도19×2프레임의 계산 비용이 든다.
후보의 고부하 통과/가속/정확도는 아직 미측정이고 생산/학습 적격성은 승격하지 않는다.

## 준비 검증

CPU fixture6개에서 원자적 저장 후 오래된 report 복구, 부분 저장 제외, 덮어쓰기/프레임 누락/상태 연결 오류/hash 손상/미승인 저장 거부,
19개 비교 입력의 시작 상태와 forcing index 정렬을 확인했다. 이 fixture는 물리 검증이 아니다.
부모 진입 모듈의 Warp 미import, Python/shell 구문을 확인했다.
원본 상태 및 동결 runtime의 hash 검증과 준비 후 ready120 조회를 수행했다.
실제 GPU frame120 이후 재계산·성능 검증은 사용자 실행 대기다. 기존 GPU 적분기 검증을 새 재생 완주로 보고하지 않는다.

## 2026-09-19 복원 완료 후 한 번에 비교 실행

복원은200프레임까지 완료됐다. 다음 명령은120부터 재생하지 않고 저장된182–200프레임의 시작 상태를 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_wind_182_200_compare.sh
```

19프레임 각각에서 기존 Newmark→Gauss8과 Newmark→half2→Gauss8을 한 번씩, 총38회 순차 실행한다.
두 방법 모두 같은 시작 상태·forcing과 새 초기화 조건을 사용한다.
완료 후 자동으로 comparison/frames.csv, attempts.csv, pairs.csv, summary.json, comparison_report.md를 만든다.
숫자 비교에서 수치 실패/미완료 쌍은 제외하고 상태를 명시한다. 회귀 예산과 학습 적격성은 자동 승격하지 않는다.

--prepare-only는 입력/hash만 확인하고, --status-only는 비교 상태만 조회한다.
기존 비교 결과가 있으면 덮어쓰거나 자동 재개하지 않는다. Ctrl+C는 소유 비교 프로세스 그룹에 전달하고 완료된 결과는 보존한다.
중단된 한 프레임은 미완료로 남을 수 있다. 다시 실행하기 전 완료 결과를 먼저 확인해야 한다.

이번 준비에서19개 raw 시작 상태·원본 forcing index181..199·held 일치와 동결 hash, 부모 Warp 미import,
Python/shell 구문을 확인했다. 실제38회 GPU 비교는 사용자 실행 대기다.
