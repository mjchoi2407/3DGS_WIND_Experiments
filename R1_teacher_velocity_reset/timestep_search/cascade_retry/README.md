# Newmark → half2 → Gauss8 국소 비교

2026-09-18 사용자 승인 범위: 저장된 고부하 프레임만 비교한다. 전체 시뮬레이션·생산 기본값은 변경하지 않는다.
[결과 보고서](report.md)의 완료 범위와 수치 차이를 먼저 확인한다.

- A: 기존 Newmark → 수렴 실패한 기본 구간만 FP64 Gauss6차8분할.
- B: Newmark → FP64 Newmark half2 → 수렴 실패하면 같은 기본 구간 시작점에서 FP64 Gauss6차8분할.
- 실패한 half의 부분 성공 상태/검산은 진단으로 보존하되 채택 궤적에서 제외한다.
- 비유한 값이나 독립 검산 오류는 다음 적분기로 우회하지 않는다. 최종 실패는 프레임 시작 상태로 복원한다.
- 기본 Newmark의 GPU별 정밀도 선택, 공식 수치 기준·외력·물성·검산·기존 P 갱신 알고리즘은 유지한다.

재현(새 출력 경로 필요):

```bash
PYTHONPATH=code .venv/bin/python -u code/scripts/compare_cascade_retry.py \
  --out experiments/artifacts/runs/teacher_timestep_search/cascade_retry_samples_NEW
PYTHONPATH=code .venv/bin/python code/scripts/analyze_cascade_retry.py \
  experiments/artifacts/runs/teacher_timestep_search/cascade_retry_samples_NEW --mass-metrics
```

기본 두 반복은 A/B 뒤 B/A 순서이며 GPU 작업은 순차 실행한다. 각 프레임 시작 raw hi/lo와 원본 forcing index를 복원하고 전처리기를 동일한 새 초기화 조건에서 시작한다. 이전 프레임의 factor cache를 재현한 장기 replay는 아니다.

실측 원본 canonical 경로:
`experiments/artifacts/runs/teacher_timestep_search/cascade_retry_samples_20260918/`.
`cases.json`에 입력 선정 근거·hash, `execution.json`에 실제 worker 명령·process wall,
`runs/*/result.json`과 `result.npz`에 모든 시도/검산/상태를 저장한다.
`frames.csv`/`attempts.csv`/`pairs.csv`/`repeat_differences.json`은 집계다.
`runtime_scenes`는 GPU별 기존 M1/M2 연결을 포함한 동결 코드와 manifest를 보존한다.
이는 5070 환경 장애를 해결한 실행이 아니며 미실행 장치 성능을 추정하지 않는다.

[후속 wind120→200 복원 스크립트](resume120.md): 사용자 승인 후 준비 완료, 매 프레임 저장 및 명시적 재개. 본 실행은 사용자 시작 대기다.

[wind182–200 실측 결과](window182_200_results.md):38회 검산 통과, half438회 성공. 전체 가속은 작고 정책 간 속도 차이가 커 기본 채택 보류.
