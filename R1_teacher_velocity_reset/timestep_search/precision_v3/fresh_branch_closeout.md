# Frame225 F64_fresh 추가 최적화 분기 종료

2026-09-17 사용자 지시에 따라 이 추가 분기를 종료한다. 추가 실행 없이 기존 측정 결과의 판정 범위만 정리했다.

| 구분 | 확정 상태 | 해석 범위 |
|---|---|---|
| frozen linear | 원래 A64 참 잔차 기준 통과, 국소 가속 관측 | 저장된 frame225 선형계에 한정 |
| line search | λ=1/8에서 승인 | line_search_checked_frozen_candidate |
| 비선형 잔차 감소 | R64 94.07%, fresh 1.14% | 같은 시작 상태의 한 번의 승인 보정 |
| 전체 Newton/substep/독립 audit | 미검증 | 전체 수렴·비용·안정성 결론 없음 |
| 운영 경로 채택 | 보류 | 기존 HL01 R64 유지 |

이 결과는 **fresh의 수치 실패나 전체 성능 저하 확정이 아니다.** 반대로 frozen linear의 가속을 전체 teacher 가속으로 보고하지 않는다. λ=1의40.52mm 및 축소 후 승인된5.065mm는 변위 보정량이며 승인된 프레임 오차가 아니다.

## 유지하는 설정과 종료 범위

[기존 선택 manifest](selection_manifest.json)의 M1/M2, GTX1080Ti C0/알려진 HL01 R64를 유지한다. summary/full 기록 옵션과 기존 full 기본값도 유지한다. production_enabled=false, training_eligible=false이며 연구 Gate를 승격하지 않는다.

추가 HL01 재생, frame236 checkpoint 생성, 전역 rebuild 정책, fresh P32, line-search 계수 변경, 전체 FP32 및 새 solver 개발은 진행하지 않는다. 저장된 재현 스크립트의 존재는 추가 실행 계획이나 승인으로 해석하지 않는다.

## 별도 미해결 항목

- RTX5070 Graph 장애: 성공 기록의 driver API13000과 후속 조회 API13040을 구분한다. 해결됐다고 간주하지 않으며 이번 분기 종료와 별개다. 이번 문서 작업에서 장치를 다시 조회하거나 복구하지 않았다.
- 학습 적격성·정확도 예산: 승인된 회귀/교차 장치 예산과 장기 teacher 적격성은 미해결이다. 이번 line search 통과가 이를 해제하지 않는다.

## 원본 근거

기존 artifact 폴더와 ZIP은 수정하지 않는다. 이 문서와 [기계 판독용 종료 상태](fresh_branch_closeout.json)가 최종 해석을 소유한다.

- [closeout 분석](closeout_report.md), [frame225 line search 분석](frozen_line_search_report.md)
- [frozen linear 원시 CSV](../../../artifacts/runs/teacher_precision_v3/bounded_closeout_20260916/HL01_linear_comparison.csv), [선형계 판정](../../../artifacts/runs/teacher_precision_v3/bounded_closeout_20260916/HL01_decision.json)
- [λ별 원시 CSV](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/measurement/line_search.csv), [진단 결과·환경·policy](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/measurement/result.json)
- [원본 linear_snapshot NPZ](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/inputs/linear_snapshot.npz)
- [저장 R64 보정 NPZ](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/inputs/R64_linear_output.npz), [저장 fresh 보정 NPZ](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/inputs/F64_fresh_linear_output.npz)
- [R64 승인 상태 NPZ](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/measurement/R64_line_output.npz), [fresh 승인 상태 NPZ](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/measurement/F64_fresh_line_output.npz)
- [입력 hash](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/input_hashes.json), [source/원본 provenance](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/provenance.json), [전체 artifact hash](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/manifest.json), [이전 closeout 보존 확인](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/preservation_check.json)
- [closeout ZIP SHA256](../../../artifacts/runs/teacher_precision_v3/bounded_closeout_20260916.zip.sha256), [line search ZIP SHA256](../../../artifacts/runs/teacher_precision_v3/frozen_line_search_20260917.zip.sha256)

이번 문서 종료 작업에서도 [원본 파일·ZIP hash 불변](fresh_branch_preservation.json)을 다시 확인했다. 추가 GPU 실행은0회다.
