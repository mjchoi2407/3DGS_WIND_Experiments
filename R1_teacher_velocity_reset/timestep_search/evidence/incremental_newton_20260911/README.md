# Newton 위치 수정 누적과 저장 실패 상태 검증

## 현재 상태

2026-09-11. 기존 물리식·float64 상태·허용오차를 유지하면서 Newton 내부 위치 갱신을
수정했다. 큰 초기 변위에서 매번 위치를 재구성하는 대신 가속도와 위치의 수정량을 함께
누적한다. 원래 Newmark 갱신식과의 차이가 반올림 범위와 위치 허용치 안인지도 검사한다.
적용 대상은 CPU 반복 풀이 및 이를 공유하는 Warp/HVP graph 경로다. 미채택 CuPy 풀이는 변경하지 않았다.

**부분 개선이다.** 세 저장 실패 step은 기존 잔차 기준을 통과했지만, sub016은 후속 구간에서
다시 `line_search`로 정체했다. 10초 전체 안정성·시간 정확도·추천 Δt는 미확정이다.

| 분할 수 | 검증 시작(s) | 마지막 완료 시간(s) | 완료 interval | 후속 판정 |
|---|---:|---:|---:|---|
| 64 | 2.64765625 | 2.68333333 | 137 | 지정 구간 통과 |
| 16 | 2.63333333 | 2.66875000 | 34 | 다음 step 실패 |
| 4 | 2.62500000 | 2.66666667 | 10 | 지정 구간 통과 |

완료한 181 interval은 모두 별도 CPU 원식·기하 검산을 통과했다. 후속 실패 하나를 이 분모에
포함해 성공으로 세지 않는다. 조건별 종료 시간이 다르므로 두 통과 후보의 장기 안정성 우열도 판정하지 않는다.
CPU 검산의 최대 힘 잔차 비는 0.9997223, 위치 갱신 최대 오차는 1.11023e-16 m였다.
[최종 요약](summary.json), [sub016 실패 시도](sub016_result.json),
[CPU 27개·CUDA 3개 회귀 검사](tests.json)를 연결한다.

sub016의 새 실패는 frame160/substep2다. 잔차 1.10022e-10 N, 허용치 1.06005e-10 N,
위치 수정 norm 4.55232e-16 m로 정체했다. 같은 지점에서 Kahan 형태의 보정 합산을
시험했으나 역시 실패했다. 이 후보는 생산 코드에 넣지 않았다.
[보정 합산 시험 결과](compensated_result.json)는 기준 완화 없이 남은 한계를 확인하는 근거다.

## 원인 분해

sub064 실패의 마지막 실제 Newton 방향을 추출해 비교했다.

- 의도한 위치 수정 norm은 4.41686e-16 m지만, 기존 상태 재구성 후 실제 변화는
  1.15176e-15 m였다. 두 변화의 차이를 의도한 수정 norm으로 나누면 1.7884다.
- 같은 저장 위치의 힘을 확장 정밀도로 재계산했을 때 GPU 힘과의 차이는 4.28798e-12 N이었다.
  같은 가속도가 나타내는 위치를 확장 정밀도로 유지했을 때 생기는 힘 차이는 1.28011e-10 N으로 더 컸다.
- 실제 수정 방향에서 확장 정밀도 힘 차분과 HVP의 상대 차이는 4.57290e-4였다.
  앞선 임의 방향 진단보다 이번 실패의 수정 방향에 직접 연결되는 근거다.

이 환경의 `np.longdouble`은 저장 형식이 128 bit여도 가수는 숨은 비트를 포함해 64 bit다.
형상/재료 계수는 기존 float64 값을 승격한 것이므로 정확한 실수 해석해가 아니다.
단순히 중간 계산만 확장 정밀도로 바꾸고 다시 float64 위치로 반올림하는 것으로는
세 실패를 모두 해결하지 못했다. 확장 정밀도 경로는 진단에만 사용하며 새 dependency는 없다.

[분해 결과](precision_split.json), [진단 상태 identity](diagnostic_state_identity.json),
[시작 시점 대비 코드·회귀 검사 diff](implementation.patch).

## 검증 조건

원본: `experiments/artifacts/runs/teacher_timestep_search/ten_second_v1`.
새 진단: `experiments/artifacts/runs/teacher_timestep_search/20260911_incremental_newton_v1`.

- 원래 실패 frame의 성공 prefix 마지막 상태에서 같은 분할 수로 시작한다.
  첫 frame의 힘은 원래 frame 시작 상태에서 평가하고, 이후에는 새 frame 시작 상태에서 60 Hz로 갱신한다.
- 후보마다 실패 frame의 남은 부분과 다음 두 frame까지만 계산한다. 실패나 검산 미달 시 해당 후보를 멈춘다.
  Rest부터 새 방법으로 수행한 전체 후보의 성공으로 처리하지 않는다.
- 모든 새 interval의 저장 u/v에서 CPU 힘·가속도를 재계산한다. 기존 원식 검산과 같은
  잔차 비 ≤1.001, 위치 갱신 최대 오차 ≤2e-14 m, 에너지 장부 허용치와 Bernstein 기하 조건을 적용한다.
  Solver 자체의 힘 잔차 기준은 ≤1이다. 고정 외력을 두 평가 경로에서 동일하게 사용한다.
- 결과 NPZ와 상세 JSON은 새 진단 폴더에 둔다. Source 30파일과 hash는 그 폴더의
  `source.zip`/`source_manifest.json`으로 동결했다. 새 manufactured-endpoint 검사는
  이 source manifest에 포함되지 않으므로 위 diff와 별도 검사 기록으로 식별한다.
- GPU는 기존 작업과 공유했다. 실행 시간은 속도 벤치마크로 사용하지 않는다.

## 재현

Workspace root에서 시작한다. 새 출력 폴더만 허용하며 원본 실행을 수정하지 않는다.
동일 결과 재현에는 위 source ZIP을 별도 경로에 풀어 그 경로를 `PYTHONPATH`로 사용한다.
현재 코드를 검증하는 명령은 다음과 같다.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
WARP_CACHE_PATH=code/outputs/warp-cache PYTHONPATH=code \
.venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/incremental_newton_20260911/validate_incremental.py \
experiments/artifacts/runs/teacher_timestep_search/새로운_단기검증_폴더
```

`capture_newton.py`는 명시적으로 기존 `ten_second_v1/runtime/code`를 `PYTHONPATH`로 지정해
실행한다. 그 결과 `/tmp/wind3dgs_newton_state.npz`를 같은 동결 소스를 사용하는
`precision_split.py`가 읽는다. 두 파일은 진단용 임시 출력이며 보존본 identity는 위에 연결했다.

## 채택 경계

이 보완은 실패 근처의 수치 풀이 개선이며 정밀도 문제의 완결 해법은 아니다.
사용자는 기존 허용오차를 유지하는 고정밀 상태 검토를 선택했으며,
[후속 효과·비용 검토](../highprecision_state_20260911/README.md)를 완료했다.
저장 정밀도/schema와 GPU 경로의 정식 반영은 별도 작업으로 남는다.
sub001의 GMRES 한도와 sub256의 운영 시간 제한,
4배 바람의 공간 속도 수렴 미달은 별도 미완료다. 원래 동결 source와 실패를 보존한다.
10초 재탐색은 수정 source를 새 출력에 동결하고 rest부터 수행해야 한다.
R1 전체 채택·학습데이터 발행·30fps 검증은 이번 결과로 올리지 않는다.
