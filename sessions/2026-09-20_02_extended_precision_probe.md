# 고부하 M2/추가 FP32 후보 준비

## 현재 상태

2026-09-20. 메인1080Ti 표시190/194/200 첫 substep, M2/확장32 각3회(18 worker) 완료·분석.
- 같은 시작 상태/held, 새 초기화와워밍업 뒤 계산+독립 검산을 측정한다. 전체 프레임 재시도 비교 아님.
- P32 조립 승인/복귀와 전체 mixed fallback을 구분하고 버린 비용도 포함한다.
- 위치/속도/힘/에너지 차이, dtype·정밀도복귀·환경/hash/실제 명령을 기록한다.
- 터미널 단계별 상태/소요시간 출력. 기존 실행/동결 결과 보존. 생산/학습 승격 없음.
- 실제18회 검산 통과. inner FP32는 선형 FP64 복귀0회로 국소 후보 유지 가능, FP32 P조립은0/9승인으로 채택 보류.
- [결과 분석](../artifacts/runs/teacher_precision_v3/extended32_20260920T020357/analysis.md). 계산+검산 누적약6.31% 단축, 장기/전체frame/5070 미검증. 운영값은 변경하지 않음.
- [실행 및 판정 범위](../R1_teacher_velocity_reset/timestep_search/precision_v3/extended_precision_probe.md).

- 항목별 시간 요청 후속: `run_extended_precision_breakdown.sh` 별도 결과의 role_report.md에 M2/확장32 초·비중 표를 생성한다.
- 일반 실행과 계측 실행을 분리하고 중첩 exclusive·미분류 wall·fallback 참고값을 보존한다. 사용자 실행 완료. 18/18 수치 통과이나 GPU 구간 합이 wall을 초과하여 시간 분해는 미검증.
- CUDA 반복 load는18개 독립 worker의 초기화 단계. 이전 측정 중 재로딩은 없었음.

- [항목별 계측 결산](../artifacts/runs/teacher_precision_v3/extended32_breakdown_20260920T022015/analysis.md): 항목 합계가 wall을1.47~5.85% 초과. 비율을 성능 근거로 사용하지 않으며 원인 미확정. R1 계약/Gate 변경 없음, TeX/PDF 미수정.
- 첫 substep 계측은 전체 프레임 비용 비교로 사용할 수 없어 후속
  `run_extended_precision_frame_breakdown.sh`를 준비했다. 동일 frame checkpoint에서
  Newmark64구간과 기존 FP64 Gauss6차8분할 복구까지 실행한다. 항목 누적값에는 버린 FP32
  시도와 FP64 재계산을 모두 포함하고, FP64 전환분을 같은 항목 옆 비가산 값으로 기록한다.
  GPU 전체 프레임 실행은 사용자 실행 대기이며 기존 운영값·Gate는 변경하지 않았다.
