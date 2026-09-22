# 초기 위치 갱신 반올림 검사 오탐 수정

2026-09-11. 사용자 실행 v1은1 frame 완료 후 frame1/substep0에서
`position_update_roundoff`로 종료했다. 시간 초과나 힘 수렴 실패가 아니다.

## 원인과 수정

- 최종 힘 잔차7.5985e-13N은 기존 한도1.000065e-10N을 만족했다.
- 원래 위치 갱신식과의 최대 차이는6.4623e-27m, 자유도 norm은1.9302e-25m였다.
- 거의 상쇄된 성분24개에서 최종 위치·가속도만으로 계산한 반올림 한도가
  중간 연산 오차를 과소평가했다. 예: 차이1.6708e-33m, 잘못 계산한 한도1.6211e-34m.
- 승인된 Newton 가속도 수정의 절댓값 합을 누적하여 반올림 오차 예산에 반영했다.
  물리식·Newton 허용오차·최종 위치 갱신 오차 norm 제한·타임스텝은 유지한다.
- 기존 시험은 변형이 큰 실패 지점 또는 n=4·약한 바람 위주였다.
  실제 n=32·원래 바람의 초기 기동 검증이 부족했다. 수정 후 그 조건을 직접 재검증했다.

## 검증과 한계

- 동결 v1 소스로 동일 실패를 재현했다([진단](guard_diagnosis.json), [원본 시도](failure.json)).
- 수정 경로에서 실제 n=32·60Hz·4분할의 초기6 frame(0.1초),24개 interval을 완료했다.
  실행기의 저장·기하·에너지 검산 및 모든 interval의 별도 CPU 고정밀 검산 통과.
- 독립 원식 잔차 최대비율0.119630, 위치 갱신 차이최대2.647e-23m,
  에너지 장부 차이최대2.647e-23J([상세](independent_audit.json)).
- Dynamics5개·고정밀 시간 탐색4개 회귀 검사 통과. 이 단기 결과는2.5초/10초 성공을 뜻하지 않는다.

## 원본과 다음 실행

- 기존 실패: `experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v1/` 보존.
- 재검증: `20260911_position_guard_check_v1/`; 동결 runtime,24개 interval 상태, 로그와 독립 검산 보존.
- 새 사용자 실행: `20260911_precision_segments_v2/` 동결 준비 완료, 아직 장시간 실행하지 않음.
- 기존 후보가 쓴17.538초를18초로 올림 차감하여 재실행 예산14382초(3시간59분42초).
  2.5/5/7.5/10초 구간·바람·물리 기준은 유지하며 rest부터 재실행한다.
- Root에서 동일 명령: `bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_segments.sh`.
  스크립트가 새 v2를 선택한다. 성공한 구간 뒤 자동 이어가며 실패·시간 초과 시 원인 검토를 위해 멈춘다.
- [수정 diff](dynamics.patch), [소스·입력 identity](identity.json).
- 재현: `PYTHONPATH=<동결 runtime/code> OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python <diagnose_guard.py>`.
  수정 검증: `PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python <check_prefix.py> <새 출력>`.
