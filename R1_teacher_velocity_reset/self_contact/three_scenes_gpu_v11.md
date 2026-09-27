# GPU 셀프 컬리전 세 씬 v11

## 현재 상태

2026-09-24. 같은 manifest의 메인·서브 v11 실행에서 손수건과 삼각 깃발은
preload/calm/wind 120/240/240 프레임을 모두 통과했다. 사각형은 메인 wind 표시169프레임,
서브 표시193프레임에서 Newton 반복 한도15회(코드1)로 종료돼 세 씬 전체 완주는 아니다.
두 실패 프레임의 `contact_path_status=0`으로 이전 v10 후보 버퍼 초과와 구분된다.
[양 GPU 원본 판정](#v11-사용자-실행-결과)을 따른다. 완료된 손수건·삼각형은
[저장 메시 뷰어](#완료-두-씬-뷰어)에 메인·서브 각각 연결했다. 뷰어 준비에는 물리 재실행이 없다.
별도 [code1 단일 프레임 진단](#사각형-wind-code1-dt2-격리-진단)은 두 실패 상태를
메인 GPU에서 dt/2로 복구했지만, 서브 GPU·wind 잔여 구간의 승인 근거는 아직 아니다.

## v10 실패 근거

원본 [사각형 wind report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10/reference_rectangle/outputs/wind/report.json)
및 [삼각형 wind report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10/triangular_flag/outputs/wind/report.json)의
`failure`와 `completed_frames`를 읽기 전용으로 확인했다. 손수건은
[shape report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10/handkerchief/outputs/report.json)의
세 phase가 모두 complete다.

| 씬 | wind 완료 / 240 | 실패 표시 프레임·substep | 실패 코드 | GMRES 잔차 / 목표 (N) |
| --- | ---: | --- | --- | --- |
| 사각형 | 172 | 173·49 | `failure=10`, `contact_path_status=3` | 0.02230 / 0.03708 |
| 삼각형 | 147 | 148·57 | `failure=10`, `contact_path_status=3` | 0.004765 / 0.03163 |
| 손수건 | 240 | 없음 | 통과 | — |

`gpu_contact_kernels.append`는 후보 index가 최종 배열 크기를 넘으면
`status=3`을 설정한다. 그 값이 `GPUShellContact.path`의 `path_status`로 전달된다.
실패 프레임의 `contact_status=0`, `finite=true`, 잔차<목표이고
`min_area_ratio_lower`도 양수이므로, 이 두 중단의 직접 원인은 GMRES 수렴이나
기하 검산이 아니다. 기존 GPU `dt/2` 복구는 코드2 선형 실패만 대상이라
코드10인 버퍼 초과에는 적용되지 않았다. 넘친 정확한 후보 수는 v10 report에
저장되지 않아 산정할 수 없다. [후보 삽입 함수](../../../code/wind3dgs/teacher/gpu_contact_kernels.py)
`append`와 [복구 자격 함수](../../../code/wind3dgs/teacher/resident_contact_diagnostics.py)
`allow_half_retry`를 따른다.

## v11 변경과 검증 범위

- 기본/half 프레임의 solver와 독립 audit 네 접촉 객체 모두 swept 후보 버퍼를
  2,000,000개로 설정한다. 기존 사각형 약139,584개, 삼각형 약52,704개,
  손수건 약70,080개에서 증가한다. 객체당 pair+kind 약40MB, 네 객체 합계
  약160MB의 예약량이다. 병렬 CCD는 실제 후보 수를 처리하지만 추가 메모리와
  초기화·graph 비용은 본 run에서 측정해야 한다. 2,000,000개를 초과하면
  기존 안전 실패를 유지하고 후보를 누락해 승인하지 않는다.
- cuDSS 0.7.1.4의 `CUDSS_CONFIG_DETERMINISTIC_MODE=1`을 analysis 전에
  설정하고 `cudssConfigGet`으로 확인한다. [양 GPU 격리 질량 풀이 결과](cpu_frozen_v10.md#cudss-결정성-설정-격리-시험)에서는
  같은 GPU 내부 반복 해시가 같았으나 서로 다른 GPU의 126/5,292성분은
  최대3 ULP 달랐다. 따라서 본 장기 wind의 dt/2 빈도와 장치 간 bitwise 일치는 미확정이다.
- v10의 FP64 hi/lo, split BVH, 정밀 기하 검산, GPU 코드2 `dt/2` 복구를 유지했다.
  준비한 [suite.json](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/suite.json)의
  `contact_policy`·`geometry_refinement_depth`·`linear_failure_recovery`·
  `performance_policy`·`precision`·`solver`·`linear_preconditioner`는
  v10과 같다. 동일한 9개 phase plan과 바람·외력 NPZ를 SHA256으로 대조했다.
- 설정 전달 테스트 6개, 관련 GPU 회귀 56개, 2M 용량의 기본/half × solver/audit
  객체 생성 테스트 1개가 통과했다. cuDSS numeric update/solve 별도 GPU 테스트도
  통과했다. 테스트 셸에 원본 cuDSS native 경로를 명시한 결과다. 초기 경로 미설정으로
  관련 테스트 11개가 import/library 탐색 단계에서 실패한 것은 환경 설정 오류로
  구분하며, 원본 native를 지정해 56개 전체를 다시 통과시켰다.
  이는 장기 시뮬레이션 성공·성능·장치 간 일치의 증명이 아니다.

## v11 사용자 실행 결과

사용자가 실행한 [메인 v11 묶음](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/suite.json)과
[서브 v11 미러](../../artifacts/runs/sub_pc/20260923T074157Z-a5333af22eca4b1dadc144633bd6398a/simulation/suite.json)는
manifest SHA256 `664d187004ec9c52a4509b6cee984c8825def83b5beb3ca9dcb9851599a204c7`이 같다.
서브의 다른 20260923T073117Z 묶음은 결과 report가 없는 준비본이므로 아래 실행과 혼동하지 않는다.

| 씬 | 메인 | 서브 |
| --- | --- | --- |
| 사각형 | preload120·calm240 완료, wind168/240 승인 후 표시169 실패 | preload120·calm240 완료, wind192/240 승인 후 표시193 실패 |
| 손수건 | 세 phase 120/240/240 완료 | 세 phase 120/240/240 완료 |
| 삼각 깃발 | 세 phase 120/240/240 완료 | 세 phase 120/240/240 완료 |

사각형의 [메인 실패 report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/reference_rectangle/outputs/wind/report.json)와
[서브 실패 report](../../artifacts/runs/sub_pc/20260923T074157Z-a5333af22eca4b1dadc144633bd6398a/simulation/reference_rectangle/outputs/wind/report.json)는
모두 `failure=1`·`newton_iteration=15`다. 메인 첫 나쁜 substep8, 서브35에서
비선형 힘 잔차/목표는 각각 6.51e-6/1.77e-9 N, 3.29e-7/1.92e-9 N이다.
반면 선형 잔차는 각 목표 이내이고 `contact_status=contact_path_status=0`,
`time_failed=false`, 기하 면적 하한은 양수다. 따라서 이 종료는 버퍼 초과나
GMRES 선형 실패가 아니라 현행15회 한도에서 비선형 Newton 승인 조건을 만족하지 못한 것이다.
기존 GPU `dt/2` 자동 복구는 코드2만 대상으로 하므로 적용되지 않았다.
실패까지 저장된 정상 프레임은 메인168·서브192개이고 실패 프레임 자체는 승인하지 않았다.

완료로 표시된 양 컴퓨터의 phase는 계획 프레임 수·저장 프레임 파일 수·프레임 승인 플래그가
일치하고 최종 checkpoint SHA256도 report와 일치했다. 손수건·삼각 깃발의 각
[메인 shape report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/handkerchief/outputs/report.json)와
[서브 shape report](../../artifacts/runs/sub_pc/20260923T074157Z-a5333af22eca4b1dadc144633bd6398a/simulation/triangular_flag/outputs/report.json)는
`full_trajectory_verified=true`다. 이는 해당 저장 궤적의 완료 판정이지 서로 다른 GPU의
궤적 bitwise 일치나 사각형 성공을 뜻하지 않는다. 기존 결과를 수정하지 않았다.

## 사각형 wind code1 dt/2 격리 진단

2026-09-24. 기존 v11 원본은 수정하지 않고, 실패 직전 승인 NPZ와 해당 프레임 외력을
[단일 프레임 진단기](../../../code/wind3dgs/evaluation/contact_code1_retry_probe.py)에 공급했다.
입력 SHA256은 원본 프레임 report와 대조하며 출력은 기존 run 밖의 고유 폴더만 허용한다.
동결된 물성·바람·기본 dt=1/3840초·Newton15·허용오차·접촉식·2M swept 용량·
cuDSS 결정성1은 유지했다. `retry_newton_limit=True`에서만 유한한 code1·정상
contact/path·시간축·승인 prefix 검산을 확인하고, 프레임 시작 raw hi/lo로 돌아가
dt=1/7680초의128단계를 한 번 실행한다. 실패 시 원래 시작 상태를 보존한다.

| 원본 시작 상태 | 원본 실패 | GTX1080Ti 재생 기본64단계 | opt-in dt/2 128단계 | 독립 검산 |
| --- | --- | --- | --- | --- |
| [메인 wind169 직전](../../artifacts/runs/p3_self_contact/diagnostics/20260924_code1_main_replay_optin_v2/report.json) | code1·substep8 | code1·substep8 재현 | passed | flags0, 최대 힘 비율0.250, 면적 하한0.471 |
| [서브 wind193 직전](../../artifacts/runs/p3_self_contact/diagnostics/20260924_code1_sub_state_on_main_gpu_optin_v2/report.json) | code1·substep35 | code1·substep35 재현 | passed | flags0, 최대 힘 비율0.281, 면적 하한0.470 |

재현 명령은 workspace 루트에서 실행한다. `--out`은 항상 아직 없는 고유 경로여야 한다.
서브 저장 상태를 메인 GPU에서 시험하려면 `run_root`만 위 표의 서브 미러 run으로 바꾼다.

```bash
native=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/native
run_root=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11
env PYTHONPATH=code CUDSS_LIBRARY_PATH="$native/libcudss.so.0" \
  LD_PRELOAD="$native/libcudss_workspace.so" WIND3DGS_CUDSS_DETERMINISTIC=1 \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1 \
  .venv/bin/python -u -m wind3dgs.evaluation.contact_code1_retry_probe \
  --run-root "$run_root" --out experiments/artifacts/runs/p3_self_contact/diagnostics/NEW_UNIQUE_NAME
```


두 입력은 **모두 메인 GTX1080Ti에서** 재생했다. 서브 RTX5070에서의 code1 복구와
이후 wind 잔여 프레임 완주는 미검증이다. GPU 자격·실제 복구·재시도 실패 rollback·
기본 code2 유지의 관련 회귀22개가 통과했다. 진단은 기존 v11 동결 bundle과
[세 씬 실행 스크립트](run_gpu_three_scenes.sh)의 code2 전용 정책을 바꾸지 않는다.
새 장기 실행 정책으로 승격하기 전에는 직렬10초 의도와 분기6초 계약부터 결정해야 한다.

calm과 wind는 같은 preload 종료 NPZ와 중력[0,0,-9.81]m/s²에서 **각각** 시작한다.
calm의 입력 바람은240프레임 전부0이고, wind는 첫 프레임0 이후 ramp를 거쳐
최대 약1.969m/s다. calm도 움직이는 천과 정지한 공기의 상대 속도에 따른 공력은
계산한다. 따라서 이 결과는 preload→wind 분기의 실패를 복구한 것이지
preload→calm→wind 연속10초 궤적을 검증한 것은 아니다.


## 완료 두 씬 뷰어

Workspace 루트의 [저장 결과 뷰어 스크립트](view_completed_gpu_scenes.sh)는
손수건(왼쪽)·삼각 깃발(오른쪽)을 나란히 재생한다. 기본은 메인 결과의
`preload` 0–2초와 `wind` 2–6초다. `calm`도 같은 preload 끝에서 분기하므로
`--phase calm`으로 별도 표시한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_completed_gpu_scenes.sh
bash experiments/R1_teacher_velocity_reset/self_contact/view_completed_gpu_scenes.sh --source sub
bash experiments/R1_teacher_velocity_reset/self_contact/view_completed_gpu_scenes.sh --phase calm
```

`--shape handkerchief` 또는 `--shape triangular_flag`는 하나만 표시한다.
`--prepare-only`는 화면 없이 CPU에서 별도 표시 캐시만 만든다.
`--source sub`는 원격 프로세스가 아닌 위 로컬 미러를 읽는다. 다른 저장 위치는
`--run PATH`와 필요 시 고유 `--cache PATH`로 지정할 수 있다.

기본 메인·서브 각 두 씬의 캐시를 이미
[표시 캐시 루트](../../artifacts/runs/shell_playback/p3_self_contact_v11/main/wind/handkerchief/manifest.json)에
별도 준비했다. 각 캐시는 preload120+분기240=360개 60Hz 프레임 경계와 초기 상태를
담는다. 원본 manifest·모델/입력 코드 hash, phase plan/입력, shape/phase report,
모든 프레임 SHA256·승인·시각/고정점, 마지막 checkpoint와 분기 초기 상태 일치를
검사했다. 재사용 시 report·캐시 hash를 검사하고 미완료 캐시는 덮어쓰지 않는다.
[메인 손수건 캐시](../../artifacts/runs/shell_playback/p3_self_contact_v11/main/wind/handkerchief/manifest.json),
[메인 삼각형 캐시](../../artifacts/runs/shell_playback/p3_self_contact_v11/main/wind/triangular_flag/manifest.json),
[서브 손수건 캐시](../../artifacts/runs/shell_playback/p3_self_contact_v11/sub/wind/handkerchief/manifest.json),
[서브 삼각형 캐시](../../artifacts/runs/shell_playback/p3_self_contact_v11/sub/wind/triangular_flag/manifest.json)에
원본/캐시 hash가 각각 남는다.

float32 표시 반올림 최대 오차는 네 캐시에서 5.96e-8m 미만이다.
기존 P3 계산점9개 표시 삼각형과 임시 체크무늬를 사용한다. 물리 solver·접촉 계산,
내부64 substep, 3DGS/원본 외관은 포함하지 않는다. 뷰어 결과를 새 수치 검산으로
간주하지 않는다. 단위/회귀7개 통과, 메인2프레임·서브1프레임 headless
OpenGL 표시 통과. 메인 [4초 표시 화면](../../artifacts/runs/shell_playback/p3_self_contact_v11/main/wind/preview.png)의
손수건·삼각형 배치를 확인했다. WSL에서 CUDA/OpenGL 직접 공유 실패 경고는 기존
copy fallback으로 처리돼 표시 자체는 성공했다. 물리 재계산·원본 변경·외부 다운로드는 없다.

## 실행 준비

아래는 실행 전 준비 당시의 명령 기록이다. 현재 메인·서브 v11 `outputs`는 이미 존재하며
같은 경로로 재실행하지 않는다. Workspace 루트의 [실행 스크립트](run_gpu_three_scenes.sh)는
기본이 `--action prepare`였고 사용자에게 `--action run`을 안내했다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
```

세 씬은 사각형→손수건→삼각형 순서로 독립 GPU worker에서 실행된다.
각 프레임의 solver/collision/audit 소요 시간과 실패 사유가 터미널 및
각 씬 `run.log`에 남는다. 다시 `prepare`하면 기존 v11 경로가 있어 거절되며,
`run`도 이미 생성된 `outputs`를 덮어쓰지 않는다. 별도 컴퓨터에서 실행할 때는
해당 컴퓨터에 새 소스와 동결 묶음을 동기화하거나 그곳에서 고유 `--out`으로
준비해야 한다. 기존 v10/현재 v11을 덮어쓰지 않는다.

[v11 bundle](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/suite.json)의
schema는 `p3_gpu_contact_three_scenes_v11`, backend는 `gpu_resident`,
`cudss_deterministic_mode=1`, `swept_candidate_capacity=2000000`이다.
[manifest.json](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v11/manifest.json)의
SHA256은 `664d187004ec9c52a4509b6cee984c8825def83b5beb3ca9dcb9851599a204c7`이다.
준비 당시 `--action status`에서 세 씬 모두 'GPU 준비 완료·미실행'을 확인했다. 현재 결과는 [실행 판정](#v11-사용자-실행-결과)을 따른다.
