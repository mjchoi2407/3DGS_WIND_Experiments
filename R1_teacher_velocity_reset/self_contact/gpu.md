# 셀프 컬리전 GPU 실행·세 씬 스크립트

## 현재 판정

**접촉 수식·BVH는 v5로 고정했고, 현재 사용자 실행 묶음은 GPU dt/2 제한 복구를 더한 v10이다.**
소폭 가속을 위한 추가 최적화는 중단한다.
고정 범위와 재검토 조건은 [v5 기준](broadphase_v5.md#실행-기준-고정추가-최적화-종료)을 따른다.
아래는 초기 v1의 실행·실패 근거이며 보존한다.
후속 정밀 기하 인증으로 기존12개 미인증 구간을 해결한 결과와 실행 상태는
[정밀 기하 보강 보고](refined_geometry.md)를 따른다. 개별 세 스크립트는 현재 같은 승인 기준의
v10을 사용하며, 최적화·성능 판정은 [BVH 개선](broadphase_v5.md), 진행 출력과 복구 범위는
[실패 프레임 재현·복구](frame112_recovery.md)를 따른다. v8 원시 계측과 실패는
[v8 기록](frame_timing_v8.md)에 보존한다.

2026-09-22의 초기 v1 판정: GTX1080Ti에서 **GPU 접촉 구현과 세 씬 연결 시험 완료**.
후보 탐색·힘·연속 충돌 검사·솔버·독립 검산·프레임 복원까지 GPU에서 실행했다.
직사각형/손수건/삼각 깃발의 중력·최대풍6프레임,384개 substep은 모두 승인됐다.
당시 v1의 각 씬 preload2초+calm4초+wind4초 전체 실행은 시작하지 않았다.
이번 smoke는 서로 독립인 rest 시작 검사이므로 장기 처짐·실접촉 궤적 완주 근거가 아니다.

별도 실제 접촉6사례는 CPU IPC와 위치·힘·시간 CCD 및 기하 실패 판정이 일치했다.
엄격한 기하 기준까지 통과한 것은 계수1,000의 저속2사례다. 다른4사례는 기하 충분조건
미해결로 거절되었으며, 성공한 동역학 사례로 세지 않는다. Gate/학습 적격성은 올리지 않았다.

구현 수식·장치별 위치·정밀도·GPU 가속의 한계는 [code 계약](../../../code/docs/p3_gpu_self_contact.md)이 소유한다.

## 세 시뮬레이션 실행

workspace 루트에서 실행한다. v5 직사각형 실행은 preload/calm을 완료했지만 wind105번째 시도에서
검산 실패해 rollback 후 종료됐으며 원본을 보존했다. 아래 스크립트는 같은 BVH v5 수치 경로에
장치별 시간을 자동 보정하고 유한한 GMRES code2만 GPU dt/2로 한 번 재시도하는 새 `manual_v10` 출력으로 준비했고
본 시뮬레이션은 아직 미실행이다.
아래 개별 스크립트는 해당 씬이 미실행일 때 실제 전체 시뮬레이션을 시작한다. 한 GPU에서는 하나씩 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_rectangle.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_handkerchief.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_triangular_flag.sh
```

세 개를 자동 순차 실행하려면 다음 하나만 실행한다(개별 실행과 중복 실행하지 않는다).

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
```

상태 확인:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action status
```

현재 스크립트 출력은 `experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10/<shape>/outputs/`다.
v1 비교 원본·중단된 v2·기존 manual_v2/v3/v4와 섞지 않는다. 현재 성능 판정은 [BVH 개선](broadphase_v5.md),
과거 관측 비용은 [v2 비용 보고](cost.md)를 따른다.
`<shape>/run.log`와 phase별 `report.json`, 프레임별 `frame_XXXX.npz`를 남긴다.
매 프레임 종료 직후 터미널에도 GPU 프레임·solver·collision·audit 시간과 GMRES 누적 횟수를
기본 출력한다. solver/collision/audit은 중첩 구간이므로 합산하지 않으며 장치별 PTX 시간은
프레임 wall에 자동 보정한다. 상세 의미는 [v9 보고](frame_timing_v9.md)를 따른다.
NPZ는 raw `u_hi/u_lo/v_hi/v_lo`, 모든 substep 검산·flags, 외력을 포함한다.
새 접촉 ON preload의 같은 위치·속도에서 calm/wind를 분기하며 속도 reset은 없다.
기존 contact-OFF checkpoint·CPU 기준 결과를 초기 상태로 재사용하지 않는다.
실패하면 GPU에서 프레임 시작 상태로 복원하고 `failed_frame_rollback.npz`를 남긴다.
원래 오류가 유한한 code2이고 이전 승인 구간의 모든 검산을 통과했으면 GPU에서 같은 시작 상태·외력·
허용오차를 유지하며 dt/2·128단계로 한 번 재실행한다. 다음 프레임은 기본64단계다.
접촉/기하/CCD/audit 오류와 재시도 실패는 승인하지 않는다. 폐기 시도 검산은 별도 NPZ에 보존한다.
실패한 preload는 후속 phase를 시작하지 않는다. 중단 결과를 덮어쓰거나 자동 재개하지 않는다.

다른 설정은 새 run에서 준비해야 한다. 기존 출력 경로는 재사용할 수 없다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh \
  --action prepare --out experiments/artifacts/runs/p3_self_contact/my_gpu_trial \
  --barrier-stiffness 1000
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh \
  --action preflight --out experiments/artifacts/runs/p3_self_contact/my_gpu_trial
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh \
  --action smoke --out experiments/artifacts/runs/p3_self_contact/my_gpu_trial
# smoke 승인과 설정 검토 후 같은 --out으로 --action run
```

## 입력·환경·변경 범위

- 원본: `experiments/artifacts/runs/teacher_timestep_search/newmark_dt_gauss_retry_bend500_v1`.
  원본 mesh·plan·wind·gravity의 byte/hash를 보존한다. 굽힘1/500은 이미 물성에 반영됐으므로 다시 곱하지 않는다.
- 60fps,64substeps/frame,dt=1/3840s. E=22,360,679.774997897Pa, ν=0.3,
  h=0.00044721359549995795m, 면밀도0.1kg/m². 중력 ramp/바람/고정 조건은 원본 그대로다.
- 접촉 시험값: proxy subdivision3, 최소 간격1mm, 활성 범위10mm, k=1,000,
  고정 공간 예산 없음. 물성 h에서 자동 산출한 접촉 두께나 최종 calibration이 아니다.
- 새 실행: R64 hi/lo Newmark, 실제 tangent는 shell+contact, current 보조 행렬은 shell-only 근사.
  공식 허용오차·내부 force fraction0.3·EW cap1e-4·`local_metric`을 유지한다.
  원본 contact-OFF M1/M2/Gauss 자동 정책은 이 경로에 적용하지 않는다. CPU/Gauss/contact-OFF fallback 없음.
- 실제 장치: NVIDIA GTX1080Ti11GiB, driver582.28/API13000. Python3.12.3,
  NumPy2.4.4, SciPy1.18.1, ipctk1.6.0, Warp1.17.0. 정확한 Python patch와 package 버전은
  [동결 suite](gpu_checks/scenes_suite.json)의 environment가 최종 기준이다.
  cuDSS0.7.1과 native shim은 원본 manifest에 맞는 library/source를 복사했다.
  별도 네트워크 설치·외부 checkout 수정·git fetch는 하지 않았다.
- GPU 실제 계산은 FP64, AABB만 외향 여유를 둔 FP32다. 전체 FP32나 RTX5070 검증은 아니다.
- 고정 topology/초기 구조와 파일 I/O는 CPU다. 프레임/step/audit graph의 cuDSS 자식과
  조건 분기 본문까지 검사하여 host copies=0, host callbacks=0을 확인했다.

## 세 씬 실행 결과

GTX1080Ti 단독 순차 실행. setup/컴파일·파일 저장을 제외한 GPU 계산+독립 검산 시간이다.
짧은 표본의 시간이며 장기 속도나 CPU 대비 가속 배수로 일반화하지 않는다.

| 씬 | P3 노드 / proxy 면 | 중력64단계 | 최대풍64단계 | 최대 힘 잔차 비율 | 판정 |
| --- | ---: | ---: | ---: | ---: | --- |
| 직사각형 | 1,813 / 3,456 | 12.613s | 22.716s | 0.10512 | 모두 flag0 |
| 손수건 | 925 / 1,728 | 9.247s | 14.192s | 0.05049 | 모두 flag0 |
| 삼각 깃발 | 703 / 1,296 | 8.835s | 13.811s | 0.12680 | 모두 flag0 |

힘 잔차 비율의 승인 한도는1이다. 위 구간에는 활성 접촉이 없으므로 실제 접촉 시험은 다음 절과 분리한다.
직사각형 rest의 unfiltered VF+EE20,139,006조합 중 AABB 후보는15,217개다.
이 수는 거리 검사의 후보 감소이며 시간 가속 배수가 아니다. 이 중 실제 활성 접촉은0개다.
고정 트리 refit 때문에 큰 변형에서 탐색 효율이 낮아질 수 있고 최악의 조합 수는 이차적이다.

## Barrier 강도·기하 비교

같은 soft 패치 재료(E100Pa,h1mm,면밀도0.1), 초기8mm 간격, 외력0,dt1ms를 사용했다.
면/엣지는8ms, 고속은12ms까지 비교했다. 기존 CPU60ms 저속 표본과 시간 분모가 다르다.
각 단계의 GPU raw hi/lo를 별도 CPU IPC로 검산하고 같은 입력의 CPU Newmark와 대조했다.

| 사례 | k | 최소 proxy 거리 | GPU 풀이 / 검산 | 엄격 기하까지 승인 | 거절 단계(1부터) |
| --- | ---: | ---: | ---: | --- | --- |
| 면0.2m/s | 1,000 | 7.261mm | 0.340 / 0.123s | 8/8 통과 | 없음 |
| 엣지0.2m/s | 1,000 | 7.780mm | 0.349 / 0.127s | 8/8 통과 | 없음 |
| 면1m/s | 1,000 | 2.421mm | 0.536 / 0.174s | 실패 | 11–12 |
| 면0.2m/s | 10,000 | 7.905mm | 0.387 / 0.134s | 실패 | 8 |
| 엣지0.2m/s | 10,000 | 8.182mm | 0.382 / 0.135s | 실패 | 7–8 |
| 면1m/s | 10,000 | 6.629mm | 0.542 / 0.171s | 실패 | 6–12 |

거리 수치는 저장 시점 하한이다. 별도로56/56개의 GPU 시간 경로가 CPU Tight Inclusion 검사를 통과했다.
GPU/CPU 위치 최대 차이4.42e-13m 미만, 기하 실패 단계도 정확히 일치했다.
모든 GPU force/position/energy/pin/time 검사는 통과했고, 거절 원인은 `local_metric` bit16뿐이다.
이 표본의 기하 상한이1/3 이상이면 면적 양수 충분조건을 확보하지 못하므로 거절한다.
계수를 키우면 간격은 넓어지지만 반발에 의한 큰 변형도 늘었다. 기준을 완화하거나10,000을 자동 채택하지 않았다.
이전 [CPU 강도 통과](README.md)는 힘·시간 CCD 진단 결과이며 이 엄격한 기하 승인까지 포함한 결과가 아니다.

[강도 비교 그림](gpu_checks/strength_comparison.png)의 ×는 거절 단계다.
그림의 평균 층 간격은 proxy 최소 거리와 다르며 충돌 판정에 쓰지 않는다.
원본·검산·기하 상한·시간·source hash는 [강도 JSON](gpu_checks/strength_report.json)이 소유한다.

재현(workspace 루트, 새 출력 경로):

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_validation.sh \
  --out experiments/artifacts/runs/p3_self_contact/gpu_strength_repeat
```

## 테스트·근거 보존

- CPU proxy/contact/두 실행기:33개 통과.
- 기존 CPU 동역학·중력·기하 회귀16개 추가 통과. 총81개이며 중복 실행을 합산하지 않았다.
- 실제 CUDA 접촉·후보 완전성·near-parallel 미분·CCD·용량 초과·복원·2프레임 재생 및
  기존 접촉 OFF GPU 회귀:32개 통과, skip0. 세 씬384단계와 위 국소56단계는 별도 실행이다.
  정확한 테스트 명령과 분모는 [검사 기록](gpu_checks/test_runs.json)을 따른다.
- GPU force/E/HVP 대조 허용오차, graph 검사, CCD·기하 거절 기준은
  `code/tests/test_gpu_shell_contact.py`, `test_resident_contact_stepper.py`, `test_resident_contact_frame.py`에 고정했다.
- 동결 실행 원본은 `experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v1`와
  `gpu_strength_v1`다. [작은 근거 묶음](gpu_checks/summary.json)에 출력 SHA-256과 검산 분모를 저장했다.
  강도 실행 당시 Python source도 raw run의 `source/wind3dgs`에 hash 대조 후 보존했다.
- 준비/worker 시작 때 동결 입력·runtime hash를 검증한다. 강도 비교는 실행 전후 source 불변도 검사했다.
  전체 궤적·실접촉 장면 calibration·곡면 전역 인증·proxy/시간 수렴·RTX5070·R1 acceptance는 남아 있다.

집계 재현 명령:

```bash
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/wind3dgs-contact-mpl .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_gpu_checks.py \
  --scenes experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v1 \
  --samples experiments/artifacts/runs/p3_self_contact/gpu_strength_v1 \
  --out experiments/R1_teacher_velocity_reset/self_contact/gpu_checks_repeat
```
