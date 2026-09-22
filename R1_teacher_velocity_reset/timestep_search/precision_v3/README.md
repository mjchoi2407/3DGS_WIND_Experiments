# FP32 우선 v3 실행 준비

현재 상태: **[frame225 추가 최적화 분기 종료](fresh_branch_closeout.md)**. 운영 채택 보류이며 추가 계산을 진행하지 않는다.

2026-09-17 후속 [frame225 line search 진단](frozen_line_search_report.md)을 완료했다.
fresh는 λ=1 거부, λ=1/8 승인이나 비선형 잔차 감소가 작다. 운영 선택과 개발 종료 범위는 유지한다.

## 현재 진입점: 가속 개발 제한 종료

전체 FP32 및 새 solver 개발을 종료했다. 현재 사례별 후보는
[선택 manifest](selection_manifest.json), 제한 시험과 완료 쌍 집계는
[closeout 보고서](closeout_report.md)를 따른다. 생산 기본값·학습 적격성을 자동 승격하지 않는다.
5070 성공 환경과 현재 환경은 다르며 Graph 충돌 복구는 별도 작업이다.

추가 실행은1080Ti M1 W30 full/summary 각1회와 저장된 HL01 frame225의
R64/F64_fresh warm-up 후3회뿐이다. 아래 v3 전체 탐색 스크립트를 다시 돌릴 필요는 없다.
새 결과 폴더를 명시하는 재현 명령:

```bash
PYTHONPATH=code .venv/bin/python -u -m wind3dgs.evaluation.teacher_bounded_closeout \
  --source experiments/artifacts/runs/teacher_precision_v3/gtx1080ti_v3 \
  --out experiments/artifacts/runs/teacher_precision_v3/NEW_BOUNDED_RESULT

PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_bounded_closeout_report \
  --out experiments/artifacts/runs/teacher_precision_v3/NEW_BOUNDED_RESULT \
  --history experiments/artifacts/runs/teacher_precision_v3/completed_dual_gpu_20260916
```

실행은 로컬1080Ti 전용의 이번 제한 비교다. 원격 실행·환경 업그레이드·새 checkpoint 재생은 없다.
기존 result 폴더를 덮어쓰지 않는다. 실제 실행의 argv·wall·telemetry는 결과 폴더 `logs/`에 남긴다.

## 아래는 v3 초기 구현·재현 명세

2026-09-16. 사용자 요청에 따라 GPU 실행은 사용자가 담당한다. 현재는 최소 M1/M2 구현,
CPU 검사와 입력 준비까지다. 실제 GPU 수렴·Graph 실행·속도는 실행 후 판정한다.
기준 문서는 `ideas/development/codex_teacher_fp32_priority_v3_2026-09-16.md`와
`dual_gpu_v2_review_2026-09-16.md`다. v1/v2 원본과 생산 solver는 덮어쓰지 않는다.

## 두 PC 실행

workspace root에서 해당 PC의 스크립트 하나를 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_precision_v3_rtx5070.sh
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_precision_v3_gtx1080ti.sh
```

기본 결과는 각각 `experiments/artifacts/runs/teacher_precision_v3/rtx5070_v3/`,
`gtx1080ti_v3/`이며 같은 이름의 ZIP도 생성한다. 기존 경로가 있으면 덮어쓰지 않는다.
다시 실행할 때 `--out experiments/artifacts/runs/teacher_precision_v3/rtx5070_v3_repeat`처럼
새 경로를 지정한다. `--prepare-only --out NEW_PATH`는 GPU 계산 없이 입력/runtime/계약을 동결한다.
두 스크립트는 공통 코드이며 GPU 대상·기준 launch 설정만 다르다. 원격 실행·설치·clock 변경은 없다.
속도 비교 중 같은 GPU에서 다른 계산을 병렬 실행하지 않는 편이 적합하다.

취합:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_precision_v3 \
  --collect experiments/artifacts/runs/teacher_precision_v3/rtx5070_v3 \
            experiments/artifacts/runs/teacher_precision_v3/gtx1080ti_v3 \
  --out experiments/artifacts/runs/teacher_precision_v3/collected_v3
```

## 자동 실행 순서와 중단 범위

1. 기존 W1 checkpoint(바람 phase 1초, 절대 3초, forcing index60)를 복원한다.
   RTX5070 기준은32/32/256, GTX1080Ti는256/256/256이다.
2. FP64 W1 3프레임을3회 실행하고 실제 Newton 로그에서 사례를 선정한다.
   L1=GMRES 반복 최대, L2=나머지 중 원래 target 최소, L0=나머지 중 반복 중앙이다.
   각 사례를 원본 checkpoint에서 다시 재생해 지정 선형계 하나를 저장한다.
   snapshot에 있는 P64는 근사 전처리 행렬이며 원래 A64와 같다고 가정하지 않는다.
3. 먼저 L1에서 R64/M1/M2 및 같은 조립 알고리즘의 fresh P64를 비교한다.
   L1의 원래 목표를 통과한 mixed만 L0/L2로 진행한다.
4. M1과 M2가 모두 FP64 fallback을 요구하면 P32 문제를 분리하기 위한
   M2_P64 한 후보만 추가한다. 원래 P의 freshness는 그대로 두고 분해/apply를 FP64로 복원한다.
   다른 조합의 전수 sweep은 없다.
5. 세 고정 선형계를 통과한 후보만 C0 1프레임/W1 3프레임을 실행한다.
   그중 유망 후보 하나와 기준을 AB/BA 6쌍으로 비교한다. 원래256 FP64도 별도로3회 측정한다.
6. W1에서 모든 검산을 통과하고 median 시간 이득이 있는 경우에만 같은 checkpoint의
   원본 forcing index60부터30프레임으로 확장하여3쌍 비교한다.

수치 미수렴은 실험 결과다. subprocess 실행 오류가 같은 경로에서2회 연속 발생하면 그 경로를
중단하고 나머지 결과를 보존한다. 미구현·미측정·수치 실패를 혼동하지 않는다.
기존 물리 retry(Gauss 포함)는 변경하지 않는다. snapshot 선정용 FP64 W1에서 물리 retry가
발생하면 현재 trace의 절대 substep 대응을 확정할 수 없어 snapshot 이후 단계는 보류한다.

## 실제 정밀도와 원래 기준

- M1: FP64 상태/힘/A64/GMRES, FP32 P 분해·apply. 입출력 cast 포함.
- M2: FP32 HVP/mass/전처리/큰 Krylov 벡터, FP64 내적·norm·작은 Hessenberg/Givens,
  FP64 master 가속도 보정과 원래 A64 참 잔차. dot은 피연산자를 FP64로 올린 다음 곱한다.
- 원래 HVP는 `uh`만 사용한다. 힘의 `uh,lo`와 구분하며 HVP에 새로운 lo 미분을 추가하지 않는다.
  보정 force의 개선이 HVP에 모두 적용된다고 가정하지 않는다.
- inner 목표1e-2, 최대6회 correction, inner iteration cap은 min(120, 기존 cap)이다.
  이는 비용 제한이며 공식 Newton/EW/검산 허용오차가 아니다.
- RHS를 FP64 norm으로 나눠 low로 전달하고 보정을 같은 norm으로 역변환한다.
  행·열 equilibration은 이번 초기 후보에 추가하지 않았다.
- 정체(rho>=0.9 연속2회), 큰 증가(rho>=2), cap/비유한/low HVP status 오류는 FP64 fallback.
  fallback은 같은 A64,b64에서 x=0으로 재시작한다. 버린 inner·보정 비용을 시간/반복에 포함한다.
- 매 Newton의 성공은 원래 A64로 재계산한 참 잔차의 기존 EW 목표 통과다.
  master/비선형 승인/hi-lo 상태 갱신/독립 auditor는 FP64 원본이다.

`acceptance_contract.json`은 policy 값·원본 함수·source hash·norm·단위·상대항을 보존한다.
생산 기본값과 `training_eligible`은 변경하지 않는다. 새 궤적 회귀/교차 GPU 정확도 예산은 미정이다.

## 원시 결과와 타이머

- `runs/<run>/`: 실제 worker 결과, snapshot/audit NPZ, device 선형 로그, dtype/전략 카운터.
- `linear_systems/`: 선정 규칙, L0/L1/L2 snapshot·metadata·manifest. 별도 dense A는 만들지 않는다.
- `linear_summary.csv`: 원래 목표, factor/build 포함 비용, fallback 없는 mixed와 fallback 포함 성공.
- 각 frozen-linear worker의 `operator_errors.csv`: 실제 b/기준 해/Krylov/seed 방향에서 K/M/A 오차,
  입력 반올림과 나머지 state/geometry/산술 효과를 분리한다.
- `run_summary.csv`: solver+audit, setup, 저장/전송, process 전체.
  `validated_generation_s`는 solver+audit+상태 전송+NPZ 저장이며 진단용 force snapshot 평가와
  선형 trace JSON/프로파일러 시간을 제외한다. process wall에는 이러한 진단 비용도 포함된다.
- `phase_times.csv`: frozen-linear Graph20회 호출 실측과 실제 구간 전체 시간을 구분한다.
  isolated 비용을 W1 호출 비중으로 환산하지 않는다.
- `logs/`: telemetry, argv, 원문 오류. Nsight가 있으면 별도 node trace와 kernel CSV를 수집하며
  setup/compile이 포함된 process trace를 ordinary 구간 시간으로 보고하지 않는다.
- `report.md`: 성공 분류·실측 비교·미판정. 해당 GPU의 결과를 다른 GPU의 수치로 채우지 않는다.

두 PC가 독립 선정한 L0/L1/L2는 같다고 보장하지 않는다. 교차 취합의 상태 비교는 공통 W1이며,
원본/source/ids 대응을 확인하고 전처리 배열 차이도 별도로 보고한다. 공통 frozen-linear의
장치 간 직접 비교가 필요하면 동일 snapshot/모델 배열의 추가 재생 계약이 필요하다.

## 미검증과 조건부 후속

GPU 실행 전에는 M1/M2 수렴·가속·cuDSS/conditional Graph 호환성을 보증하지 않는다.
W1 세부 비용 귀속은 Nsight raw를 해석해야 하며 도구 부재 시 미측정으로 남는다.
HVP block 추가 후보, TwoProduct-FMA, predictor32, 더 긴 inner budget은 실측 근거 없이
자동 실행하지 않는다. M1이 성공하고 M2만 정체하는 경우 HVP/직교성 원인 분리는 후속 판정이다.
R1 teacher Gate와 정확도 기준은 유지한다.

CPU 준비 검증의 소스 hash와 범위는 [preparation_validation.json](preparation_validation.json)을 따른다.

## 고하중·과도응답 추가 (2026-09-16)

기존 두 GPU 실행 스크립트에 자동 포함된다. 새 강풍 sweep은 없다.
`high_load/selection.json`, `load_catalog.csv`가 선정 원본/범위/hash를 소유하고,
`high_load/summary.json`, `trajectory_differences.csv`가 실제 비교 판정을 소유한다.
실행 전 CPU 선정 근거는 `high_load_preparation/`에 보존했다.

조사 범위는 `newmark_dt_gauss_retry_bend500_v1`의 3형상×240 wind 프레임이다.
직사각형 41–79번(하중/과도)과 215–239번(풀이 난도/시간)이 선정됐다(0-based).
64/720프레임이 당시 계산 시간의 약25.3%를 차지한다. 이는 과거 측정 비중이며
새 GPU 실행 시간 예측이 아니다. 236번 최대 비용 프레임 뒤의 기록은 짧아
충분한 감소 후 응답 검증은 **미완료**다. 전체 생성 범위의 최대도 아니다.

선정 후보가 없거나 해당 창의 원래 A64 선형 목표를 통과하지 못하면 mixed 적분을
진행하지 않는다. 각 창은 우선1쌍 비교이며 별도의 W1 반복 통계와 섞지 않는다.
같은 시작 FP64 실패, mixed 실패, 보정 비용으로 가속 소실, FP64 복귀 포함 가속,
FP32 중심 통과를 구분한다. M1은 전처리만 FP32인 별도 분류다.
실패 직전 상태의 FP64 재실행은 별도 진단 비용으로 기록한다.

## W1_profile 오류 수정과 단독 재실행

기존 node trace는 두 GPU에서 CUDA 메모리 접근 오류가 발생했다. 새 경로는 Nsight NVTX와
GPU 내부 연산군 시간 계측을 사용한다. 노드별 kernel trace가 복구됐다고 부르지 않는다.
기존 실험·동결 runtime·실패 결과를 보존하고 추적만 별도 실행할 수 있다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/retry_teacher_v3_profile.sh \
  --run experiments/artifacts/runs/teacher_precision_v3/gtx1080ti_v3 \
  --out experiments/artifacts/runs/teacher_precision_v3/gtx1080ti_profile_retry
```

5070에서는 `--run`에 해당 PC의 기존 `rtx5070_v3` 결과 폴더를 넣는다. `--out`은 새 폴더여야 한다.
전체 실험을 다시 돌릴 필요가 없다. 일반 성능 측정과 동시에 실행하지 않는다.
앞으로 새로 준비하는 두 v3 스크립트에는 수정 경로가 자동 포함된다. 이미 진행 중인 프로세스와
동결 runtime에는 소급 적용하지 않는다.

실측 근거: `experiments/artifacts/runs/teacher_precision_v3/profile_repair_20260916/final/report.md`.
1080 Ti에서 원래 독립 검산, .nsys-rep/NVTX CSV와 device_phase_times.csv 생성을 확인했다.
계측 연산군 중 preconditioner apply가 가장 컸다. 세부 시간/위치·속도·힘 차이는 원본
`role_totals.csv`, `measurement_summary.json`, `state_differences.csv`가 소유한다.
5070 수정 경로는 아직 미실행이다. 생산 설정/학습 적격성은 변경하지 않았다.

## 완료 데이터 취합

2026-09-16 사용자 요청으로 메인 HL01 mixed를 종료하고 두 PC의 완료 시험만 묶었다.
Canonical 산출물은 `experiments/artifacts/runs/teacher_precision_v3/completed_dual_gpu_20260916.zip`이다.
같은 이름의 폴더에서 report.md, GPU별 summary.json/excluded_runs.json과 manifest를 확인한다.
원본은 보존하고 미완료 시뮬레이션 배열은 제외했다. 실패 이력·미판정은 유지한다.

512MB 업로드 제한용 무손실 압축본은 같은 경로의
`completed_dual_gpu_20260916_compact.zip`이다. 동일 파일 중복 저장을 제거하고 큰 JSON에는
ZIP LZMA를 사용한다. 업로드는 ZIP 하나로 가능하며, 분석 시 내부 `COMPACT_README.md`와
`restore_completed_v3.py`를 따라 원래 구조를 복원한다. SHA-256 기준 원본 파일 바이트는 같다.
표준 Python 3.11 이상으로 복원할 수 있으며 일부 기본 ZIP 뷰어는 LZMA를 지원하지 않을 수 있다.

## 고부하 연산별 FP64/FP32 비용 진단

[사용자 실행 스크립트·입력 범위](highload_fixed_work.md). 기존 전체 FP32 개발 재개 없이 동결 연산을 고정 작업량으로 비교한다. GPU 측정 대기.

[추가 FP32/M2 첫 substep 비교](extended_precision_probe.md): 별도 사용자 실행, 기존 운영 선택 보존, 단계별 시간 출력.

[Gauss 전용 FP32 우선/FP64 묶음 복구 비교](gauss_precision_frame_probe.md): 표시190/194/200의
같은 시작 상태에서 Newmark 없이 Gauss512단계를 실행한다. 실제 GPU 측정 대기이며 기존 선택은 유지한다.
