# GPU 최적화 결과 종합

## 현재 상태

- 확인일:2026-09-13. 사용자 요청의 당일 GPU 성능·검산 결과를 [종합 보고서](../R1_teacher_velocity_reset/timestep_search/gpu_resident/optimization_summary.md)에 정리했다.
- 최종 생성 summary와 GPU 검산 comparison 원본을 읽고 단계별 시간·반복/갱신 횟수·대조 판정을 선별 JSON으로 보존했다.
- 생성/초기화/검산/입력 읽기의 경계 차이와 캐시 재사용·서로 다른 실행 시점의 한계를 명시했다. 합산 수치를 end-to-end 실측으로 승계하지 않는다.
- 천 비교의 매 프레임 동기화·2초 저장·Ctrl+C·10초 visual 기하 경고는 별도 운영 조건으로 연결했다.
- [새 솔버 구현 지침](../../code/docs/gpu_solver_design.md)이 알고리즘 적용 조건을 소유하며 이 보고서가 상세 실험 수치를 소유한다.
- 로컬 snapshot 확인만 수행. GPU 실행·기존 결과 변경·외부 fetch·다운로드 없음. 문서 링크·diff 검증, commit·push 없음.
- 다음:10초 결과의 실제 움직임과 수치 실패를 확인한다. 학습 발행 보류와 strict 연구 Gate는 유지한다.
