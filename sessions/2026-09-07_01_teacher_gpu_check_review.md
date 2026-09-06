# 2026-09-07 01 Teacher GPU 검사 결과 보존

## Context

Wind3DGS experiments-side. 사용자가 직접 실행한 Teacher GPU 검사 12/12단계 통과 로그를 전달했고,
후속 검토 후 현재 진행 내용을 문서/Git에 반영하도록 요청했다. 기존 GPU run의 compact evidence를
보존하는 작업이며 새 simulation이나 material 보정 실험을 수행하지 않았다.

## 변경과 관찰

- [R1_teacher_smoke/README.md](../R1_teacher_smoke/README.md)에 setup·재현 명령·검토 결과·남은 문제를 기록했다.
- `R1_teacher_smoke/review.json`에 실행 summary/checks/environment/cuda와 비교 metadata를 보존했다.
- `R1_teacher_smoke/artifact_inventory.json`에 원본 191개 파일의 byte 수/SHA-256을 보존했다.
- Experiments README와 sessions index에 현재 검증 진입점을 연결했다.
- GTX 1080 Ti 실제 실행은 53.912초, 12/12단계 통과다. 수렴 상태는 `not_assessed`다.
  공간 velocity 차이는 비감소, 시간 마지막 상대 RMS 차이는 11.41%, 자유감쇠 공간 차이는 193.25%다.
- Native bending 초기 에너지는 mesh 4에서 0.000374910875186 J, mesh 8에서 0.000218695028197 J다.
  기존 초기 위치의 읽기 전용 기하학 계산이며 원인 확정이나 material 계수 변경 근거로 승인한 것은 아니다.

## 검증

- 사용자 GPU 결과의 raw/probe 7쌍을 입력으로 비교 3개를 다시 계산해 source binding/report hash를 확인했다.
- 실행 시점 source SHA-256 24개와 보존할 code snapshot이 일치함을 확인했다.
- 원본 inventory 검토 전후 191개 파일이 동일하며 삭제·덮어쓰기·추적 추가를 하지 않았다.
- README의 읽기 전용 명령 두 개를 실행해 모두 통과했고 JSON 내용, 링크·whitespace·개인 경로를 검증했다.
  GPU simulation/replay를 agent 환경에서 다시 수행한 결과로 보고하지 않는다.

## Git 범위와 다음 작업

- Code 구현 commit `7010682`의 source SHA-256 24개가 실행 snapshot과 일치한다.
  전체 SHA를 `review.json`의 후속 snapshot 참조에 기록하고 실험 문서를 별도 commit한다.
- 이 저장소의 기존 `.gitignore`, `AGENTS.md`, README의 artifact 정책 문구, sessions index의 정책 문구와
  8월/9월 1일 기존 session은 이번 GPU 결과 commit에서 제외하고 worktree에 보존한다.
- Root/ideas 기존 변경, 원본 artifact와 환경 설정은 수정하지 않았다. Network fetch/download/push는 수행하지 않는다.
- 다음 후보는 bending mesh 의존성 감사다. 아직 새 기능 구현 승인을 받지 않았고 이번 작업에서는 문서/Git만 정리했다.
