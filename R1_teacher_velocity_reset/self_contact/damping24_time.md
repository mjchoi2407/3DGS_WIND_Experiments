# 감쇠24 사각형64/128 교차 장치 실행

## 현재 상태

- 사용자 후속 관찰: 감쇠24의wind 움직임이 둔하다. 수치 통과와 별개로 시각 채택은 보류하고 [wind8/16 비교 준비](wind_damping.md#현재-상태)로 이어간다.

- 완료 결과 [전용 뷰어](#완료-결과-뷰어) 연결: 기본64·wind 시작5초,128 선택 가능. 두600프레임 캐시 검증과64 한 프레임 실제 렌더 확인. 사용자 wind 시각 판정은 별도다.

- 확인일2026-09-29. [서브 완료 결과 분석](#서브-완료-결과-분석)의 같은 RTX5070 감쇠24 사각형64/128이 각각600프레임 완주했다.
- 처음부터 감쇠24를 적용한 preload1/calm4/wind5초의 독립10초 궤적이다. 이후 논의한 공통5초 상태 재사용/wind-only 방식은 적용하지 않았다.
- 기존 비교기를 CPU 실행한 결과 `numerical_pass_visual_pending`: wind 전체/후반2초 위치·속도 모두 사전 기준 통과.
- 1200프레임 저장 flag 오류0·감쇠 검산 오류0·복구0. 원본 입력/결과 hash·연결·시간 검사 및 비교 산출물6개 hash 확인.
- [결과 식별·수치·한계](damping24_pair_results.json)의 `comparison_report`, `windows`, `runs`가 상세 근거다. 분석에서 새 GPU 계산은 하지 않았다.
- 이 설정의 기본64를 유지할 수치 근거가 생겼다. 현재 결과 때문에256 추가 실행을 요구하지 않는다. wind 시각 판단이 다음 단계다.
- 다른 씬·공간 민감도·연속 재료 감쇠 채택·학습 적격성·R1 완료 판정은 미완료다. 무감쇠 v13의 이전 비교 실패는 별도 결과로 보존한다.
- [단일 PC 실행](#단일-pc-통합-실행), [준비 검증](damping24_pair_checks.json), [이전 개별 입력 준비](damping24_time_checks.json)를 당시 근거로 유지한다.
- R1의 CG 개발 진입/시각 대기 경계를 확인했다. 잠정 감쇠 모델의 제한 진단 결과이며 canonical 판정 변경은 없어 TeX/PDF 수정·빌드는 없다.

## 단일 PC 통합 실행

메인컴 프로젝트 루트에서:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_v13_damping24_pair.sh --action run
```

서브컴에서 같은 스크립트를 사용하려면:

```bash
bash /mnt/wind3dgs/experiments/R1_teacher_velocity_reset/self_contact/run_gpu_v13_damping24_pair.sh --action run
```

둘 중 실제 계산할 **한 PC에서 한 번만** 실행한다. 자동64→128 순차 실행이며 사용자가 두 명령을 따로 이어줄 필요가 없다.
기본 action은 status이며 run에서만 cuda:0을 확인하고 시뮬레이션을 시작한다.
서브는 로컬 `WIND3DGS_PYTHON` 또는 `~/wind3dgs-worker/venv/bin/python`을 사용한다.
메인은 프로젝트 `.venv/bin/python`을 사용하며 `WIND3DGS_PYTHON`으로 명시할 수 있다.

같은 호출 경로에서 `--action status`는 상태, 두 실행 완료 후 `--action compare`는 CPU 비교 보고서를 새 timestamp 폴더에 만든다.
run 뒤 비교를 자동 시작하지는 않는다. 비교 수치 통과도 최종 시각/학습 승인이 아니다.

메인 기본 출력은 `experiments/artifacts/runs/p3_self_contact/rectangle_gpu_drape_v13_damping24_single_pc_01`,
서브 기본 출력은 `/mnt/wind3dgs-sub-results/damping24_single_pc_01`이다.
각각 `steps64/`, `steps128/`, `pair.json`을 가지며 원본에 결과를 쓰지 않는다.
다른 경로는 `--out <새 경로>`로 지정하고 이후 status/compare에도 동일하게 전달한다.
기존 출력·로그·실패 준비 경로를 보존하며, 자동 재개/덮어쓰기하지 않는다. lock으로 같은 묶음의 중복 실행을 거절한다.

GPU는 첫 run에서 두 묶음에 동일하게 기록하고, 이후 다른 모델에서 해당 묶음을 실행하면 거절한다.
한 프로세스가 같은 PC의 cuda:0으로 두 worker를 순차 호출하므로 앞선 교차 GPU 혼합 조건이 해소된다.
원본64/128의 동결 runtime을 그대로 복사하며 현재 worktree의 solver를 다시 동결하지 않는다.

## 실행

이 절은 앞선 교차 장치 개별 실행 명령이다. 현재는 위 단일 PC 통합 실행을 사용한다.

메인컴 프로젝트 루트:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_v13_damping24_64.sh --action run
```

서브컴(현재 worker 디렉터리에서도 실행 가능):

```bash
bash /mnt/wind3dgs/experiments/R1_teacher_velocity_reset/self_contact/run_gpu_v13_damping24_128_sub.sh --action run
```

서브 래퍼는 `WIND3DGS_PYTHON` 또는 로컬 `~/wind3dgs-worker/venv/bin/python`을 사용한다.
읽기 전용 공유의 준비된128 묶음을 `/mnt/wind3dgs-sub-results/damping24_steps128_01`로 최초 run 때 복사한 후 동결 runtime으로 실행한다.
공유 코드/입력 폴더에는 결과를 쓰지 않는다. 다른 결과 경로는 `--out <새 경로>`로 지정한다.
복사 실패 staging·이미 존재하는 출력/로그를 덮어쓰거나 재시작하지 않는다.
각 명령의 `--action run`을 `--action status`로 바꾸면 상태만 확인한다. 기본 action도 status다.
두 컴퓨터에서 동시에 실행해도 출력 경로가 분리되며, 각 궤적 내부의 세 구간은 순차 실행한다.

프로젝트를 로컬 쓰기 가능 디렉터리에 둔 서브 환경은 `run_gpu_v13_damping24_128.sh --action run`도 사용할 수 있다.
새 입력 준비는 각 일반 래퍼의 `--action prepare --out <새 경로>`다. 필요하면 prepare에만 `--gpu-model <모델명>`을 주어 같은 GPU에서 후속 비교할 별도 묶음을 준비할 수 있다.
이미 준비된 기본 경로에는 prepare를 반복하지 않는다. run은 동결 대상 GPU와 실제 GPU가 다르면 solver 전에 거절한다.

## 감쇠 및 비교 경계

`diagnostic_frame_damping_s_inv=24`가 suite와 각 phase plan의 실행 선택이다.
`damped_trajectory`에는 대상 GPU·단계·감쇠 법칙·구간·원본 manifest를 기록한다.
원본에서 물려받은 `gravity_experiment.extra_damping=false`는 원본 프로그램 설명이며 새 선택값을 덮지 않는다.
실제 프레임의 `frame_velocity_damping` 기록으로 적용과 검산을 확인한다.

공통 실행기의 `execute_shape`는 명시된 감쇠를 preload/calm/wind 모두에 전달한다. 옵션 없는 기존 실행은 원래 경로를 유지한다.
비교기는 감쇠율 일치와 프레임의 감쇠 검사 통과도 확인하도록 보강했다. GPU 모델 불일치는 계속 거절한다.
현재 두 결과는 wind 시각/운동 경향을 확인할 교차 장치 진단이다. 시간 민감도만 판단하려면 이후 같은 GPU의64/128 쌍이 필요하다.
감쇠는 프레임 시작마다 `exp(-24/60)`을 적용하는 분할 속도 감쇠다. 연속 재료 점성·전 구간 안정성·학습 적격성의 확정 근거는 아니다.
R1 기준·완료 판정은 변경하지 않아 TeX/PDF 수정·빌드는 없다.

## 서브 완료 결과 분석

2026-09-29 확인. 실행 ID `20260929T002107Z-65221d3a61d34d0f93b4d01006eb5602`.
바로 앞 `20260929T001755Z-04ca30a89fa04a87a0cfdbde973a8b22`는 `prepared_not_run`이며 완료 결과로 세지 않는다.
완료본은 각 초기 상태부터 감쇠24를 적용한 사각형10초이며, 두 실행 모두 RTX5070이다.

[비교 HTML](../../artifacts/runs/sub_pc/20260929T002107Z-65221d3a61d34d0f93b4d01006eb5602/simulation/comparison_20260929T015341221133Z/index.html),
[원본 비교 JSON](../../artifacts/runs/sub_pc/20260929T002107Z-65221d3a61d34d0f93b4d01006eb5602/simulation/comparison_20260929T015341221133Z/report.json),
[요약 검증 JSON](damping24_pair_results.json).

| 판정 구간 | 위치 차이/L (%) | 위치 RMS 차이 (µm) | 속도 차이/기준 속력 (%) | 판정 |
|---|---:|---:|---:|---|
| wind5–10초 | 0.00006582 | 0.8227 | 0.2626 | 통과 |
| wind8–10초 | 0.00009892 | 1.2365 | 0.3800 | 통과 |

기준은 위치1%·속도10%, L=1.25m, 공통512점의 면적·시간 RMS다.
preload/calm/full도 각각 통과했으며, 최종 상태는 `numerical_pass_visual_pending`이다.
별도 물리 정답과의 오차나 수렴 차수를 산출한 것은 아니다.

64/128 각각600프레임, 실패·재시도·저장 검산 오류·감쇠 검사 오류0.
Top 보고서 wall은 각각1448.75초(24.15분),2483.09초(41.38분)이며 독립 성능 벤치마크는 아니다.
Wind 기준 속력 RMS는 약0.13965m/s,5초 상태 대비10초 위치 RMS 이동은 약123.79mm다.
움직임이 모두 사라져서 비슷해진 결과는 아니지만, 바람 반응이 자연스러운지는 원본 메시의 시각 검토가 필요하다.

기본64 유지가 합리적이며 추가256은 현재 수치로 요구되지 않는다.
무감쇠 v13은 다른 설정이므로 그 실패를 이번 통과로 덮지 않는다.
분석은 원본 manifest·raw 기록·감쇠 기록과 기존 비교기를 검증했으며 기존 GPU 물리 검산 자체를 CPU로 재실행하지 않았다.
원본 결과/동결 입력/실행 중 작업은 수정하지 않았다. 시각 승인·공간 민감도·최종 teacher/학습 판정은 보류다.

## 완료 결과 뷰어

기본64의 원본 천 메시를 전체5초(wind 시작)에서 일시정지 상태로 연다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v13_damping24.sh
# 기본128 결과 선택
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v13_damping24.sh --steps 128
# 처음부터 확인
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v13_damping24.sh --time 0
```

Space로 재생, Time 슬라이더는 전체0–10초, Playback speed로 느린 재생을 선택한다.
기본64/128은 각각 별도 창으로 실행할 수 있으며 현재 스크립트는 한 결과를 표시한다.
정확한 입력은 완료 run `20260929T002107Z-65221d3a61d34d0f93b4d01006eb5602/simulation/steps64` 또는 `steps128`이다.

서브컴에서는 동일 스크립트 경로 앞에 `/mnt/wind3dgs/`를 붙인다.
서브의 `WIND3DGS_PYTHON` 또는 worker 로컬 venv를 사용하고 표시 캐시는 worker 로컬 cache에 저장한다.
메인은 프로젝트 venv와 기존 버전별 표시 캐시를 사용한다. 원본 결과를 덮어쓰지 않는다.
`--prepare-only`는 렌더 없이 캐시만 검증·준비한다.

2026-09-29 검증: 셸 구문,64/128 각각600프레임 hash·시간·고정점·raw 구간 연결/최종 checkpoint 확인 및 캐시 생성 통과.
기본64는 전체5초의 한 프레임 headless 렌더와 이미지 확인을 완료했다. 메인 WSL의 CUDA/OpenGL 직접 공유는 불가해
기존 viewer의 버퍼 복사 경로로 정상 표시됐으며 물리 solver fallback과는 무관하다.
128의 실제 렌더·서브 GUI·사용자의 연속 wind 시각 승인은 이번 검사에 포함하지 않았다.
시뮬레이션/학습은 실행하지 않았으며 R1 판정과 TeX/PDF는 변경하지 않았다.
