# 완료한 직사각형·손수건 재생 준비

## 현재 상태

- 2026-09-13 후속: 10초 재생 wrapper의 기본 대상을 완료된 서브컴3조건×3메시 run으로 연결했다. [사용법](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/README.md#완료된-서브컴10초-결과-재생).
- Bash 문법·도움말 확인 및 `bend_001 --shape handkerchief --prepare-only` 성공. 원본 chunk hash·600프레임 검증 후 표시 캐시 생성 완료. 이번에는 OpenGL 창을 새로 실행하지 않았다.
- 물리 solver·동결 runtime·원본 상태는 보존했다. experiments wrapper·안내·본 기록만 변경했으며 commit·push 없음.

## 이전 두 씬 재생 검증

- 확인 기준일: 2026-09-13. 두 씬의 저장10초 재생 준비·OpenGL 표시 확인 완료.
- [실행 명령·원본·검증](../R1_teacher_velocity_reset/timestep_search/evidence/saved_viewer_20260913/README.md).
- 각600개 확정 trace hash 확인 후 별도 표시 캐시 생성. 표시 화면은 실제 크기·변위를 사용하고 배치 위치만 이동한다.
- 물리 재계산·원본 변경 없음.3DGS 및 원본 고해상도 외관은 포함하지 않는다.
- [구현 기록](../../code/sessions/2026-09-13_01_saved_mesh_viewer.md). commit·push 없음.
