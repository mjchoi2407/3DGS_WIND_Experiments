# 과거 작업 목록

당시 결과와 미완료 상태를 보존한 목록이다. 현행 상태는 [최신 요약](README.md)을 먼저 읽는다.

- [2026-09-09 변화 바람·속도 초기화 비교](2026-09-09_02_teacher_velocity_reset.md): Native 고정 폭 실패와 P3 해결 경로. P3 최종36 trace의 완전 재실행·19 window/76 patch sample 생성·원본 검증 완료.
- [2026-09-09 Teacher 누적 실험·데이터 checkpoint](2026-09-09_01_teacher_checkpoint.md): 현재 진입점. 전체 계보, 논문용 연구 기록, 개발 sample/P3 판정과 Git 보존 범위.
- [2026-09-08 공간 수렴 보완](2026-09-08_07_teacher_spatial_remediation.md): 원래 stencil 내부 힘 결함 재현, P2/P3/독립 판 비교와 네 run 재현. P3 처방 압력 조건의 공간/방향/기준 1% 통과, 원래 x² 초기 속도 실패 유지.
- [2026-09-08 Teacher 개발용 샘플 데이터](2026-09-08_06_teacher_sample_dataset.md): 3개 시계열·15 window, 원본 대조·CPU replay·batch loading 검증 완료. 본 학습용 적격성 false와 데이터/그래프 보존.
- [2026-09-08 Shell 선형 공간 응답](2026-09-08_05_teacher_shell_linear_spatial.md): 두 run의 각 92,169 frame·전체 검산 완료. 공간·방향 기준 실패, numerical/source 검사 통과와 evidence 보존.
- [2026-09-08 Shell 한 주기 전체 시간 refinement](2026-09-08_04_teacher_shell_full_refinement.md): 원본·독립 재실행의 각 143,360 step·전체 검산 완료. Full 속도 차이 6.05976% → 2.97472% → 0.868281%, 기준 통과와 compact evidence 보존.
- [2026-09-08 Shell 가속도 Newmark 짧은 구간 시간 refinement](2026-09-08_03_teacher_shell_refinement.md): 원본·독립 재실행의 새 3,072 step 완료. 공통 시각의 short 속도 차이 2.20620% → 0.612308% → 0.154044%로 감소해 기준 통과, full refinement는 미실행이다.
- [2026-09-08 Shell Newmark 가속도 변수 정밀도 회귀](2026-09-08_02_teacher_shell_precision.md): 기존 step 5 실패 재현과 후보 3,457 step 완료. 정밀도 회귀 통과, short 응답 2.20620%·full 단일 대조 11.7491% 실패와 원본·벡터 검산 기록.
- [2026-09-08 Shell 모드·독립 시간 기준·시간 해상도 진단](2026-09-08_01_teacher_shell_temporal.md): 독립 기준 자체 대조 통과, full 응답 실패·short 미완료와 5번째 step의 line search 실패를 보존했다. 관련 131개 검사와 원본 재검산, compact evidence를 기록한다.
- [2026-09-07 CPU shell 동역학 기준 solver](2026-09-07_06_teacher_shell_dynamics.md): 19개 rollout·2,105 step, 독립 재실행·상태 재검산 일치와 수치 계약 통과. 비선형 속도 시간 대조 실패, XY/Z 분해와 원본·compact evidence 보존.
- [2026-09-07 3D shell 구조 연산자](2026-09-07_05_teacher_shell_structure.md): 네 CPU run의 1,200개 사례. 회전·미분·선형 극한 통과, 총에너지 오차 상쇄/인공 막 에너지와 실패 상태, 재계산·evidence 보존.
- [2026-09-07 곡률 기반 선형 판 기준 모델](2026-09-07_04_teacher_plate_reference.md): 두 CPU run의 408개 사례, 방향·영모드·일반 변형 진단 통과와 재계산·compact evidence 보존.
- [2026-09-07 Teacher bending 매핑 검사](2026-09-07_03_teacher_bending_mapping.md): 기본 변형 112개, 두 대각선의 방향 편향, 해석식/정밀도 검사와 compact evidence.
- [2026-09-07 Teacher bending 감사](2026-09-07_02_teacher_bending_audit.md): native bending 에너지의 mesh 의존성, 해석식 대조와 compact evidence.
- [2026-09-07 Teacher GPU 검사 결과 보존](2026-09-07_01_teacher_gpu_check_review.md): 사용자 GPU 12/12단계 통과, 원본 연결 재계산, 수렴 미확정과 compact evidence.
