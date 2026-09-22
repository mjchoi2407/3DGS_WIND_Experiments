# Adaptive Mixed32 세 장면 준비

## 현재 상태

- 확인 기준: 2026-09-20.
- `run_gpu_adaptive_mixed_scenes.sh`는 직사각형·손수건·삼각 깃발의 현행 adaptive 후보만 실행한다.
- 예전 FP64 hi/lo `newmark_dt_gauss_retry_bend500_v1`은 입력 동일성과 완료 구간 비교에만 재사용하며 새 baseline lane은 실행하지 않는다.
- 같은 굴힘1/500, mesh/P3/구적/물성/고정점/forcing을 유지하고 GPU별 Newmark M1/M2와 직접 Gauss R64/mixed32를 선택한다.
- 분기와 버린 시도 비용, 실제 정밀도, 반복량과 독립 검산을 프레임 기록에 남긴다.
- CPU prepare-only와 manifest/runtime namespace 검증은 통과했다. GTX1080Ti용 세 장면×세 phase는 `gpu_gtx1080ti_adaptive_integrator_bend500_v1`에 모두 `ready0`로 준비했다. 본 GPU 실행과 완료 비교는 사용자 실행 대기다.
- `production_enabled=false`, `training_eligible=false`를 유지했고 commit·push는 수행하지 않았다.
