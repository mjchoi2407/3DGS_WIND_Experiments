# Newmark half2 후 Gauss8 고부하 표본 비교

## 현재 상태

- 후속 wind182–200 요청은 사용자 승인 후 복원 스크립트 준비 완료다. 원본 상태120부터200까지 별도 재생하며 매 프레임 저장한다. 447개 동결 hash와 시작 상태 정확 일치, CPU fixture6개를 확인했다. ready120·실제 GPU 재생 미시작. [실행·중단/재개·후속 비교](../R1_teacher_velocity_reset/timestep_search/cascade_retry/resume120.md). 기존3표본 측정 결과와 구분한다.

- 확인 기준: 2026-09-18. 제한 비교 완료, 기존 기본 정책 유지.
- 과거 실제 실패2프레임과 최근 확정 저장 범위의 고비용1프레임을 선택했다. 동일 입력 두 정책을 AB/BA 두 반복으로 비교하고 raw CSV/NPZ/입력·source hash·재현 명령을 보존했다.
- 세 표본×두 정책×두 반복의 기존 검산 통과. 일부 실패 표본의 시간은 감소했지만 끝 속도 차이가 크므로 동일 정확도의 teacher 가속으로 채택하지 않는다.
- 재시도 없는 고비용 표본에는 개선 근거가 없다. 실제 half 실패→Gauss 고하중 회복은 미관측이며 작은 GPU 실패 주입 검사만 통과했다.
- 정확도·적격성 예산 미정, 장기 궤적/손수건/5070은 미검증. 기존 M1/M2/R64·생산/학습 상태·기존 Gauss와 half 스크립트를 유지한다.
- [원시 근거·측정 한계·재현 및 판정](../../experiments/R1_teacher_velocity_reset/timestep_search/cascade_retry/report.md).
- 다음: 승인된 정확도 예산이나 별도 참조 검증 없이 기본값으로 승격하지 않는다.
- 관련 worktree에만 변경을 남겼으며 stage/commit/push 없음.
