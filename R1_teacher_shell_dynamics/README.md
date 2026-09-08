# CPU shell 동역학 기준 solver 진단

2026-09-07 구현·실제 진단·독립 재실행을 완료했다. 수치 계약은 통과했고,
비선형 속도의 시간 대조는 실패했다. **학습 Teacher 채택은 미확정**이다.

## 목표·범위

승인된 [code 동역학 설계](../../code/sessions/2026-09-07_12_teacher_shell_dynamics_design.md)에 따라
기존 3D 구조 힘/HVP에 질량·rest 위치 고정·held force와 Newmark/GMRES를 연결한다.
작은 mesh에서 시간 적분·반력·정지/실패 계약을 독립 검증하는 개발 실험이다.
이전 [구조 에너지 진단](../R1_teacher_shell_structure/README.md)의 실패를 소급 변경하지 않는다.
구조 모델의 공간 해·thin-limit 적격성, 공력/감쇠·GPU/GUI·Registry/학습 데이터 발행은 후속 단계다.

Training/evaluation 전용 synthetic flat mesh다. Dataset/object/model/split은 `not_applicable`이며
무작위 선형 RHS와 반력 load의 seed는 20260907이다. Target runtime은 실행하지 않는다.
질량은 metric의 M_ref만 소유하고 rest face 면적의 1/3씩 정점에 나눈다.
Pin에는 전체 xyz rest 위치만 고정한다. 왼쪽 직선 경계의 rigid rotation을 제거하지 않는다.

## 입력과 재현 명령

1m×1m, E=1e6Pa, ν=0.3, h=0.01m, M_ref=0.1kg는 수치 검증용 조합이다.
재료/질량은 CLI에서 모두 명시하며 학습 preset으로 채택한 값이 아니다.
질량·normal 영모드·작은 dense LU/GMRES 비교는 n=4/8, 세 삼각분할에서 실행한다.
응답은 n=4에서 계산한다. 실제 CPU 성능과 실패 기록도 보존한다.

Workspace root에서 실행한다. 상대 output은 launcher가 이동한 `code/` 기준이다.
결과 폴더는 배타적으로 만들며 재실행에는 새 이름을 사용한다.

```bash
bash code/scripts/audit_teacher_shell_dynamics.sh \
  --young-modulus-pa 1000000 --poisson-ratio 0.3 --thickness-m 0.01 \
  --reference-mass-kg 0.1 --width-m 1 --height-m 1 \
  --output ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1
```

## 검사 기준

| 진단 | 고정 기준 |
| --- | --- |
| 질량 | 면적 상대 오차 ≤1e-10, 질량 상대 오차 ≤1e-12, 모든 mass 정상 양수 |
| GMRES | 상대 오차 1e-10, atol=0, restart 50/free DOF 중 작은 값, 최대 20 cycles |
| 비선형 solve | 설계의 mass-weighted 잔차와 전체 correction 조건을 모두 충족; 최대 30회 correction |
| Line search | 실제 잔차 merit의 Armijo c1=1e-4, α를 1/2씩 축소, 최대 20회 backtrack |
| 병진·일정 가속도·외력 전환 | 해석 x/v 대조의 정규화 오차 ≤1e-8 |
| 반력·객관성 | All-pinned 반력, 12개 회전/이동의 x/v·반력 공변 오차 ≤1e-8 |
| 선형계 독립 대조 | n=4/8의 GMRES와 dense LU correction 상대 차이 ≤1e-8 |
| 선형 진동 | 이산 해와 q/v·전체 x/v 오차 및 전체 에너지 drift ≤1e-6 |
| 선형 시간 정확도 | 40/80/160 step의 위상 오차 감소, finest ≤1e-3 rad, 차수 1.8~2.2 |
| 비선형 시간 대조 | 40/80/160을 320 step과 비교; x/v 오차 감소, finest ≤1%, 에너지 defect ≤1e-3 |
| 선형 극한 | 같은 320 step에서 A/L=1e-3, 5e-4, 2.5e-4의 nonlinear/linear x/v 차이 감소 |

첫 양의 normal 굽힘 모드의 T1=2π/ω를 한 주기 계산한다. 왼쪽 pin의 normal 영모드 하나는
모드 선택에서 분리하며 물리 H는 clipping하지 않는다. 선형 기준은 별도의
`structure_mode=rest_linear_reference`로 식별하고, θ=2 atan(ω dt/2)의 해석 이산 해와 비교한다.
비선형 선형극한 대조도 같은 시간 격자의 해석 이산 선형 모드를 기준으로 쓴다.
총 19개 rollout을 실행했다: 해석 이동/반력 4개, 선형 9개, 비선형 시간 4개, 추가 진폭 2개다.
각 run은 2,105 step과 초기 상태 포함 2,124개 frame이다. 객관성은 기준 1개와 변환 12개의
별도 13 step이며, 작은 선형계/모드 검사도 rollout 수에 포함하지 않는다.

외력은 interval마다 고정된 SI world vector다. 전환 시 가속도를 새 외력으로 다시 구하고
이전 endpoint와 이번 interval start의 가속도·외력 hash를 구분한다.
Work는 F_held·Δx이며 정지 pin의 reaction work는 0이다.
비선형 에너지 defect를 속도 rescaling·감쇠·timestep 자동 축소로 없애지 않는다.

## 기록 방식

원본에는 report/config/CSV/environment/manifest/한국어 로그를 남긴다. `cases/<id>/`에는
실제 x/v/a·외력/반력·시각의 `states.npz`, 성공 step의 `steps.jsonl`, case summary와 실패 사유를 둔다.
이 전체 상태 배열과 detailed trace는 ignored artifact로 보존한다. Manifest는 생성된 부분 파일의
byte/hash, 완료된 case와 미실행 case도 기록한다. 실패 trial은 성공 frame에 넣지 않는다.

최종 report/config/CSV/environment/manifest/log를 compact evidence로 선택 복사하고 provenance에
원본 연결과 byte/hash를 기록한다. 재실행 manifest와 재검산 결과·해당 두 run 전용 검산 script도 보존한다.
시간/UUID를 제외한 수치 payload hash로 독립 재실행을 대조한다.
Source hash에는 기존 구조 source와 새 실행 경로를 모두 포함하고 미commit HEAD와 구분한다.

계산 상태 `completed`, 수치 계약의 `solver_check`, 응답 진단의 `response_check`는 별개다.
항상 `teacher_eligible=false`, `convergence_status=not_assessed`다.
응답 진단이 실패하면 기존 기준과 실패 결과를 보존한다. 수치 계약 실패는 구현 완료로 보고하지 않는다.
완료 gate는 실제 run, 관련 회귀 검사, 재실행 수치 대조, 원본/evidence·manifest/source의 무결성 확인이다.

## 실제 결과

Python 3.12.3, NumPy 2.4.4, SciPy 1.18.1의 CPU에서 아래 두 run을 실행했다.
각각 모든 rollout이 완료됐고 수치 결과는 정확히 일치했다.

| 항목 | 결과 |
| --- | --- |
| 계산 | `completed`, 19/19 rollout·2,105/2,105 step |
| 수치 계약 | `solver_check=passed` |
| 응답 진단 | `response_check=failed`: 비선형 속도 차이의 감소·1% 조건 실패 |
| 해석 병진·가속도·외력 전환 | 최대 정규화 오차 1.13091e-12, 반력 검사 통과 |
| 회전/이동 공변 | 최대 정규화 오차 1.86727e-11 |
| n=4/8, 세 분할의 GMRES/dense 차이 | 최대 2.62248e-10 |
| 선형 이산 해의 전체 x/v 차이 | 최대 5.09075e-10 |
| 선형 전체 에너지 drift | 최대 7.86038e-14 |
| 선형 시간 정확도 | 관측 차수 1.9960~1.9990, 160-step 위상 오차 약 8.07268e-4rad |
| 실제 비선형 풀이 | 최대 Newton update 3회, 모든 accepted step의 잔차·correction 기준 통과 |
| 관련 자동 검사 | 새 24개 + 기존 82개 = 106개 통과, 21.205초 |

아래 비선형 시간 대조는 320-step을 비교 기준으로 쓴다. 위치·속도 값은 파일에서 각각
`positions_m`, `velocities_m_s`라는 원래 배열 이름을 쓰지만 **오차 값 자체는 무차원**이다.
위치는 A, 속도는 Aω₁로 나눈 동일 free mass RMS의 공통 시각 최대값이다.

| T1당 step | 위치 차이 | 속도 차이 | 상대 energy defect |
| --- | ---: | ---: | ---: |
| 40 | 0.400855% | 10.175993% | 3.50260e-4 |
| 80 | 0.106937% | 10.459735% | 6.82388e-5 |
| 160 | 0.058855% | 11.393922% | 1.66130e-5 |

위치와 에너지 기준은 통과하지만 속도 차이가 감소하지 않는다.
에너지가 작게 변한다는 사실만으로 속도/위상 정확도를 보장할 수 없다.
320-step도 수렴이 확인된 정답이 아니므로 물리 응답에 대한 채택 기준으로 사용하지 않는다.

초기 진폭을 줄이는 선형 극한 대조는 같은 320-step의 해석 이산 선형 모드를 기준으로 한다.

| A/L | 정규화 위치 차이 | 정규화 속도 차이 |
| --- | ---: | ---: |
| 1e-3 | 0.127418% | 6.310848% |
| 5e-4 | 0.035052% | 3.154948% |
| 2.5e-4 | 0.015452% | 1.577415% |

두 차이는 모두 감소했다. 이 개발 기준의 통과는 앞의 시간 대조 실패를 바꾸지 않는다.

## 속도 차이의 추가 분해와 다음 판단

동일한 원본 상태의 속도 차이를 XY/Z 성분으로 나눴다.
각 성분의 시간 최대값이 다른 시각일 수 있으므로 두 표 값을 단순 합산하지 않는다.

| T1당 step | XY 속도 차이 | Z 속도 차이 |
| --- | ---: | ---: |
| 40 | 10.175745% | 0.519167% |
| 80 | 10.459624% | 0.125152% |
| 160 | 11.393922% | 0.033202% |

차이를 지배하는 성분은 XY다. 같은 n=4 rest의 free xyz tangent를 질량으로 스케일한
`M^(-1/2) H M^(-1/2)`의 고유값으로 계산하면 최고 각속도는 3,820.137rad/s이며,
첫 굽힘 모드 5.861682rad/s의 651.7135배다. 320-step에서도 `dt*omega_max=12.7964`다.
빠른 면내 진동을 현재 시간 간격으로 충분히 구분하지 못했을 가능성을 후속 검증 대상으로 삼는다.
모든 고주파가 실제 응답을 지배한다고 확정하는 결과는 아니며, 전체 modal projection과 더 촘촘한
시간 기준해는 아직 계산하지 않았다.

다음은 같은 작은 mesh에서 XY/Z·모드별 속도와 더 촘촘한 시간 기준해를 대조하는 진단의 설계다.
그 결과를 확인한 뒤 common probe의 공간 응답으로 진행한다. Solver 정책·물성·감쇠를 바꾸어
실패를 통과시키지 않았다. 기존 정적 구조 실패도 유지하며 최종 물리 수렴은 `not_assessed`다.

## 원본·evidence와 재검산

- Reference: `artifacts/runs/teacher_shell_dynamics/20260907_reference_v1/`
- Replay: `artifacts/runs/teacher_shell_dynamics/20260907_reference_v1_replay/`
- [원본 연결·파일 SHA-256](provenance.json), [수치 report](evidence/reference/report.json),
  [검산 결과](evidence/verification.json), [재실행 manifest](evidence/replay_manifest.json).

Compact evidence는 총 9개 파일·299,967byte다. Provenance 자체와 README는 이 합계에서 제외한다.
각 원본 manifest는 자신을 제외한 62개 파일을 열거하며, NPZ 상태와 JSONL 반복 로그를 포함한다.
전체 원본은 ignored artifact에 보존하고 삭제·덮어쓰지 않는다. Git checkout만으로는 상태 배열을
회수할 수 없으므로 위 로컬 원본 또는 별도 보존본에서 manifest의 상대 경로·byte/hash로 검증해야 한다.

두 수치 report의 semantic SHA-256은 다음과 같다. 실행 시간과 run UUID는 이에 포함하지 않는다.

```text
71fb96550403e551b7d88c67d37e6e01fafd90a0c38c620efdc210177a456348
```

Source 16개, 두 원본의 file inventory·JSON/CSV·114개 상태 배열·상태 및 trace checksum을 검증했다.
두 실행의 총 4,210 step에서 저장된 위치·속도·가속도·힘으로 운동방정식과 Newmark 갱신식을 다시 계산했다.
최대 잔차/bound는 0.992185, 위치 갱신 차이는 2.17429e-16m, 속도 갱신 차이는 3.36103e-18m/s다.
Pin x/v/a와 반력, 기록된 막/굽힘 에너지도 일치했다.
Reference의 accepted step 계산 시간 합은 153.842초, replay는 154.159초다.
Setup·모드·별도 객관성·I/O를 제외한 합이며 전체 wall time이나 GPU 성능으로 해석하지 않는다.
`hvp_count=175625`도 rollout의 GMRES/Jacobian·merit 호출 수이며 선형 기준 에너지 평가 내부의 HVP까지 센 값은 아니다.

원본 두 폴더가 있을 때 workspace root에서 다음 실험 전용 검산 명령을 실행할 수 있다.
결과는 stdout과 `/tmp/wind3dgs_shell_dynamics_verification.json`에 기록하고 원본을 수정하지 않는다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_dynamics/evidence/verify_reference.py
```

실행 source는 미commit 파일을 포함한다. Code HEAD `7010682`, experiments HEAD `61d972e`는
실행 시의 로컬 snapshot이며 `environment.json`의 개별 source SHA-256이 실제 구현을 식별한다.
이번 구현·실험은 미commit·미push 상태다. Network fetch·설치·다운로드는 하지 않았다.
