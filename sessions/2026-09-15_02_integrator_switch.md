# Newmark/Gauss 전환의 실제 프레임 비교

## 현재 상태

- **실제 옛 기하 실패5건 재계산 완료:** 실패 직전1substep에서 Newmark/Gauss 모두 투영 경고 재현, Gauss로 해결0/5건. 둘 다 현행 국소·물리 검산은 통과. 현재 국소 인증 실패의 해결률/시간 정확도는 미검증. [원본·범위·결과](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/logged_geometry_retry.md).

- **후속 기하 전용 시험 완료:** 같은 두 국소 입력의4회 선택 모두 Newmark 단일 계산/검산 통과.128분할 감시 없음. 프리로드1~2초 범위 재확인; 시간 정확도 개선은 아님. 실제 기하 경고 해결률/장기 teacher 채택은 미완료. [설정·수치·검증](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/geometry_switch_trial.md).

- 후속 사용자 확인: 추가128분할 시간 오차 감시를 제외하고 기하 flag16 단독 때만 재계산하는 별도 `geometry` 시험으로 전환했다. 다른 물리/솔버 실패는 그대로 실패하며 기본 생성기/teacher 기준은 유지한다.

- 확인 기준: 2026-09-15. 직사각형1/500의 초기 처짐/바람 저장 상태에서 Newmark64 우선·128분할 감시·Gauss 재계산과 Gauss 단독을 교대로 비교했다. 모두 FP64 hi/lo이며 기존 결과는 보존했다.
- 원래 물리 검산은 통과했지만 시간 분할 차이로 모든 실제 전환 시험이 Gauss를 선택했다. 원상 복원은 Gauss 단독과의 끝점/궤적 및 원시 시작 쌍으로 확인했다.
- 초기 처짐은 추가 감시 비용으로 느려졌다. 바람은 반복 수가 같아도 시간이 크게 흔들려 고정 배속을 확정하지 않는다. 다른 타이머/장치의 수치를 섞지 않았다.
- 임계값 민감도는 저장 지표의 사후 분석이다. 작은 절대 차이를 허용한 학습데이터 생성/연속 실행을 승인하거나 완료한 것이 아니다.
- 선행 시간 지표 시험의 미완료 항목은 정확도 예산과 다른 시점의 저차 채택 가능성 판단이다. 기본값·장기 안정성·teacher 적격성·Gate는 유지한다.
- [소유 보고서와 compact evidence](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/integrator_switch_trial.md)가 설정·전체 수치·분모·원본/hash와 명령을 소유한다.
- main에서 순차 계산했고 sub_pc 기존 결과는 조회만 했다. 원격 fetch/download 없음. experiments worktree 변경만 있으며 stage·커밋·푸시 없음.
