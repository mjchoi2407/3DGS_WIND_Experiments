# 두 GPU launch 비교 사용자 실행 준비

## 현재 상태

- 2026-09-16. [실행/취합 명령](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/dual_gpu_launch.md).
- 현재 풀이 유지. 두 PC의 source/input을 공유하되 환경별 설정/측정/출력은 분리한다.
- 사용자가 실행하므로 서브컴 원격 실행과 로컬 GPU 계산을 하지 않았다. 가속률/최적 block 미측정.
- prepare-only 원본 `artifacts/runs/teacher_timestep_search/dual_gpu_preparation_20260916_v1.zip`은 입력/코드 동결 및 ZIP 경로 검증이며 GPU 결과가 아니다.
- 후속 스크립트에 선택적 isolated NCU/취합을 연결했다. Pascal은 NCU를 생략하고 설치/환경 변경을 하지 않는다.
- 캐시/선정 CPU 검사7개 통과, GPU 회귀는 미검증. 원본 시뮬레이션 결과와 사용자 dirty 파일은 보존했다.
- 구현/검증 문서만 추가했다. 연구 Gate·R1 정확도 계약 불변, TeX/PDF 변경 및 커밋/푸시 없음.
