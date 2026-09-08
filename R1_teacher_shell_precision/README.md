# Shell Newmark 가속도 변수 정밀도 회귀

사용자가 [설계](../../code/sessions/2026-09-08_02_teacher_shell_precision_design.md)를 승인한 개발 진단이다.
기존 Newmark의 위치 차분에서 생긴 작은 dt의 풀이 실패를 가속도 변수 경로와 대조한다.
기존 힘·HVP·물성·pin·held force·Newmark β/γ·잔차 및 correction tolerance를 유지한다.
Training/evaluation 전용 n=4 forward 1m 평판, E=1e6Pa, ν=0.3, h=0.01m, M_ref=0.1kg,
A=0.001m 첫 normal 모드, 외력·감쇠 0이며 seed는 20260907이다.
Dataset·object package·model checkpoint는 `not_applicable`, target runtime은 실행하지 않는다.

## 실행과 보존

Workspace root에서 실행한다. Launcher의 상대 경로는 `code/` 기준이며 output은 새 폴더여야 한다.

```bash
bash code/scripts/audit_teacher_shell_precision.sh \
  --dynamics-source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --temporal-source-run ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1
```

독립 재실행은 output 끝에 `_replay`를 붙인다. 각 audit의 wall-clock 상한은 900초다.
원본 dynamics·temporal inventory와 실행 source 18개, 상태·반력·에너지·시각·policy를 검증한다.
새 runtime source 21개와 환경·입력·배열·report/trace hash를 기록한다.
기준은 기존 DOP853 a/b 자체 대조를 재검산한 reference_b의 저장 배열이다. 새로운 DOP853 실행이 아니다.

| 사례 | 시작 | 최대 step |
| --- | --- | ---: |
| legacy_restart_5 | 기존 실패 직전 state | 실패 재현 1회 시도 |
| acceleration_restart_5 | 같은 기존 state | 1 |
| acceleration_short_2560 / 5120 / 10240 | 각각 frame zero, 초기 T1/20 | 128 / 256 / 512 |
| acceleration_full_2560 | frame zero, 전체 T1 | 2560 |

새 성공 step 상한은 3,457개다. 기존 실패와 다르거나 기준 해의 검증이 실패하면 후보 실행을 시작하지 않는다.
후보 풀이 실패 뒤의 case도 미실행으로 남긴다. 각 후보는 독립 초기화하며 restart 결과를 full 궤적에 이어 붙이지 않는다.
64 step 이하 단위로 상태·iteration/trial 벡터·trace를 checkpoint하고 예외/중단 시 마지막 성공 상태와 부분 파일을 보존한다.
원본 두 run 및 이전 실험을 삭제·덮어쓰지 않는다. 전체 상태·trial 배열은 ignored artifact에 유지하고,
manifest/config/environment/report/CSV/log·검산 결과를 compact evidence로 선택한다.

## 사전 판정

Source, reference, legacy 실패 재현, solver·정밀도 회귀, short 응답과 full 단일 기준 대조를 분리한다.
정밀도 회귀는 원래 잔차·correction 기준으로 모든 후보 구간을 완료하고 Newmark 갱신 검산을 통과해야 한다.
Short는 세 해상도에서 정규화 x/v 차이 감소·finest ≤1%, 최대 상대 energy drift ≤1e-3를 검사한다.
Full은 후보 N=2560 하나를 reference와 대조하며 같은 1%/1e-3 기준을 보고한다.
Full refinement는 실행하지 않아 `full_response_check=not_assessed`다.
정규화 차이는 free mass RMS의 시간 최대값을 A 또는 Aω1로 나눈 값이다.
별도 경로의 integrator identity는 `newmark_average_acceleration_acceleration_unknown_v1`이다.

항상 `teacher_eligible=false`, `convergence_status=not_assessed`다. 기존 고주파 시간 차이의 해결이나
학습 Teacher 채택을 이 기능의 구현 완료와 혼동하지 않는다. 상세 test/실행 상한과 제외 범위는 승인 설계를 따른다.

## 2026-09-08 실제 결과

Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU에서 원본과 독립 재실행을 실행했다.
두 run 모두 기존 5번째 step 실패를 재현했고, 후보 5개 case의 **3,457 step을 전부 완료**했다.
Legacy 대조의 `failed`는 예상했던 풀이 실패를 그대로 보존한 상태다.

| 분리 판정 | 결과 |
| --- | --- |
| source / reference / legacy_failure_replay | 모두 `passed` |
| solver / precision_regression / short-full prefix | 모두 `passed` |
| short_response_check | `failed` — finest 속도 차이 1% 초과 |
| full_reference_error_check | `failed` — N=2560 단일 기준 대조 |
| full_response_check | `not_assessed` — 후보 full ladder는 미실행 |
| convergence_status / teacher_eligible | `not_assessed` / `false` |

| 후보 구간 | T1당 N | 실제 step | 정규화 x 차이 | 정규화 v 차이 | 최대 상대 energy drift |
| --- | ---: | ---: | ---: | ---: | ---: |
| 초기 T1/20 | 2560 | 128 | 2.88843e-4 | 6.91220% | 1.25368e-8 |
| 초기 T1/20 | 5120 | 256 | 1.45617e-4 | 5.50795% | 4.82444e-9 |
| 초기 T1/20 | 10240 | 512 | 4.97580e-5 | 2.20620% | 1.38046e-9 |
| 전체 T1 | 2560 | 2560 | 6.24816e-4 | 11.7491% | 1.48614e-7 |

비교 기준은 원본에서 재검증한 reference_b다. A=0.001m, ω1=5.8616816393rad/s,
T1=1.0719083181s다. 정규화 속도 차이의 분모는 Aω1이며 순간 속도에 대한 상대 오차가 아니다.
Short는 x/v 차이가 모두 감소하지만 finest 속도 차이가 1%보다 커 통과하지 못했다.
Full 단일 결과는 기존 위치 기반 경로와 거의 같다. 두 경로 사이의 정규화 최대 속도 차이는
short N=2560에서 1.05992e-9, short N=5120에서 7.59297e-10, full N=2560에서 3.31711e-9다.
기존 실패 때문에 없던 N=10240 short 전체 결과를 이번에 확보했다.

## 정밀도 보정의 효과와 한계

기존 실패 직전 state에서 후보 step 5는 Newton update 1회로 완료했다.
마지막 잔차는 **3.12274e-10m/s²**, 원래 허용값은 **1.34886e-8m/s²**다.
즉 허용값의 약 2.315%다. 마지막 위치 환산 correction/L은 8.38428e-19다.
기존 실패 trace의 잔차·correction·21개 trial은 원본 그대로 재현됐다.

같은 후보의 저장 위치 x_end에서 기존 predictor p로 a=(x_end-p)/(βdt²)를 역산해 보면,
운동방정식 잔차가 **2.45592e-8m/s²**로 다시 허용값을 초과한다.
직접 푼 a와 역산한 a의 free mass RMS 차이는 2.45048e-8m/s²다.
이것은 두 별도 궤적을 비교한 값이 아니라 동일한 시작 상태·끝 위치에서의 산술 대조다.
후보는 독립 위치/속도 갱신 검산도 통과했다. 이 fixture의 정밀도 문제를 해결한 근거이며,
내부 힘 평가의 모든 반올림 한계를 제거했다는 뜻은 아니다.

Short의 새 fine run과 full run을 모두 완료해 `precision_regression_check=passed`다.
기존 응답 차이가 유지되는 해상도도 확인됐으므로, 남은 시간 해상도 문제와 정밀도 보정을 구분한다.
다음 검토 대상은 이 경로를 이용한 더 작은 dt의 응답 대조다. 이번 실행은 승인한 N=10240 이하와
지정 구간에서 끝냈고 추가 해상도나 새 적분기를 자동으로 실행하지 않았다.

## 검산·재현성과 artifact 회수

새 24개와 기존 131개를 합친 **155개 테스트가 통과**했다. 실제 두 run의 semantic report,
모든 상태·modal·iteration/trial 배열, runtime을 제외한 trace hash가 일치했다.
각 run의 source 21개·inventory 198개, 저장 상태 3,463개, 반복 벡터 55,702개,
trial 벡터 묶음 5,982개와 NPZ chunk 108개를 검산했다. 저장 상태 수는 각 case의 시작 상태도 포함한다.
새로운 후보의 accepted step 수는 실행당 3,457개다.

Pin·반력·힘·에너지·state chain, 모든 성공 step의 위치/속도 갱신,
각 iterate와 trial의 가속도·위치·보정량·실제 위치 변화·merit/Armijo 판정을 다시 계산했다.
Short/full·기존 경로 대조의 모든 수치와 CSV도 일치했다.
성공 step의 최대 잔차/허용값 비는 0.999232, 위치/속도 갱신 결함의 최대 roundoff bound 비는 0.0290237이었다.
검산의 `passed`는 기록의 정확성과 재현성이며 응답 수렴 판정과 구분한다.

두 report의 semantic SHA-256은
`093fd1b440f61b7e604167abd25a902c1f0170071d018df3348245067c397be6`이다.
Case runtime 합은 원본 120.953s / 재실행 121.730s다. Source 검산과 case 최종 파일 저장 등을 포함한
전체 wall time과는 구분하며, 두 audit은 각각 900초 상한 내 종료했다.

[Provenance](provenance.json)는 선택 evidence **9개·430,310byte**와 원본 위치를 연결한다.
원본과 재실행의 inventory는 각 198개·142,905,367 / 142,905,457byte다(manifest 자체 제외).
전체 배열·실패/반복 trace·chunk는 두 ignored run에 그대로 유지했다.
회수 시 provenance의 manifest hash와 각 manifest의 상대 경로·byte/hash를 확인한다.

실제 실행한 검산 보조 파일을 evidence에 복사했다. 기존 두 source run과 이번 두 run 및
environment에 기록된 source snapshot이 필요하다. Workspace root에서 재검산한다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_precision/evidence/verify_reference.py
```

새 검산 결과는 `/tmp/wind3dgs_shell_precision_verification.json`에 쓴다.
[선택 검산 결과](evidence/verification.json), [수치 보고서](evidence/reference/report.json),
[CSV](evidence/reference/comparisons.csv), [code 구현 기록](../../code/sessions/2026-09-08_02_teacher_shell_precision_design.md)을 함께 확인한다.
Dependency 설치·외부 조회·fetch·commit·push는 수행하지 않았다.
