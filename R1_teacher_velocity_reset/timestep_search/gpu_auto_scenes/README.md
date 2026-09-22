# GPU 자동 선택으로 기존 세 씬 비교

2026-09-18 추가 실행: [Newmark 절반 dt 복구](half_retry.md). 아래는 기존 Gauss 복구 실행이다.

2026-09-17 사용자 요청으로 동결된 M1/M2/R64 선택을 새 실행 진입점에 연결했다.
기존 `newmark_dt_gauss_retry_bend500_v1` 결과와 스크립트는 보존한다.
새 수치 알고리즘이나 F64_fresh 개발을 재개하지 않는다.

## 실행

Workspace root에서 다음 명령을 사용한다. 두 PC에서 같은 스크립트를 쓰며 cuda:0의 실제 GPU를 탐지한다.

```bash
# 세 씬 순차 실행: 직사각형, 손수건, 삼각 깃발
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_auto_scenes.sh

# 한 씬만 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_auto_scenes.sh --shape reference_rectangle
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_auto_scenes.sh --shape handkerchief
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_auto_scenes.sh --shape triangular_flag

# 같은 PC에서 새 R64 대조 실행; 가속 실행과 동시에 돌리지 않는다.
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_baseline_scenes.sh
```

기본 출력은 `experiments/artifacts/runs/teacher_timestep_search/gpu_<GPU>_<policy>_bend500_v1`이다.
GPU는 `gtx1080ti`, `rtx5070`, 미등록이면 `unknown`; policy는 `auto` 또는 `baseline`이다.
`--out`으로 별도 경로를 지정할 수 있다. 준비만 하려면 `--prepare-only`, 상태는 `--status-only`를 붙인다.
GPU 없는 준비에는 `--out`도 지정한다. 실행 중인/중단된/실패한 결과는 자동 재개하지 않는다.
완료된 phase는 보존하고 건너뛴다. 동일 GPU의 씬을 동시에 실행하면 속도 비교가 오염된다.

## 자동 선택과 범위

| GPU / 구간 | 선형 방법 | volume/interior/boundary block |
|---|---|---|
| GTX1080Ti 일반 바람 | M1 | 256/256/256 |
| GTX1080Ti 직사각형 wind index 215–239 (기존 HL01) | R64 | 256/256/256 |
| RTX5070 일반 바람 | M2 | 32/32/256 |
| 양쪽 중력 준비·무풍, 미등록 GPU, `baseline` | R64 | 256/256/256 |

무풍 계열은 보수적으로 R64를 유지한다. 이 index 예외를 다른 forcing에 적용하지 않도록
원본 세 씬의 config/plan/inputs SHA-256을 실행 준비 시 확인한다.
M1은 기존 FP32 보조 행렬 분해/apply, M2는 기존 FP32 내부 선형 풀이와 FP64 보정이다.
FP64 hi/lo 상태, 원래 A64 참 잔차, 비선형 힘/line search, 독립 검산과 Gauss6 retry는 유지한다.
M1/M2 내부 FP64 fallback 비용도 계산 시간에 포함된다.
프레임 경계의 M1→R64 전환은 현재 네 hi/lo 배열을 그대로 넘기고 Graph를 다시 생성한다.
전환 준비·전송·종료 저장은 process wall에 포함하며, 준비 비용을 별도 기록한다.

**5070 Graph 장애는 미해결이다.** 과거 성공은 driver API13000이며 이후 API13040에서 충돌했다.
5070에서 API가13000과 다르면 계산 전에 실행을 보류한다. API13000 일치만으로 장기 안정성을
보증하지 않는다. 드라이버/라이브러리 변경이나 자동 환경 복구는 하지 않는다.
이번 로컬 검증은1080Ti이며 5070 신규 실행은 미측정이다.

## 동일하게 유지하는 씬

굽힘1/500, 기존 mesh/P3/구적/물성/고정점,60fps, Newmark64분할(dt=1/3840초),
실패한 기본 구간의 Gauss6차8분할 복구를 유지한다.
중력2초(120프레임) 후 같은 preload 상태에서 무풍4초와 바람4초(각240프레임)를 분기한다.
중력·바람 ramp 각각60프레임, 저장120프레임을 유지한다. 총600프레임/씬이다.
원본 inputs를 byte 단위 복사하며 `reference_inputs.json`과 manifest에 대응 hash를 남긴다.
물리식·허용오차·dt/retry 정책·독립 검산을 바꾸지 않았다.

## 완료 후 비교

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_gpu_scene_compare \
  --baseline experiments/artifacts/runs/teacher_timestep_search/newmark_dt_gauss_retry_bend500_v1 \
  --candidate experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_auto_bend500_v1 \
  --out experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_auto_comparison_v1.json
```

5070은 candidate의 GPU 이름을 바꾼다. 새 R64 대조는 baseline을 `gpu_<GPU>_baseline_bend500_v1`로 바꾼다.
완료된 동일 phase/입력/프레임끼리만 비교한다. solver+audit와 외부 process wall 가속률을 분리하며,
과거 결과에 process wall이 없으면 비워 둔다. 다른 GPU는 cross_gpu로 표시한다.
저장된 모든 프레임의 위치/속도 성분 최대 차이와 preload checkpoint 일치 여부를 함께 보고한다.
과거 실행과의 시간 비교는 환경·동시 부하가 통제된 반복 벤치마크가 아니다.

새 세 씬 실행은 작은 프레임 요약/혼합 반복·fallback 수와 기존 필수 상태·audit chunk를 저장한다.
큰 frozen-linear trace를 생성하는 v3 진단 harness와 구분하며, 기존 v3의 `full/summary` 옵션은 그대로 보존한다.
`mixed_counts` 순서는 linear_calls, corrections, inner_iterations, stagnation_or_budget,
fallback_calls, fallback_iterations다. 초기/전환 Graph와 실제 force launch 설정을 report에 기록한다.
생산 인증과 학습 적격성은 자동 승격하지 않는다(`production_enabled=false`, `training_eligible=false`).
세 씬 전체에서의 가속·장기 정확도는 사용자 본 실행 후 판정한다.

## 제한 검증

- CPU 정책 검사:1080Ti HL01 진입/이탈 경계, 무풍 R64,5070 환경 차단, 미등록 GPU 안전 경로 통과.
- 손수건 preload/calm/wind 각1프레임: R64/R64/M1 선택 및 기존 독립 검산 통과. M1 선형 호출160회, FP64 fallback0회.
- 동일 R64 smoke와 저장 상태 차이: [원시 비교](../../../artifacts/runs/teacher_timestep_search/gpu_auto_smoke_comparison_20260917.json).
  서로 독립적으로 계산한 preload의 반올림 차이도 포함한다. GPU 동시 부하가 있어 가속률 근거로 쓰지 않는다.
- smoke 원본: `experiments/artifacts/runs/teacher_timestep_search/gpu_auto_smoke_20260917_v1`,
  `gpu_baseline_smoke_20260917_v1`. 본600프레임/씬은 미실행이다.

- 최종 직사각형·삼각 깃발 smoke도 각3단계 독립 검산 통과. 원본은 `gpu_auto_smoke_20260917_v2`이며
  [검증 요약](validation.json)에 각 run 경로·방법·fallback 수를 보존했다.
- 두 GPU의 기본 auto 출력 경로에 각각 세 씬을 ready0으로 준비했다. 기존 범용 이름의 준비 폴더는
  초기 연결 확인본이며, 본 실행 canonical 경로는 위 `gpu_<GPU>_auto_bend500_v1`이다.

후속 [공통 경로 성능 진단](../launcher_diagnostic/README.md): 과거 지연은 재현되지 않았다.
M1 정밀도나 부모 CUDA context로 원인을 확정하지 않는다. 짧은 동일 바람3쌍의 M1 가속만 별도 관측했다.

[후속 half2→Gauss8 표본 비교](../cascade_retry/report.md): 일부 시간 감소와 큰 끝 속도 차이를 분리하며 기존 실행 기본값은 유지한다.
