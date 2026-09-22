# 4배부터 실제 계산 속도 개선 검토

2026-09-11 사용자 선택: 무보정4배 → 행렬 재사용 → 필요하면 준뉴턴 → 통과 시32배·64배.
기존256배 전용 탐색은 보류한다. 물리식·허용오차·공력60Hz는 유지한다.
같은 구간의1배에도 같은 최적화를 적용해 순수 계산과 검산·저장 포함 시간을 분리 비교한다.
1배보다 느린 후보는 장기 실행에 채택하지 않으며 다른 방법/중단의 분기에서 사용자에게 질문한다.
본 실행 잔여7998초와2.5초 구간 방침은 변경하지 않는다. 개발 진단은 별도이며 장기 실행은 시작하지 않았다.

## 첫 시험

[probe_baseline.py](probe_baseline.py)는 저장된3.2666667초 상태에서1/960초 동안
Newmark1배(256분할 중16단계),4배(64분할 중4단계)를 순차 비교한다.
시작 상태는 `20260911_gauss256_stage4_v1/endpoint.npz`, 공력은
`20260911_target256_segments_v2/wind.npz`의196번 바람에서 처음 계산하고 고정한다.
이는 어려운 상태의 짧은 선별 시험이며 전체 바람 프레임·전체 궤적 정확도 판정이 아니다.
기존rest 보조 행렬은 이미 같은dt에서 재사용된다. 현재 변형 행렬의 재사용 효과는 미검증이다.
각 단계는 독립CPU 고정밀 힘 잔차·위치 갱신·연속 구간 기하·에너지 장부를 검사한다.
끝 상태 차이는 참해 오차가 아니며 참조 세분과 전체 곡선 검증은 별도로 필요하다.
원본코드와 실행probe는 출력의source.zip/probe.py로 동결한다.

```bash
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/acceleration4_20260911/probe_baseline.py experiments/artifacts/runs/teacher_timestep_search/20260911_acceleration4_baseline_v1
```

첫 선별 결과와 한계는 아래에 정리한다.

## 4배 선별 결과

지수 보정·준뉴턴 없이 현재 변형 보조 행렬을4회 선형 풀이마다 갱신한다.
실제 Newton 연산자·힘·선형 참 잔차·허용오차는 유지한다.
첫1/960초 구간은 기존rest 재사용에서1배23.946초/4배12.897초,
현재 변형 재사용에서1배24.163초/4배9.264초다. 서로 다른 시행의 개발 측정이다.
현재 변형 재사용은1배에서 가속하지 못했으므로 모든 배율에 유리하다고 주장하지 않는다.
같은 배율의 두 경로 끝점 최대 차이는 위치3.226e-18m, 속도2.628e-13m/s 이하.
이는 경로 비교이며 checkpoint 재시작 시험을 대체하지 않는다.
[기본 보고](baseline_report.json), [재사용 보고](reuse_report.json).

확장1/240초 구간의 현재 변형 재사용은0.5배184.788초,1배92.652초,4배34.009초다.
4배는 같은 최적화1배 대비 순수 계산2.724배 가속이다. setup·검산·저장은 이 시간에서 제외한다.
같은 GPU에서 순차 측정했지만 반복 benchmark·전체10초 속도 보장은 아니다.
0.5배 참조 대비 Newmark 전체 수치 보간의 consistent-mass norm 상한은
4배 속도0.582615%, 변위0.000217275%, 구간 변위 변화0.0190055%다.
1배→0.5배의 속도 차이 상한도0.268037% 남아 있어 참해 오차 인증으로 표현하지 않는다.
모든 단계의 독립 힘·갱신·연속 기하·에너지 장부 검산을 통과했다.
이는3.2666667초의 기존 저장 상태에서 시작한 국소 시험이며 rest부터4배로 도달한 궤적이 아니다.
2.5초·10초·해상도 수렴·R1 채택은 미완료다.

재현: 첫 명령의probe를 `probe_reuse.py` 또는 `probe_refined.py`로 바꾸고
각각 새 출력 `20260911_acceleration4_reuse_v1`, `20260911_acceleration4_refined_v1`을 사용한다.
`compare_curves.py 출력_경로 [참조_출력_경로]`는 기존 저장 상태의 수치 보간만 비교한다.
이차 위치 보간의 Bernstein 제어점 norm과 선형 속도 끝점 norm으로 상한을 구한다.
부동소수점 계산이며 interval arithmetic 또는 연속 ODE 인증은 아니다.

구현 검증: `PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s code/tests -p test_teacher_p3_shell_colored_preconditioner.py -v`의3개 검사 통과.

## 32배·64배 확장

같은1/240초 구간에서32배는2단계 중 두 번째 `line_search` 실패,
64배는1단계와 독립 검산 및 전체 수치 보간 비교를 통과했다.
64배 순수 계산10.7025초,0.5배 참조 대비 속도0.647209%, 변위0.00300853%,
구간 변위 변화0.263164%다. 같은 최적화1배 대비8.657배 속도이나 단1단계이므로
연속 궤적 성공/10초 소요 시간으로 외삽하지 않는다.
[확장 보고](expand_report.json), [전체 수치 보간 비교](expand_curve_comparison.json),
[4배·참조 보고](refined_report.json), [4배·참조 비교](refined_curve_comparison.json).

32배 실패는 선형 참 잔차 통과 후 발생했다. 마지막 Newton 수정은 약14.38m이며
line search 최소 비율에서도 힘 잔차가 줄지 않았다. 이는 비선형 풀이의 실패이며
물리적 불가능이나 실제 끝 상태의 발산을 증명하지 않는다.
행렬 재사용 원인 여부는 `probe_expand_fresh32.py`의 매번 재구축 대조로 확인한다.

확장은 `probe_expand.py`, 출력 `20260911_acceleration4_expand_v1`이다.
비교 명령의 두 번째 출력 인자로 `20260911_acceleration4_refined_v1`을 지정한다.
원본 계획/바람과 이전 실패 자료는 유지한다. 외부 fetch·다운로드는 수행하지 않았다.

매번 재구축 대조도 같은 두 번째 단계에서 `line_search` 실패했다
([대조 보고](fresh32_report.json)). 마지막 선형 참 잔차는 통과했으며 force residual은
허용값보다 크게 남았다. 재사용에만 기인한 실패는 지지되지 않는다.
준뉴턴은 아직 구현하지 않았다. 다음 분기는4배의 더 긴 구간 검증 우선 또는32배 비선형 풀이 보완이다.
사용자 선택 전 장기 실행·허용오차 변경·물리 감쇠 추가는 하지 않는다.
