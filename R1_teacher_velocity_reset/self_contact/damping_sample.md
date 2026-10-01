# v13 짧은 감쇠 비교 샘플

## 현재 상태

- 2026-09-29 wind에서24가 둔하다는 사용자 관찰로 최종 시각 채택은 보류했다. [공통5초 상태의8/16 비교 준비](wind_damping.md#현재-상태)를 후속으로 진행한다.

- 2026-09-29 [감쇠24 사각형10초의64/128 완료 비교](damping24_time.md#서브-완료-결과-분석)가 수치 통과했다. wind 시각 판정과 최종 채택은 보류다. 아래 잠정 선택의 후속 근거다.

- 확인일2026-09-29. 사용자가8/16/24 비교에서24 s^-1의 비주얼이 괜찮다고 판단해 [잠정 선택](#감쇠율-잠정-선택)을 승인했다.
- 후속 감쇠 실험의 기준은24 s^-1이다. 이전 약한 감쇠 우선 권고·8/s 선호를 대체하며, wind 확인 후 변경 가능하다.
- 근거는 삼각 깃발 무풍1초에 대한 사용자 시각 판단이다. 이번 작업에서 고감쇠 결과 파일/독립 검산을 새로 분석하지 않았다.
- 바람 반응·다른 씬·장기 궤적·시간 민감도·최종 재료 및 학습 적격성은 미확정이다.
- 구현은 프레임 시작 속도 감쇠이며 연속 재료 점성의 채택이 아니다. solver 기본값이나 기존 동결 입력·결과는 수정하지 않았다.
- [0/1/3 완료 분석](#완료-결과-분석), [3/5/8 준비](#강화-감쇠-비교-준비), [8/16/24 준비](#고감쇠-비교-준비)는 각 당시 검증 범위를 보존한다.
- 다음은24 s^-1을 기준으로 wind 시각 반응을 검토하는 것이다. 새 실행 묶음 준비·시뮬레이션은 이번 결정 기록에 포함하지 않았다.

## 바로 실행

작업 루트에서 실행한다. 로컬 기본 묶음은 완료됐다. prepare/run을 반복하지 않는다. 아래 run은 최초 실행 참고용이다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_sample.sh --action run
```

control → weak → strong을 같은 컴퓨터에서 순차 실행한다. 한 조건이 실패하면 뒤 조건을 시작하지 않는다.
이미 결과나 실행 로그가 있는 조건은 재시작하지 않는다. 기본 action은 status다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_sample.sh --action status
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_damping_sample.sh
```

뷰어는 완료된 세 조건만 왼쪽부터 control/weak/strong으로 표시한다. 시작은 일시정지다.
Space로 재생, Time0–1초는 원본 궤적3–4초이며 Playback speed로 느리게 볼 수 있다.
동일 카메라·축척·체크무늬를 사용하며, 시간 보간 없는60Hz 저장 프레임 표시다.
다른 GPU 모델에서 따로 계산한 조건들을 한 비교로 재생하지 않는다.

한 조건만 먼저 실행/표시하려면 양쪽 스크립트에 `--case control`, `--case weak` 또는 `--case strong`을 붙인다.
새 반복은 새 경로로 준비한다. 아래는 입력/코드 준비만 하며 계산하지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_sample.sh \
  --action prepare --out experiments/artifacts/runs/p3_self_contact/damping_sample_v13_02
```

새 경로는 이후 run/status/view에도 같은 `--out`을 전달한다.

## 비교 조건과 목적

| 조건 | 감쇠율 | 비교 목적 |
|---|---:|---|
| control | 0 s^-1 | 같은 시작 상태에서 원래 GPU 경로 재생 |
| weak | 1 s^-1 | 약한 감쇠로 잔떨림이 줄어드는지 |
| strong | 3 s^-1 | 감쇠 효과와 지나친 둔화를 함께 확인 |

원본은 [서브 완료 v13](three_scenes_gpu_v13.md#서브-컴-완료-결과와-연결)의
`triangular_flag/outputs/calm/frame_0119.npz`, 전체3초다. 원시 u_hi/u_lo/v_hi/v_lo를
세 조건에 똑같이 넘긴다. 속도를0으로 초기화하거나 새 preload를 계산하지 않는다.
원본 calm의 다음60개 외력(중력−9.81, 무풍)을 그대로 사용한다.

삼각형은 기존 실행에서 사각형보다 계산 부담이 작고 dt/2 복구 없이도 떨림이 관찰되어 골랐다.
기존 RTX5070 기록의 삼각형3–5초 계산은 약1,047초였다. 샘플은 총3초지만 setup과 장치/감쇠에 따른
풀이 비용이 있으므로 즉시 끝나는 계산은 아니며, 기존 wall을 새 소요시간 보장으로 사용하지 않는다.

시각적으로는 control과 비교해 잔떨림이 줄고 큰 처짐/흔들림이 남는지 본다.
strong에서 거의 굳거나 지나치게 느려지면 최종값으로 채택하지 않는다. 원인이 감쇠 부족인지
가늠하는 첫 진단이며, 굽힘·고정 경계·바람 효과를 동시에 바꾸지 않는다.

## 감쇠와 검산의 의미

프레임 시작에 `v <- exp(-rate/60) * v`를 FP64 hi/lo로 적용한다. 위치는 그대로다.
이는 `dv/dt = -rate*v`의 정확한 감쇠 부분을 프레임마다 분리 적용한 진단이다.
시간에 연속인 재료 점성 또는 변형률 기반 내부 마찰을 구현한 것은 아니다.
회전/큰 움직임의 속도도 함께 줄어드므로 최종 cloth damping으로 자동 채택하지 않는다.

별도 GPU 검사는 감쇠 전후 원시 상태로 위치 불변·고정점·유한성·속도 배율을 확인하고,
consistent mass로 운동에너지를 다시 계산하여 `K_after = factor^2 K_before`와 비증가를 검사한다.
제거된 에너지는 매 프레임 `frame_velocity_damping.dissipated_energy_j`에 분리 기록한다.
그 뒤 기존 Newmark substep의 힘·업데이트·에너지·접촉·기하·시간 검산을 그대로 수행한다.

code1/2 복구는 이미 감쇠한 프레임 시작 상태에서 dt/2로 재시도하며 감쇠를 두 번 적용하지 않는다.
감쇠 검사 실패는 code91/flag128로 중단한다. 감쇠 또는 물리 단계가 실패하면 감쇠 전 원시 상태로 복원하고
실패 report/NPZ를 보존한다. CPU/contact-OFF fallback이나 허용오차 완화는 없다.
분할 단계까지 포함한 연속 재료 모델 정확도를 기존 Newmark 검산 통과로 주장하지 않는다.

기본 teacher/v13과 CG 민감도·R1 완료 기준은 바뀌지 않는다. `training_eligible=false`,
`production_enabled=false`, `r1_complete=false`를 유지한다. 관련 R1의 CG 진입/구조 감쇠 미채택
경계를 확인했고, 이번 미실행 시각 진단 준비는 canonical 변경이 아니므로 TeX/PDF는 수정·빌드하지 않았다.

## 구현과 검증 위치

- [진단 준비·실행·뷰어](../../../code/wind3dgs/evaluation/teacher_gpu_damping_sample.py)의 `prepare`, `run`, `cache_case`.
- [GPU 감쇠와 독립 검사](../../../code/wind3dgs/teacher/resident_frame_damping.py)의 `FrameVelocityDamping`, `inspect_damping`.
- [GPU 복구 연결](../../../code/wind3dgs/teacher/resident_contact_retry.py)의 선택적 `frame_velocity_damping_s_inv`; 기본0은 기존 물리 경로다.
- [CPU 검사](../../../code/tests/test_gpu_damping_sample.py): hi/lo/비대각 질량 에너지·변조 거절·복구 선택·원본 상태 보존·동결/덮어쓰기 거절·실패 중단·표시 캐시.
- 함께 실행한 기존 회귀: `test_teacher_gpu_contact_scene_suite.py`, `test_teacher_gpu_contact_drape_suite.py`.
- 실제 GPU 샘플을 실행하지 않았으므로 CUDA graph 구성/실행과 물리 검산은 사용자 실행에서 확인해야 한다. 뷰어는 CPU 캐시 검사만 했고 새 실결과 렌더링은 미실행이다.

## 완료 결과 분석

2026-09-28 확인. 기본 묶음 `damping_sample_v13_01`, manifest
`5dde7ab328c43863aac8c93b459152a6c3230d9f76c0f72219e50e764580bb4c`.
세 조건 모두 GTX1080Ti에서60/60프레임, 실패0/180·재시도0/180.
weak/strong 감쇠 검사120개 기록상 통과, 최대 에너지 배율 오차7.81e-18 J.
독립 GPU 검산 기록과 저장 상태 확인이며 모든 물리 검사를 CPU로 재계산한 것은 아니다.

동일 P3 공통512점·면적 가중으로 후반3.5–4초를 비교했다.

| 조건 | 저장 속도 RMS (m/s) | 프레임 위치 2차 차분 RMS (mm) | 위치 변화 RMS (mm) |
|---|---:|---:|---:|
| control | 0.279 | 1.246 | 13.53 |
| weak (1/s) | 0.195 | 0.896 | 11.14 |
| strong (3/s) | 0.102 | 0.438 | 6.55 |

2차 차분은 프레임 위치 변화의 급격한 변화를 나타내는 보조 지표이며 순수 잔떨림만 분리하지 않는다.
위치 변화는 구간 평균에 대한 편차로 드리프트도 포함한다.
weak/strong의 속도는 control 대비30%/63%, 2차 차분은28%/65% 줄었다.
시작 대비 끝 위치 RMS 이동도52.15 → 35.88 → 21.99mm로 줄어 큰 움직임 억제를 함께 확인해야 한다.
감쇠가 운동을 줄이는 효과는 확인했지만 떨림의 유일한 원인이 감쇠 부족임을 증명하지는 않는다.
약한 감쇠를 우선 시각 비교 후보로 권장한다. 삼각형·무풍1초·60Hz 저장으로
바람 반응/장기 안정성/시간 수렴/학습 적격성을 확정하지 않는다.
기존 R1 미채택 경계와 기준을 유지하며 TeX/PDF는 수정·빌드하지 않았다.
뷰어 캐시는 세 조건 모두 검증했으며 실제 화면 재생은 이번 분석에서 실행하지 않았다.
앞의 준비 단계 GPU 미실행 설명은 당시 상태이며 이 절이 해당 완료 상태를 대체한다.

## 강화 감쇠 비교 준비

2026-09-28 사용자 요청으로 감쇠율3/5/8 s^-1 (`rate3/rate5/rate8`)을 준비했다.
새 묶음은 `experiments/artifacts/runs/p3_self_contact/damping_sample_v13_stronger_01`이다.
기존0/1/3 묶음과 결과는 보존한다. 원본 삼각형3초 raw hi/lo 위치·속도와 외력은 기존 감쇠 묶음과 동일하다.
각 조건은 무풍3–4초,60프레임·기본64substeps/조건부128 재시도이며 기존 검산·rollback을 유지한다.
3/s도 새 묶음에서 함께 순차 계산하여 같은 GPU의 기준으로 비교한다. 프레임 감쇠 구현·재시도 솔버 파일은 기존 동결본과 동일하다.

```bash
# 사용자가 실행: 3 → 5 → 8/s 순차 실행
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_stronger.sh --action run
# 상태
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_stronger.sh --action status
# 세 조건 완료 후, 왼쪽부터 3/5/8/s
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_damping_stronger.sh
```

기본 action은 status다. 기존 출력/로그가 있으면 run을 거절하며 실패 시 뒤 조건을 중단한다.
일부만 실행/표시하려면 `--case rate3`, `--case rate5`, `--case rate8`을 사용한다.
다른 경로에서는 `--out <bundle>`을 전달한다. 기본 묶음은 준비 완료이므로 prepare를 반복하지 않는다.
새 반복 준비는 `run_gpu_damping_stronger.sh --action prepare --out <새 경로>`로 한다.

[준비 검증 JSON](damping_stronger_checks.json)의 manifest·source·validation을 확인한다.
CPU24개 검사, 셸 구문, 실제 새/기존 manifest, 시작 상태·외력·감쇠/재시도 구현 동일성 검사 통과.
새 조건 GPU 실행·완주·실제 화면 재생은 미검증이다. 5/s를 주 후보,8/s를 둔화 확인용으로 둔다.
무풍 시각 후보를 고른 뒤 바람 반응을 확인해야 하며 이번 묶음은 바람 테스트를 포함하지 않는다.
기존 R1/학습/재료 채택 기준은 변경하지 않았고 TeX/PDF 수정·빌드는 없다.

## 고감쇠 비교 준비

2026-09-28 사용자 요청으로8/16/24 s^-1 (`rate8/rate16/rate24`)을 별도 준비했다.
묶음은 `experiments/artifacts/runs/p3_self_contact/damping_sample_v13_high_01`.
이전과 같은 삼각 깃발3초 raw hi/lo 위치·속도에서 각각 무풍1초60프레임을 진행한다.
8/s도 함께 순차 실행해 동일 GPU에서 기준과 비교한다. 물성·중력·경계·기본64/조건부128 재시도·검산 허용오차는 유지한다.
감쇠율 입력 상한만10→24 s^-1로 확장했으며, 감쇠 커널·독립 에너지 검사·rollback은 변경하지 않았다.
기존0/1/3 및3/5/8 동결 묶음/결과는 보존한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_high.sh --action run
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_high.sh --action status
# 완료 후 왼쪽부터8/16/24/s
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_damping_high.sh
```

기본 action은 status. 기존 출력/로그가 있으면 실행 거절, 실패 시 뒤 조건 중단.
선택 실행/표시는 `--case rate8|rate16|rate24`, 별도 결과 경로는 `--out <bundle>`이다.
현재 기본 묶음은 준비 완료라 prepare를 반복하지 않는다.
새 반복은 `run_gpu_damping_high.sh --action prepare --out <새 경로>`로 준비한다.

[검증·manifest·원본 식별](damping_high_checks.json): CPU28개 검사 통과(16/24의 hi/lo 속도 배율·비대각 질량 에너지 감소·상한 초과 거절·프로필 전달 포함).
셸 구문, 실제 동결 manifest, 이전 묶음과 raw 초기 상태/외력 동일성, 상한 외 감쇠 구현 동일성·재시도 솔버 동일성 확인.
GPU 계산은 실행하지 않았고 새 결과/로그가 없음을 확인했다. 새 조건 GPU 검산·완주·시각 판정은 미완료다.
프레임 속도 감쇠 진단이며 연속 재료 점성/학습 채택이 아니다. 강한 감쇠의 바람 반응은 별도 확인이 필요하다.
이번 묶음에는 바람 구간을 추가하지 않았다. R1 기준·완료 판정 변경이 없어 TeX/PDF 수정·빌드는 없다.

## 감쇠율 잠정 선택

2026-09-29 사용자 시각 판단에 따라 **24 s^-1을 후속 실험의 잠정 기준값으로 고정**한다.
대상은8/16/24 비교의 `rate24` 조건(삼각 깃발, 무풍 궤적3–4초)이다.
선택 근거는 사용자가24의 비주얼을 수용했다는 것이며, 이전 약한 감쇠 우선 권고와8/s 선호를 대체한다.
고감쇠 결과의 완료/독립 검산 수치 재확인은 이번 기록에서 수행하지 않았다.

wind 씬은 아직 시각 검토 전이다. 이후24를 기준으로 바람에 충분히 반응하는지 확인하고,
움직임이 지나치게 둔하거나 원하는 천의 인상과 다르면 감쇠율을 다시 조정한다.
모든 씬의 최종 물성·연속 재료 감쇠·학습용 teacher 채택이나 R1 완료 판정은 아니다.
기존 solver 기본값·동결 config·결과는 유지하며, 이후 새 실험을 준비할 때 이 선택값을 명시적으로 적용한다.
새 GPU 실행·wind 묶음 생성은 하지 않았다. 연구 계약/완료 판정 변경이 없어 TeX/PDF 수정·빌드는 없다.
