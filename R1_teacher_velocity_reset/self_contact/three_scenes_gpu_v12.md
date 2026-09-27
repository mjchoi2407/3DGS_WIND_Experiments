# GPU 세 씬 v12 연속 10초

## 현재 상태

2026-09-27 사용자 승인에 따라 기존 분기 궤적을 새 bundle에서 연속 궤적으로 전환했다.
사각형·손수건·삼각 깃발 모두 preload 2초(120프레임) → calm 4초(240프레임)
→ wind 4초(240프레임), 60Hz 총600프레임이다. 본 시뮬레이션은 미실행이다.

## 실행

프로젝트 루트에서 세 씬을 GPU 순차 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
```

현재 로컬에는 준비가 완료됐다. 새 환경에서는 먼저 같은 스크립트의 `--action prepare`를 실행한다.
상태 확인은 `--action status`다. 기존 출력은 덮어쓰지 않으며 재실행은 새 `--out`으로 준비해야 한다.

실행 묶음: [v12 suite.json](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/suite.json).
`trajectory_mode=serial`, `phase_start_s={preload:0,calm:2,wind:6}`,
`retry_newton_limit=true`가 동결됐다.
[manifest](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/manifest.json) SHA256:
`0be6397195b505b314fa8b8913aa41b28c2249593f366ea2c05529f5536c994e`.

## 연결과 복구 계약

- preload 끝 raw hi/lo 위치·속도 → calm 초기 상태 → calm 끝 상태 → wind 초기 상태.
  속도 초기화 없이 전달하며 앞 phase 실패 시 뒤 phase는 시작하지 않는다.
- 원본 물성·외력 배열·dt·허용오차는 유지한다. wind의 기존 바람 ramp는 전체 시간6초부터 시작한다.
  calm에도 움직이는 천의 공기 저항은 남는다. 기존 v11 wind와 초기 상태가 다르므로
  과거 실패 프레임이나 완주 결과를 새 궤적에 그대로 승계할 수 없다.
- 유한한 code1/code2와 기존 접촉·시간축·prefix 검사 조건을 만족한 경우에만
  프레임 시작에서 GPU dt/2 한 번 재시도한다. 실패 증거 보존·독립 검산·rollback은 유지한다.
  swept 후보2M 및 cuDSS 결정성1도 유지한다.
- 프레임 NPZ의 `phase_time_s`는 구간 시간, `trajectory_time_s`는 전체 시간이다.
  phase report의 `phase_start_s`와 `trajectory_mode`도 기록한다.
- 기존 v11 bundle·결과·6초 표시용 뷰어는 변경하지 않았다. 기존 뷰어를 v12의
  10초 뷰어로 간주하면 안 된다. v12 전체 궤적 뷰어 연결은 이번 준비 범위 밖이다.

## 검증과 한계

현재 구현 보존 revision은 code commit `a5e4d8e`다. 이미 준비한 v12의 실제 실행 소스는
위 manifest의 runtime 파일 hash가 식별하며 후속 commit ID로 대체하지 않는다.

2026-09-27 commit 전 진단·CPU 동결·뷰어·실행기 관련 회귀33개가 통과했다.
GPU 본 실행이나 체크포인트 재생을 추가로 수행하지 않았다.

실행기 단위 검사8개 통과: 준비/hash, 순차 hi/lo 전달, preload/calm 실패 중단,
복구 옵션 전달, 전체 시간 기록, 실패 증거 보존 등.
세 씬의 동결 입력120/240/240프레임과 phase 시작0/2/6초 및 총10초를 확인했고
manifest 검증과 셸 구문 검사를 통과했다. GPU 본 실행·장기 완주는 아직 검증하지 않았다.
code1 복구의 이전 단일 프레임 GPU 근거는
[v11 사각형 진단](three_scenes_gpu_v11.md#사각형-wind-code1-dt2-격리-진단)에 있다.
