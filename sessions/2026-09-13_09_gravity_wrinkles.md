# 중력·굽힘 비교 실험 인계

## 현재 상태

- 2026-09-14 정확도 후속: Newmark16/32세분화1프레임 및128/256세분화의 짧은 기준 독립검산 통과. 순간 속도 시간수렴은 큰 구간에서 미달. 기존6차Gauss8분할이 원래1substep 끝에서 fine256기준0.15% 차이이나 독립Gauss검산/전체정확도/성능은 미완료다. 기본 설정·학습label 변경 없음. [정확도·비용·한계](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/bend500_accuracy.md).

- 2026-09-14 후속: 1/500 실패 프레임을 별도 GPU 진단으로 재현했다. GMRES720회 초과, 갱신16/반복1440은 실패. dt절반은3프레임384단계 독립검산 통과지만 더 작은dt와 속도 차이가 커 시간 수렴/teacher 적격은 미판정. 원본·기본 설정 변경 없이 진단 후보로만 기록한다.

- 확인일2026-09-14. 기본 FP64 hi/lo·중력2초→자체 상태에서 무풍4초/바람4초·384삼각형 깃발을 사용한다. 자세한 설정은 [실행 문서](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_wrinkles.md).
- 손수건1/100 완료 결과는 [이전 분석](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_wrinkles_results.md)에 보존한다. 사용자가 깃발을 의도했으므로 기본 대상을 수정했다.
- 깃발1/100: 본38400단계 경고0·재생 확인. 중력 하강0.132mm로 가시적 처짐 준비는 달성하지 못했고 바람에는 큰 접힘이 나타났다. [결과](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_flag_results.md).
- 깃발1/300: 본38400단계 경고0·재생 확인. 중력/무풍은1/100과 실질적으로 같고 바람 궤적은 달라졌다. 사용자는 자연스러워졌다고 평가했으나 잔주름 정량 개선·자기 교차는 미판정. [결과](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_bend300_results.md).
- 깃발1/500: 준비/외력 동일 검증 후 사용자가 실행. 확인 시 중력·무풍 완료, 바람 실행 중. 본 전체 검산/재생/비교는 아직 미완료. [설정](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_bend500.md).
- 최초 하이브리드 비교: hybrid preload완료·calm interrupted120, wind/현재 lane 미실행. 사용자가 직접 종료했으며 추가 비교·재개 보류. 양쪽 완주 가속률 없음. [비교 계약](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_speed_compare.md).
- 다음은1/500 결과 확인 후 굽힘을 고정한 별도 셀프컬리전 실험. 국소 기하 통과와 자기 교차 방지는 별개이며 접촉 모델·연구 Gate·학습 적격성은 미완료다.
- [코드 인계](../../code/sessions/2026-09-13_13_gravity_wrinkles.md). 이번 정리는 저장 상태 조회와 문서/링크 확인만 수행했다. 시뮬레이션·GPU 검산 재실행, 원본 수정, 외부 fetch·stage·commit·push 없음.
