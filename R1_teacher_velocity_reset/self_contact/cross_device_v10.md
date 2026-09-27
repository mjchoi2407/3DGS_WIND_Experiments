# v10 메인·서브 복구 차이: 읽기 전용 진단과 1프레임 재현

## 현재 판정

2026-09-23 확인. 기존 run·로그·checkpoint는 수정/중단/재시작하지 않았다.
처음에는 저장 결과와 CPU 단위 검사만 확인했고, 이후 **사용자가 실행한 양쪽 GPU 반복 결과**를 읽어 분석했다.
후속 [CPU 계수 동결·원시 질량 경계 결과](cpu_frozen_v10.md#원시-질량-경계-결과)는 초기 힘과 첫 RHS 차이를 제거했고, [독립 질량 풀이 결과](cpu_frozen_v10.md#독립-질량-풀이-결과)는 같은 GPU의 고정 분해 객체에서 직접 solve도 비트 비결정적임을 확인했다. [공통 메인 wind115 상태의 양쪽 재생](cpu_frozen_v10.md#공통-메인-wind115-상태-1프레임-결과)은 모두 기본 dt로 승인됐고, 원래 서브 checkpoint와의 상태 차이를 확인했다. 장기 wind 복구 차이의 원인은 아직 미확정이다.
AGENTS/README와 접촉 GPU 계약을 확인했다. root 및 해당 저장소의 작업 진입점에서 `STATUS.md`는
찾지 못했으며, 최신 상태는 sessions 색인과 실제 report로 확인했다.

핵심은 **같은 원본 manifest가 실제 solver 수치 입력의 비트 일치까지 보증하지 않는다는 것**이다.
preload 첫 프레임의 적분 전 held 중력 힘부터 차이가 있다. GPU 접촉 atomic만의 문제로 결론 내릴 수 없다.
CPU 전처리 입력 차이와 같은 GPU의 반복 비트 불일치를 각각 확인했다.
구체적인 최초 GPU 연산 원인·race/미초기화 여부·장기 오차의 허용 가능성은 아직 미확정이다.

## 사용자 반복 실행으로 확인한 결과

메인 [3회 반복](../../artifacts/runs/p3_self_contact/diagnostics/20260922T151703Z-6a3a1cead8474177a28667f48ed6366e_main_preload_first_replay/runs.json),
서브 [3회 반복](../../artifacts/runs/sub_pc/20260922T152711Z-8c256e3275b24e5eb3a65e7df1000ac7_sub_preload_first_replay/runs.json)의
`trial_00`–`trial_02`를 분석했다. 서브의 사용자 경로는
`/mnt/wind3dgs-sub-results/20260922T152711Z-8c256e3275b24e5eb3a65e7df1000ac7_sub_preload_first_replay`다.
공유 마운트의 저장 파일을 읽었으며 새 원격 다운로드/fetch·GPU 실행은 하지 않았다.

- 같은 rest NPZ와 preload 첫 외력, fresh-process 1프레임. **6/6 실행의64단계 검산 통과**, GMRES 누적192,
  dt/2 없음, flags[0], trace 각1,541 events. 계측 경로의 결과이며 비계측/sanitizer 판정은 아니다.
- 각 PC 안의 host/upload 입력 hash는3회 모두 같지만 최종 상태 hash는3회 모두 다르다.
  **같은 GPU에서도 비트 결정성이 없음을 확인**했다. 최종 hi 최대 쌍 차이는
  메인 약1.35e-17m·4.69e-13m/s, 서브 약1.40e-17m·5.04e-13m/s다.
- 메인의 최초 관측 수치 차이는 event index4, substep0의 `mass_solve_predictor` 출력 요약이다.
  `mass_acceleration` 최대값이0.011116788750672926 대0.011116788750672929로 갈라진다.
  GMRES와 swept CCD 이전이다. 같은 CSR/RHS의 cuDSS mass factor/solve 또는 wrapper 경로를 우선 조사한다.
  **라이브러리 자체의 문제로 확정하지 않는다.**
- 서브는 event index5의 swept 후보 순서 지문부터 다르고 첫 벡터 요약 차이는 index8 Newton RHS다.
  앞선 mass 요약 일치가 원시 벡터 전체의 비트 일치를 증명하지는 않는다.
  양쪽 모두 substep0 종료 상태부터 차이가 있다. 이 프레임에서 GMRES/Newton 반복 수는 동일하다.
- 활성 접촉은 전체0. 따라서 이 표본의 최초 차이를 **접촉 힘/HVP의 FP64 atomic 누적 탓으로 볼 수 없다**.
  Swept 후보15,217개와 순서 무관 지문은 같지만 순서 지문은 달랐다. 지문 일치는 집합 완전성의
  수학적 증명은 아니며 후보 누락의 근거도 확인되지 않았다.
- **교차 PC host 배열13개가 이미 GPU 이전에 다름**: gravity_weights, mass_values, volume N/G/H 및 edge N/G/H 일부.
  최대 차이는 gravity_weights 5.76e-20, mass_values 3.39e-20, volume N 1.22e-15,
  G 5.68e-14, H 3.64e-12다. GPU의 자유 질량·초기 보조행렬 값도 서로 다르다.
- 각 PC의 저장 gravity_weights에 원래 첫 중력을 곱하면 **각자의 원래 v10 held_force_n과 bitwise 일치**한다.
  따라서 원래 preload 적분 전의 held force 차이를 CPU 생성 중력 가중치 차이에 연결할 수 있다.
  CPU5800X 대7600, NumPy/OpenBLAS 빌드와 thread1 설정은 같지만 실제 BLAS/SIMD dispatch·최초 CPU
  연산 차이까지 추적한 것은 아니다. 드라이버 세부 빌드도582.28 대581.80으로 다르다.

사용자 결정으로 먼저 [공통 CPU 입력 동결](cpu_frozen_v10.md#공통-입력과-검증-근거)을 적용한다.
그 뒤에도 남는 같은 GPU/교차 GPU 차이를 분리한다. 작은 preload 오차와 국소 검산 통과를
wind의mm·m/s 차이 승인이나 장기 dt/2 안정성 해결로 승계하지 않는다.

## 원본과 확인 분모

- 메인: `artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10/`.
- 서브: 메인에서 `artifacts/runs/sub_pc/20260922T134104Z-1515e916c2144b25bc5d37b7316c3120/simulation/`.
  서브의 `/mnt/wind3dgs-sub-results/<run ID>/simulation/`과 같은 공유 데이터다.
- 양쪽 manifest의 **290개 실제 파일을 각각 SHA256 재검증**, 누락/변조0.
  manifest: `f94f52dcdd823e45fff039e1255b56694eaea5270ac61a9cda2ed9d1ea56a562`.
  suite: `1419da7a8413c4ab2603c51501bfecc27e802769da401e8c2498c2a63180fd4e`.
  runtime Python, native cuDSS/shim, plan, 원본 forcing이 이 검증에 포함된다.
- rest 초기 NPZ: `fd3db24c136fc9691e29ced99de53cfcbe42ed10a0dcf9b316b0b0002d715ab7`.
- 저장 policy/material/contact/performance 설정 일치. Python3.12.3, NumPy2.4.4,
  SciPy1.18.1, IPC1.6.0, Warp1.17.0 버전 일치. 양쪽 시작 로그는 CUDA Toolkit12.9, Driver API13.0.
  **드라이버 세부 빌드, CPU/BLAS dispatch, 설치 패키지 파일 hash까지 같다는 근거는 없다.**
- 읽기 전용 감사 결과: [summary.json](../../artifacts/runs/p3_self_contact/v10_cross_device_readonly_20260923_01/summary.json),
  [프레임별 wind 비교](../../artifacts/runs/p3_self_contact/v10_cross_device_readonly_20260923_01/wind.jsonl),
  [preload 비교](../../artifacts/runs/p3_self_contact/v10_cross_device_readonly_20260923_01/preload.jsonl).
  summary SHA256: `f7306bef4e4f5ad5bf135fae9b9bf4f26208d091522d310cf27fd88d01cbe4f7`.
- report를 한 번 읽은 snapshot 기준이며 각 비교 NPZ도 report의 state hash와 대조했다.
  wind snapshot은 메인155·서브192개 저장 프레임이 있었지만 **양쪽 표시1–143만 비교**했다.
  이 구간 복구는 메인20/143, 서브22/143이다. 따라서 다른 진행 시점의5회 대26회를 그대로
  장치별 실패율로 해석할 수 없다. 최초121 대115와 서로 다른 복구 패턴은 재확인됐다.

| 관찰 위치 | 최대 변위 hi 차이(m) | 최대 속도 hi 차이(m/s) | 의미 |
| --- | ---: | ---: | --- |
| preload 표시1 종료 | 1.8101571e-17 | 3.9408701e-13 | 종료 checkpoint보다 훨씬 이른 차이 |
| preload 표시120 종료 | 1.4606914e-16 | 5.1125370e-12 | 사용자 관찰 재확인 |
| wind 표시10 종료 | 1.5625386e-16 | 4.6612098e-12 | GMRES 누적2925 대2926 첫 불일치 |
| wind 표시84 종료 | 2.2724054e-6 | 0.0025042198 | dt/2 이전 증폭 |
| wind 표시101 종료 | 0.0056463763 | 2.6442187 | 장기 차이를 단순 반올림 오차로 승인할 수 없음 |

위 숫자는 raw `u_hi/v_hi` 비교다. raw low 배열도 감사 JSONL에서 별도 비교했다.
절대 rest 좌표를 더해 작은 변위 차이를 소실시키지 않았다. preload에서 누적 GMRES는120프레임 모두 같았다.

### 가장 이른 저장 근거

preload 표시1은 wind=(0,0,0), gravity=(0,0,-0.00808417…)이며 시작 u/v는 같은0이다.
이 프레임의 `held_force_n`은 **1,620개 성분**, Z방향 최대 `4.499862532288471e-22 N` 차이;
전체 힘의 최대 성분은 약 `7.105224609375004e-7 N`이다.
이 배열은 substep 적분 **전에** 프레임 시작 상태로 계산해 고정한다.
독립 검산 `checks[0,0]`도 첫 substep(index0)에서 이미 다르다.
다만 이것은 최초 **검산값** 차이이며 첫 solver/상태 차이의 정확한 kernel을 저장 기록만으로 알 수는 없다.

코드 경로는 [consistent_mass](../../../code/wind3dgs/teacher/p3_surface.py)에서 CPU 행렬곱으로 요소 질량을 만들고,
[P3Shell](../../../code/wind3dgs/teacher/p3_shell.py)에서 sparse 조립한 뒤,
[GravityShellStepper](../../../code/wind3dgs/teacher/resident_gravity.py)의 CPU `mass @ ones`를 GPU로 올린다.
무풍·정지의 공력은0이고 `add_gravity`는 정점별 독립 FP64 곱/덧셈이다. 따라서 CPU 질량/구적 계수·
BLAS 경로 차이를 초기 가설로 삼았다. 후속 [반복 실행 분석](#사용자-반복-실행으로-확인한-결과)에서
CPU weights 차이와 원래 held force의 대응을 확인했다. 최초 CPU 연산과 구현 버그 여부는 별도 미확정이다.

## 경로별 조사와 남은 구분

| 경로 | 코드에서 확인한 사실 | 판별 방법·최소 수정 후보 |
| --- | --- | --- |
| CPU 모델 전처리 | plan에서 질량·구적·강성 계수를 매번 재생성; manifest는 생성된 배열 hash를 포함하지 않음 | `host_inputs`의 mass/weights/N/G/H 비교부터. 차이가 확인되면 한 번 생성한 동일 FP64 계수 묶음을 입력으로 동결·검증하여 로드. 물성/수식은 유지 |
| 접촉 힘/HVP | `gpu_contact_parallel.assemble_force/hessian_action`의 공유 정점 FP64 `atomic_add` | 같은 후보·미분값인데 누적 힘이 갈라지는지 확인. 필요 시 canonical pair ID와 정점별 고정 순서 gather/segment reduction. **후보 정렬만으로 atomic 덧셈 순서는 고정되지 않음** |
| BVH 후보 | raw와 active append에서 atomic으로 슬롯 예약; 정렬 없이 미분/에너지/HVP에 사용. worker 수는 SM 수에 따라 달라짐 | 개수+순서 지문+순서 무관 지문을 비교. 순서만 다름/후보 자체 다름을 구분. CPU 전수 oracle·경계거리 확인은 후보 집합 차이가 확인된 뒤 |
| GMRES 내적 | Warp `TiledDot`, 기본 tile512·다단계 reduction; 해당 구현은 전역 atomic sum이 아님. solver norms도 고정 pair tree | 같은 RHS/M⁻¹RHS에서 bn/mn, Arnoldi norm·내부 반복·참 잔차의 최초 불일치 비교. 모든 reduction을 atomic 비결정성으로 묶지 않음 |
| cuDSS | 같은0.7.1 native hash. IR/hybrid memory/hybrid execute OFF. 결정성 모드 명시 설정은 없음 | 같은 CSR/RHS의 factor/solve 출력 대조. 해당 동결 버전 지원을 먼저 확인한 후 결정성 모드를 격리 A/B 후보로 검토; 지금 solver 옵션 변경 없음 |
| 미초기화/race | 접촉 출력·count/status 초기화, 후보 유효 prefix, 초과 시 거절/전체 fallback을 확인. GMRES scratch는 zeros/매-cycle reset, reduction scratch는 사용 prefix를 채움 | 정적 점검에서 확정 버그는 못 찾음. `memcheck → initcheck`, 추가 racecheck/synccheck. 통과했다고 모든 global race가 없음을 증명하지 않음 |
| 시간 계측 보정 | `ResidentContactRetryFrame.run_frame`의 GPU graph 완료 후 host 시간 집계 | dt/2 GPU 자격 검사에 배율 입력 없음. 원인 후보에서 제외하되 계측이 스케줄링을 바꾸는 영향은 비계측 대조로 구분 |

NVIDIA는 cuDSS 결정성 모드의 비트 일치 보장을 **동일 아키텍처·SM 수·입력·설정**으로 제한한다.
따라서 켜더라도1080Ti↔5070 비트 일치 해결책으로 일반화하지 않는다.
[공식 cuDSS 문서](https://docs.nvidia.com/cuda/cudss/types.html#c.cudssConfigParam_t.CUDSS_CONFIG_DETERMINISTIC_MODE).
또한 racecheck의 주 대상은 shared-memory hazard이며 global memory 초기화 검사는 initcheck다.
[Compute Sanitizer 공식 문서](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html).
라이브러리 문서는 현재 웹 문서이며0.7.1에 새 기능을 역으로 가정하지 않는다.

### dt/2와 solver 안정성

서브 표시115: substep index48, GMRES720, 잔차0.0765735771N > 목표0.0362861875N(2.11배).
메인 표시121: substep index1, GMRES531, 잔차0.0575217118N > 목표0.0345919553N(1.66배).
두 경우 Newton index0, 유한한 code2, contact/path status0, GMRES cycle 수3, 마지막 breakdown flag0이다.
GMRES는 **최대240회인 cycle을3번** 허용한다. 매 cycle이 조기 종료할 수 있어531회도
3-cycle 소진 후 참 잔차 미달로 실패할 수 있다. 항상720회를 쓴 뒤에만 실패하는 정책이 아니다.

이는 충돌 침범 코드가 아니라 **선형 풀이 수렴 여유 부족**이다. 같은 prefix의 복구율20 대22는
서브만의 압도적인 불안정성을 입증하지 않지만, 두 장치 모두 후반부 기본dt 풀이의 강건성은 재검토 대상이다.
작은 전처리/연산 차이 → 궤적/상태 의존 공력 변화 → 조건수/GMRES 종료 변화 → 서로 다른 dt/2
분기로 더 갈라지는 설명은 현재 근거와 부합한다. 각 연결 고리의 최초 kernel은 재현으로 확인해야 한다.
초기1e-16m 차이는 반올림 크기와 양립하지만 wind101의mm·m/s 차이를 허용 가능하다고 판정할
장기 오차 예산/시간 수렴 근거는 없다. 개별 프레임 독립 검산 통과와 장기 정확도는 다른 기준이다.

현재는 원래 tolerances/cycles/dt/retry/barrier를 유지한다. 입력 일치·결정성을 분리한 후에도
같은 상태의 참 잔차 미달이 반복되면 재직교화·잔차 replacement 또는 contact-aware 보조행렬 같은
**동일 물리 연산자의 수치 풀이 개선**을 별도 후보로 비교한다. 한도를 늘리거나 허용오차를 완화해서
이번 원인 진단을 대신하지 않는다. 아직 그런 수정은 적용하지 않았다.

## 사용자 실행: 먼저 CPU 입력, 그다음 동일 상태 한 프레임

[diagnose_v10_repro.sh](diagnose_v10_repro.sh)는 실행마다 UUID 출력 폴더를 만들고 기존 run과
겹치는 출력을 거절한다. 어느 PC에서도 **메인에 저장된 같은 시작 NPZ**를 사용하며 SHA를 고정 검사한다.
서브에서 자체 preload 결과를 시작점으로 선택하지 않는다. 원본 run은 실행 중이어도 읽기만 한다.
서브 결과 공유가 해제되어 있으면 중단하며 로컬 저장으로 fallback하지 않는다.
서브는 기존 worker Python venv를 활성화하거나 `WIND3DGS_PYTHON`에 그 interpreter를 지정한다.
main은 workspace `.venv/bin/python`을 기본 사용한다. 아래는 workspace 루트에서 실행한다.

```bash
# GPU 계산 없음: CPU에서 만든 질량·중력 가중치·구적 계수만 기록
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_repro.sh \
  --computer main --mode host --case preload_first --repeats 1
# 서브에서는 위 --computer main만 --computer sub로 변경

# 같은 입력으로 새 프로세스에서 한 프레임씩3회; 프레임을3개 이어서 계산하지 않음
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_repro.sh \
  --computer main --mode replay --case preload_first --repeats 3
# 서브: --computer sub. 양쪽 동일 NPZ, 각자 동결 runtime/native 사용
```

| `--case` | 재생 표시 프레임 | 공통 시작 NPZ(메인 outputs 기준) | 목적 |
| --- | --- | --- | --- |
| `preload_first` | preload1 | `preload/initial_state.npz` | 이미 갈라진 preload를 입력으로 삼지 않고 최초 생성 위치 찾기 |
| `wind10` | wind10 | `wind/frame_0008.npz` | 첫 누적 GMRES 차이를 같은 시작 상태에서 대조 |
| `wind115` | wind115 | `wind/frame_0113.npz` | 서브 최초 실패 시점의 forcing, **메인 공통 상태**로 분리 |
| `wind121` | wind121 | `wind/frame_0119.npz` | 메인 최초 실패 시점 대조 |

`wind115` 공통 상태 재생은 서브의 원래 궤적을 재현하는 시험이 아니다. 같은 상태에서도 장치가
다르게 판단하는지 확인하는 시험이다. 원래 서브 상태 자체의 재현은 아래 일반 CLI에 그 NPZ와 SHA를
명시해서 별도 출력으로 수행한다. 모든 경우 한 프레임만 실행한다.

출력은 main의 `artifacts/runs/p3_self_contact/diagnostics/<UUID…>/`, sub의
`/mnt/wind3dgs-sub-results/diagnostics/<UUID…>/`이다. `trial_00`, `trial_01`, `trial_02`는 fresh process이며
첫 trial 대비 비교가 `compare_00_01/comparison.json` 등에 자동 생성된다.
서로 다른 GPU 결과 비교는 main에서 다음 CPU 전용 명령을 사용한다(실제 새 디렉터리 경로로 치환).

```bash
.venv/bin/python code/wind3dgs/evaluation/contact_determinism.py compare \
  --main <메인_진단/trial_00> --sub <서브_진단/trial_00> --out <존재하지_않는_비교폴더>
```

`--mode plain`은 같은1프레임을 원래 비계측 graph로 실행하는 대조다. 계측/비계측의 최종 상태 및
실패 판단을 먼저 비교한다. `--mode memcheck`, 이어 `--mode initcheck`는 동일1프레임을
Compute Sanitizer로 감싸며 반복은1회로 제한한다. `racecheck/synccheck`도 지원하나 toolkit/GPU별
지원 여부와 CUDA conditional graph 계측 지원을 결과 로그에서 확인해야 한다. sanitizer 실행은 오래 걸릴 수 있다.
GPU 설정/공식 허용오차를 바꾸는 옵션은 없다. 선택한 진단은 **사용자가 실행**한다.

### 기록과 해석 경계

- `host_inputs.npz/json`: GPU 실행 전 mass CSR, gravity weights, geometry/N/G/H/weights 등의 원시 배열·SHA.
  여기서 다르면 교차 GPU만의 비교가 아니다. `--mode host`는 여기까지만 수행한다.
- `environment.json`, `gpu.json`: CPU·BLAS 정보, 패키지 버전, GPU/CC/SM 수, driver/CUDA.
  `uploaded_inputs.npz/json`: GPU에 올린 질량·초기 보조행렬·중력 가중치.
- `base_substeps.jsonl`, 조건부 `half_substeps.jsonl`: Newton index, 마지막 GMRES 횟수와 해당 substep
  실제 총횟수, 선형 잔차/목표, pending/최종 failure, 후보 수, 프레임 dt/2 선택, raw 상태/RHS/delta SHA.
- `*_events.jsonl`: 초기 힘 RHS → 질량 풀이 predictor → Newton 판정 → GMRES 입력/첫 M⁻¹RHS·norm →
  cycle 종료/출력, 모든 active/swept query 완료와 접촉 힘 평가 완료를 기록한다.
  GMRES 내부 Arnoldi 종료는 `--focus-substep`(기본index0)에서만 추가 기록한다.
  `*_trace.npz`에 원시 controls/stats 및 벡터 고정 순서 sum/sum-of-squares/max/nonfinite 요약을 저장한다.
  `gmres_stats`의 bn/mn은 각각 RHS norm과 M⁻¹RHS norm이며 `w`는 단계에 따라 전처리/Arnoldi 벡터다.
- 후보 지문은 `(kind, 네 정점 ID)`의 순서-sensitive64bit와 순서 무관 sum/xor64bit다.
  **SHA나 집합 동일성의 증명은 아니다.** 개수·순서/내용 차이의 탐색 지표이며 지문이 같아도
  의심 구간은 후보 원시 ID를 추가 덤프해 정확 대조해야 한다. Overflow는 별도 표기하고 완전성으로 세지 않는다.
- 성공 substep도 원래 run에는 잔차/후보/내부 iteration trace가 없었다. 과거 데이터에서 없던 값을
  복원했다고 주장하지 않는다. 실패 tail의 stale GMRES stats는 `gmres_ran=false`로 구분한다.
  벡터 요약은 해당 stage에서 유효한 입력/출력만 해석한다. `current_matrix_built` 표식 자체가
  각 동적 factor 내부 수치를 덤프한 것은 아니므로 cuDSS를 단독 원인으로 확정하려면 추가 CSR/RHS 대조가 필요하다.
- 첫 base substep0과 half substep0은 각 attempt의 첫 시간 구간이다. substep 번호는0-based이며
  half의 동일 index는 base와 같은 물리 시각이 아니다. dt/2 선택은 GPU graph 완료 후 기록하는
  프레임-level 결과이지 개별 substep이 임의로 dt를 바꾸었다는 뜻이 아니다.
- 관측 버퍼는 solver 입력/조건에 연결하지 않으며 원래 GPU retry/검산/rollback을 유지한다.
  그래도 추가 kernel과 fresh 초기화가 스케줄링·LBVH/분해 준비를 바꿀 수 있어 성능 측정에 쓰지 않는다.
  기존 long run의 숨은 cache/분해 상태까지 직렬화한 replay는 아니다.
- trace32,768 event 한도를 넘으면 원래 계산 결과는 저장하되 trace 완전성 실패로 반환한다.
  GPU 실행 경로/conditional graph/커널 컴파일은 이번에 **미검증**. CPU 검사6개와 AST/Bash 구문만 통과했다.

## 남은 결정과 완료 조건

1. 양쪽 `host_inputs`가 다르면 먼저 mass/구적 계수 동결 입력 패치를 제안하고 승인 후 적용한다.
2. 동일 host/NPZ에서 같은 GPU 반복이 다르면 비결정성 경로를 먼저 찾는다. 안정적으로 같으면
   교차 GPU 비교로 이동한다. 소수회 일치만으로 결정성이 수학적으로 보장되지는 않는다.
3. 동일 입력에서 처음 갈라지는 stage와 base/half 실패 판단을 확정한다. 후보 순서만 다른 경우와
   후보 내용·force·M⁻¹RHS·dot 결과가 다른 경우를 분리한다.
4. 비유한 값/예상 밖 입력 변경/sanitizer 오류면 race·초기화·수명 수정이 우선이다.
5. 수치 풀이 개선은 참 잔차·기하·CCD·허용오차를 유지하고 동일 상태에서 비교한 뒤 채택한다.
   세 씬 장기 완주·시간 수렴·R1 완료/학습 적격성은 아직 이 진단으로 승격하지 않는다.

기존 R1의 제한 개발 검증/장기 미검증 경계를 확인했으며 이번에는 연구 계약·Gate·TeX를 변경하지 않았다.
PDF 빌드는 이번 진단에 해당하지 않는다. 기존 사용자 TeX/PDF/bundle 변경은 보존했다.
