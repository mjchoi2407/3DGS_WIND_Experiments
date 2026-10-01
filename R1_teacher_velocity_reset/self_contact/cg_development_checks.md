# CG 개발용 Teacher 검사와 스크립트 실행 계획

## 현재 상태

2026-09-28 [v13 사각형 기본128/복구256 실행·비교 연결](v13_time128.md#현재-상태)을 준비했다.
원본 동결 코드/입력 보존·CPU25개 검사 확인. 실제128 GPU 실행·시간 민감도 판정은 미실행이다.
이 좁은 v13 시간 비교 준비는 아래 당시 v12 통합 T/S·예산 runner 계획과 구분한다.

2026-09-28 후속 사용자 선택으로 [v13 초기 굽힘·1/4/5초](three_scenes_gpu_v13.md#현재-상태) 시각 후보를 먼저 준비했다. 서브 컴의 완주·저장 결과 연결을 확인했으며 시각 채택은 아직 별도다.
[서브 컴 뷰어·분석·비교 명령](three_scenes_gpu_v13.md#서브-컴-완료-결과와-연결)을 따른다. 아래 v12 기준 B/T/S 계획은 당시 계획으로 보존한다. v13을 채택하면 비교 대상 모두 같은 초기 상태·외력·시간축으로 맞추고, wind 평가 창도5–10초와 마지막2초8–10초로 갱신해야 한다. 서로 다른 v12/v13 결과를 시간·공간 민감도 쌍으로 쓰지 않는다.

2026-09-28 사용자가 CG 목적에 맞춰 초기 검증을 완화하는 안을 채택했다.
계약은 [R1](../../../ideas/development/r1_teacher_probe_oracle.tex)의
`sec:r1-cg-development-entry` / `cg_teacher_dev_v1`, 제한 학습 범위는
[R2](../../../ideas/development/r2_single_case_global_overfit.tex)의 `sec:r2-cg-development-entry`가 소유한다.
기준은 위치 RMS 1%L·속도 RMS 10% 및 시각적 이상 없음이며, 대표 씬의 두 해상도 비교를 먼저 한다.
이 문서는 실행 설정·명령·순서와 미구현 범위를 소유한다. **뷰어와 CPU 처짐 분석·512점 매핑은 구현·검증 완료, CPU 비교기는 구현 완료, T/S 준비·실행기는 미구현이다.
[비교기 실제 CLI·검증 범위](cg_comparator.md#현재-상태)를 따른다.**
[분석/매핑 명령·v12 근거·24 해상도 제약](motion_analysis.md#현재-상태)을 따른다.
[뷰어 실행·조작·검증](three_scenes_gpu_v12.md#연속10초-뷰어)을 따른다. 새 비교 묶음·시뮬레이션·학습은 수행하지 않았다.
기존 [v12 결과·복구·비용](three_scenes_gpu_v12.md#v12-사용자-실행-결과)은 보존하며 새 기준으로 자동 통과시키지 않는다.
다음은 v13 시각 확인과 비교/준비/실행 래퍼 구현이다. 공통 평가점은 구현됐지만 GS 매핑 완료는 아니다.
본 계산은 사용자가 직접 수행하며 첫 묶음은 사각형 신규2개·합계6시간 예산이다.

## 확정된 첫 비교 묶음

기준 원본은 [v12 manifest](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/manifest.json),
SHA256 `0be6397195b505b314fa8b8913aa41b28c2249593f366ea2c05529f5536c994e`다.
사각형 각 phase의 `plan.json`에서 `reference_rectangle_resolution=16`, `substeps=64`를 확인했다.
구간은 preload120/calm240/wind240프레임, 60Hz 연속10초다.

| ID | 용도 | resolution | 기본/복구 substep | 비교 상대 | 새 본 계산 |
| --- | --- | ---: | --- | --- | --- |
| B | 기존 사각형 v12 | 16 | 64 / 128 | T의 기준 원본 | 없음 |
| T | 시간 간격 민감도 | 16 | 128 / 256 | B ↔ T | 1개 |
| S | 메시 포함 경로 민감도 | 24 | 128 / 256 | T ↔ S | 1개 |

각 실행은 rest·초기 속도부터10초 전체를 계산하고 phase 간 raw hi/lo를 연속 전달한다.
B의 wind 직전 상태를 T/S의 시작점으로 쓰지 않는다. 복구는 같은 code1/code2 조건의 한 번 dt/2이며
실제 dt·폐기 증거·비용을 유지한다. 기존 문구의 고정 `128단계 복구`도 새 실행에서는 기본 단계 수의
2배로 표시하도록 실행기 metadata/로그를 일반화해야 한다.

물성·형상 크기·부착의 물리 영역·중력/바람 프로그램·60Hz 공력 평가/hold 규칙·공식 solver 허용오차,
접촉 ON·barrier 계수·proxy subdivision3·최소 간격·swept2M·cuDSS 결정성1은 유지한다.
각 궤적의 공력은 해당 상태에서 다시 계산하며 B의 `held_force_n`을 T/S에 강제하지 않는다.
S는 구조 메시 증가와 함께 proxy 표본 수도 달라지는 **전체 경로의 해상도 민감도**다.
Unweighted IPC의 접촉 에너지가 표본 수에 의존하므로 독립 접촉 공간 수렴으로 명명하지 않는다.
성능·수치 비교의 첫 장치는 B와 같은 GTX1080Ti로 고정하며 다른 장치 확대는 별도 계획이다.

새 suite의 예정 경로는 `experiments/artifacts/runs/p3_self_contact/cg_teacher_dev_v1/`이다.
그 아래 `time_128/`, `space_24_128/`, `comparisons/`, `budget.json`으로 구분한다.
기존 경로가 있으면 새 suite 이름을 요구한다. 원본 B 및 동결 완료된 T/S 입력을 수정하거나 덮어쓰지 않는다.

## 기존 도구와 미구현 경계

- [기존 실행 셸](run_gpu_three_scenes.sh)은 완료된 v12를 가리킨다. `--action status`는 사용 가능하지만
  기존 출력에 `--action run`을 다시 실행하지 않는다.
- [GPU suite main](../../../code/wind3dgs/evaluation/teacher_gpu_contact_scene_suite.py)의 `main`에는
  `--shape`, `--out`은 있으나 substeps·rectangle resolution을 바꾸는 CLI가 없다.
  준비를 마친 run의 JSON과 hash를 수동으로 고치는 방식은 사용하지 않는다.
  현재 `rectangular_mesh`는4/8/16/32만 허용하므로 계획된24는 입력 runner 구현 때 지원/검증해야 한다.
  매핑 확인용16/32 정적 검사는 이 계획을 대체하지 않는다.
- [현재 모델 생성기](../../../code/wind3dgs/evaluation/teacher_scene_model.py)의 `build_scene_model`은
  `reference_rectangle_resolution`을 읽는다. 새 준비 경로에서만16/24 및 모든 phase 설정을 동결해야 한다.
- [기존 뷰어 셸](view_completed_gpu_scenes.sh)과
  [뷰어 prepare](../../../code/wind3dgs/evaluation/view_gpu_contact_recording.py)는 v11 손수건·삼각형의
  셸 기본값은 v11 분기용이다. 현재 prepare 모듈은 v12/v13 연속 재생도 지원하며 각 버전 전용 셸을 사용한다.
- [기존 수렴 비교기](../../../code/wind3dgs/evaluation/teacher_convergence.py)의
  `compare_teacher_refinements`는 Teacher/probe artifact를 요구한다. v12 raw NPZ와 P3 공통 평가점의
  연결 중 raw→공통512점 위치/속도는 구현됐다. 직접 run 경로를 받는 CPU 비교기도 구현됐으며, 단순 노드 RMS를 공간 비교의 대용으로 사용하지 않는다.

## 스크립트 단위 구현과 사용 순서

아래에서 **아래 표의1번 뷰어와4/6번 비교기는 구현 완료**이며 입력 준비·실행 runner는 예정 인터페이스다.
별도 선행 도구인 `analyze_gpu_motion.sh`와 `prepare_gpu_surface_samples.sh`는 구현 완료했다.
셸은 얇은 래퍼로 두고, 재사용 구현은 `code/wind3dgs/`가 소유한다.
모든 스크립트의 상대 경로 기준은 프로젝트 root다.

| 순서 | 예정 스크립트 | 역할·입출력 | 진행 조건 |
| --- | --- | --- | --- |
| 1 | [view_gpu_v12.sh](view_gpu_v12.sh) **구현 완료** | B의 세 씬을600프레임·전체0–10초로 재생, 별도 표시 캐시·카메라 설정 생성 | 원본 해시·승인 상태·phase 경계 검증 후 표시; 물리 재계산 없음 |
| 2 | `prepare_gpu_cg_checks.sh` | B를 읽어 T/S 신규 입력·runtime·512 평가점·기준값·예산 동결 | 출력 미존재, 모델·공력·연속 시간·복구 배수 검증; 본 실행 없음 |
| 3 | `run_gpu_cg_time.sh` | T만 순차 실행, 상태·원본 오류·복구·비용 저장 | prepare 검증, 장치/프로세스/남은 예산 확인; 사용자 직접 실행 |
| 4 | [compare_gpu_cg_checks.sh](compare_gpu_cg_checks.sh) `--axis time` **구현 완료** | B/T 공통점 오차 JSON·곡선·겹쳐보기 및 시각 검토 기록 | T 완주·검산·hash 통과; 시각 검토 전에는 최종 pass 발행 금지 |
| 5 | `run_gpu_cg_space.sh` | S만 실행 | time 비교/시각 검토 pass, 남은 예산 확인; 사용자 직접 실행 |
| 6 | [compare_gpu_cg_checks.sh](compare_gpu_cg_checks.sh) `--axis space` **구현 완료** | T/S 같은 평가점·시간 창에서 비교 | S 완주·검산·hash 통과; contact 포함 경로 민감도로 명시 |
| 7 | `check_gpu_cg_learning_ready.sh` | 비교2개·시각·GS 매핑·작은 network-free fit의 근거를 집계 | 누락 시 blocked 사유; GS 매핑/fit 자체를 이 스크립트가 자동 완료하지 않음 |

작업1 뷰어와 공통점 변환·4/6 비교기는 준비했다. 남은2/3/5는 입력 준비·실행·예산 runner이며 실제 두 정밀도 비교는 아직 수행하지 않았다. 작업7은 그 이후의 GS 매핑/기준 모델 작업에 연결한다.
해당 학습 진입 보고서가 통과하기 전에는 학습 스크립트를 준비 완료로 표시하지 않는다.

### 구현 후 사용할 예정 명령

아래 묶음 전체는 아직 실행할 수 없다. prepare/run은 미구현이고 compare만 준비됐지만 새 T/S 결과는 없다. 이름·옵션을 바꾸면 이 절도 함께 갱신한다.

```bash
CG_BASELINE=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12
CG_SUITE=experiments/artifacts/runs/p3_self_contact/cg_teacher_dev_v1
CG_SCRIPTS=experiments/R1_teacher_velocity_reset/self_contact

bash "$CG_SCRIPTS/prepare_gpu_cg_checks.sh" --baseline "$CG_BASELINE" --out "$CG_SUITE"
bash "$CG_SCRIPTS/run_gpu_cg_time.sh" --suite "$CG_SUITE" --action run
bash "$CG_SCRIPTS/run_gpu_cg_time.sh" --suite "$CG_SUITE" --action status
bash "$CG_SCRIPTS/compare_gpu_cg_checks.sh" --candidate "$CG_BASELINE" --reference "$CG_SUITE/time_128" --axis time --out "$CG_SUITE/comparisons/time"
# time 비교와 시각 검토를 마친 뒤 다음 명령을 사용한다.
bash "$CG_SCRIPTS/run_gpu_cg_space.sh" --suite "$CG_SUITE" --action run
bash "$CG_SCRIPTS/run_gpu_cg_space.sh" --suite "$CG_SUITE" --action status
bash "$CG_SCRIPTS/compare_gpu_cg_checks.sh" --candidate "$CG_SUITE/time_128" --reference "$CG_SUITE/space_24_128" --axis space --out "$CG_SUITE/comparisons/space"
```

현재 실행 가능한 뷰어와 상태 확인 명령은 다음과 같다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v12.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action status
```

## 비교 출력과 중단 기준

수치 판정은 R1 `cg_teacher_dev_v1`의 정의를 따른다. 설정·probe·카메라와 평가 창은
정밀 결과를 보기 전에 prepare에서 hash로 동결한다. Wind6–10초와 후반8–10초를 각각 판정하며,
preload/calm은 보조 지표로 보존한다. 한 지표나 한 구간만 통과한 결과를 전체 pass로 올리지 않는다.
표면512점은 사각형 rest의32×16 cell 중심과 양의 면적 가중치로 정의한다.
고정점·끝점은 별도 보조 지표다. P3 10-shape 보간의 constant/affine 재현·단위/속도 일치를 검사한다.

예정 비교 산출물은 `comparisons/time/report.json`, `comparisons/space/report.json`,
각 곡선·겹쳐보기 영상 및 카메라/hash와 검토 사유가 있는 시각 판정 기록이다.
수치 pass/시각 대기/실패/예산 미완료를 구분하고 검사 대상 frame·probe 분모를 보존한다.
통과 시 다음 단계로 가며, 미달이면 해당 오차가 드러난 구간과 매핑/접촉/시간축부터 진단한다.
세 번째 정밀도·추가 씬·GPU 장치 비교·budget 연장은 자동 추가하지 않는다.

총 예산21,600초는 T/S 두 실행의 setup·계산·검산·폐기 시도·저장을 포함한다.
사용자는 run을 하나씩 시작하며 같은 GPU의 실험은 동시 실행하지 않는다.
새 run에서 프레임 완료 후 예산을 확인하고 소진되면 `budget_exhausted`로 종료한다.
진행 중 프레임을 강제로 끊지 않으므로 최대 마지막 한 프레임만큼 예산을 초과할 수 있고 그 비용도 기록한다.
기존 v12나 다른 작업을 중단하는 기능은 포함하지 않는다. 외부 종료·실패·budget 종료의 prefix는
전체10초 완료로 집계하지 않으며, 재실행은 새 출력과 별도 사용자 판단을 요구한다.

## 완료 판정과 학습 연결

실행 완료, 민감도 검사 통과, 제한 개발 학습 진입을 별도 상태로 둔다.
두 비교 pass 뒤에도 Teacher→GS 변위/속도·고정점·회전·SPD·단위/공력 의미와 작은 응답 fit을 확인해야 한다.
조건을 만족한 하나의 object/input/GS에만 새 진입 보고서를 발행한다.
기존 run의 `training_eligible=false`는 바꾸지 않으며 개발 scope와 근거 hash를 따로 기록한다.
정식 R1/R2 완료·다물체/다입력 성능·강한 자기접촉 지원은 주장하지 않는다.
시간·공간 검사를 모든 씬에 한꺼번에 늘리거나 미세한 솔버 오차를 줄이는 추가 최적화를 먼저 하지 않는다.
