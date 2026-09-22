# Frame225 보정의 line search 확인

## 현재 상태

최종 결정: frame225 추가 최적화 분기 종료. [종료 문서](../R1_teacher_velocity_reset/timestep_search/precision_v3/fresh_branch_closeout.md)에 다섯 판정 층을 분리했다.
Frozen linear 통과/국소 가속, λ=1/8 승인과 잔차 감소율을 보존하며 전체 Newton/substep/audit는 미검증, 운영 채택은 보류다.
수치 실패·전체 성능 저하 확정이나 전체 teacher 가속으로 해석하지 않는다. 추가 계산 없이 M1/M2·HL01 R64·summary/full을 유지한다.
5070 Graph 장애와 학습 적격성/정확도 예산은 별도 미해결이다. 원본 artifact와 ZIP은 보존했다.

확인 기준: 2026-09-17. 새 HL01 재생 없이 저장된 선형계와 두 보정으로 국소 진단 완료.

- [보고서](../R1_teacher_velocity_reset/timestep_search/precision_v3/frozen_line_search_report.md): 초기 RHS 정확 재현, 기존 λ별 residual/Armijo/status/승인/비용 기록.
- R64는 전량 승인, fresh는3회 backtrack 후 승인됐지만 비선형 잔차 감소가 작다. 어느 쪽도 한 보정으로 Newton 종료 기준을 충족하지 않는다.
- line_search_checked_frozen_candidate만 기록한다. frame236·완전한 substep Newton/audit 미측정, 장시간 checkpoint 재생 없음.
- 원본은 `artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/`. 이전 closeout ZIP/hash/운영 선택을 보존했다.
- 저장 P 재사용·유한성, HVP 및 cuDSS info 확인. 새 assembly/선형 풀이/FP32/전역 P 정책 변경 없음.
- [구현 기록](../../code/sessions/2026-09-17_01_frozen_line_search.md), [R1 기록](../../ideas/sessions/2026-09-17_01_frozen_line_search.md). 커밋·push 없음.
