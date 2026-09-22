# 시뮬레이션 artifact 정리

## 현재 상태

- 사용자 승인으로 시각·성능 확인이 끝난 raw 프레임, chunk, 중복 runtime/native/cache를 정리했다.
- `experiments/artifacts`는 378,361,958,400바이트에서 51,054,501,888바이트로 줄었다.
- 기하 실패 원본, 최신 두 GPU 적응형 결과, 선택한 1/500 원본, checkpoint/linear snapshot은 유지했다.
- 10초 9개 visual은 72MB playback cache로 전환했고 source/report/cache hash 및 9개 재생 진입을 확인했다.
- 상세 범위와 재생성 계약은 [보존 보고서](../R1_teacher_velocity_reset/timestep_search/artifact_retention_20260922.md)가 소유한다.

## 재발 방지

- 성능 전용 실행은 완료 후 config·hash·반복·검산·시간 보고서를 남기고 raw 궤적을 report-only로 닫는다.
- 시각 전용 실행은 승인 후 60Hz playback cache를 만든 뒤 substep 기록을 제거한다.
- 실패 진단은 전체 prefix 대신 실패 전후 checkpoint와 원본 forcing index를 보존한다.
- compact 폴더를 완전한 raw 실행으로 취급하지 않으며 재계산은 항상 새 output 경로를 사용한다.
