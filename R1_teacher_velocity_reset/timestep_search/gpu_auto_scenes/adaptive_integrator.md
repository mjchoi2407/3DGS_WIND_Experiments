# GPU별 Newmark→Gauss adaptive 세 씬 실행

2026-09-20 선택을 별도 run으로 검증한다. 기존 FP64 hi/lo
`newmark_dt_gauss_retry_bend500_v1` 결과를 대조로 재사용하므로 baseline을 다시 계산하지 않는다.
기존 결과와 `run_gpu_auto_scenes.sh`의 이전 정책은 수정하지 않는다.
이 wrapper가 새로 실행하는 lane은 현행 adaptive 후보 하나뿐이며, FP64 baseline lane은 없다.

## 실행

```bash
# 직사각형→손수건→삼각 깃발 순차 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_adaptive_mixed_scenes.sh

# 한 씬만 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_adaptive_mixed_scenes.sh --shape reference_rectangle
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_adaptive_mixed_scenes.sh --shape handkerchief
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_adaptive_mixed_scenes.sh --shape triangular_flag

# 준비와 상태 확인
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_adaptive_mixed_scenes.sh --prepare-only
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_adaptive_mixed_scenes.sh --status-only
```

기본 출력은
`experiments/artifacts/runs/teacher_timestep_search/gpu_<GPU>_adaptive_integrator_bend500_v1`이다.
같은 GPU에서 씬을 병렬 실행하지 않는다. 중단·실패 결과는 자동 재개하지 않으며 새 `--out`으로 다시
실행한다. GTX1080Ti와 RTX5070은 같은 스크립트를 사용한다.

## 고정 조건과 분기

- 기존 굽힘1/500, 세 mesh/P3/구적/물성/고정점과 forcing hash를 유지한다.
- 중력2초 후 같은 checkpoint에서 무풍4초와 바람4초를 분기한다.
- Newmark64분할 `dt=1/3840`초, 직접 Gauss6차512분할 `dt=1/30720`초다.
- 첫16 Newmark substep의 복구 가능한 실패3회와 실측 잔여 비용 조건을 모두 만족할 때만 프레임
  시작 상태로 복원하여 전체 Gauss로 다시 계산한다.
- GTX1080Ti 직접 Gauss는 R64, RTX5070은 mixed32다. 바람 Newmark는 각각 M1/M2이고 저부하는 R64다.
- FP64 hi/lo master, 공식 허용오차, FP64 참 잔차, line search와 독립 검산은 유지한다.
- 버린 Newmark/복구 비용, 분기 추정값, 선택 정밀도와 실제 반복량을 `frame_timings.jsonl`에 남긴다.

## 완료 후 기존 FP64 hi/lo 결과와 비교

GPU별 새 결과 경로를 `--candidate`에 지정한다.

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_gpu_scene_compare \
  --baseline experiments/artifacts/runs/teacher_timestep_search/newmark_dt_gauss_retry_bend500_v1 \
  --candidate experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_adaptive_integrator_bend500_v1 \
  --out experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_adaptive_integrator_comparison_v1.json
```

RTX5070에서는 candidate와 출력 이름만 해당 GPU 경로로 바꾼다. 비교기는 물리 입력과 plan hash가
같은 완료 phase만 계산하며, 실행 정책 필드는 물리 입력 동일성 판정에서 분리한다. 속도·상태 차이는
승인된 학습 오차 예산이 아니며 생산 기본값과 학습 적격성을 자동 변경하지 않는다.
