# 두 GPU v2 사용자 실행

2026-09-16: 후속 지시서와 review를 반영한 실행 준비. GPU 측정은 사용자가 실행한다.
v1 결과와 생산 기본값은 보존한다. `training_eligible`은 변경하지 않는다.

workspace root에서 각 PC에 해당하는 명령 하나를 실행한다. 기존 출력 폴더는 덮어쓰지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_dual_gpu_v2.sh --gpu-profile gtx1080ti --worker-id gtx1080ti --out experiments/artifacts/runs/teacher_timestep_search/dual_gpu_gtx1080ti_v2
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_dual_gpu_v2.sh --gpu-profile rtx5070 --worker-id rtx5070 --out experiments/artifacts/runs/teacher_timestep_search/dual_gpu_rtx5070_v2
```

두 번째 PC에서도 같은 공유 코드와 입력 파일을 사용한다. 원격 실행·환경 변경은 없다.
GPU 이름이 선택과 다르면 오류를 기록하고 중단한다. 동시에 같은 GPU에 다른 계산을 실행하지 않는 것이 측정에 적합하다. 다른 프로세스를 자동 종료하지 않는다.
입력 준비만 확인하려면 새 출력 경로와 `--prepare-only`를 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_dual_gpu_v2.sh --collect experiments/artifacts/runs/teacher_timestep_search/dual_gpu_gtx1080ti_v2 experiments/artifacts/runs/teacher_timestep_search/dual_gpu_rtx5070_v2 --out experiments/artifacts/runs/teacher_timestep_search/dual_gpu_collected_v2
```

- C0: v1의 preload 완료 상태, 무풍 첫 1프레임. 5070은 3쌍, 1080 Ti는 6쌍.
- W1: 완료된 `newmark_dt_gauss_retry_bend500_v1/reference_rectangle`의 wind `chunks/0000.npz` 60번 저장 상태. phase 1초, preload 포함 3초, 다음 forcing index 60부터 연속 3프레임. 두 장치 모두 6쌍. 1080 Ti 변동성이 크면 W1 수치는 남기되 성능 승리를 주장하지 않는다.
- A=256/256/256, B=5070 32/32/256 또는 1080 Ti 64/64/64. 쌍 순서는 AB/BA 교대. 매 run은 동일 checkpoint로 새 process를 만들며 warmup은 별도 결과다.
- FP32는 legacy와 기존 `stable_metric_pair` 보정 후보만 사용한다. 후자는 기존 stable_strain_report의 근거가 있는 개발 후보이며 canonical teacher 채택을 뜻하지 않는다.
- 각 사례·블록·정밀도별 eager와 20회 호출 단일 Graph를 별도 실행한다. 각각 5회 측정하며 mode 간 표본을 섞지 않는다. full assembly의 zero/copy/assembly/checks는 포함한다.
- 실제 원시값은 `workers/<worker>/`가 canonical이다. `cases/*/preparation_metadata/`는 준비 helper의 빈 표이며 측정 결과가 아니다.
- 결과는 `corrected_report.md`, 원시 CSV/NPZ, telemetry JSONL, 실제 명령 로그, 소스/입력 hash와 별도 ZIP에 남긴다. timing의 Gauss solver/audit 분리는 기존 구조에서 불가능하면 combined로 보존한다.
- 정확 일치는 관측값이다. 독립 검산/성능/Graph/회귀 예산/생산 승격을 분리한다. 회귀 예산은 `budget_not_defined`, 비교 누락은 `incomplete`다. 승인 profile 부재로 실제 cache hit는 미검증이며 fixture를 생산 profile로 발행하지 않는다.
- 교차 비교는 실제 ids/shape 대응과 원본/source hash를 먼저 확인한다. G/H/weights 차이는 배열별 정량값으로 남긴다. 새 교차 장치 허용오차를 만들지 않는다.

준비 검증: CPU 단위 테스트와 W1 checkpoint/forcing/물리 시각 검증, Python·shell 문법 확인. GPU Graph capture/실행·가속률은 사용자 실행 전 미검증이다. profiler 설치/추가 실행은 이 v2 wrapper에 포함하지 않는다.
