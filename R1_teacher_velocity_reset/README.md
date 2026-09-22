# 변화 바람과 도달 형상의 속도 초기화 비교

Wind3DGS R1 개발 탐색. Rest에서 바람으로 도달한 형상을 유지한 채 속도를 0으로 만들고,
동일한 미래 바람에 대한 응답을 원본과 비교한다. 재생 오차·개입 에너지·mesh/time 의존성을 구분한다.

## 목표와 반증 질문

원본 prefix를 새 simulation에서 재생한 결과가 일치하는가? 속도 개입 시 위치·rest/material·절대 시각이
유지되는가? 새 속도로 frame-start 공력을 다시 계산하는가? 이후 응답이 유한하며 refinement에 견고한가?
상태/공력/개입 검산 실패는 실행 실패이며, refinement 차이 1% 초과는 개발 진단 실패로 별도 보존한다.

## 입력과 범위

1 m XZ flag의 training-only mesh, x=0 pin, 질량 0.1 kg, native Newton stiffness 1000/1000 N/m,
material damping 0.1 s, bending 10 N, bending damping off, gravity off, kappa 0.6.
CPU VBD iterations10, 60 fps, 90 frame(1.5 s). Seed20260909의 PCG64로 12 frame마다
random unit direction와 0.25–0.5 m/s target를 뽑고 **vector**를 선형 보간한다.
처음은 wind0, 마지막 18 frame은 ambient0이며 air drag는 유지한다. 보간 중 풍속은 target 하한보다 작을 수 있다.
원본 18/42/66 frame(0.3/0.7/1.1 s)에 각각 독립적인 velocity-reset 분기를 만든다.

Mesh4/8/16 at substeps32와 mesh8 at substeps8/16/32의 합집합 5개 조건이다.
각 조건은 원본·무개입 독립 재생·3개 reset으로 구성한다. Reset을 한 경로에서 연속 반복하는 실험은 아니다.
공통 25개 nodal probe와 합이 1 m²인 trapezoid 가중치를 사용한다. 원본·분기는 한 source group이다.
Dataset/object package/model version은 `not_applicable`: 학습 데이터를 발행하거나 runtime 모델을 구현하지 않는다.

기존 Teacher 모드는 방향을 고정하므로, 방향 setter가 있는 기존 `demo` 모드에 명시적 gravity-off/rest를 적용한다.
별도 `wind3dgs.velocity_reset_development.v1`이며 **training_eligible=false / teacher_accepted=false**다.
P3 shell이 아니며 native bending의 기존 공간 의존성을 해결한 것으로 간주하지 않는다.

## 재현 명령

Workspace root에서 실행한다. Launcher가 code로 이동하므로 인자는 code 기준이다.

```bash
bash code/scripts/check_teacher_velocity_reset.sh \
  --output ../experiments/artifacts/runs/teacher_velocity_reset/20260909_velocity_reset_v1
bash code/scripts/check_teacher_velocity_reset.sh \
  --verify ../experiments/artifacts/runs/teacher_velocity_reset/20260909_velocity_reset_v1
```

기존 폴더 덮어쓰기와 자동 재시도는 없다. Wall time 기본 상한은 900초다.
Raw NPZ, 실제 frame vector, event JSON, config/environment/source hash, report, inventory와 로그를 보존한다.
실패 시 부분 결과를 보존하고 완료로 표시하지 않는다. Compact evidence와 실제 판정은 아래에 보존한다.

## 판정 계약

- Restart는 `deterministic_prefix_replay_v1`: 새 solver에 저장 입력을 재생해 내부 상태를 재구성한다.
  빠른 full-state deserialization 또는 임의 형상의 solver 초기화가 아니다.
- 두 state buffer의 velocity만 0으로 만든다. 개입 전 속도를 별도 저장하고 위치 hash 동일성,
  제거 운동에너지와 음의 intervention work를 검산한다. 공력 work/구조 damping 손실에 섞지 않는다.
- 배열은 checkpoint의 **개입 후** 속도를 저장한다. 이전 interval의 끝 속도는 `pre_reset_velocity_m_s`로
  복원해야 한다. Reset 경계를 정상 smooth transition 학습 label로 쓰면 안 된다.
- 공간/시간 오차는 공통 frame에서 area-weighted probe RMS 차이의 최댓값을 fine의 peak response로 나눈다.
  Reset 비교는 checkpoint 이후 구간이다. 변위는 원래 rest를 기준으로 한다. 1%는 이번 관측 기준이며,
  연속 시간 상한·방향·독립 기준·비선형 shell/accepted Teacher의 인증 기준을 대체하지 않는다.
- 공력은 실제 위치/속도에서 two-sided normal quadratic drag를 NumPy로 독립 재계산한다.
  저장 force/work·pin·mass·clock·prefix와 전체 무개입 replay도 검산한다.

## 완료 gate

- [x] Manifest/schema/hash/path 검증
- [x] 원본·재생·속도 초기화와 공력/에너지 검산
- [x] Mesh/time 실패와 적용 범위 기록
- [x] 실제 결과·재현 명령·compact evidence 확인

## 실행 결과와 적절성 판정

**25개 trace(5개 원본·5개 독립 replay·15개 reset), 2,250 interval/2,275 state를 생성·검산했다.**
CPU 373.876초. Raw inventory는 manifest 제외 55개 파일/6,791,538 byte이며 54,000 VBD substep을 실행했다.
다섯 replay의 위치·속도·힘·work 최대 차이는 모두 0이다. Pin drift=0, guard=0이고 모든 상태가 유한하다.
관측한 edge stretch 최대는 1.000017469, rest 대비 face area 최소는 0.999981978이다.
이 값은 원소의 국소 뒤집힘/자기 교차나 장기 안정성 전체를 보증하지 않는다.

신규 검사 8개(5.636초)와 기존 Newton 관련 85개(139.697초)가 통과했다. 저장 파일을 새 프로세스에서
재로드하고 공력·개입·보고서를 다시 계산했다. Producer source 25개와 Newton VBD source hash도 대조했다.
새 GPU 검사는 하지 않았다. [보고서](evidence/report.json), [검산](evidence/verification.json),
[환경](evidence/environment.json), [manifest](evidence/run_manifest.json), [provenance](provenance.json)를 보존한다.

### 속도 초기화는 작동하지만 학습 이득은 미검증

Mesh8/substeps32에서 각 분기의 checkpoint와 이후 원본 대비 차이는 다음과 같다.
마지막 열은 같은 이후 바람을 넣은 **두 물리 상태의 차이**이며 모델 예측 오차가 아니다.

| Reset 시각 [s] | Checkpoint 최대 nodal 변위 [mm] | 제거 운동에너지 [μJ] | 이후 최대 probe RMS 위치 차이 [mm] |
| --- | ---: | ---: | ---: |
| 0.3 | 2.038361 | 9.689417 | 8.651398 |
| 0.7 | 21.667045 | 52.273766 | 16.597835 |
| 1.1 | 38.493980 | 67.954399 | 13.712264 |

위치는 개입 직전/직후 정확히 같고 속도는 0이다. 모든 분기는 이후 다시 움직인다.
개입 전에 갖고 있던 운동량을 제거한 만큼 이후 경로가 달라진다. 1.2–1.5 s의 ambient0 구간도 drag는 유지한다.
1.5 s만 관측했으므로 평형 회복 완료나 장기 안정성, 굽힘 energy 해방의 정량 검증을 주장하지 않는다.

[변화 바람·변위·속도·운동에너지 그림](evidence/velocity_reset_response.png)은 초기화 순간을 수직 점프로 표시한다.

### 공간/시간 속도 진단은 실패

가장 촘촘한 pair만 모은 결과다. 각 reset 분기는 해당 checkpoint 이후를 비교한다.

| 비교 | 분기 | 변위 차이 [%] | 속도 차이 [%] | 속도 절대 차이 [mm/s] |
| --- | --- | ---: | ---: | ---: |
| 공간8→16 / sub32 | 자연 연속 | 0.520181 | 12.040068 | 4.657035 |
| 공간8→16 / sub32 | 0.3s reset | 0.667281 | 13.827964 | 4.743307 |
| 공간8→16 / sub32 | 0.7s reset | 0.887863 | 20.503919 | 4.435040 |
| 공간8→16 / sub32 | 1.1s reset | 0.654738 | 81.148231 | 3.389095 |
| 시간16→32 / mesh8 | 자연 연속 | 0.077190 | 2.176690 | 0.835145 |
| 시간16→32 / mesh8 | 0.3s reset | 0.069383 | 2.400700 | 0.816840 |
| 시간16→32 / mesh8 | 0.7s reset | 0.158086 | 3.546817 | 0.757634 |
| 시간16→32 / mesh8 | 1.1s reset | 0.223625 | 17.756006 | 0.555413 |

모든 finest pair가 속도 1% 기준을 넘는다. 공간 자연 연속의 속도 차이는 6.2530%→12.0401%로 커졌고,
시간 자연 연속은 8.2148%→2.1767%로 감소했으나 기준에 못 미쳤다.
1.1 s reset의 공간 81.1482%는 절대 차이 3.38910 mm/s, fine peak 4.17643 mm/s이고,
시간 17.7560%는 0.555413 mm/s / 3.12803 mm/s다. 작은 분모와 절대 차이를 함께 해석해야 한다.
공간 비교에도 시간 오차가 남으므로 mesh만의 오차로 단정하지 않는다.
[전체 ladder 그림](evidence/velocity_reset_refinement.png)을 보존하며 학습 적격성은 false다.

### 고정 조건은 굽힘 상태 coverage에도 한계가 있다

현재 x=0 모서리는 **위치만** 고정되어 있다. 원래 XZ 평면을 그 모서리인 Z축 주위로 강체 회전해도
고정부와 원소 rest 길이/면적/dihedral을 보존할 수 있다. 따라서 큰 위치 변화가 큰 탄성 굽힘을 뜻하지 않는다.
25개 공통 probe에서 면적 가중 최소제곱으로 그 한 자유도 회전을 맞춘 [진단](evidence/rotation_diagnostic.json)은
0.7 s에서 회전 1.241208°, 전체 변위 RMS 12.700918 mm 중 회전으로 설명되지 않는 RMS가 **0.002380 mm**였다.
1.1 s에서는 전체 22.540597 mm 중 잔차 0.035869 mm다. 이것은 위치 분해이며 탄성 에너지 비율이 아니다.

따라서 이번 결과는 **분기·속도·공력 처리 검증과 실패 발견**까지의 개발 성과다.
단일 seed·짧은 horizon·거의 회전인 상태만으로 실제 굽힘 상태의 데이터 적절성 또는 학습 이득을 확정할 수 없다.
후속 후보는 고정 모서리의 기울기도 제한하는 조건 또는 동일 물리 폭의 고정 영역을 사용해 굽힘 상태를 확보하고,
같은 backend의 시간 오차를 먼저 줄인 뒤 공간·입력/상태 coverage를 다시 판단하는 것이다.
해상도마다 단순히 두 vertex 열을 고정하면 고정 폭이 달라지므로 동일 boundary라고 간주하지 않는다.
이는 후속 설계이며 이번에 경계 조건이나 물성 backend를 교체하지 않았다.

## 그림 재현

Raw run과 설치된 Matplotlib/CJK 글꼴을 사용한다. 출력은 새 폴더를 지정한다.

```bash
PYTHONPATH=code MPLCONFIGDIR=/tmp/wind3dgs_reset_matplotlib \
  .venv/bin/python experiments/R1_teacher_velocity_reset/evidence/verify_and_plot.py \
  --run experiments/artifacts/runs/teacher_velocity_reset/20260909_velocity_reset_v1 \
  --output /tmp/wind3dgs_velocity_reset_new_figures
```

원본 25개 trace는 개발 진단 데이터이며 새 학습용 patch/window dataset을 발행하지 않았다.
기존 15개 development window와는 별도 산출물이다. Compact evidence만으로 raw NPZ를 복원할 수 없다.
