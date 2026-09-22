# Gauss 전용 혼합 정밀도 프레임 비교

## 현재 상태

- 확인 기준: 2026-09-20. 수정 후 GTX1080Ti 저부하1개·고부하3개를 완료했다.
- `GAUSS_R64`와 `GAUSS_MIXED32_FALLBACK64`를 같은 한 프레임 조건에서 순차 실행한다.
- 혼합 solver/독립 검산 실패 묶음만 FP64 Gauss로 재계산하며 버린 혼합 비용도 포함한다.
- 결과는 새 timestamp 폴더에 저장하고 원본 고부하 결과와 진행 중 실행은 수정하지 않는다.
- Newmark M2용 low namespace의 FP64 Gauss 커널이 FP32 pair 함수와 결합된 runtime 구성 오류로 확정했다. FP32 수렴 실패로 해석하지 않는다.
- 검산된 기존 Gauss FP32 low package를 manifest hash로 확인해 새 runtime에 복제하고, 완료 R64 lane만 새 timestamp 폴더에 검증·재사용하도록 수정했다.
- 네 조건 모두 512/512단계와 독립 검산을 통과했고 FP64 복구는 0개였다. 끝 상태 최대 차이는 위치1.40e-16m, 속도1.64e-12m/s, 힘8.83e-13N이며 모든 flag가 0이었다.
- 혼합은 저부하에서 R64보다 3.59% 느렸다. 고부하3프레임 합계는 2.66% 빨랐지만 개별 결과가 -4.47~+7.87%로 혼재했고 GMRES가 8.97% 늘어 기본 채택 근거는 부족하다.
- 저부하 직접 Gauss는 선행 Newmark보다 현저히 느렸고, 고부하 직접 Gauss는 선행 Newmark+반복 복구보다 크게 짧았다. Newmark 저부하+고부하 직접 Gauss 전환을 후속 방향으로 보존한다.
- Graph 자식 커널의 역할 분류가 되지 않아 항목별 속도 판정은 미완료다. 생산 기본값과 학습 적격성은 변경하지 않았다.
- RTX5070 고부하3프레임도 전부 통과/복구0이다. 합계는 R64 98.676초, 혼합76.145초로 혼합이22.83% 짧았고 GTX1080Ti 대비 각각1.521배·1.919배 빨랐다.
- 두 장치의 입력/plan/runtime hash가 일치하고 R64 GMRES/rebuild도 동일하다. 교차 끝 상태 최대 차이는 위치1.12e-15m, 속도2.21e-12m/s, 힘1.13e-12N이다. 정확도 budget은 미정이다.
- 동결3프레임 성능 후보는 RTX5070 혼합 FP32 우선, GTX1080Ti R64 Gauss다.
- RTX5070 프리로드도 두 lane 모두 512/512단계·검산 통과·복구0이다. R64 24.389초, 혼합20.994초로 혼합이13.92% 짧았고, GTX1080Ti 대비 각각1.359배·1.636배 빨랐다.
- 프리로드 동일 lane의 장치 간 끝 상태 최대 차이는 위치2.25e-17m, 속도1.40e-12m/s, 힘8.23e-13N이다. 정확도 budget은 미정이다.
- RTX5070 혼합 Gauss도 선행 GTX1080Ti Newmark 참고값보다11.50배 느리며 장치·harness가 달라 paired 비교는 아니다. 저부하 Newmark 유지와 고부하 직접 Gauss 전환 방향은 바뀌지 않는다.
- 후속으로 평면 rest·중력 ramp 첫 프레임 저부하 입력 한 개를 같은 두 lane에 연결했다. 고부하 결과 폴더와 분리한다.
- [실행 명령과 결과 형식](../R1_teacher_velocity_reset/timestep_search/precision_v3/gauss_precision_frame_probe.md).
