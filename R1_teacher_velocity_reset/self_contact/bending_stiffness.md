# P3 굽힘 강성 절반·마지막2초 비교

## 현재 상태

- 2026-09-30 사용자 실행의 `rectangle_bend1000_tail2_main_01`에서 첫 검사1/1·본120/120 완료를 확인했다. 이번 수정에서 시뮬레이션은 재실행하지 않았다.
- [실험 조건](#실험-조건): 기존1/500 재사용, 새1/1000. 막5ms·굽힘/전역 감쇠0, 같은8초 raw 위치·속도에서8→10초 비교다.
- 막 강성·질량은 유지하고 굽힘 재료 행렬·요소 경계 굽힘 항을1/2로 조정했다. 원본 Python269개/native는 보존하고 새 실행기만 추가했다.
- [시간 기록 호환 수정](#시간-기록-호환-수정): 동결 기록기는 `phase_time_s`를 구간0–2초로 저장했으나 뷰어가wind3–5초를 요구해120프레임 모두 거절했다. 전체 `trajectory_time_s`는8–10초로 정상이다.
- 현재 뷰어는 검증된 동결 기록식을 식별하고 저장 시간·전체 시간을 검사한 뒤 공통0–2초로 표시한다. 원본 NPZ·보고서·동결 runtime·manifest는 수정하지 않았다.
- [수정 검증 근거](bending_stiffness_viewer_fix_checks.json)의 `tests`·`actual`·`preservation`: CPU/모의 실행20개 통과, 실제 두 궤적의121상태 캐시 및1초 시점 한 프레임 렌더 성공.
- 표시 CUDA/OpenGL interop 미지원은 기존copy fallback으로 처리됐다. 물리 계산을 대체한 것이 아니며 이번에는 물리 계산 자체를 실행하지 않았다.
- [화면 가림 수정](#화면-가림-수정): 두 결과는 로드됐으나 좁은 창/큰 UI에서 왼쪽 천이 사이드바 뒤로 가려지는 문제를 재현했다. 전체 궤적·표시 영역에 맞춰 카메라를 배치하고 창 크기 변경 시 다시 맞춘다.
- 공용 뷰어 포함38개 검사 통과. 실제1280/960폭 UI 화면에서 두 천 표시를 확인했다. `Fit all recordings` 버튼과 로드 수 표시를 추가했다. [실행과 재생](#실행과-재생)의 기존 명령을 사용하며 본run 재실행은 불필요하다.
- 구현 준비 당시11개 검사·동결 입력 검증은 [준비 근거](bending_stiffness_checks.json)에 보존했다. 당시 새 후보 미실행 상태를 현재 완료 결과로 덮어쓰지 않는다.
- [사용자 시각 평가](#사용자-시각-평가): 기본 두 조건 비교에서 하늘색 기존1/500의 움직임을 주황색1/1000보다 선호했다. 잔진동 해결·시간/공간 민감도·학습 채택은 미판정이다.
- 원본 phase 메타데이터의 의미 차이는 남아 있으며 후속 분석도 suite offset과 함께 해석해야 한다.
- 후속 검토 권고는 기존1/500을 움직임 비교 기준으로 유지하고 잔진동 억제를 검토하는 것이다. 강성 추가 감소의 우선순위는 낮추되, 새 방법 채택·구현·계산 승인을 뜻하지 않는다.
- R1 제한 CG 경계를 확인한 별도 진단이다. 이번 선호 기록은 canonical/완료 기준/TeX/PDF를 바꾸지 않는다. 코드·물리 계산·이전 검증 재실행 없이 experiments 문서만 갱신했고 기존 dirty·원본·실행을 보존했다. commit/push/fetch·외부 다운로드 없음.

## 실행과 재생

프로젝트 루트에서 실행한다. 기본 묶음은 준비됐으므로 prepare를 다시 호출할 필요가 없다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_bending_stiffness.sh --action run
```

새 후보의 첫 프레임 검사를 먼저 수행한다. 성공하면 첫 프레임의 끝 상태를 이어 쓰지 않고 원본8초 raw로 돌아가 본120프레임을 계산한다.
따라서 본 계산120프레임과 별도 검사1프레임이 있다. 첫 실패에서 중단하며 실패 로그·raw rollback·버린 재시도 증거는 기존 실행기 규칙대로 보존한다.
메인 GTX1080Ti와 원본 동결 환경을 요구한다. 다른 GPU로 임의 대체하지 않는다.

상태 확인은 적분하지 않는다. 옵션 없이 호출해도 상태만 표시한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_bending_stiffness.sh --action status
```

완료 후 기존/절반 강성을 함께 재생한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_bending_stiffness.sh
```

기본 두 조건 비교에서 왼쪽 하늘색은 **bend500: 기존**, 오른쪽 주황색은 **bend1000: 굽힘 강성1/2**다. 둘 다 막5ms·굽힘 감쇠0이며 표시0–2초는 전체8–10초다.
사이드바의 `Loaded recordings: 2`로 두 결과 로드를 확인하고 `Fit all recordings`로 모두 보이도록 카메라를 복원한다. 창 크기/UI 배율 변경 시 자동으로 다시 맞춘다.
`--case bend500|bend1000`은 단독 재생, `--prepare-only`는 원본 hash·시간·핀·외력·소산·checkpoint와 캐시만 확인한다.
새 후보가 미완료면 전체 비교를 거절한다. 기존 기준의 미완료 구간이나 새 실패 구간을 정상 완료로 표시하지 않는다.

새 경로에 입력을 다시 준비해야 할 때만 다음을 쓴다. 기존 묶음은 덮어쓰지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_bending_stiffness.sh --action prepare --out <새_경로>
```

## 사용자 시각 평가

2026-09-30 사용자는 기본 두 조건 비교에서 하늘색인 기존 굽힘1/500의 움직임을 더 선호했다. 비교 대상인 주황색은 굽힘1/1000이며, 두 조건 모두 막 감쇠5ms·굽힘 감쇠0·전역 감쇠0이다. 색상은 기본 비교의 표시 순서에 따른 것이므로 단독 재생의 색상으로 조건을 식별하지 않는다.

이번 선호에 따라 기존1/500을 후속 움직임 비교 기준으로 유지하는 것을 권고한다. 강성을 더 낮추는 방향의 우선순위는 낮추고, 기존 움직임을 살리면서 잔진동을 억제하는 방법을 검토한다. 이는 강성 절반 후보의 진동이 수치적으로 더 크다는 판정이나 기존 조건의 진동 해결·최종 teacher 채택을 뜻하지 않는다.

비교 범위는 같은8초 raw 상태에서 이어진 마지막2초이며 새 후보의8초 물성 전환 반응을 포함한다. 사용자 선호만 기록했으며 새 시뮬레이션·구현·수치 분석은 수행하지 않았다.

## 실험 조건

| 조건 | 기존 bend500 | 새 bend1000 |
| --- | ---: | ---: |
| 원래 물성 대비 굽힘 비율 |1/500 |1/1000 |
| 현재 기준 대비 굽힘 강성 |1 |0.5 |
| 막 강성 (N/m) |10989.010989010989 |동일 |
| 굽힘 강성 (N·m) |1.8315018315018315e-4 |9.157509157509158e-5 |
| 면밀도 (kg/m²) |0.1 |동일 |
| 막 감쇠 시간 계수 |5ms |동일 |
| 굽힘/전역 감쇠 |0/0 |동일 |
| 전체 궤적 구간 |8–10초 재사용 |8–10초 새 계산 |

기존 `scaled_material`/`with_bending_ratio`로 두께를sqrt(1/2)배, E를sqrt(2)배 바꿔 Eh는 유지하고 Eh³를 절반으로 만든다.
따라서 물성 입력의 E·h 숫자는 바뀌지만 막 강성은 같고, 별도 면밀도를 쓰는 질량 행렬도 같다.
경계 굽힘 penalty의 무차원 계수 자체를 임의로 낮추지 않으며 Eh³에 비례하는 굽힘 항을 함께 조정한다.
이번 시험에서1ms/5ms 굽힘 감쇠 후보는 새로 계산하지 않는다.

60Hz·기본64단계, 기존 조건을 만족한 code1/2만 프레임 시작점에서128단계로 한 번 재시도한다.
힘·기하·접촉·시간 검산, cuDSS 결정성1, swept 후보 용량2,000,000, 공력의 프레임 시작 평가/hold는 원본 그대로다.
wind·중력 입력은 원본300프레임의 `[180:300]`이다. 공력은 새 궤적의 상태에서 평가되며 원본 공력 배열로 강제하지 않는다.

## 입력과 식별

- 새 [suite.json](../../artifacts/runs/p3_self_contact/rectangle_bend1000_tail2_main_01/suite.json)의 `cases`, `reference0`, `phase_start_s`, `phase_time_offset_s`가 실험 범위를 식별한다.
- 새 [manifest.json](../../artifacts/runs/p3_self_contact/rectangle_bend1000_tail2_main_01/manifest.json) SHA256: `c34f537d7ff0baa247dcd39fdb221bac98c042ed5442fcd6e7227fede2a1f483`.
- 원본은 [막 감쇠 완료 결과](internal_damping.md#완료-결과-분석)의 `rectangle_wind_internal1_5ms_main_01/tau5ms`다.
- 원본 manifest SHA256: `3c5ef6764035b84cf5953e4228f563577f7355b31022e036168361d6bccbe8a1`.
- 시작 상태는 `tau5ms/reference_rectangle/outputs/wind/frame_0179.npz`, 전체8초·wind3초다. SHA256: `00d845e64efba0ae4dc337c07f219b0e3b32b556fbc9064b7a109b63d8eb1972`.
- 새 `initial_state.npz`는 원본 메타데이터를 제외하고 네 raw 배열을 그대로 저장한다. 파일 hash와 원본 파일 hash의 차이는 상태 변경을 뜻하지 않는다.
- [검증 JSON](bending_stiffness_checks.json)의 `reference`, `material_reference`, `material_candidate`, `checks`에 식별·전체 물성·준비 검증을 보존한다.
- 입력 묶음의 `reference/source_manifest.json`, `source_suite.json`, `source_plan.json`은 원본 설정을 보존한다. 원본 runtime269개/native와 새 실행기를 모두 manifest로 검사한다.
- 이 동결 실행의 본 NPZ는 `phase_time_s=1/60→2초`, `trajectory_time_s=8+1/60→10초`다. 기존 계획에 적었던wind3+1/60→5초는 suite의 offset3초를 더한 해석값이며 원본 저장값과 구분한다. [시간 기록 호환 수정](#시간-기록-호환-수정)을 따른다.
- 사용자 실행 후 `bend1000/preflight/contact_frame/report.json`, `bend1000/reference_rectangle/outputs/wind/report.json`, `smoke.log`, `wind.log`가 실행 근거가 된다. 2026-09-30 사용자 실행의 첫 검사1/1·본120/120 완료를 확인했다.

## 시간 기록 호환 수정

기존 solver를 byte 그대로 동결하면서 과거 기록기의 `phase_time_s=(frame+1)/fps` 형식을 준비 단계에서 놓쳤다.
물성 전환 진단의 시작offset3초를 사용하는 뷰어와 달리 이 기록기는 새 구간의0–2초를 저장했다.
새 후보 첫 프레임은 phase1/60·trajectory8+1/60, 마지막은phase2·trajectory10이다. 기준1/500은 원래5초wind의 뒤2초여서phase3+1/60→5초를 저장한다.
두 결과의 위치·속도·외력이나 전체 궤적 시간이3초 어긋난 것은 아니다. 이번 확인에서 본120프레임 완료·저장 검산·전체 시간을 확인했다.

`recorded_phase_origin`은 manifest로 검증한 동결 `simulation`의 저장식을 AST로 읽어 구간 시간 또는offset을 포함한wind 시간으로 식별한다.
저장값이 통과하도록offset을 추정하지 않는다. 식별된 형식별 기대 시간과 `trajectory_time_s`를 각 프레임에서 검증하고,
알 수 없는 기록식·잘못된offset·전체 시간 오류·NaN은 거절한다. cache manifest의 `source.time_contract`에 표시 해석을 기록한다.
원본 NPZ·checkpoint·보고서·runtime·입력 manifest는 그대로 보존했다. 현재 worktree의 뷰어 코드만 수정했으므로 원본 동결 실행기와의 차이는 의도된 표시 호환 수정이다.

[수정 검증 JSON](bending_stiffness_viewer_fix_checks.json)의 `writer_sha256`, `actual`, `preservation.hashes`, `evidence_folder`가 정확한 버전·시간·원본 보존·렌더 근거다.
기존11개 검사에 과거/현재 기록식·오류 시간/NaN·실제 구간 시간 형식의 캐시와 원본 보존 회귀9개를 추가해20개 통과했다.
실제 두 결과의121상태를 비교 캐시로 만들고 한 프레임 렌더를 확인했다. 사용자 시각 선호·잔진동 개선 판정은 별도다.

## 화면 가림 수정

두 캐시는 각각121상태·1813노드·3456표시 면을 포함하고 유한한 움직임을 가진다. 초기/1초 렌더에서도 두 결과가 로드된 것을 확인했다.
다만 기존 고정 카메라는 사이드바를 제외하지 않아960×800·사이드바300px 조건에서 왼쪽 천이121상태 중40상태에서 완전히 가려졌다.
1280×800·사이드바450px 조건에서도15상태가 완전히 가려졌다. 사용자 환경의 어느 쪽 미표시인지 답변은 아직 없으므로 관찰한 로딩 문제와 동일한 원인이라고 단정하지 않는다.

공용 `view_shell_recording.fit_recording_camera`는 전체 저장 궤적의 표시 범위를 원근 투영해 사이드바 오른쪽 영역 안에 맞춘다.
천의 위치/축척/물리 데이터를 바꾸지 않고 카메라만 조절한다. 창 크기·UI 배율이 바뀌면 다시 맞추며, 사용자 카메라 조작 후에는 `Fit all recordings` 버튼을 쓸 수 있다.
로드된 결과 수를 표시하고 기존 세 조건 배치·색상·시간/재생 기능을 유지했다.

[화면 검증 JSON](bending_stiffness_visibility_checks.json)의 `original_at_960x800`, `projection_checks`, `evidence_folder`에 재현·수정 검증을 남겼다.
두 궤적 전121상태를5가지 창/UI 조건으로 투영해 표시 영역 안에 들어오는 것을 확인했다. 단일/세 결과 배치도 회귀 검사에 포함했다.
공용 뷰어·GPU 저장 뷰어·굽힘 강성 실행기38개 CPU 검사 통과, 기본1280폭과 좁은960폭에서 실제 UI 포함 렌더를 확인했다.
원본 NPZ·보고서·동결 runtime·manifest는 보존했다. 물리 시뮬레이션을 재실행하거나 진동 개선 여부를 판정하지 않았다.

## 검증과 한계

[실행기](../../../code/wind3dgs/evaluation/teacher_gpu_bending_stiffness.py)의 `prepare`, `verify`, `worker`, `run`, `cache_case`를
[검사 코드](../../../code/tests/test_gpu_bending_stiffness.py)의 준비 당시11개 CPU/모의 실행 검사로 확인했다. 시간 호환 회귀를 추가한 현재20개 검사 결과는 위 수정 절을 따른다.
실제 작은 P3 모델의 막/굽힘 에너지·질량·경계 항, 원본 solver 보존, 다른 설정 변경 거부,
raw 전달·외력 절단, 첫 검사 실패 시 본 계산 중단, 기존 로그 보존, 뷰어 시간/소산 오류 거부, 기본status의 비실행을 포함한다.

실제1813노드 입력에서도 네 raw 배열·질량·막 강성·굽힘 행렬·경계 항·외력 절단·동결 파일을 확인했다.
동결 원본 솔버의 실제 함수 서명으로 smoke/wind 호출을 모의 검증했다. 장치 조회와 적분 함수를 대체한 검사이며 실제 GPU 프레임 검산을 대신하지 않는다.
준비 당시 기존 원본 뷰어 캐시121상태만 확인했고 새 후보는 가상 결과로 검사했다. 이후 이번 수정에서 실제 후보까지 두 캐시와 한 프레임 렌더를 확인했다.

원본 상태에서 물성을 바꿔 이어가는 단기 비교이므로 초반 전환 반응과 후반 움직임을 구분해야 한다.
큰 펄럭임이 살아 있는지, 잔진동이 줄었는지, 접힘이 과해지지 않았는지를 함께 본다. 강성 감소만으로 진동 제거·계산 가속을 보장하지 않는다.
시간 수렴1%/10% 기준은 서로 다른 물성의 움직임 차이에 적용하지 않는다. 새로운 수치 합격 기준을 추가하거나 기존 solver 검산을 완화하지 않았다.

관련 R1 `sec:r1-cg-development-entry`를 확인했다. 이번은 별도 물성 진단 준비이며 기존 수렴 결과·시각 선호를 새 후보의 학습 적격성으로 승계하지 않는다.
canonical 수식·R 완료 체크·TeX/PDF는 변경하지 않았다. code·experiments 미커밋, commit/push/fetch·외부 다운로드 없음.
