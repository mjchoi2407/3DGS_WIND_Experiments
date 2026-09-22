# 고부하 FP64/FP32 고정 작업량 비교 준비

## 현재 상태

2026-09-20. 메인1080Ti 사용자 실행 완료·로컬 저장 결과 분석 완료. 5070 자체 추출 표본 대조 완료. 내부 snapshot 비일치와 전처리 차이는 별도 기록.
- 완료된182–200 저장 상태 중 표시200/194/190 선정. 첫 substep의 Newton 표본이며 전체 최대 선형계 아님.
- 두 GPU가 동일한 추출 snapshot을 공유할 수 있도록 --samples 옵션 제공.
- block256 공통 대조, 기존 low 경로·Graph·출력/오류·변환 비용 분리. 새 solver/정책 변경 없음.
- CPU 테스트2개와 실제 동결 입력 준비 통과. 원본/진행 실행 보존, 생산/학습 승격 없음.
- [명령과 산출물 정의](../R1_teacher_velocity_reset/timestep_search/precision_v3/highload_fixed_work.md).

- 실측: P 분해/풀이 약1.5배, A약1.3배, 벡터 우위 미확정. P32 출력 상대 차이75–101%로 정확도와 속도 분리.
- [원본 분석](../artifacts/runs/teacher_precision_v3/highload_fixed_20260920T012954/analysis.md), 같은 폴더 report/raw/NPZ 및 P_residual_analysis.csv. P 잔차는 Newton A 잔차가 아니다.

- 5070 P 분해2.53배/풀이2.16배/A약4배. FP32 A의 장치 간 차이는약5.9배로 혼합 경로 격차 확대 근거. 큰 P 출력 차이는 양쪽 유사, 원인 미확정.
- [교차 분석·원시 시간/입력 차이](../artifacts/runs/sub_pc/20260919T163801Z-7d44413e89d241a79f20000466abcc21/benchmark/cross_gpu_analysis.md). 전체 M1/M2 성능을 합성하지 않는다.
