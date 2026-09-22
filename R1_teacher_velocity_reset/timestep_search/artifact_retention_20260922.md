# 2026-09-22 시뮬레이션 artifact 정리

사용자 승인으로 시각 확인·성능 비교가 끝난 raw 궤적을 playback-only 또는 report-only로 정리했다.
물리식·솔버·검산 기준과 추적된 결과 수치는 변경하지 않았다.

## 결과

- `experiments/artifacts`: 378,361,958,400 → 51,054,501,888 bytes.
- 회수 공간: 327,307,456,512 bytes.
- 디스크 사용률: 71% → 39%.
- 삭제 작업: 3,257개 경로.
- 원본 삭제 목록·이유·보존 경로: `artifacts/retention/20260922_cleanup/cleanup_manifest.json`.

## 보존 범위

- 기하 실패 원본 `sub_pc/20260912T162242Z-59eb2516b2124c6d997d086fcd6f86e6`.
- 최근 RTX5070 적응형 실행 `sub_pc/20260919T194142Z-4d98ab0f6f2a40d18a91eaf77e62a872`.
- 최근 GTX1080Ti 적응형 실행 `teacher_timestep_search/gpu_gtx1080ti_adaptive_integrator_bend500_v1`.
- 선택한 1/500 visual 원본 `teacher_timestep_search/gravity_wrinkles_flag_bend500_v1`.
- 입력·wind·config·report·summary·manifest·checkpoint·linear snapshot.
- v2를 직접 참조하는 158–163 frame.
- P3 reset66 미달 비교의 n16/n32 대표 66·67·89 frame.
- precision v3 compact/closeout/frozen-line-search ZIP.

완료된 서브컴 10초 3조건×3메시는 9개 playback cache로 보존했다. 각 cache의 source report hash와
`positions.npy`·`geometry.npz` hash를 확인한 뒤 38GB substep chunk를 제거했다. 원본 삭제 후
`view_cloth_coarse_10s.sh`의 9개 `--prepare-only` 조합이 모두 통과했다.

## 재생성 계약

삭제한 visual/physics 배열은 남은 실행기·config·입력·source identity를 사용해 새 output 경로에서
처음부터 계산한다. 과거 wall-clock은 장치 상태와 환경에 의존하므로 보존 report가 authority이며 동일 시간
재현을 요구하지 않는다. 중간 상태에서 시작하는 진단은 남긴 checkpoint/snapshot을 사용한다.
`prepared_not_run`과 최신 결과로 대체된 중단 prefix는 재생성 대상이 아니다.

기존 완료 폴더에 누락 frame을 이어 쓰지 않는다. report-only 폴더의 전체 궤적이 필요하면 새 폴더에서
재실행하고, 현재 compact 폴더를 완전한 raw 실행으로 해석하지 않는다.
