# 두 PC 공통 FP64 launch / 기존 FP32 fixed-work 실행

2026-09-16. `ideas/development/codex_teacher_precision_dual_gpu_request_2026-09-15.md`와
`teacher_precision_analysis_2026-09-15.md`를 읽고 만든 사용자 실행용 스크립트다.
이 작업에서는 사용자 지시에 따라 **GPU 계산을 시작하지 않았다**. CPU 검사와 준비/ZIP 경로만 확인했다.
최적 block이나 가속률은 실측 전이므로 정해 두지 않았다.

## 실행

두 PC가 같은 공유 코드/원본 입력을 사용하는 동안 각각 아래 명령을 실행한다.
기존 출력 폴더는 덮어쓰지 않으므로 재실행에는 새 이름을 사용한다. GPU별로 한 실행만 구동한다.

GTX 1080 Ti:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_dual_gpu.sh \
  --mode tune --worker-id gtx1080ti \
  --out experiments/artifacts/runs/teacher_timestep_search/dual_gpu_gtx1080ti_v1
```

RTX 5070:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_dual_gpu.sh \
  --mode tune --worker-id rtx5070 --with-ncu \
  --out experiments/artifacts/runs/teacher_timestep_search/dual_gpu_rtx5070_v1
```

`--with-ncu`는 선택 사항이다. 설치된 도구만 이용하며 Pascal에는 실행하지 않는다.
조건부 graph 대신 같은 입력의 isolated volume/interior-edge 첫 호출을 baseline/선택 설정에서
제한적으로 측정한다. profiler 시간은 일반 비교에 넣지 않는다. 연속2회 실패 시 해당 경로를 중단한다.

완료 후 결과 폴더 두 개를 취합한다. 각 PC 실행과 통합 모두 결과 폴더 옆에 ZIP을 만든다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_dual_gpu.sh \
  --collect experiments/artifacts/runs/teacher_timestep_search/dual_gpu_gtx1080ti_v1 \
            experiments/artifacts/runs/teacher_timestep_search/dual_gpu_rtx5070_v1 \
  --out experiments/artifacts/runs/teacher_timestep_search/dual_gpu_comparison_v1
```

## 기본 구간과 작업량

- 기존 직사각형1/500의 완료된 preload checkpoint → wind 첫1프레임(1/60초, 기본64단계).
  `--source-run`으로 같은 형식의 씬 root, `--frames`로 저장 외력 범위 안의 길이를 지정한다.
- baseline3회 → 역할별 FP64 block32/64/128/256 fixed-work → 기존 FP32 hi/lo·단일 FP32
  같은4개 block 및 FP64 유망 조합 → 조합 frame3회와 사이사이 baseline3회.
- fixed-work는 각 후보3회, 반복마다20호출, 최초5회 warmup이다. `--calls`는 고정 호출 수를 바꾼다.
  force 핵심 kernel-only와 reset/copy/조립을 포함한 전체 evaluate 시간을 각각 CUDA event로 기록한다.
- 입력·코드·기존 cuDSS/shim을 동결하고 각 full-frame 반복은 별도 프로세스로 시작한다.
  기존 FP64 hi/lo·Newmark/Gauss 재시도·물리/검산 계약은 그대로다.

## 모드와 캐시

기본 모드는 `baseline`이다. `--mode explicit --blocks '{"volume":32,"interior_edge":64,"boundary_edge":128}'`
처럼 후보를 지정할 수 있다. 위 숫자는 사용 예이며 추천값이 아니다.
`--mode cached --profile <이전workers/worker/selected_launch_profile.json>`은 정확히 일치하는 검증 profile만 쓴다.
명시 설정과 cache의 혼용은 거부한다. identity/schema/checksum/검산 상태가 맞지 않으면 baseline으로 복귀한다.

GPU UUID/SM/compute capability, 환경/라이브러리·소스 hash, mesh/구적 입력·논리 shape,
dtype/정밀도/Graph·checkpoint·구간을 exact-match한다. 다른 GPU/mesh 크기로 일반화하지 않는다.
cache hit에도 현재 구간3회 재생 검증을 수행한다. timestep/capture 안에서는 설정을 고르지 않는다.

## 결과와 판정

`report.md`, 원시 CSV, 환경/입력/source hash, 모든 worker 로그, raw hi/lo snapshot,
검산 배열, launch/실제 Graph block/grid, 변경 diff를 보존한다. FP32 source specialization도 결과에 포함한다.
`run_summary.csv` 전체 가속률은 직접 측정한 compute+audit wall 중앙값을 사용하며 min/max/MAD를 함께 낸다.
분리 가능한 base solver/audit는 기존 동기화 경계의 wall 시간이다. Gauss가 개입하면 두 시간을 null로 두고
결합 시간을 raw result에 남긴다. 제어·초기 외력 등 나머지 구간을 중복 합산하지 않는다.

표본은 시작과 끝(여러 프레임이면 각 프레임 끝)의 위치/속도/탄성 조립 힘/탄성·운동 에너지다.
snapshot 힘은 solver와 다른 연산자 버퍼로 재계산하며 solver 캐시를 건드리지 않는다.
hi/lo 차이는 longdouble에서 hi 차이와 lo 차이를 먼저 계산하고, free 성분 RMS/최대 절대 차이를 보고한다.
이 비교 누적 자체가106비트 double-double 정확도를 보장하는 것은 아니다.
힘은 궤적별 snapshot과 같은 입력 fixed-work를 구분한다.
기하 오차는 기존 volume 진단의 면적비J·최대 변형률 성분을 사용한다. 새 기하 수식은 추가하지 않았다.

기존 검산에 통과하고 Graph 설정이 확인되며 전체 시간 이득이 MAD보다 뚜렷한 후보만 cache 후보가 된다.
상태/힘/에너지가 동일하게 관측되면 회귀 통과 근거로 사용한다. 차이가 있으면 새로운 허용치를 만들지 않고
`decision_required`로 남겨 baseline을 유지한다. Bitwise 동일성을 연구의 새 필수 조건으로 선언하지 않는다.
장부 검산값은 본래 허용치 통과로 판정하며 재계산 bitwise 동일성을 요구하지 않는다.
각 step Newton/GMRES/HVP/backtrack 총계는 기존 기록이 없어 null이다. 기존 batch counter와 실제 GMRES/rebuild/retry는 보존한다.

교차 장치 판정은 `budget_not_defined`다. 새 정확도 예산, 전체 FP32 solver, 학습 적격/장기 안정성 승격은 없다.
Profiler 미지원은 일반 측정을 막지 않는다. 실행 실패는 로그에 남기며 같은 stage/precision 연속2회 실패 시 남은 동일 경로를 생략한다.

## 준비 검증

CPU 설정/캐시/역할 필터/Graph metadata 판정/오차 처리 검사7개, 기존 FP32 specialization19모듈×2경로
문법 확인, CLI·shell/Python 문법 및 `--prepare-only` 입력 동결/ZIP 생성 확인 완료.
실제 CUDA launch/Graph·cuDSS·성능/수치 회귀는 사용자 실행 전이므로 미검증이다.
준비 근거: `artifacts/runs/teacher_timestep_search/dual_gpu_preparation_20260916_v1.zip`.

## v2 후속

후속 실행은 [v2 실행 안내](dual_gpu_v2.md)를 따른다. v1 결과와 별도 폴더/ZIP을 사용한다.
