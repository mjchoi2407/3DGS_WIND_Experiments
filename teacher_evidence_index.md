# Teacher 실험 근거 목록

각 실험 당시의 결과 목록이다. 현행 진행 상태는 [최신 요약](sessions/README.md)을 먼저 확인한다.

- [P3 작은 굽힘의 검증된 sample](R1_teacher_velocity_reset/p3_samples/README.md): 새 고정 폭/바람/reset의 공간·시간·독립 기준 및 전체 배열 재실행 통과. 19 window/76 patch sample의 원본·NumPy batch 검증 완료. 큰 변형/R1 전체는 미완료.
- [고정 폭 굽힘·시간 보완·실패 원인](R1_teacher_velocity_reset/clamped_samples/README.md): Native 굽힘 격자 의존성을 확인해 이 source의 sample 발행을 보류했다. 사용자가 선택한 P3 후속 범위에서 해결했으며 native 실패 자체는 보존한다.
- [변화 바람·도달 형상 속도 초기화](R1_teacher_velocity_reset/README.md): rest 원본과 동일 미래 바람의 reset 분기 비교, 재생·공력·개입 에너지 및 mesh/time 개발 진단. 본 학습용 적격성은 false다.
- [Teacher 공간 수렴 보완](R1_teacher_spatial_remediation/README.md): 내부 힘 결함 재현과 P2/P3/독립 판 비교. P3 처방 압력 조건은 연속 시간 상한을 포함해 공간·방향·독립 기준 1% 통과. 99개 검사와 네 run 재현 확인, 원래 x² 초기 속도 실패와 비선형/실제 공력 미검증 유지.
- [Teacher 개발용 샘플 데이터](R1_teacher_sample_dataset/README.md): 3개 시계열·15 window 생성·검증 완료. 원본 대조·세 CPU replay·batch loading 통과, 데이터 위치·읽기 예제·그래프 제공. 본 학습용 채택은 false다.
- [Shell 선형 공간 응답 검사](R1_teacher_shell_linear_spatial/README.md): 관련 228개 검사·두 run의 각 92,169 frame 및 검산 완료. 공간 속도 차이 22.7–23.2%, 방향 최대 51.5%로 물리 기준은 실패했다.
- [Shell 한 주기 전체 시간 refinement](R1_teacher_shell_full_refinement/README.md): 관련 184개 검사와 두 run의 각 143,360 step·전체 상태·반복 검산 완료. 속도 차이 6.05976% → 2.97472% → 0.868281%로 full 응답 통과, 공간·공력 등 R1 전체 검증은 남아 있다.
- [Shell 가속도 Newmark 짧은 구간 시간 refinement](R1_teacher_shell_refinement/README.md): 관련 171개 검사와 원본·독립 재실행의 새 3,072 step 완료. Short 속도 차이 2.20620% → 0.612308% → 0.154044%로 기준 통과, full/공간 수렴과 학습 Teacher 채택은 후속 검증이다.
- [Shell Newmark 가속도 변수 정밀도 회귀](R1_teacher_shell_precision/README.md): 관련 155개 검사와 기존 실패 재현, 후보 3,457 step의 정밀도 회귀 통과. Short finest 속도 차이 2.20620%, full 단일 대조 11.7491%로 시간 해상도 검증은 계속 필요하다.
- [Shell 모드·독립 시간 기준·시간 해상도 진단](R1_teacher_shell_temporal/README.md): 관련 131개 검사 통과, 독립 DOP853 기준 자체 대조 통과. Full N=2560 속도 차이 11.7491%, short N=5120은 5.50795%이며 N=10240의 5번째 line search가 실패했다. 시간 오차·위치 차분 정밀도를 후속 검토하며 학습 Teacher는 미확정이다.
- [CPU shell 동역학 기준 solver](R1_teacher_shell_dynamics/README.md): 관련 106개 검사와 수치 계약 통과, 19개 rollout·2,105 step 및 독립 재실행 일치. 비선형 속도의 시간 대조는 실패했으며 빠른 XY 응답의 시간 해상도를 후속 검증한다. 학습 Teacher는 미확정이다.
- [3D shell 구조 연산자](R1_teacher_shell_structure/README.md): E·ν·h 네 조합, 1,200개 사례와 관련 82개 테스트. 회전·미분·선형 극한 통과, h=0.01의 일부 총에너지 오차 감소 조건 실패와 얇은 재질의 인공 막 에너지를 보존했다. 동역학 연결 전 적용 범위 검토가 필요하다.
- [곡률 기반 선형 판 기준 모델](R1_teacher_plate_reference/README.md): ν=0/0.3의 408개 사례 계산 완료. 방향·영모드·일반 변형 개발 진단 통과. 동역학 Teacher 연결과 물리 수렴은 후속 단계다.
- [Teacher bending 매핑 검사](R1_teacher_bending_mapping/README.md): 기본 변형 112개 계산 완료. 면적 가중 후보의 방향 반례, 수치 오차 분리와 실행 로그를 보존했다. 후보의 방향 검사는 실패다.
- [Teacher bending mesh 감사](R1_teacher_bending_audit/README.md): 같은 변형의 mesh 4/8/16/32 에너지와 해석식 대조. 고정 native 계수의 mesh 의존성을 확인했으며 물성 보정은 후속 설계다.
- [R1 Teacher GPU smoke](R1_teacher_smoke/README.md): 2026-09-07 사용자 GTX 1080 Ti 실행 12/12단계 통과와 compact evidence. 공간·시간 수렴은 `not_assessed`이며 학습 dataset은 아직 발행하지 않았다.
- 누적 구현과 다음 작업: [code 누적 checkpoint](../code/sessions/2026-09-09_01_teacher_checkpoint.md).

`R1_teacher_smoke/`는 현재 Teacher 개발 경로의 지원 검증 기록이다. R1 전체 완료나 새로운 acceptance 기준을 뜻하지 않는다.

