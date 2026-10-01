# 시뮬레이션 artifact 정리

## 현재 상태

- 2026-10-01 사용자 승인 정리 완료: 물리 중간 자료 9.48 GiB와 M04 퇴역 자료 239.05 GiB를 정리했다. 세부 분류·삭제 명세·재생성은 [현행 보존 보고서](../R1_teacher_velocity_reset/timestep_search/artifact_retention_20260922.md#2026-10-01-정리)를 따른다.
- 현재 비교 마일스톤·후속 입력·중요 실패 원본과 과거 playback-only 결과를 유지했다. M04는 대표 mesh·기록만 남기며 원본 mesh에서 렌더 이미지를 만드는 현재 경로와 구분한다.
- ZIP 중복본만 제거했고 과거36개 중간 trace는 report/input 보관으로 전환했다. 해당7개 실행 폴더의 `retention_status.json`에 압축 복원 또는 새 경로 재계산 방법을 기록했다.
- 최근 핵심 11,215개 파일의 삭제 전후 상태, ZIP3개·mesh28개 hash와 네 뷰어 준비 검사를 확인했다. 새 계산·연구 판정 변경은 없다.

## 2026-09-22 당시 상태

- 사용자 승인으로 시각·성능 확인이 끝난 raw 프레임, chunk, 중복 runtime/native/cache를 정리했다.
- `experiments/artifacts`는 378,361,958,400바이트에서 51,054,505,984바이트로 줄었다.
- 기하 실패 원본, 최신 두 GPU 적응형 결과, 선택한 1/500 원본, checkpoint/linear snapshot은 유지했다.
- 10초 9개 visual은 72MB playback cache로 전환했고 source/report/cache hash 및 9개 재생 진입을 확인했다.
- 상세 범위와 재생성 계약은 [보존 보고서](../R1_teacher_velocity_reset/timestep_search/artifact_retention_20260922.md)가 소유한다.

## 재발 방지

- 성능 전용 실행은 완료 후 config·hash·반복·검산·시간 보고서를 남기고 raw 궤적을 report-only로 닫는다.
- 시각 전용 실행은 승인 후 60Hz playback cache를 만든 뒤 substep 기록을 제거한다.
- 실패 진단은 전체 prefix 대신 실패 전후 checkpoint와 원본 forcing index를 보존한다.
- compact 폴더를 완전한 raw 실행으로 취급하지 않으며 재계산은 항상 새 output 경로를 사용한다.
