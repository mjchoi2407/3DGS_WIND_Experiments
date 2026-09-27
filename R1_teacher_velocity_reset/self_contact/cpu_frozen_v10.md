# v10 CPU 계수 동결: 첫 통제 단계

## 현재 상태

2026-09-23. 사용자 요청으로 CPU 전처리 동결만 우선 적용했다. 원래 v10 source/native,
세 씬 실행기·결과·시작 NPZ·물성·바람·dt·허용오차·cuDSS 옵션은 변경하지 않았다.
동결 GPU 첫 프레임 재생과 후속 원시 질량 경계 시험은 각각 메인·서브 각3회 모두 승인됐다.
첫 substep의 RHS는 여섯 실행에서 비트 단위로 같고, 같은 GPU의 반복에서도 질량 풀이 후
가속도부터 차이가 난다. 독립 풀이에서는 같은 분해 객체의 직접 solve도 반복마다 달라졌다.
공통 메인 wind115 상태의 양쪽 GPU 각3회는 전부 dt/2 없이 승인됐고,
원래 서브 시작 상태와의 큰 차이가 남았다. [독립 풀이 결과](#독립-질량-풀이-결과)와
[공통 상태 재생 결과·다음 명령](#공통-메인-wind115-상태-1프레임-결과)을 따른다.
원인 근거는 [앞선 양쪽 반복 결과](cross_device_v10.md#사용자-반복-실행으로-확인한-결과),
구현·수명·로드/거절 계약은 [code 문서](../../../code/docs/frozen_cpu_diagnostics.md#저장과-로드-계약)를 따른다.

## 공통 입력과 검증 근거

- 새 CPU 원본: [cpu_inputs.npz](../../artifacts/runs/p3_self_contact/diagnostics/20260922T155046Z-dddbdc49008c4cd6ba1eea917fd03bbd_main_cpu_frozen/cpu_inputs.npz).
  메인 workspace의 같은 파일을 양쪽 PC가 읽는다. 서브에서 다시 생성하지 않는다.
- NPZ SHA256: `c742796976565b56bb30b3b10630f65555d8d2a8517ceb5c1d18034ac4d7bf8e`.
  77개 수치 배열, 1,498,963 bytes. 모델/강성/중력·기본/half 보조행렬뿐 아니라 proxy·기하 검산 map을 포함한다.
- Source v10 manifest: `f94f52dcdd823e45fff039e1255b56694eaea5270ac61a9cda2ed9d1ea56a562`.
  실제 manifest 검증 후 원래 `runtime`으로 reference_rectangle preload 모델을 생성했다.
  [freeze.json](../../artifacts/runs/p3_self_contact/diagnostics/20260922T155046Z-dddbdc49008c4cd6ba1eea917fd03bbd_main_cpu_frozen/freeze.json)에
  전체 contract·생성 당시 driver/helper SHA·roundtrip·크기를 기록했다.
  [environment.json](../../artifacts/runs/p3_self_contact/diagnostics/20260922T155046Z-dddbdc49008c4cd6ba1eea917fd03bbd_main_cpu_frozen/environment.json)은 생성 환경이다.
- 재로드 후 원본 35개 host 배열의 hash가 모두 일치했다. 이전 메인
  `20260922T151703Z-6a3a1cead8474177a28667f48ed6366e_main_preload_first_replay/trial_00/host_inputs.json`의
  35개와도 전부 일치했다. 같은 trial의 **실제 GPU 업로드 기록**에 있는 gravity_weights,
  mass_values, current_values 3개도 동결 bundle의 대응 CPU 배열과 bitwise 일치했다.
  새 GPU 실행으로 확인한 것이 아니라 이전 저장 배열/hash를 읽어 대조한 결과다.
- 새 [CPU-only host 결과](../../artifacts/runs/p3_self_contact/diagnostics/20260922T155205Z-d50770f4d38f41eaa2b31833c6416454_main_preload_first_host/trial_00/config.json):
  pinned wrapper로 공통 NPZ 검증/모델 복구/CPU 파생 입력 검사를 통과했다. GPU 초기화·프레임0회.
- CPU 단위 검사18개와 원시 경계 캡처의 실제 GPU graph 6회가 통과했다. 장기 wind 검증은 별도다.

이 NPZ는 Git ignored artifact이며 삭제/재생성 대상이 아니다. 파일이 없으면 같은 SHA의 원본을
공유/복구해야 한다. 소스만 받아서 자동 재생성한 파일을 이 비교의 공통 입력이라고 간주하지 않는다.

## 사용자 실행

Workspace 루트에서 실행한다. 기존 본 run과 별도의 UUID 출력이 생긴다. 서브는 기존 worker
Python 환경을 활성화하고 공유 마운트를 유지한다. 매회 같은 메인 frame-start NPZ와 CPU NPZ를 쓴다.

먼저 서브의 CPU 로드 검사(메인은 이미 통과):

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer sub --mode host --repeats 1
```

이후 양쪽 GPU에서 각각 실행한다. 각 프로세스는 preload 첫 프레임 하나만 계산하며 새 프로세스3회 반복이다.

```bash
# 메인
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer main --mode replay

# 서브
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer sub --mode replay
```

GPU 초기화가 끝나면 `공통 CPU → GPU 정적 입력 …개 bitwise 검증 통과`가 출력된다.
불일치하면 재생을 거절하며 허용오차를 늘리거나 해당 검사만 생략하지 않는다.
CPU-only `host` 완료는 GPU 업로드 검증 통과와 구분한다.

메인 출력: `artifacts/runs/p3_self_contact/diagnostics/<새 ID>_main_preload_first_replay/`.
서브 출력: `/mnt/wind3dgs-sub-results/diagnostics/<새 ID>_sub_preload_first_replay/`,
메인에서 `artifacts/runs/sub_pc/<같은 ID>_sub_preload_first_replay/`로 읽는다. 실제 이번 공유 미러 위치를 따른다.
비동결 대조는 기존 [diagnose_v10_repro.sh](diagnose_v10_repro.sh)를 CPU 옵션 없이 사용한다.
`--case wind10|wind115|wind121`도 같은 모델 계약에 연결할 수 있으나 이번 우선 비교는 preload_first다.

## 결과를 판단하는 순서

1. 양쪽 `config.json`의 시작 NPZ/CPU NPZ/source/helper SHA 및 정책이 같은지 확인한다.
2. 각 trial의 `frozen_uploaded_inputs.json`이 존재하고 모두 같은지 확인한다.
3. 같은 GPU의3회에서 최초 force/RHS·mass solve·substep 상태 차이를 비교한다.
4. 양쪽 GPU의 초기 force 차이가 사라졌는지, 남은 최초 차이가 어느 단계인지 확인한다.

동결 이후에도 같은 GPU의 mass solve 차이가 남으면 앞서 관찰한 **별도의 GPU 풀이 결정성**을
다음 단계로 좁힐 수 있다. 아직 cuDSS 자체·wrapper graph·미초기화/race를 분리 완료하지 않았다.
이 검사는 장기 wind의 dt/2 빈도가 줄었는지, 긴 궤적 오차가 허용 범위인지 증명하지 않는다.
R1 완료 조건·연구 수식·claim/Gate 변경이 없어 관련 R1 접촉 절을 확인만 했고,
기존 사용자 TeX/PDF/bundle 변경은 보존했다. 이번 작업에서는 TeX 수정·PDF 빌드를 하지 않았다.

## 동결 GPU 재생 결과와 다음 시험

사용자 완료 실행: 메인
[3회 결과](../../artifacts/runs/p3_self_contact/diagnostics/20260923T000447Z-ab933ab36b484b40b6d5fd18c3162a09_main_preload_first_replay/runs.json),
서브 공유 미러의
[3회 결과](../../artifacts/runs/sub_pc/20260923T000453Z-3cefdbe1fd3740549e9e17303fccef24_sub_preload_first_replay/runs.json).
원본 v10 run과 다른 UUID 폴더이며 이 분석에서는 결과만 읽었다.

- 6/6 fresh-process preload 첫 프레임 통과, 각64 substep·GMRES 누적192회,
  실패 코드0·활성 접촉0·dt/2 전환0. 입력 NPZ `fd3db24c136fc9691e29ced99de53cfcbe42ed10a0dcf9b316b0b0002d715ab7`,
  공통 CPU NPZ `c742796976565b56bb30b3b10630f65555d8d2a8517ceb5c1d18034ac4d7bf8e`.
- 두 PC·세 반복의 config/host 입력, solver·독립 검산의 GPU 정적 업로드196개가 bitwise 일치.
  첫 `held_force_n`도 6회 전체 bitwise 일치. 원래 서브와 이 힘의 최대 차이는
  `4.499862532288471e-22 N`; 원래 메인과는 정확히 같다.
- 같은 GPU 반복의 최종 `u_hi` 최대 차이는 메인 약1.45e-17 m, 서브 약1.32e-17 m.
  메인 trial00 대 서브 trial00은 약1.23e-17 m. 첫 substep 종료부터 원시 상태가 다르다.
  첫 수치 요약 차이는 대부분 event4 `mass_solve_predictor`이고, 모든 쌍의 event3
  `initial_force_rhs` 요약은 같다. 원시 RHS와 `a0`는 이 실행에서 저장하지 않았다.
- 후보 순서 지문은 같은 GPU 반복에서도 달라졌지만 순서 무관 sum/xor 지문은 일치했다.
  이 프레임에 활성 접촉은0이며 순서 지문 차이는 질량 풀이 구간보다 뒤에 관측된다.
  후보 집합의 완전성이나 GPU library의 race 부재를 지문만으로 증명하지 않는다.

CPU 계수 차이로 인한 초기 힘 불일치는 제거됐다. 남은 동일 GPU 비트 불일치의 최초 연산과
wind 장기 dt/2 빈도의 변화는 아직 확인하지 않았다. 이번 시험의 결과를 본 실행 승인이나
수렴 문제 해결로 확장하지 않는다.

다음은 **각 PC에서 한 번씩** 실행한다. 스크립트는 매번 새 UUID 출력에 첫 preload 프레임 하나를
새 프로세스3회 계산한다. 시작 NPZ·동결 CPU 계수·물성·외력·dt·허용오차는 위와 같다.
준비한 진단 driver SHA256은 `e447108c71441baef7bf036c8567419e68a167fd418ef1f4ad54d2c4c6993ec4`,
trace SHA256은 `118faf36dd5c6dd67cc9ee1daa527d25f594ea33e925b8341d73ecfeb4f556d4`다.
각 새 `trial_*/config.json`의 `trace_driver_sha256`·`trace_kernel_sha256`와 대조한다.

```bash
# 메인 GPU
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer main --mode massprobe --repeats 3

# 서브 GPU
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer sub --mode massprobe --repeats 3
```

각 trial에 `base_mass_probe.npz`와 `result.json`의
`observations.base.mass_probe.{focus_substep,hits,complete,arrays}`가 생긴다. RHS, 질량 풀이 후
가속도, 예측 위치 hi/lo를 원시 배열로 저장하며 각 기록 횟수는1이어야 한다.
`compare_00_01/comparison.json`, `compare_00_02/comparison.json`의
`attempts.base.mass_probe.first_different_vector`가 같은 GPU 첫 불일치 배열이다.
이번 사용자 실행 결과와 교차 대조는 아래 절에 기록했다. 추가 캡처 kernel은
스케줄링을 바꿀 수 있으므로 시간 비교에 쓰지 않는다. [코드 계약](../../../code/docs/frozen_cpu_diagnostics.md#원시-질량-경계-진단)에 캡처 시점을 명시했다.

## 원시 질량 경계 결과

사용자 완료 실행: 메인 [3회 결과](../../artifacts/runs/p3_self_contact/diagnostics/20260923T004520Z-77ed63f3d4cf49b9900fad78a833c3cf_main_preload_first_massprobe/runs.json),
서브 공유 미러 [3회 결과](../../artifacts/runs/sub_pc/20260923T005618Z-1928662fd5024a46b8664b5aba352179_sub_preload_first_massprobe/runs.json).
기존 v10 run·동결 NPZ는 읽기만 했다. 두 run의 시작 NPZ SHA256은
`fd3db24c136fc9691e29ced99de53cfcbe42ed10a0dcf9b316b0b0002d715ab7`,
CPU NPZ는 `c742796976565b56bb30b3b10630f65555d8d2a8517ceb5c1d18034ac4d7bf8e`다.
manifest·진단 driver·trace source SHA도 양쪽 config에서 일치했다.

- 6/6 preload 첫 프레임 통과: 각64 substep·GMRES192회·실패 코드0·활성 접촉0·dt/2 전환0.
  네 원시 캡처는 각각 정확히 한 번씩 기록되고 유한했다. CPU host77개·GPU 정적 업로드196개
  기록은 여섯 실행에서 bitwise 일치하며 `base/mass_factor` CSR도 같다.
- 첫 substep `rhs_before_mass_solve` 5292개 FP64 값은 여섯 실행에서 bitwise 일치
  (배열 SHA256 `4e893ab72dc5b90d0c57446e3c0aae3e993203594d022c5973ab6ae8fc802c52`).
  [메인 반복 비교](../../artifacts/runs/p3_self_contact/diagnostics/20260923T004520Z-77ed63f3d4cf49b9900fad78a833c3cf_main_preload_first_massprobe/compare_00_01/comparison.json)와
  [서브 반복 비교](../../artifacts/runs/sub_pc/20260923T005618Z-1928662fd5024a46b8664b5aba352179_sub_preload_first_massprobe/compare_00_01/comparison.json) 모두
  첫 차이 배열은 `mass_acceleration`이다. 다른 반복 및 양쪽 대응 trial 교차 비교도 같다.
- 같은 GPU 반복·양쪽 교차의 `a0` 최대 절대차는 `6.94e-18`–`8.67e-18 m/s²`,
  성분별 최대 상대차는 `8.90e-16` 이하다. 예측 `u_hi`도 최대 `3.11e-25 m` 정도 다르다.
  동결 CSR로 CPU에서 독립 계산한 `||M a0 - RHS||∞ / ||RHS||∞`는 여섯 출력 모두
  `2.61e-16`–`2.98e-16`이다. 원시 hash 확인 후 읽기 전용으로 검산했다.

최초 불일치는 `pack_sum` 후 RHS와 `predict` 전 `a0` 사이의
`mass_factor.matvec`: RHS 복사→cuDSS GPU graph solve→FP64 `scaled_copy` 경계다.
첫 substep에서 Newton·GMRES·활성 접촉 전에 생기므로 접촉 후보 삽입/힘 atomic이 **이 최초 차이의 직접 원인**은 아니다.
cuDSS의 현행 설정은 결정성 옵션을 켜지 않는다. [NVIDIA cuDSS 0.7 계열 문서](https://docs.nvidia.com/cuda/archive/13.0.1/cudss/general.html#results-reproducibility)는
기본 모드의 atomic 연산 때문에 같은 환경에서도 bitwise 재현이 보장되지 않는다고 설명한다.
관측된 작은 차이·정상 잔차와 부합하지만, cuDSS 내부와 wrapper graph/버퍼의 잠재 race를
분리한 증명은 아니다. cuDSS 결정성 모드는 같은 아키텍처·SM 수에서만 bitwise 보장을
약속하며 느려질 수 있다. 메인 GTX1080Ti와 서브 RTX5070 사이 일치를 보장하지 않는다.

다음에는 **원래 solver 옵션 그대로** 동결 CSR·RHS의 독립 `CuDSSFactor` 풀이를
fresh process/동일 process에서 반복해 내부 factor·solve와 graph wrapper를 분리하는 편이 안전하다.
결정성 옵션 시험은 solver 설정 변경이므로 별도 사용자 결정 전에는 적용하지 않는다.
이번 무접촉 preload 한 프레임만으로 wind 장기 dt/2 빈도·수렴 안정성·허용 가능한 궤적 차이,
race/미초기화 메모리 부재를 판정하지 않는다. 본 세 씬 실행 승인으로 승계하지 않는다.

## 독립 질량 풀이 시험 준비

원시 경계에서 남은 `mass_factor.matvec`를 분리하는 별도 시험이다. 첫 massprobe의
메인 trial00에서 추출한 같은 RHS 5292개와 CPU 동결 CSR 86058 nonzero만 양쪽 PC에 공급한다.
원본 v10 runtime/native와 workspace shim을 사용하고, 물성·바람·dt·허용오차·cuDSS 옵션은
변경하지 않는다. 본 시뮬레이션·체크포인트 재생·접촉 계산은 하지 않는다.

```bash
# 메인컴 — workspace 루트
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_mass_only.sh --computer main

# 서브컴 — 같은 공유 workspace 루트
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_mass_only.sh --computer sub
```

각 컴퓨터에서 새 UUID 폴더를 만들고, fresh process3개가 각자 단일 cuDSS 분해 객체로
graph/직접 풀이를 번갈아 4회씩 수행한다(프로세스당8회, 컴퓨터당24회). 매 풀이의
cuDSS 내부 `x`, wrapper 출력 `a0`, 상태 코드, `||M a0-RHS||∞/||RHS||∞`를 기록한다.
`trial_*/solutions.npz`의 원시 해와 `result.json`, `trial_*.log`, `summary.json`의
`same_process`·`graph_vs_direct`·`fresh_process`를 확인한다. 실패하면 해당 새 출력은
보존하고 뒤 trial/summary를 만들지 않는다. 속도 비교 자료로 사용하지 않는다.

동결 CPU 파일·첫 RHS·원래 업로드 CSR·manifest 290개 파일은 GPU 시작 전에 검증한다.
진단 소스 SHA256 `ecd4ba02b9255d9649c0305820b6af4a39cce46770eafa8e2c1cf1d45890eac6`,
wrapper SHA256 `5cf6a314a19900f01e833f6a0694d9b7dc93d3cfaad6fed3a97d9b5fe416518b`다.
실행 시 `inputs.json`에 고정 입력·진단 소스 hash를, 각 `gpu.json`에 원본 cuDSS
소스/native hash·GPU 정보를 남긴다.
CPU 단위 검사22개·실제 양쪽 보관 manifest/고정 입력 사전검증·Bash 구문은 통과했다.
독립 GPU 시험은 아래 사용자 완료 결과로 갱신했다. 이 시험은 장기 wind의 dt/2 복구 빈도 문제
해결을 곧바로 입증하지 않는다. [코드의 판독 한계](../../../code/docs/frozen_cpu_diagnostics.md#고정-질량-풀이-분리-진단)를 따른다.

## 독립 질량 풀이 결과

사용자 완료 실행: 메인 [요약](../../artifacts/runs/p3_self_contact/diagnostics/20260923T013941Z-86c2bb4504f342d78cdc8112e0b36d3d_main_preload_mass_only/summary.json),
서브 공유 미러 [요약](../../artifacts/runs/sub_pc/20260923T015148Z-b6cfa334ba2d48ccaa6441cff0929e14_sub_preload_mass_only/summary.json).
각 폴더의 inputs.json, trial_00–trial_02의 gpu.json, result.json, solutions.npz,
trial_*.log를 읽기 전용으로 검사했다. 본 시뮬레이션·체크포인트 재생은 이 시험에서 실행하지 않았다.

- 양쪽 모두 같은 CPU NPZ SHA256 c7427969…, 첫 RHS 4e893ab7…, 질량 CSR 세 배열 hash,
  v10 manifest f94f52dc…, 첫 massprobe trial config와 진단 driver hash를 기록했다.
  원본 cuDSS source/native·workspace shim hash도 두 PC에서 일치한다. GPU는
  메인 GTX 1080 Ti(sm_61), 서브 RTX 5070(sm_120)이고 양쪽 Warp 1.17.0,
  CUDA Toolkit 12.9·Driver API 13.0이다. 장치 아키텍처·SM 수는 다르다.
- 각 PC 3 fresh process × 각 process 4회 graph+4회 직접 solve = PC당24회,
  총48회가 상태 코드0으로 완료됐다. 저장된 원시 벡터 hash와 동결 CSR/RHS로 재계산한
  상대 ∞잔차가 기록과 모두 일치했다. 잔차 범위는 2.235e-16–2.980e-16이다.
- **같은 GPU·같은 분해 객체·같은 RHS에서도** 각 process의 graph 4회와 직접 solve 4회는
  각각 해 hash가 모두 달랐다. graph와 직접 solve도 같은 cycle에서 bitwise 불일치했고,
  새 process 3개의 첫 출력도 모두 달랐다. 같은 process의 최대 절대차는 메인
  8.674e-18, 서브 6.939e-18 m/s²; 대응 cycle의 양쪽 GPU 최대 차이는
  1.041e-17 m/s²다. 격리 graph 첫 해는 원래 메인 massprobe trial00의 a0와
  메인·서브 모두 최대 6.939e-18 m/s² 차이로 같은 수치 범위다.
- 모든 48회에서 cuDSS 내부 x와 wrapper의 a0는 bitwise 같았다. graph를 우회한 직접
  solve도 달랐으므로 scaled_copy나 graph capture **만으로** 설명할 수 없다. 고정 분해 객체의
  반복 solve 출력부터 비결정적이라는 관찰은 [NVIDIA의 기본 atomic/재현성 설명](https://docs.nvidia.com/cuda/archive/13.0.1/cudss/general.html#results-reproducibility)과
  부합한다. 내부 구현의 실제 atomic 지점이나 race·미초기화 부재를 증명한 것은 아니다.

즉 **원본 경로의 동일 GPU 비트 불일치는 확인됐고, 이 첫 오차 자체는 질량 방정식 잔차 기준으로
매우 작다.** 하지만 비선형·접촉·GMRES 수렴 경계에서 장기 증폭될 수 있으므로 wind의
첫 복구115/121 차이와 빈도, 물리적으로 허용 가능한 장기 궤적 차이, solver 안정성 문제는
아직 판정하지 않는다. 원래 solver 설정·물성·dt·허용오차는 바꾸지 않았다.

완료된 통제 시험은 기존 [CPU 동결 1프레임 진단기](diagnose_v10_frozen_cpu.sh)로 **동일한 메인
wind 표시115 시작 상태**를 양쪽 PC에 공급해 substep·Newton/GMRES·복구 판단을 대조했다.
이 입력은 메인 frame_0113.npz이며 SHA256
1d5663d129438fcb6c5fa9b866b191ace0a00a256fb094ba39ab6d39d2dcdba9다.
각 명령은 원본 run과 별도 UUID 출력의 한 프레임을 3 fresh process에서 수행한다.
원래 서브의 표시115 상태와 같은 시작 상태가 아니므로 원래 실패의 재현 시험은 아니다.
사용자 실행 결과와 한계는 아래 절에 기록했다.

~~~bash
# 메인컴 — workspace 루트
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer main --mode replay --case wind115 --repeats 3

# 서브컴 — 같은 공유 workspace 루트
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer sub --mode replay --case wind115 --repeats 3
~~~


## 공통 메인 wind115 상태 1프레임 결과

사용자 완료 실행: 메인 [3회 실행 목록](../../artifacts/runs/p3_self_contact/diagnostics/20260923T021112Z-0df6e023d1734eda88592da87c130dc9_main_wind115_replay/runs.json),
서브 공유 미러 [3회 실행 목록](../../artifacts/runs/sub_pc/20260923T021829Z-b82efa2a3bbb4a2f92b261504334a9e4_sub_wind115_replay/runs.json).
각 trial의 config/result, frozen host·GPU 업로드, 원시 event/substep/state를 읽었다.
이보다 늦게 생성된 메인 20260923T024620Z-438a66983cc54578b6cbfc3596439683 폴더는
빈 trial_00.log와 입력 사본만 있고 runs.json이 없으며 실행 프로세스도 보이지 않았다.
완료 분모에서 제외하고 삭제·덮어쓰지 않았다.

- 6/6 한 프레임 승인, 각각 기본 dt의 64 substep·dt/2 없음·실패 코드0·trace 완전.
  입력 frame-start SHA256 1d5663d1…, CPU NPZ c7427969…, v10 manifest f94f52dc…,
  plan/forcing/solver/contact 정책·host 기록·GPU 정적 업로드196개가 여섯 실행에서 같다.
  시작 원시 상태도 bitwise 같다. 별도 GPU 실행을 이 분석자가 수행하지 않았다.
- GMRES 프레임 합계는 메인 29,479/29,438/29,475, 서브 29,479/29,438/29,479.
  여섯 실행의 15쌍 중 12쌍은 substep0의 mass_solve_predictor 요약(event4)이 첫 차이이고,
  나머지 3쌍은 swept_query_end(event5)의 순서 지문이 첫 차이다(후자는 순서 무관 지문 동일).
  event0–3는 여섯 실행에서 같고, event4 요약이 같은 쌍의 원시 mass 해 bitwise 일치는
  이 계측으로 증명하지 못한다. 첫 substep 종료 원시 상태는 여섯 실행 모두
  bitwise 같지 않지만, 한 프레임 종료의 모든 쌍 최대 차이는 u_hi 1.11e-16 m,
  v_hi 6.86e-13 m/s다. GMRES substep 합계가 다른 쌍에서는 최초 차이가
  substep13 또는15이며, 일부 쌍은 64단계 합계가 모두 같다. Newton 종료 반복
  index·실패 코드·dt/2 결정은 모든 64 substep에서 같다.
- 접촉이 전혀 없는 시험은 아니다. event 전체에서 최대 활성 후보47·접촉력 요약 최대
  약0.028 N이며, 메인 trial00의 활성 후보는 substep13·58에 관측됐다.
  반면 원래 서브 실패 위치인 substep48 부근의 이 공통 상태 시험에서는 두 GPU 모두
  실패 코드0, substep47/48의 event별 GMRES 최대138/119였다. 원래 서브의
  표시115 실패 시도는 substep48에서 선형 반복720, 잔차 약0.0766 N 대 목표 약0.0363 N이었다.
  [원래 실패 코드·잔차 근거](cross_device_v10.md#dt2와-solver-안정성)를 따른다.
- 원래 두 run의 표시115 **직전** frame_0113.npz를 직접 대조하면 서브 입력은
  메인 입력과 u_hi 최대0.0040583 m, v_hi 최대2.39315 m/s 다르다.
  서브 원본 SHA256은 80b11379c8b1d78c7553317581447fdab1b03d90bc379509ac0ec482ded24bdc다.
  원래 메인 표시115는 기본64단계 승인·해당 프레임 GMRES29,478,
  원래 서브는 실패 뒤 dt/2 128단계 승인·GMRES30,917이었다.

**판정:** 공통 메인 시작 상태에서는 서로 다른 GPU여도 원래 서브의 dt/2를 재현하지 않았다.
장치 아키텍처만으로 동일 상태의 즉시 분기를 설명하는 근거는 없다. 원래 실행은 이미 크게
다른 궤적 상태에서 시작했고, 재생은 CPU 계수 동결·새 solver 프로세스·계측 경로이므로
차이의 주원인이 시작 상태인지, 원래 GPU/CPU 입력·숨은 상태 또는 계측 효과인지 아직
단독 확정할 수 없다. 무접촉·전체 wind 안정성의 승인으로 승계하지 않는다.

다음은 **원래 서브의 표시115 직전 checkpoint를 양쪽 GPU에 동일하게 공급**하는 반대 방향
통제 시험이다. 기존 wrapper에 sub_wind115를 추가했다. 메인에서는 서브 공유 미러,
서브에서는 원래 /mnt 결과를 읽되 같은 고정 SHA256이 아니면 GPU 계산 전에 거절한다.
출력은 매번 새 UUID이며 원래 run·물성·바람·dt·허용오차·solver 옵션은 변경하지 않는다.
수정한 wrapper SHA256은 f3782378163167a6cc71b4d9e06780c7d7e96b3b481ae5fda096fce9a9408db2다.
Bash 구문·도움말과 메인 공유 미러 입력 SHA를 GPU 계산 없이 확인했다.
각 컴퓨터에서 사용자가 실행한다; 이 서브 시작 상태 GPU 재생은 미완료다.
양쪽 모두 dt/2라면 시작 상태 의존성이, 장치별로 갈리면 같은 상태의 장치/실행 경로 차이가,
둘 다 기본 dt라면 원본의 비동결 CPU·숨은 실행 상태·계측 차이가 우선 후속 조사 대상이다.

~~~bash
# 메인컴 — workspace 루트
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer main --mode replay --case sub_wind115 --repeats 3

# 서브컴 — 같은 공유 workspace 루트
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_frozen_cpu.sh --computer sub --mode replay --case sub_wind115 --repeats 3
~~~

## cuDSS 결정성 설정 격리 시험

2026-09-23의 **설정만 바꾼 질량 풀이** 시험이다. 원본 v10 runtime/native/manifest와
CPU 동결 CSR·첫 RHS는 고정했다. `libcudss-dev` 0.7.1.4의 `cudss.h`에서
`CUDSS_CONFIG_DETERMINISTIC_MODE` enum 값25를 확인했다. 사용한 개발 헤더 패키지는
[conda-forge 0.7.1.4](https://conda.anaconda.org/conda-forge/linux-64/libcudss-dev-0.7.1.4-hee47b17_0.conda),
SHA256 `bd5d36f774e3e6615ed79c1748cdb59f43c09138f6937ffea6aa044c9d544850`이다.
진단 CLI의 선택형 `--cudss-deterministic`은 config 생성 직후 값1을 설정하고
`cudssConfigGet`으로 확인한다. 이 옵션은 **격리 진단에만** 적용된다. 원래 세 씬 실행
설정·물성·바람·dt·허용오차·solver 코드와 기존 결과는 변경하지 않았다.

메인 GTX1080Ti에서 [결정성 결과](../../artifacts/runs/p3_self_contact/diagnostics/20260923T062614Z-d737d61c58c641d8af3e4d77d3647b52_main_preload_mass_only_cudss_deterministic/summary.json)를
[기본 옵션 결과](../../artifacts/runs/p3_self_contact/diagnostics/20260923T013941Z-86c2bb4504f342d78cdc8112e0b36d3d_main_preload_mass_only/summary.json)와
비교했다. `inputs.json`의 동결 CPU·RHS·CSR·v10 manifest·원래 trial 설정 신원은
모두 동일하다. 기본 옵션의 각 process는 graph/direct 각4회 해시4개,
fresh process의 첫 해시3개였지만, 결정성 옵션의 2 fresh process × graph/direct 각4회
총16 solve는 같은 process·fresh process·graph/direct 모두 해시1개로 일치했다.
cuDSS 상태0, 내부 `x`와 출력 `a0`의 bitwise 일치, 상대 ∞잔차
`2.98031727996565e-16`도 확인했다. 설정 전후 `a0` 최대 절대차는
`1.3877787807814457e-17 m/s²`이다. 이는 반복 질량 풀이의 **비트 결정성 개선**이지
전체 프레임/장기 wind 승인이나 속도 향상 판정은 아니다. solve 시간은 공정한 동일 부하로
계측하지 않았다. [NVIDIA 재현성 설명](https://docs.nvidia.com/cuda/archive/13.0.1/cudss/general.html#results-reproducibility)에
따라 같은 아키텍처·SM 수에서만 bitwise 보장되며, GTX1080Ti와 RTX5070의 완전 동일성은
여전히 보장되지 않는다. 나머지 Warp atomic/GMRES·접촉 후보 경로도 이 시험 범위 밖이다.

사용자가 서브 RTX5070의 동일 설정 시험도 완료했다. [서브 미러 요약](../../artifacts/runs/sub_pc/20260923T063948Z-280dc863f21c4bc5ab788740bd758bc6_sub_preload_mass_only_cudss_deterministic/summary.json)과
두 trial의 `result.json`·`solutions.npz`를 읽기 전용으로 검산했다. 양쪽 `inputs.json`의
전체 identity와 driver SHA, 원본 v10 cuDSS source/native·workspace shim SHA,
CUDA Driver/Toolkit·Warp 버전은 같다. 기록된 GPU 필드 중 이름·아키텍처·SM 수가 다르다
(메인 sm61/28, 서브 sm120/48). 서브도 2 fresh process × graph/direct 각4회,
총16 solve가 상태0·설정 readback 성공·`x=a0` bitwise 일치·반복 및 graph/direct
해시1개였다. 양쪽 상대 ∞잔차는 모두 `2.98031727996565e-16`이다.

**장치 간 해는 bitwise 같지 않다.** 5,292개 가속도 성분 중126개가 다르고,
최대3 ULP, 최대 절대차 `5.204170427930421e-18 m/s²`, 해의 ∞norm 대비
최대차 `4.68136126776305e-16`이다. 즉 설정은 같은 GPU의 재실행 비결정성을
이 격리 풀이에서 제거했지만, 서로 다른 GPU의 완전 일치를 만들지 않았다.
이 질량 방정식의 잔차·차이 규모는 작다. 그러나 장기 비선형 궤적·GMRES 분기·dt/2 빈도,
다른 GPU 경로의 race/미초기화 여부까지 판정한 결과는 아니다. 원래 세 씬 실행과
체크포인트 재생은 수행하지 않았으며, 이 결과를 전체 시뮬레이션 승인으로 승계하지 않는다.

서브 시험 재현 명령은 아래와 같다. 기존 결과를 덮어쓰지 않고 새 UUID를 만든다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/diagnose_v10_mass_only.sh --computer sub --cudss-deterministic --repeats 2 --cycles 4
```

진단 driver SHA256은 `047f555218c564b5147831b798f9b2ec4b9436ee5c86e0609c63e10f9b597d18`,
wrapper SHA256은 `aed76b1333a68c2c2c812b0b4f7d60ef2bc527b24df0a71793a7ccce953a6877`이다.
`PYTHONPATH=code .venv/bin/python -m pytest -q code/tests/test_contact_mass_isolation.py`는
5/5 통과했고 Bash 구문 검사도 통과했다. 원래 v10 run에 이 옵션을 자동 적용하지 않는다.
