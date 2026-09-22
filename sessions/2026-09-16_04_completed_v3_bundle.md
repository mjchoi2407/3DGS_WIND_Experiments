# v3 완료 결과 두 PC ZIP

## 현재 상태

- 확인일: 2026-09-16. 사용자 요청으로 메인 v3 실행 종료. 원본 main/sub run은 보존했다.
- Canonical 취합: `artifacts/runs/teacher_precision_v3/completed_dual_gpu_20260916/` 및 같은 이름 `.zip`.
- [취합 보고서](../artifacts/runs/teacher_precision_v3/completed_dual_gpu_20260916/report.md)에 완료 범위·비교·미판정·다음 순서가 있다.
- 두 PC에서 완료된 시험121개와 환경 산출물2개를 포함한다. 각 GPU의 summary/excluded_runs가 정확한 목록을 소유한다.
- main HL01 mixed, sub HL01 reference 및 W30 마지막 reference는 미완료 원시 배열을 제외했다. 제외 목록과 오류 로그는 보존했다.
- 원시 CSV/NPZ, 실제 dtype·A/P·입력/source hash, 동결 코드/변경 diff, 검산·snapshot, telemetry·프로파일러 출력과 재현 명령 포함.
- ZIP 22,123개 항목의 CRC와 manifest 대상 파일 전체 SHA-256 일치 검증을 완료했다. ZIP 옆 `.zip.sha256`은 전체 압축파일 checksum이다.
- 재취합 명령: `PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_precision_completed_bundle --main MAIN_RUN --sub SUB_RUN --out NEW_BUNDLE`.
- 최종 학습 적격성/교차 정확도 승인 없음. 중단된 최대비용 구간의 mixed 완주를 주장하지 않는다.
- commit/push 없음.
- 512MB 업로드용 `completed_dual_gpu_20260916_compact.zip`은 458,364,702바이트. 같은 내용은1회만 저장하고 큰 JSON은 ZIP LZMA 사용. 수치 데이터 변경 없음. 표준 Python 복원기로 원본22,122개 파일을 실제 복원하고 전부 SHA-256 일치 확인. 내부 COMPACT_README/복원기 포함, 원본 큰 ZIP 보존.
