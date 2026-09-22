# Newmark 절반 dt 복구로 세 씬 실행

2026-09-18 사용자 요청으로 기존 절반 dt 복구를 GPU 자동 선택 경로에 연결했다.
기존 Gauss8 복구와 별도 실행이며, 현재 실행/보존 결과/허용오차를 변경하지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_auto_half_retry_scenes.sh
# 한 씬만 실행할 때 추가: --shape reference_rectangle / handkerchief / triangular_flag
```

- 기존 세 씬의 굽힘1/500,중력2초→동일 처짐 상태에서 무풍4초·바람4초 분기를 유지한다.
- 기본 단계:Newmark64분할(dt=1/3840초),GPU/구간별 기존 M1/M2/R64 선택.
- 기존 복구 가능 조건(유한 값·검산 통과 prefix·수렴/line-search 실패 코드)에 해당할 때만
  실패한 기본 구간 직전 승인 상태에서 FP64 Newmark dt=1/7680초를 두 번 수행한다.
- 두 half 모두 기존 독립 검산을 통과하면 기본 dt로 돌아간다.
- half 실패 시 추가1/4dt나 Gauss로 넘어가지 않고 프레임 시작 상태로 복원하여 실패 처리한다.
- M1/M2 선형 fallback은 원래대로 유지한다. half solver는 R64로 고정해 혼합 정밀도를 상속하지 않는다.
- 실제 성공한 단계의 dt와 검산,half_dt_retries를 기존 형식으로 기록한다. 실패 시도 비용도 포함한다.

기본 출력:
`experiments/artifacts/runs/teacher_timestep_search/gpu_<GPU>_auto_half_bend500_v1`.
1080Ti의 세 씬은 ready0으로 준비했다. 긴 본 실행은 시작하지 않았다.
5070은 기존 driver/Graph 환경 보호 규칙을 그대로 따른다. 환경 장애를 해결한 옵션이 아니다.
`--prepare-only --out <새 경로>`, `--status-only`를 지원한다.
R64 대조가 필요하면 같은 스크립트에 `--policy baseline`을 붙인다(별도 baseline 출력).

검증 원본: `experiments/artifacts/runs/teacher_timestep_search/gpu_half_retry_check_20260918/`.
작은 메시의 check_v3에서 M1 정상 경로의 기존 독립 검산, 실패 주입 후 승인 prefix 복원/FP64 half2,
half 실패 시 추가 세분화 금지·프레임 시작점 복원을 확인했다(종료 코드0).
이는 제어 경로 검사이며 실제 고하중 수렴·세 씬 속도 향상 검증이 아니다.
최초 check는 R64와 M1을 순수 경로 동등성 허용치로 비교해 실패했고,
check_v2는 두 M1 반복에도 같은 동등성 검사를 적용해 실패했다.
check_v3는 해당 동등성을 승인 기준으로 사용하지 않고 반복 차이를 관측값으로 기록했다.
원래 solver/audit 허용오차는 유지했다. 위치 hi/lo·속도 hi/lo의 반복 차이 최대는 각각
3.25e-17/1.60e-24/2.50e-13/6.32e-21이며 승인된 회귀 예산으로 해석하지 않는다.
생산/학습 적격성과 기존 Gauss 시험 결과는 자동 승격/대체하지 않는다.

후속 [half2 후 Gauss8 국소 비교](../cascade_retry/report.md)는 별도 개발 경로다. 이 half 전용 스크립트와 기존 Gauss 기본은 변경하지 않았다.
