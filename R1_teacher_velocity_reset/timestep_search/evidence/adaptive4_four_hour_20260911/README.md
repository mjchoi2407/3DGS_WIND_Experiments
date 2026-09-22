# 4배 전환 방식: 10초 본 실행의 새4시간 계획

## 현재 상태

2026-09-11 사용자 정정에 따라4시간은 새 설정의10초 본 실행 전체에 적용한다.
이전 실패 실행과 개발·검증 시간을 차감한 해석을 폐기했다.
새v2를 초기 상태·누적 사용0초로 동결 준비했으며 본 실행은 시작하지 않았다.
[계획](plan.json), [검증](checks.json), [코드 동결](runtime_manifest.json).

- 최종10초,60Hz,600frame. 4배 타임스텝=1/(60×64)초.
- rest 우선, 반복32회 이상이면 다음step부터current. current 보조 행렬4회마다 갱신.
- 기존 물리·허용오차 유지. [방법 검증](../adaptive4_20260911/README.md).
- 2.5/5/7.5/10초에서 정지. 구간별 판정 후 같은 명령으로 이어간다.
- 본 실행 전체의 누적 준비·계산·원식 검산·저장 등 활성 시간 한도14,400초.
- 각2.5초 구간마다4시간으로 초기화하지 않는다. 이전 별도 실행의 비용은 합산하지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_adaptive4_segments.sh
```

출력: `experiments/artifacts/runs/teacher_timestep_search/20260911_adaptive4_segments_v2`.
준비 확인은 `--prepare-only`, 상태 조회는 `--status-only`를 붙인다.
이번에는 위 두 확인 명령만 실행했다. 시뮬레이션worker·GPU 계산은 실행하지 않았다.

## 검증과 보존

shell 문법, 동결runtime hash, 계획 검증,150/300/450/600frame 구간,
새 누적 예산0초와trial 없음, 기존v1 plan/runtime/search/status 불변을 확인했다.
실행기 코드 변경은 없으며 새 수치 시험을 실행하지 않았다.
2.5초·10초·공간 수렴 완료나 시간 정확도 통과를 새로 선언하지 않는다.
이전v1 계획과 결과는 보존한다. [이전wrapper 원본](previous_wrapper_v1.sh),
[이전v1 확인hash](previous_identity.json)은 잘못 차감했던 준비 상태의 재현 근거다.
이전 기록의 잔여7368초/7998초는 이번v2에 적용하지 않는다.
외부fetch·다운로드·commit·push는 수행하지 않았다.
