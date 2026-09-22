# GPU 상주 적분·보조 행렬 갱신 비교

## 현재 상태 — 2026-09-13

[오늘 최적화 종합 결과](optimization_summary.md): 실제 완료된 단계별 비용·GPU 검산·현행 천 비교와의 차이. 아래 초기 준비/대기 표현은 각 작업 당시 기록이다.

**채택 평가 재사용·무압축 후보 실행 완료. GPU 상주 검산도 전체640구간의 기존 검산 대조를 통과했다. 현재 명령은 [GPU 상주 검산](#gpu-상주-검산--현행-실행)을 따른다.**
기존 실행·동결 runtime·설정·원본 결과는 변경하지 않았다. 학습 적격성·기존 Gate도 유지한다.
작은 통합 실행과 실제 메시2단계의 검증 범위는 아래에 구분한다. 장기 본 시뮬레이션의 정식 대체 판정은 아직 아니다.

## 실행

기존 시뮬레이션을 직접 중지한 뒤 workspace root에서 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_comparison.sh
```

VSCode/터미널 종료와 분리하려면 다음처럼 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_comparison.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_comparison.sh --logs
```

`--status-only`는 상태·비용 요약을 표시한다. `--prepare-only`는 입력·코드·의존성만 준비한다.
준비만 실행하여 기본 출력 `artifacts/runs/teacher_timestep_search/20260913_gpu_resident_10frames_v1`을 만들었다.
그 안에 동결 코드·초기 상태·바람·manifest·native workspace 라이브러리가 있다. **두 비교 worker는 미시작이다.**

스크립트는 같은 초기 상태에서 **하이브리드10프레임 → GPU10프레임 → 독립 검산**을 순차 실행한다.
로그는 `comparison.log`, 최종 결과는 `comparison.json`, 상태는 `status.json`이다.
GPU의 프레임 로그는 비동기 계산의 **제출**을 뜻하며, 완료는 저장 경계에서 확인한다.
다른 teacher 프로세스가 남아 있으면 시작을 거부한다. 기존 프로세스를 자동 중지하지 않는다.

기존 결과는 덮어쓰지 않는다. 끝난 backend는 재사용하고, 중단·실패한 backend는 새 `--out 새_경로`로 다시 실행한다.
이번 비교 스크립트는 실패한10프레임 구간 중간에서 자동 재개하지 않는다.
설정 변경도 새 출력 경로가 필요하다. 같은 경로에 다른 설정을 조용히 적용하지 않는다.

## 저장 설정

[`comparison.json`](comparison.json)의 `recording.save_interval_s` 기본값은 **시뮬레이션 시간2초**다.
`save_interval_by_mesh_s`에 예를 들어 `{"reference_rectangle": 1.0, "handkerchief": 0.5}`를 넣으면 해당 메시만 변경된다.
60Hz 프레임의 정수배 간격을 사용하며 **프레임당64단계의 위치·속도 기록은 모두 유지**한다.
간격은 재개 시작 시점부터 센다. 마지막 짧은 구간은 종료할 때 저장한다.
이 설정은 새 개발 경로용이며 기존 실행기의 저장 빈도는 바꾸지 않는다.

기록은 위치·속도 각각 float64 hi/lo인 `resident_pair_f64_v1`이다.
기존 `hi_lo_v1` loader/뷰어와 자동 호환되는 포맷은 아니다. 통합 재개·뷰어 연결은 후속 작업이다.
실패 시 `failure_state.npz`는 진단용이며 검증된 학습 궤적으로 취급하지 않는다.

## 비교 조건과 비용 해석

- 원본: `artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4`.
- 메시: `reference_rectangle`, 계산점7081개. 원본 해상도·물성·dt·바람을 유지한다.
- 시작: 원본166번 프레임 마지막 상태. **0-based167–176번 연속10프레임/640단계**,2.7833333333–2.95초.
- 선택 근거: 원본 직사각형에서 가장 느린167번 프레임을 포함한다.
- 과거 같은 구간: 계산730.820792초, 검산36.263159초, 저장18.052503초, 전체785.817015초.
  과거값은 참고이며 새 속도 비율의 분모로 사용하지 않는다.
- 새 실행의 `fixture/manifest.json`이 원본/input/trace 해시와 정책을 소유한다.
  원본 전체 manifest·166–176번 완료 파일을 검증하고, 기존 teacher 구현도 원본과 해시가 같은지 확인한다.
- 실제10프레임은1/6초라 종료 때 한 번 저장한다. 상태 버퍼만435,736,416 bytes(415.55MiB).
  같은 고해상도 메시의2초 상태 버퍼는4.863GiB이며 solver 작업 메모리는 별도다.

`setup_s`는 모델·행렬·GPU 버퍼·그래프 준비다. `generation_s`는 그 뒤 적분부터 상태·진단 저장까지다.
`compute_and_buffer_s`는 generation 중 상태 전송·압축 저장을 제외한 적분·공력·버퍼 유지 비용이다.
CPU 제어·GPU 동기화 대기 및 최초 적분 그래프 실행 준비는 이 비용에 포함될 수 있다.
두 방식의 `generation_s`와 `compute_and_buffer_s`를 각각 비교한다. 순수 커널 시간이라고 부르지 않는다.
독립 검산 `audit_s`는 별도다. 공유 GPU에서 한 작은 검증의 시간은 성능 결론으로 사용하지 않는다.

## GPU로 옮긴 범위

초기 CPU 작업은 메시·희소 구조·coloring·입력 준비다. 계산 중에는 다음을 GPU에 유지한다.

- Newmark 위치·속도 갱신, 고정밀 위치 기하와 힘/HVP,60Hz 공력.
- Newton 수렴·line search·EW 내부 선형 허용오차와 GMRES MGS/Givens/내부 조기 종료.
- 반복32회 이상이면 rest에서 current로 전환, rest 선형 실패 시 같은 입력으로 current 재시도.
- current 호출64회마다 GPU HVP로 행렬 값을 복원·검산하고 **cuDSS에서 수치 분해를 갱신**.
- GPU 상태 버퍼와 에너지 장부. CPU 결과 조회는 저장·별도 검증 경계에서만 한다.

초기 고정 LU 시험은 채택하지 않았다. 기존 힘·변위 허용오차,15회 Newton 한도,12회 line search,
GMRES restart240×3,EW cap1e-4와 내부 힘 목표0.3배를 유지한다.
cuDSS와 SuperLU의 ordering/pivot 및 부동소수점 연산 순서는 다르므로 bitwise 일치를 주장하지 않는다.
초기 rest 분해는 새 경로에서 한 번 준비하여 재사용한다. 현재 행렬 갱신은 GPU에서 계속 수행한다.

저장된 두 궤적 모두 기존 `audit_step`으로 힘 잔차·위치 갱신·에너지 장부·기하·고정점을 독립 재검산한다.
이 별도 검산은 CPU/GPU를 사용하며 적분 중 CPU fallback과 구분한다.
또한 궤적 일치 기준은 rtol1e-6, 위치 atol1e-10m, 속도 atol1e-8m/s다. 물리 허용오차를 완화하는 설정은 아니다.
두 검산과 궤적 비교를 통과해야 속도 비율을 발행한다. 실패하면 `validation_failed`, 속도 비율은 null이다.

## 검증과 남은 한계

- GPU 회귀4개: 변경된 행렬의 조건부 재분해, SciPy와 같은 GMRES 조기 종료/zero RHS,
  반복 current 갱신, 선형 실패→current 재시도→상태 보존 확인.
- CPU 기록4개: 기본2초·메시 override·잘못된 간격 거부·종료 잔여 저장 확인.
- 작은 메시1프레임/64단계: controller→동결 worker2개→저장→독립 검산 통과.
- 실제7081점 메시2단계: current 갱신을 포함한 원식 검산과 과거 같은 상태 비교.
  상세 수치는 [`validation.json`](validation.json), 원시 근거는 그 파일의 artifact 링크를 따른다.
- **실제10프레임 속도·장기 안정성·메시별 성능은 미확인**. 학습 발행·R1 완료 판정은 false다.

GPU 회귀는 전용 CUDA 환경에서 `code/tests/test_resident_cudss_gpu.py`, `test_resident_stepper_gpu.py`를 실행한다.
현재 검증 장치는 GTX1080Ti, Warp1.17.0·cuDSS0.7.1이다. 서브 컴의 실제 검증 결과는 아직 없다.

## 의존성과 구현 제한

스크립트는 기존 venv를 변경하지 않고 ignored vendor 경로에 `nvidia-cudss-cu12==0.7.1.6`을 설치한다.
Linux·C compiler·CUDA12의 `libcublas.so.12`가 필요하다. Python은 `WIND3DGS_PYTHON`으로 변경할 수 있다.
공식 package 설치를 원할 때의 optional dependency는 `teacher-gpu-resident`다.

cuDSS의 hybrid memory/execute 모드를 끄면 수치 분해·풀이는 GPU에서 수행된다.
구조 분석은 초기화에 둔다. [NVIDIA cuDSS 설명](https://docs.nvidia.com/cuda/cudss/general.html).
cuBLAS의 capture 중 임시 할당을 피하려고 새 비교 프로세스에만 native workspace shim을 적용한다.
handle당32MiB를 초기화 때 제공하고 stream 변경 뒤에도 유지한다.
[NVIDIA cuBLAS의 그래프·workspace 설명](https://docs.nvidia.com/cuda/cublas/index.html#cuda-graphs-support).

cuDSS 작업 버퍼도 초기 pool에서 재사용하며, 고정 구조 범위의 작은 host upload는 초기 GPU 상수로 옮긴다.
조건부 그래프에서 예상하지 않은 host 전송·할당 node는 허용하지 않는다.
Warp 내부 graph/TiledDot API와 cuDSS0.7.1 API에 의존하는 개발 구현이므로 버전을 임의 변경하지 않는다.

실제2단계 검산은 `code/scripts/check_teacher_gpu_resident_actual.py --out 새_검증_경로`로 재현할 수 있다.
동결 경로를 `PYTHONPATH`로 지정하고, 위 wrapper와 같은 `CUDSS_LIBRARY_PATH` 및
`LD_PRELOAD` workspace 라이브러리를 해당 프로세스에 전달한다. 기존 검증 경로는 덮어쓰지 않는다.

## 같은 구간의 GPU 실행 추적 — 2026-09-13

본10프레임 비교는 완료·검산 통과했다. 원본 결과는
`artifacts/runs/teacher_timestep_search/20260913_gpu_resident_10frames_v1/comparison.json`이다.
생성332.401→162.366초, 계산·버퍼314.738→151.767초이며 두 방식 모두 선형 반복14156회·current 갱신10회다.
위 준비 대기 문구는 초기 준비 시점 기록이다. 후속 최적화 전에 다음 추적을 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_profile.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_profile.sh --logs
```

- 기본 출력: `artifacts/runs/teacher_timestep_search/20260913_gpu_profile_v1`.
- 완료 기준: `profile_status.json`의 `추적·검산·통계 완료`, `comparison.json`의 `passed`.
- `gpu_trace.nsys-rep`: CUDA graph node별 실행 추적. `nsys_stats.txt`: 커널·전송·CUDA API 시간 통계.
- 기준 실행의 동결 runtime·fixture·하이브리드 결과를 독립 복사하고 해시 확인한다. GPU worker만 재계산한다.
- 초기 준비도 추적에 포함된다. 분석 시 초기화와640단계 계산을 구분해야 한다.
  공통 커널의 기능별 귀속은 이름별 합계만으로 확정하지 않는다. 조건부 graph 내부 수집 범위도 실제 trace에서 확인한다.
- 검산은 추적 밖에서 수행한다. 감사기 원문 로그의 속도 비율은 사용하지 않으며 최종 JSON의 비율은 null로 처리한다.
- 추적 오버헤드가 있으므로162.366초와 직접 성능 비교하지 않는다. 개선 후에는 추적 없는 같은 구간 비교가 필요하다.
- 로그는 `artifacts/runs/teacher_timestep_search/gpu_profile_launcher.log`에 누적된다.
- 기존 출력 경로는 재사용·덮어쓰기하지 않는다. 재시도는 `--out 새_경로`를 지정한다.
- `--baseline 기준_경로`, `--prepare-only` 지원. 준비 전용도 출력 경로를 소비하므로 실제 실행은 새 경로를 사용한다.
- 로컬 `nsys`와 기존 cuDSS vendor가 필요하다. 자동 설치·기존 프로세스 중지는 하지 않는다.
- 준비 복사·해시·C shim 컴파일과 shell 구문 검증 완료. 실제 GPU 추적은 사용자 실행 대기다.
  추적 파일 용량·오버헤드는 아직 측정하지 않았다. 솔버 개선은 추적 분석 후 수행한다.

## GPU 내부 timestamp 계측 — 현행 실행 방법

Nsight2024.5.1 node 추적은 WSL2+GTX1080Ti에서 종료139·UUID 오류로 실패했고,
`20260913_gpu_profile_v1`에는 완료 상태·진단 궤적이 없다. 제출9프레임을 완료로 해석하지 않는다.
WSL의 Nsight/CUPTI 추적은 [CUDA13.0 지원표](https://docs.nvidia.com/cuda/archive/13.0.2/wsl-user-guide/index.html)상 Volta 이상이다.
기존 실패 산출물은 보존한다. 같은 조합에서 기존 Nsight wrapper를 실행하면 시작 전에 거부한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_timing.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_resident_timing.sh --logs
```

- 기본 출력: `artifacts/runs/teacher_timestep_search/20260913_gpu_timing_v1`.
  재실행은 `--out 새_경로`. 전경 실행은 `--background`를 생략한다.
- 로그: `artifacts/runs/teacher_timestep_search/gpu_timing_launcher.log`.
- 원본 정상 비교의 runtime·fixture·hybrid를 독립 복사하고, **계측 모듈2개만 추가**한다.
  원본 솔버 파일과 물성·정책은 그대로다. manifest에 추가 모듈 해시를 기록한다.
- `gpu_timing.json`: 힘/HVP, GMRES 내적·직교화, 보조 행렬 구성·분해·적용,
  수렴 판단·에너지 합산 등50개 중첩 경로의 시간과 호출 수.
- 각 구간 앞뒤에 작은 GPU kernel을 넣어 `%globaltimer`를 읽고 GPU 배열에 누적한다.
  적분 중 CPU 동기화나 결과 복사를 추가하지 않는다. 초기화 때 누적값을 초기화하고 종료 시 읽는다.
- `inclusive_s`는 자식 구간 포함이므로 서로 합산하지 않는다.
  `exclusive_s`는 직접 자식 시간만 뺀 값이다. 둘 다 marker·scheduling 비용을 포함한다.
  짧은 구간은 timer 해상도·계측 오버헤드의 영향을 크게 받는다. 순수 커널 실행 시간이나 최적화 예상 이득으로 단정하지 않는다.
- CPU 제출 대기, 기록 복사, 초기화·압축·별도 검산은 구간 합계에 모두 들어가지 않는다.
  기존 worker의 계산·버퍼 시간과 함께 해석하고 잔여 시간을 특정 병목으로 단정하지 않는다.
- 계측 결과 자체의 성능 비율은 null. 다음 개선은 동일 구간의 계측 없는 실행으로 비교한다.
- 완료: `profile_status.json`의 `추적·검산·통계 완료`, `comparison.json`의 `passed`, timer의640단계 확인.
- 검증: GPU 중첩 marker 확인, 최종 동결 runtime으로 실제7081점2단계·current 갱신1회·선형 반복57회,
  기존 독립 검산 통과. timer 단계 수·norms·조건부 factor 호출 및 음수가 아닌 exclusive 확인.
  [검산](timing_validation/validation.json), [시간 기록](timing_validation/timing.json), [추가 소스 해시](timing_validation/sources.json).
  짧은 검증의 시간은 성능 결론으로 사용하지 않는다. 전체640단계 계측은 아직 실행하지 않았다.

재현 검증기는 `code/scripts/check_teacher_gpu_timing_actual.py --run 준비한_계측_경로 --out 새_검증_경로`다.
준비는 timing wrapper의 `--prepare-only --out 새_준비_경로`로 수행한다.
`PYTHONPATH`는 준비 runtime/code, `CUDSS_LIBRARY_PATH`는 기존 vendor,
`LD_PRELOAD`는 준비 runtime/native/libcudss_workspace.so로 지정한다.
학습 발행·R1 Gate는 유지한다.

## 병렬 합산 비교 — 현행 다음 실행

내부 계측640단계·검산 통과. GPU 내부 중첩 제외 시간의35.0%가 순차 합산,
34.2%가 보조 행렬 적용이었다. GPU timer 합계146.407초와 CPU 계산·버퍼140.039초의
불일치가 있어 내부 시간을 그대로 절약량으로 해석하지 않는다.
먼저 합산만 병렬화하고 보조 행렬 적용은 후속 변경으로 분리한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_parallel_comparison.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_parallel_comparison.sh --logs
```

- 기본 출력: `artifacts/runs/teacher_timestep_search/20260913_gpu_parallel_v1`.
- **계측 없는 기존 GPU10프레임 → 검산 → 계측 없는 병렬 합산 GPU10프레임 → 검산**을 순차 실행한다.
  하이브리드는 새로 계산하지 않고 동일한 원본 결과를 각 경로에 복사해 검산 기준으로 쓴다.
- `summary.json`의 `passed`, `generation_speedup`, `compute_and_buffer_speedup`을 확인한다.
  분모는 이번에 새로 실행한 기존 GPU 결과다. 하위 comparison의 비율은 사용하지 않는다.
- `--out 새_경로`, `--prepare-only` 지원. 이미 있는 경로를 덮어쓰거나 중간 재개하지 않는다.
- 원본 동결 runtime에 `resident_parallel_reductions.py`, `teacher_gpu_parallel_worker.py`만 추가한다.
  실행 프로세스에서 대상 kernel 호출만 바꾸고 원본 solver 파일·진행 중 실행은 보존한다.
- 대상: `norms`, `after_linear`의 크기 계산, `energy_balance`의 일 합산,
  `reduce_volume`, `reduce_edge`의 합·최소·최대. 공력·힘 식·보조 행렬·GMRES 정책·물성·dt는 유지한다.
- 두 값을 합치는 고정 순서 tree를 여러 GPU thread에서 처리한다. atomic 합산은 쓰지 않는다.
  홀수 길이를 처리하고 초기화 때만 두 작업 버퍼를 할당한다. 계산 중 host 조회·동기화를 추가하지 않는다.
- 덧셈 순서가 달라져 bitwise 일치는 요구하지 않는다. 기존 물리 검산·공통 기준 궤적 비교를 통과해야 한다.
- 실제7081점2단계·행렬 갱신1회·반복57회 검산 통과.
  [검산](parallel_validation/validation.json), [추가 소스 해시](parallel_validation/sources.json).
- 기존/병렬 두 동결 경로의 준비·해시·shim 컴파일 확인 완료. 전체10프레임 속도는 사용자 실행 대기.
- 동일 장치에서 순차 실행하지만 OS/클럭/공유 부하까지 통제한 반복 벤치마크는 아니다.
  최종 장기 안정성·학습 적격성·Gate는 여전히 미완료다.

- 추가 GPU 회귀4개 통과:홀수 길이 합·최소·최대, 고정점 인덱스·반복 실행, current 반복 갱신, 선형 실패 복구.

## 보조 행렬 적용 개선·기준 재사용 — 현행 실행

병렬 합산 비교는 완료·검산 통과했다. 이전 기존 GPU 생성165.933초 대비 병렬 합산110.461초,
계산·버퍼155.238→99.941초다. 원본은 `20260913_gpu_parallel_v1/summary.json`을 따른다.
이제 사용자의 요청에 따라 **이전 하이브리드·GPU·병렬 합산의 실행과 검산을 재사용하고 새 후보만 계산·검산**한다.
위 이전 절의 두 GPU 순차 재실행 설명은 과거 방식이며 현행 wrapper에는 적용되지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_preconditioner_comparison.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_preconditioner_comparison.sh --logs
```

- 기본 출력: `artifacts/runs/teacher_timestep_search/20260913_gpu_preconditioner_v1`.
- `candidate/`만 새로 계산한다. `summary.json`의 `passed`, `speedups_vs_cached`와 `status.json`을 확인한다.
  `cached_references.json`에 기준 경로·manifest/result 해시·시간을 기록한다.
- 재사용 기준: `20260913_gpu_resident_10frames_v1`의 hybrid,
  `20260913_gpu_parallel_v1/reference`의 기존 GPU,
  `20260913_gpu_parallel_v1/parallel`의 병렬 합산 GPU.
  이 경로들은 모두 `artifacts/runs/teacher_timestep_search/` 아래다.
- 기준의 통과 판정·소스/결과 해시·fixture 초기 상태·바람·물리 정책 일치를 확인한 뒤 사용한다.
  기준 궤적을 읽어 새 결과와 비교하지만 기준 시뮬레이션이나 기준 물리 검산은 재실행하지 않는다.
- 과거와 현재의 GPU 부하·클럭은 다를 수 있다. 이전 결과 대비 비율이며 동시 조건의 통제 비교라고 주장하지 않는다.
- `run_gpu_parallel_comparison.sh`도 새 병렬 후보만 실행하도록 변경했다.
  기본 출력은 충돌을 피한 `20260913_gpu_parallel_cached_v1`이다.
- `--out 새_경로`, `--prepare-only`, `--baseline`, `--gpu-baseline`, `--parallel-baseline` 지원.
  완료·실패 결과는 보존하고 재실행은 새 출력 경로를 쓴다.

개선은 GMRES 첫 cycle에서 같은 `M^-1 b`를 두 번 계산하던 것을 한 번 계산해 재사용하는 것이다.
새 선형 풀이마다 다시 계산하고, restart는 잔차가 달라지므로 반드시 다시 적용한다.
병렬 합산 개선은 포함하며 cuDSS 분해·행렬 갱신·정렬 설정·물리 정책·GMRES 정확성 기준은 유지한다.
이전과 같은1280회 선형 풀이가 발생하면 적용1280회가 줄어든다. 전체 속도 개선율은 본 실행 전에는 미확정이다.

- 검증:restart가 여러 번 발생하는 문제에서 적용 횟수1회 감소·반복 수 및 결과 일치, RHS 변경·zero RHS 통과.
- 기존 current 반복 갱신·선형 실패 복구 회귀2개 통과.
- 실제7081점2단계·current 갱신1회·반복57회와 기존 힘·에너지·기하 검산 통과.
  [검산](preconditioner_validation/validation.json), [소스 해시](preconditioner_validation/sources.json).
- 새 후보 전용 검산기는 저장된640단계로 확인하여 이전 검산 최대값·궤적 비교 수치와 일치했다.
  [검산기 검증](preconditioner_validation/cached_audit_check.json). 이 확인에서는 재시뮬레이션하지 않았다.
- 준비·기준 해시·동결 추가 모듈·shim 컴파일·shell 구문 확인 완료. 새 후보10프레임은 사용자 실행 대기.

짧은 실제 행렬 적용 시험에서 superpanel 비활성화는 기본값보다 느렸고,
reordering ALG1은 기존 초기 메모리 pool의 배열 크기 한계를 넘어 초기 분해에 실패했다.
따라서 두 설정은 채택하지 않는다. 설정 의미는 [cuDSS0.7 계열 공식 API](https://docs.nvidia.com/cuda/cudss/doc_output/types.html)를 확인했다.
관련하여 라이브러리 교체나 메모리 확대를 자동 수행하지 않았다.

실제2단계 검증기는 `code/scripts/check_teacher_gpu_preconditioner_actual.py --out 새_경로`다.
앞 절과 같은 vendor/shim/PYTHONPATH 환경을 사용한다. 학습 발행·장기 안정성·R1 Gate는 유지한다.

## current 우선 후보 — 현행 다음 실행

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_current_first_comparison.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_current_first_comparison.sh --logs
```

- 기본 출력: `artifacts/runs/teacher_timestep_search/20260913_gpu_current_first_v1`.
- 매 프레임 첫 선형 풀이부터 현재 형상 행렬을 구성한다. 이후 **current 보조 풀이64회마다 갱신**한다.
  64는 프레임/시간 단계 수가 아닌 선형 풀이 호출 수다. 프레임 경계의 갱신 카운터는 계속 초기화한다.
- 병렬 합산·중복 적용 제거는 포함한다. 물리 식·dt·물성·정확성 기준은 유지한다.
  rest 전환 임계값을 낮추는 방식 대신 매 프레임 current 선택으로 실험한다. 프레임 간 행렬 유지 개선은 아직 포함하지 않는다.
- 이전 기준4개(hybrid, 기존 GPU, 병렬 합산, 중복 제거)를 검증 후 재사용한다.
  새 후보640단계만 계산·독립 검산한다. 기준 시뮬레이션·기준 검산은 재실행하지 않는다.
- 중복 제거 기준 추가 경로: `20260913_gpu_preconditioner_v1/candidate`.
  `--preconditioner-baseline`으로 변경 가능하다. 나머지 경로 옵션은 앞 절과 같다.
- `summary.json`의 `speedups_vs_cached.preconditioner`가 직전100.625초 대비 비율이다.
  같은 시점·동일 부하의 통제 비교는 아니며, 반복 수와 행렬 갱신 수도 함께 확인한다.
- 실제7081점 첫2단계에서 선형 반복57→7회, current 갱신1회, 기존 독립 검산 통과.
  [짧은 검산](current_first_validation/validation.json), [추가 소스 해시](current_first_validation/sources.json).
  이 감소율을 전체10프레임 속도 개선율로 외삽하지 않는다.
- 기준4개·동결 추가 모듈·shim 컴파일·shell 구문 준비 검증 완료. 전체10프레임은 사용자 실행 대기.
- 재현: `code/scripts/check_teacher_gpu_current_first_actual.py --out 새_경로`, 앞 절의 GPU 환경 사용.
  GPU graph가 참조하는 병렬 합산 workspace의 수명을 유지하도록 context는 생성부터 실행·close까지 감싼다.
- 기존 결과·원본 solver는 보존한다. 학습 발행·장기 안정성·R1 Gate는 유지한다.

- 작은 메시2프레임/128단계 GPU 회귀 통과:프레임별 current 시작·64회 갱신·계산 중 CPU 조회 없음 확인.

## 채택 평가 재사용·무압축 후보 — 현행 다음 실행

이 절의 실행 대기 문구는 준비 당시 기록이다. 후보 실행은 완료됐으며
현재 다음 작업은 [GPU 상주 검산](#gpu-상주-검산--현행-실행)을 따른다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_reuse_uncompressed_comparison.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_reuse_uncompressed_comparison.sh --logs
```

- 기본 출력: `artifacts/runs/teacher_timestep_search/20260913_gpu_reuse_uncompressed_v1`.
- 새 후보10프레임만 계산·검산한다. 이전5개 기준(hybrid/GPU/병렬 합산/중복 보조 풀이 제거/current 우선)은 재사용한다.
- `summary.json`의 `speedups_vs_cached.current_first`가 직전67.887초 대비 비율이다.
  계산·버퍼와 저장 시간을 나눠 본다. 이전 시점의 결과와 비교하므로 동일 부하를 보장하지 않는다.
- `--current-first-baseline`의 기본값은 `20260913_gpu_current_first_v1/candidate`이며,
  다른 경로 옵션·완료 및 실패 결과 보존·새 출력 경로 사용 규칙은 앞 절과 같다.
- 채택한 line search의 힘·잔차·진단값과 통계0/1/3을 다음 Newton 판정에 재사용한다.
  보정량·EW 이력은 보존한다. 각 Newton 시작에 유효 표시를 지우고 채택 성공 때만 켠다.
  미채택/오류 경로는 기존 평가·실패 처리로 돌아간다. 새로운 상태에서는 새로 계산한다.
- 별도 worker 안에서 NPZ 저장을 무압축으로 바꾼다. 상태·진단·진단용 실패 기록에 적용한다.
  배열 이름·float64 hi/lo·시간축·기록 단계 수·기본2초 저장/메시별 override·파일 확정 절차는 유지한다.
  기존 `resident_pair_f64_v1` loader는 그대로 사용한다. Legacy viewer와의 별도 포맷 통합은 여전히 후속이다.
- 이전 상태 파일은 압축 전415.56MiB, 압축 후395.29MiB였다. 무압축 파일은 약5% 커지며 GPU 기록 버퍼 크기는 같다.
  물리 설정·정확성 기준·current64회 갱신·병렬 합산·보조 풀이 중복 제거를 유지한다. 독립 검산은 변경하지 않는다.
- 검증:최종 동결 코드로 실제7081점2단계·current1회·반복7회 물리 검산 통과.
  [검산](reuse_uncompressed_validation/validation.json), [추가 소스 해시](reuse_uncompressed_validation/sources.json).
- line search를 한 번 거부시키는 GPU 회귀에서 재사용 전후 상태·반복 수 일치 및 평가 호출 감소 확인.
- 기록 회귀3개 통과:기존/무압축 저장 경계·값·시간축, ZIP_STORED와 NumPy 읽기 확인.
  실제2단계 검증 NPZ도 무압축임을 확인했다.
- 기준5개·동결 모듈·shim 컴파일·shell/Python 구문 확인 완료. 전체10프레임 성능은 사용자 실행 대기.
- 재현: `code/scripts/check_teacher_gpu_reuse_uncompressed_actual.py --run 준비한_후보_경로 --out 새_검증_경로`.
  GPU 환경·context 수명 규칙은 앞 절을 따른다. 기존 결과 보존·학습 발행 보류·Gate 유지.

## GPU 상주 검산 — 현행 실행

채택 평가 재사용·무압축 후보의640구간 생성·검산은 완료됐다. 위 실행 대기는 준비 당시 기록이다.
이제 기존 완료 결과를 입력으로 GPU 검산만 실행할 수 있다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_audit.sh
# 백그라운드 실행과 로그 확인
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_audit.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_audit.sh --logs
```

앞의 일반 실행과 백그라운드 실행은 대안이다. 같은 기본 출력으로 두 번 실행하지 않는다.
재실행은 `--out experiments/artifacts/runs/teacher_timestep_search/새_이름`을 지정한다.

- 기본 입력:`20260913_gpu_reuse_uncompressed_v1/candidate`, 기본 출력:`20260913_gpu_audit_v1`.
  두 경로 모두 `experiments/artifacts/runs/teacher_timestep_search/` 아래다.
- `--source`로 완료 후보를, `--out`으로 새 출력 경로를 지정한다. 기존 시뮬레이션·검산은 덮어쓰지 않는다.
  상태는 `audit_run.json`과 `results/status.json`, 최종 결과는 `results/comparison.json`이다.
- `--chunk-steps 64`는 GPU에 올리는 검산 입력 묶음이다. 기본64구간에서7081점 후보·기준 상태 버퍼 합계는 약84.3MiB다.
  추가 GPU 작업 공간은 별도로 필요하며 전체 VRAM 사용량을 뜻하지 않는다. 메시별로 이 값을 바꿀 수 있다.
  원래 시뮬레이션의 기본2초 파일 저장 간격과 기록 빈도는 변경하지 않는다.
- CPU는 초기 구조 준비·파일 읽기/해시·청크 업로드·요약 저장을 담당한다. 청크 안에서는 GPU가
  힘·에너지·질량 풀이·위치·기하 상한·기준 궤적 대조와 판정을 수행한다. CPU 병렬 작업 풀을 사용하지 않는다.
- 앞으로 `profile_run.py --reuse-audit`를 사용하는 새 GPU 후보는 이 검산기를 기본으로 쓴다.
  개발 비교용 기존 검산기는 보존하며 해당 runner의 `--legacy-audit`로 명시적으로 선택할 수 있다.
  기존에 동결된 실행과 구형 본 시뮬레이션 실행기는 변경하지 않는다.
- 실제640구간의 기존 검산 대조·회귀7개·GPU graph의 host 전송 부재 검증 완료.
  [정확한 조건·시간 범위·검증·해시](audit_validation/README.md).
- 새 GPU 후보 실행기의 동결 준비도 `--prepare-only`로 확인했다. 검산 변경 검증에서 새 시뮬레이션은 실행하지 않았다.
- 적용 범위는 현재 P3 얇은 셸 개발 경로다. 학습 발행 보류와 연구 Gate는 유지한다.
