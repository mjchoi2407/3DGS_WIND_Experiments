# Teacher 가속 개발 제한 종료

## 현재 상태

확인 기준: 2026-09-16. 두 제한 시험을 완료하고 사례별 후보를 동결했다. 이후 전체 FP32/새 solver 개발을 진행하지 않는다.

- [선택 manifest](../R1_teacher_velocity_reset/timestep_search/precision_v3/selection_manifest.json): 5070 일반/HL00 M2 32/32/256,1080Ti 일반/HL00 M1 256/256/256,1080Ti C0/알려진 HL01 R64.
- [결과 보고서](../R1_teacher_velocity_reset/timestep_search/precision_v3/closeout_report.md): W30 full/summary 각1회와 저장된 HL01 frame225 R64/F64_fresh warm-up 뒤3회.
- W30 모두 기존 검산 통과, 필수 snapshot/audit와 마지막 trace/보정 보존 확인. 비영 수치 차이와 반복 수 차이를 공개하고 회귀 판정은 미정으로 둔다.
- F64_fresh는 저장된 frame225에서 기준/비용 조건을 통과하여 promising_frozen_candidate로만 남긴다. frame236/전체 HL01 재생·전역 갱신 정책은 미검증이다.
- 5070 W30은 완료2쌍만 사용했다. 추가 mixed와 미완료 prefix는 제외하며 겹치는 구간을 합산하지 않는다.
- production_enabled/training_eligible은 false다. 5070 API13000 성공과 현재 API13040의 차이, 미해결 Graph 문제를 기록했다.
- Canonical 원시 결과: `artifacts/runs/teacher_precision_v3/bounded_closeout_20260916/`. 원시 CSV/NPZ/로그·telemetry·환경/hash·명령/diff를 함께 보존한다.
- 첨부 문서2개는 미발견; 사용자 메시지 기준으로 수행했으며 첨부 대조는 미완료다.
- [구현 기록](../../code/sessions/2026-09-16_05_bounded_closeout.md), [R1 기록](../../ideas/sessions/2026-09-16_01_teacher_closeout.md). 커밋·push 없음.
