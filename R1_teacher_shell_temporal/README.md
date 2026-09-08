# Shell 모드·독립 시간 기준·시간 해상도 진단

## 목표와 승인 범위

사용자가 [시간 해상도 진단 설계](../../code/sessions/2026-09-08_01_teacher_shell_temporal_design.md)를
“ㅇㅋ”로 승인했다. 기존 [CPU 동역학 결과](../R1_teacher_shell_dynamics/README.md)의 속도 차이를
모드별로 분리하고 같은 운동방정식의 독립 시간 적분 결과와 대조하는 개발 실험이다.
기존 Newmark/GMRES·구조 법칙·물성·고정점은 유지한다.

Training/evaluation 전용 synthetic n=4 forward 평판이며 target runtime은 실행하지 않는다.
Dataset/object/checkpoint/split은 `not_applicable`이다. 기존 seed 20260907과 source hash를 기록한다.
E=1e6Pa, ν=0.3, h=0.01m, M_ref=0.1kg, 1m×1m, 왼쪽 rest 위치 pin,
첫 normal 굽힘 모드의 A=0.001m 초기 변위와 외력·감쇠 0을 사용한다.
물리 Teacher 채택·공간 refinement·공력/감쇠·GPU/GUI·Registry·학습 dataset 발행은 포함하지 않는다.

## 원본과 실행 명령

Source 원본은 `artifacts/runs/teacher_shell_dynamics/20260907_reference_v1/`다.
Report/manifest·파일 inventory·현재 source·model·initial state·배열·Newmark 식을 검증한 뒤
기존 40/80/160/320-step을 읽기 전용으로 재사용한다. 기존 실패 판정은 변경하지 않는다.

Workspace root에서 실행한다. 상대 CLI 경로는 launcher가 이동한 `code/` 기준이다.
결과 폴더는 새로 만들며 기존 폴더와 source의 내부/상위 폴더는 출력으로 사용할 수 없다.

```bash
bash code/scripts/audit_teacher_shell_temporal.sh \
  --source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1
```

독립 재실행은 output 이름 끝에 `_replay`를 붙인다. 현재 source 18개와 Python/NumPy/SciPy,
원본·policy·상태/배열의 hash를 기록한다. 미commit source와 로컬 HEAD는 별도로 식별한다.

## 사전에 고정한 검사

Rest mass-scaled tangent를 접선/법선 block으로 분리하고 영모드, 대칭성, 고유잔차,
질량 정규직교성과 Parseval을 상대 1e-9로 검사한다. Block별 cutoff는 1e-9,
인접 양의 고유값의 cluster relative gap은 1e-8이다. XY/Z 성분과 modal cluster의
속도 차이 제곱합을 함께 보고한다. Null mode를 물리 dynamics에서 제거하지 않는다.

독립 기준은 같은 내부 힘과 질량을 사용하는 DOP853이며 free displacement와 velocity를
각각 A와 Aω1로 스케일한다. SI 시간으로 적분하며 pin은 rest·0이다.

| 기준 | rtol / atol | 최대 dt |
| --- | --- | --- |
| reference_a | 1e-8 / 1e-10 | min(T1/320, 0.5/omega_max) |
| reference_b | 1e-9 / 1e-11 | min(T1/640, 0.25/omega_max) |

둘을 10,240개 구간의 동일 시각에서 대조한다. Free mass RMS의 최대 x/v 차이를
A와 Aω1로 나눈 값이 ≤1e-4이고, internal/output 두 시각 집합의 최대 상대 total energy drift가
각각 ≤1e-5여야 reference_b를 개발 진단 기준으로 사용한다. 실패하면 새 Newmark 계산은 미실행으로 남긴다.
같은 구조 힘을 사용하므로 이 대조는 시간 적분의 독립 검증이며 구조 법칙의 정답을 제공하지 않는다.

| Newmark 구간 | T1당 step N | 새 실제 step 수 |
| --- | --- | ---: |
| 전체 T1 | 640 / 1280 / 2560 | 4480 |
| 초기 T1/20 | 5120 / 10240 | 768 |

총 최대 5개 새 rollout·5,248 step이다. Short ladder의 앞 구간은 full run의 같은 dt prefix를 사용한다.
Full/short 오차·에너지·판정을 분리한다. Primary x/v 오차 감소와 finest ≤1%, 상대 energy drift ≤1e-3를
검사하며, 관측 차수는 reference 차이/float floor의 10배를 넘는 구간에서만 보조로 보고한다.
좌표 ULP/(beta dt²), 실제 잔차/bound, 전체 correction·반력/에너지도 기록한다.
작은 시간 간격에서 수치 풀이가 실패하면 기존 기준을 완화하지 않고 이후 새 Newmark case를 건너뛴다.

## 실행 상한과 보존

각 reference는 accepted internal step 50,000회, RHS 1,000,000회까지다.
한 audit은 wall-clock 1,800초까지이며 재실행에도 같은 상한을 적용한다.
비용 상한 도달은 수렴이나 계산 완료의 근거가 아니다.

원본 `cases/`에는 sample/internal NPZ와 summary·step trace·runtime을 저장한다.
Reference internal state와 dense output sample을 구분한다. `chunks/`에는 주기적으로 성공 prefix와
반복 기록을 flush하고, 중단·예외 시 마지막 성공 상태·미실행 case 및 부분 파일 inventory를 남긴다.
강제 종료 시에는 마지막 checkpoint 범위를 확인한다. 실패 trial은 성공 frame으로 발행하지 않는다.
Manifest/config/environment/JSON·CSV/한국어 로그와 선택 요약만 아래 compact evidence로 보존했다.
전체 상태·trace는 ignored artifact로 보존하며 삭제·덮어쓰지 않는다.

## 완료 기준과 상태 해석

새 modal/adapter/sampling/중단/무결성 검사와 기존 관련 106개 회귀 검사, 실제 run·독립 재실행,
source/상태/JSON/CSV·원본/evidence hash 검산을 완료한다.
수치 계약이나 기록 구현이 틀리면 완료로 보고하지 않는다. 응답이나 reference 진단이 실패하면
결과를 그대로 기록하며 정책을 바꿔 통과시키지 않는다.

`source_check`, `modal_check`, `reference_check`, `newmark_solver_check`,
`full_response_check`, `short_response_check`를 분리한다. 미실행은 이유가 있는 `not_assessed`다.
항상 `teacher_eligible=false`, `convergence_status=not_assessed`다.

## 2026-09-08 실제 결과

Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU에서 원본과 독립 재실행을 완료했다.
두 실행 모두 7개 case 중 6개 완료, 마지막 case의 성공 4 step과 실패 기록을 보존했다.
새 Newmark 성공 step은 실행당 4,740개다. `status=completed`는 진단 절차의 종료를 뜻한다.

| 분리 판정 | 결과 |
| --- | --- |
| source / modal / reference | 모두 `passed` |
| newmark_solver_check | `failed` |
| full_response_check | `failed` |
| short_response_check | `not_assessed` — finest 구간 미완료 |
| convergence_status / teacher_eligible | `not_assessed` / `false` |

Rest modal basis는 XY 40개·Z 20개 자유도로 분리됐고, nullity는 각각 0·1이다.
ω1=5.8616816393rad/s, T1=1.0719083181s, ωmax=3820.1370527rad/s다.
Block coupling은 0, mass 직교성 오차는 1.13557e-14로 검사를 통과했다.
Report의 `eigenvalues_s2`는 λ의 단위 1/s²를 뜻한다.

| 독립 기준 | accepted internal step | RHS 호출 | 최대 상대 에너지 drift |
| --- | ---: | ---: | ---: |
| reference_a | 8,191 | 122,867 | 4.88329e-10 |
| reference_b | 16,380 | 245,702 | 8.06520e-11 |

두 기준은 각각 10,241개 시각으로 sample했다. 정규화 최대 차이는 x=1.24085e-11,
v=6.93487e-9로 자체 대조를 통과했다. 이후 비교 기준은 reference_b다.
아래 x/v는 free mass RMS 차이의 시간 최댓값을 A=0.001m, Aω1=0.00586168m/s로 나눈 값이다.
순간 reference 속도에 대한 상대 오차나 tip 하나의 오차가 아니다.

| 전체 T1의 N | 정규화 x 차이 | 정규화 v 차이 | 최대 상대 에너지 drift |
| --- | ---: | ---: | ---: |
| 40 (원본 재사용) | 4.07925e-3 | 10.8197% | 3.50260e-4 |
| 80 (원본 재사용) | 1.13263e-3 | 10.1981% | 6.82388e-5 |
| 160 (원본 재사용) | 6.18659e-4 | 10.5116% | 1.66130e-5 |
| 320 (원본 재사용) | 5.85460e-4 | 11.2999% | 6.69308e-6 |
| 640 | 6.13537e-4 | 11.0803% | 1.62159e-6 |
| 1280 | 6.06507e-4 | 11.2063% | 4.45408e-7 |
| 2560 | 6.24816e-4 | 11.7491% | 1.48646e-7 |

에너지 drift는 감소하지만 응답 차이의 감소·finest 1% 조건은 실패했다.
N=2560의 최대 속도 차이는 6.88697e-4m/s이며 XY 성분이 거의 전부다.
Z 성분의 정규화 최대 차이는 1.48261e-4다. 전체 ladder의 수치와 XY/Z·modal 상세는
[CSV](evidence/reference/comparisons.csv)와 [report](evidence/reference/report.json)에 있다.

| 초기 T1/20의 N | 실제 step | 정규화 x 차이 | 정규화 v 차이 | 최대 상대 에너지 drift |
| --- | ---: | ---: | ---: | ---: |
| 2560 (full prefix) | 128 | 2.88843e-4 | 6.91220% | 1.27376e-8 |
| 5120 | 256 | 1.45617e-4 | 5.50795% | 4.79494e-9 |
| 10240 | 4/512 성공 | 구간 미완료 | 구간 미완료 | 전체 구간 판정 없음 |

Short 5120에서도 속도 차이는 1%보다 크다. Short 10240은 5번째 step의
`line_search_failed`로 중단돼 전체 short 판정을 내리지 않았다.
실패 직전 dt는 1.0467854669e-4s이며 마지막 Newton 반복에서 다음을 관찰했다.

- 비선형 잔차 1.51874e-8m/s² > 허용값 1.34886e-8m/s².
- 전체 correction/L=4.10444e-17, 실제 GMRES 잔차 검사는 통과.
- 21개 line-search trial이 모두 실패했고 마지막 성공 상태를 유지.
- 좌표 한 ULP/(beta dt²)=8.10559e-8m/s². 절대 위치 차분의 반올림 영향을 의심할 근거지만 원인은 미확정.

Full N=2560의 속도 차이 제곱합에서 XY 모드 1040.43/901.59/1457.63rad/s의 비중은
37.28/16.80/8.61%다. Short N=5120에서는 2464.70/2553.27/2617.34rad/s의 비중이
21.57/17.91/11.57%다. 이는 저장된 시각의 공간 modal projection 제곱합이며,
최대 오차 시각의 비중이나 연속 시간 주파수 spectrum을 뜻하지 않는다.
고주파 위상 오차와 작은 dt의 풀이 정밀도 문제를 구분해 조사해야 한다.
기존 수렴 tolerance를 완화하거나 Newmark를 변경하지 않았다.

## 재검산·재현성과 보존

새 25개와 기존 106개, 총 **131개 테스트가 통과**했다. 원본과 독립 재실행의 수치 report,
모든 상태·modal 배열과 runtime을 제외한 반복 trace hash가 일치했다.
각 run의 source 18개·inventory 453개, 72개 case 배열의 총 49,800개 frame,
248개 NPZ chunk를 검산했다. Frame 수는 internal/sample과 case 초기 상태의 중복을 포함한다.
Pin·반력·운동방정식·에너지, Newmark 갱신·state chain, 기준 자체 대조·full/short·기존 320 비교와 CSV를
저장된 원본으로 다시 계산했다. 성공 step의 최대 잔차/허용값 비는 0.965412였다.
위치·속도 갱신식의 최대 차이는 2.19806e-16m / 4.33681e-19m/s다.
이 검산 통과는 기록의 정확성과 재현성이며 응답 수렴 통과를 뜻하지 않는다.

Report semantic SHA-256은 두 run 모두
`33ddc889a428d70a814d0e2df894a265f4469ab54c97e2260908137fd6a16579`다.
Case runtime 합은 원본 451.723s, 재실행 455.850s이며 source/modal·case 외 I/O 등을 포함한 전체 wall time은 아니다.
두 run은 1,800초 budget 내 종료했다.

[Provenance](provenance.json)는 선택 evidence **9개·749,815byte**의 hash와 원본 위치를 연결한다.
원본·재실행의 inventory는 각각 453개·190,075,838byte / 453개·190,075,917byte다
(각 manifest 자체는 제외). 전체 NPZ·modal basis·trace·chunk는 두 ignored run에 그대로 보존했다.
회수 시 provenance의 manifest hash와 해당 manifest의 상대 경로·byte/hash를 확인한다.
원본 삭제·덮어쓰기나 dataset 발행은 하지 않았다.

Workspace root에서 기록 검산을 다시 실행할 수 있다. 기존 두 run과 environment에 기록된 source가 필요하며
검산 결과는 `/tmp/wind3dgs_shell_temporal_verification.json`에 쓴다. 두 고정 run을 검토하는 실험 전용 보조 파일이다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_temporal/evidence/verify_reference.py
```

[검산 결과](evidence/verification.json)와 [code 구현 기록](../../code/sessions/2026-09-08_01_teacher_shell_temporal_design.md)에
검증 범위와 테스트 명령을 남겼다. 다음 기능 후보는 작은 dt에서의 위치 차분·잔차 정밀도 검토다.
그 해결만으로 고주파 시간 수렴이나 학습 Teacher 적격성을 확정하지 않는다.
