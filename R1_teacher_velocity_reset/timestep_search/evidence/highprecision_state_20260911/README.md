# 고정밀 상태 표현의 효과·비용 검토

## 현재 상태

2026-09-11. 사용자 선택에 따라 기존 허용오차를 유지하는 별도 시험본을 검토했다.
**남아 있던 sub016 실패 지점부터 8 step을 통과했고, 고정밀 상태의 저장·재시작 일치도 확인했다.**
기존 저장 schema나 정식 계산 경로에 고정밀 표현을 반영한 것은 아니다.

| 확인 항목 | 결과 |
|---|---|
| 구간 | frame160/substep2–9, 2.66875–2.67708333초 |
| 고정밀 저장 상태에서 재계산한 최대 힘 잔차/허용치 | 0.00049336 (허용치의 약 0.0493%) |
| 같은 결과를 float64 u/v로 내린 뒤 기존 식으로 재계산 | 8개 모두 미달, 잔차 비 1.00246–1.45980 |
| 고정밀 위치 갱신 최대 오차 | 2.71051e-20 m |
| hi/lo 저장 후 한 step 재시작 | 위치·속도·시간이 연속 실행과 정확히 일치 |

뉴턴 위치 수정 누적의 [앞선 부분 개선](../incremental_newton_20260911/README.md)에서
남았던 실패를 재사용했다. 모든 상태는 같은 기존 고정 외력을 사용한다. 새로운 바람 조건이나
허용오차 완화를 도입하지 않았다. Solver 수렴과 저장 상태의 운동방정식·위치 갱신을 확인했으며,
전체 기하/에너지 인증·전체 시간 수렴·10초 안정성·다른 후보의 보장은 아니다.

## 원인과 구현 경계

별도 Python 프로세스 안에서만 `ShellState`의 u/v와 기하·힘 계산을 `np.longdouble`로
유지했다. 현 플랫폼에서는 숨은 비트를 포함한 가수 64 bit로, IEEE binary128의 가수 113 bit가 아니다.
기존 float64 형상/재료 계수를 승격했으며 새로운 고정밀 해석해나 새 물리 모델이 아니다.
GMRES와 GPU HVP는 float64로 유지하고, CPU 선형 풀이 입력은 명시적으로 float64로 변환한다.
힘·질량 잔차는 확장 정밀도로 계산한다. 실제 정책 값은 [원본 report](report.json)에 있다.

힘 평가만 개선하고 마지막에 기존 float64 상태로 내보내면 원식 잔차가 다시 기준을 넘었다.
따라서 이 시험의 정확도를 보존하려면 저장과 재시작까지 작은 자릿수를 유지해야 한다.
진단 NPZ는 longdouble의 padding byte를 직접 저장하는 대신 `u_hi/u_lo/v_hi/v_lo`의
float64 쌍으로 저장했다. 확장 정밀도로 두 부분을 더하면 모든 저장 상태가 정확히 복원된다.
이는 **시험용 표현이며 canonical raw schema로 채택하지 않았다.**

## 비용

같은 초기 상태의 힘 평가를 준비 호출 후 경로별로 3회 순차 측정했다.

- 기존 GPU float64: 평균 0.004204초/회.
- CPU 확장 정밀도: 평균 0.523757초/회, 약 124.58배.
- 상태 행렬 payload: 기존 float64 3,058,992 byte → hi/lo 6,117,984 byte로 2배.
  이는 이 시험의 u/v payload이며 압축 파일·전체 실행 저장량의 배율이 아니다.

외부 GPU 부하를 통제하지 않은 짧은 측정이다. 전체 solver 실행 시간의 배율이나 GPU 고정밀
구현의 비용을 뜻하지 않는다. CPU 고정밀 force를 그대로 긴 실행에 채택하기에는 비용이 크다.
후속 설계에서는 고정밀 상태를 보존하는 GPU 힘 평가 또는 필요한 연산만 정밀도를 높이는 경로를
검토해야 한다. 이번 CPU 시험만으로 그러한 경로의 정확도·속도를 보장하지 않는다.

## 원본과 재현

Raw: `experiments/artifacts/runs/teacher_timestep_search/20260911_highprecision_state_v2`.
`report.json`, `states_hi_lo.npz`, `source.zip`, `restart_check.json`을 보존했다.
[요약](summary.json), [재시작 검산](restart_check.json), [입력·출력·스크립트 identity](identity.json).
동결 source ZIP의 Python 파일 hash는 report의 `source_sha256`과 대조했다.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
WARP_CACHE_PATH=code/outputs/warp-cache PYTHONPATH=code \
.venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/highprecision_state_20260911/probe_state.py \
experiments/artifacts/runs/teacher_timestep_search/새로운_고정밀_진단_폴더

PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
WARP_CACHE_PATH=code/outputs/warp-cache PYTHONPATH=code \
.venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/highprecision_state_20260911/replay_state.py
```

동일 numerical source 재현에는 ZIP을 별도 경로에 풀고 그 경로를 `PYTHONPATH`로 지정한다.
첫 스크립트는 새 출력 폴더만 허용한다. 두 번째는 보존된 v2를 읽어 결과를 표준 출력으로
내보낸다. 원실행의 재시작 결과 저장 코드는 재현 스크립트에서 제거해 기존 결과를 덮어쓰지 않는다.
원본 첫 시험 v1은 SuperLU dtype 연결 오류로 물리 step을 완료하지 못했으며 별도 보존했다.

## 다음 단계

효과·비용 검토는 완료했다. 정식 반영은 고정밀 상태의 저장·재시작·원식 검산 계약,
GPU 계산 경로와 영향 범위의 추가 검증을 함께 설계하는 별도 작업이다.
현재 code의 직접 누적 보완은 부분 개선으로 유지하며 10초 추천·R1 채택·학습 발행은 보류다.
