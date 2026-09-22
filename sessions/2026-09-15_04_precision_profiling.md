# Teacher 성능 진단 사용자 실행 준비

## 현재 상태

- 2026-09-15. 사용자 RTX 5070 서브컴에서 직접 실행한다. 본 시뮬레이션은 시작/변경하지 않았다.
- [전용 스크립트/사용법](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/teacher_precision_profiling.md).
- 기본: 기존 직사각형1/500 preload checkpoint → wind 첫1프레임을 독립3회, 별도 Nsight Systems.
- 원본 `precision_profile_20260915_v1`은 실제 GTX 1080 Ti 확인으로 `blocked_device`; solver 반복0회/미측정.
- Nsight 두 도구 버전/환경 원문 및 hash 동결 근거를 결과에 보존했다. 기존 sub_pc 결과를 이번 측정으로 사용하지 않았다.
- 후속 스크립트는 새 timestamp 폴더에 raw CSV·검산/상태·정밀도·코드 대응·재현 명령을 기록한다.
- Systems 뒤 상위 최대3개 커널 NCU를 자동 시도하며 각 첫 호출1개로 제한한다. GPU 미실행·CPU 검사3개 통과. FP64/FP32 고정 작업량 비교만 후속 미구현이다.
- R1 계약 확인, 수식/판정/검증 근거 변화가 없으므로 TeX/PDF 변경 없음. 커밋/푸시 없음.
