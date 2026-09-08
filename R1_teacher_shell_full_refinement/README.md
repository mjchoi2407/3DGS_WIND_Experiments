# Shell 한 주기 전체 시간 refinement

2026-09-08, Wind3DGS R1 개발 진단. [승인된 설계](../../code/sessions/2026-09-08_04_teacher_shell_full_refinement_design.md)의
동일 n=4 shell을 N=20480/40960/81920으로 한 주기 T1 전체 적분한다.
관련 **184개 검사가 통과**했고 원본·독립 재실행의 세 full case가 모두 완료됐다.
두 보고서는 동일하며 **full 응답 기준을 통과**했다. 두 run 각각의 모든 native 상태·반복 벡터 검산도 완료했다.

기존 가속도 변수 Newmark·물성·초기 상태·tolerance를 유지한다.
네 선행 원본의 연결과 short 상태를 다시 검사한 뒤, 각 full case를 frame zero에서 독립 시작한다.
DOP853 reference_b의 10,241개 고정 시각에서 위치·속도를 비교하며 후보는 stride 2/4/8로 선택한다.
에너지 drift는 모든 native step을 집계한다. 세 level의 위치·속도 차이가 감소하고 finest가 모두 1% 이하,
finest energy drift가 1e-3 이하일 때만 full 응답 통과다.

## 한 주기 응답 결과

| 적분 N | 위치 차이 [%] | 속도 차이 [%] | 모든 native 시각의 최대 상대 energy drift |
| --- | ---: | ---: | ---: |
| 20480 | 0.0174305602 | 6.05975811 | 2.14091145e-9 |
| 40960 | 0.00679436464 | 2.97472254 | 6.80004941e-10 |
| 81920 | 0.00187127486 | 0.868280813 | 3.67369912e-10 |

위치·속도는 free mass RMS의 공통 시각 최대 차이를 각각 A와 Aω1로 나눈 값이다.
두 차이가 엄격히 감소하고 finest가 모두 1% 이하이며 energy drift도 1e-3 이하이므로 통과했다.
관측 차수는 위치 1.35921 → 1.86032, 속도 1.02651 → 1.77652다.
차수 2를 필수 조건으로 추가하거나 기준을 완화하지 않았다.

`source_check`, `reference_check`, `short_regression_check`, `prefix_check`, `solver_check`,
`full_response_check`가 모두 `passed`다. N=20480/40960의 초기 short 구간은 기존 원본과 일치했다.
N=81920의 개별 prefix는 같은 dt의 선행 short가 없으므로 `not_assessed`다.
정규화 속도 차이는 주로 XY 성분이며 finest XY=0.00868280189, Z=1.22830740e-5다.
Modal 값은 고정 rest basis에서의 진단이며 비선형 모드 분리나 연속 시간 최대 오차의 인증이 아니다.

Fixture는 기존 n=4 forward 1m shell, E=1e6Pa, ν=0.3, h=0.01m, M=0.1kg,
A=0.001m 첫 normal 모드, 외력·감쇠 0, seed=20260907이다.
T1=1.0719083180935054s이며 동일 DOP853 reference_b의 저장 시각을 재사용했다.
기준 자체 차이는 정규화 위치 1.24085090e-11, 속도 6.93486662e-9다.
기존 full N=2560의 11.7491% 결과는 [정밀도 회귀](../R1_teacher_shell_precision/README.md)에 그대로 보존돼 있다.

## 실행과 보존

Workspace에서 다음 명령을 실행한다. Launcher가 `code/`로 이동하므로 인자 경로는 `code/` 기준이다.
출력은 기존 폴더를 덮어쓸 수 없다. 원본과 독립 재실행은 별도 새 폴더에 저장한다.

```bash
bash code/scripts/audit_teacher_shell_full_refinement.sh \
  --dynamics-source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --temporal-source-run ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1 \
  --precision-source-run ../experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1 \
  --refinement-source-run ../experiments/artifacts/runs/teacher_shell_refinement/20260908_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_full_refinement/my_new_run
```

실행당 143,360 step, audit당 wall-clock 상한 7,200초다. `--max-wall-time-s`는 상한을 줄일 때만 사용한다.
원본·독립 재실행은 CPU 별도 프로세스에서 수행하며 GPU는 사용하지 않는다.
256개 성공 endpoint마다 native 상태·trace·모든 iteration/trial 벡터를 저장하고 메모리 buffer를 비운다.
초기 상태는 별도 파일, 공통 grid 선택본과 집계는 case 파일에 보존한다.
성공 chunk만 hash chain과 manifest checkpoint에 등록하고 I/O 실패는 recovery/부분 파일로 구분한다.
중단 run을 자동 재개하거나 덮어쓰는 기능은 없다.

Raw run은 ignored `artifacts/runs/teacher_shell_full_refinement/`의
`20260908_reference_v1`와 `20260908_reference_v1_replay`에 계속 보존한다.
최종 [provenance](provenance.json), [원본 보고서](evidence/reference/report.json),
[원본 manifest](evidence/reference/manifest.json), [재실행 manifest](evidence/replay_manifest.json),
[검산 결과](evidence/verification.json)와 [검산 스크립트](evidence/verify_reference.py)를 보존했다.
Compact evidence는 9개 파일이며 전체 native 배열·반복 벡터는 raw run에만 둔다.

## 검산·실제 비용

두 run 각각 143,360 step, 초기 상태를 포함한 143,363 frame, 560개 chunk,
1,576,960개 반복/trial 벡터를 확인했다. 각 run의 143,360개 trial과 286,720개 선형 correction을 재계산했다.
배열·runtime 제외 trace·chunk hash chain·공통 grid 선택본·보고서·CSV와 판정이 일치한다.
단순히 재실행끼리 비교한 것에 더해, 두 run 각각의 힘·반력·에너지·EOM·Newmark 갱신·state chain,
각 반복의 correction·merit·Armijo와 HVP를 사용한 선형 correction 잔차를 다시 계산했다.

최대 EOM 잔차/bound는 0.0549453, 최대 kinematic defect/bound는 0.0306161 이하다.
저장된 GMRES 잔차는 원래 solver bound를 만족한다. Scaled 변수로 correction을 재구성할 때는
선행 검산과 동일한 256ε×연산 항 크기의 roundoff 허용량을 별도로 더했으며 최대 비율은 0.998848 이하다.
이는 solver tolerance를 바꾼 것이 아니다.
실제 최대 buffer는 256 endpoint와 2,816개 벡터였으며 전체 native 상태를 case 끝에 중복 저장하지 않았다.

| run | audit 시간 [s] | 세 case 시간 합 [s] | inventory 파일 수 | inventory byte |
| --- | ---: | ---: | ---: | ---: |
| 원본 | 2742.384 | 2679.208 | 2262 | 2183688760 |
| 독립 재실행 | 2750.674 | 2687.586 | 2262 | 2183688237 |

각 audit은 약 45.7–45.8분으로 7,200초 상한 안에서 끝났다.
두 run의 inventory 합은 약 4.37GB다. 표의 inventory 크기는 최상위 manifest 자체를 제외한다.
16 logical CPU 환경에서 두 독립 계산과 checkpoint 검산을 겹쳐 실행했으므로 시간은 자원 경합·I/O를 포함한다.
검산 프로세스의 2395.712초에는 아직 기록되지 않은 chunk를 기다린 시간도 포함되며 순수 연산 benchmark가 아니다.

두 semantic report SHA-256은 다음과 같다.

```text
14700c5346b3f9502f724abd32febcc7a7a6266771ab08fbb750dae531e985f5
```

Source snapshot은 기존 23개와 새 audit/launcher 2개, 총 25개다.
원본 회수 시 provenance와 각 manifest의 상대 경로·byte/hash 및 chunk descriptor의
state/trace/vector identity·이전 chunk hash를 확인한다. 네 선행 원본도 함께 필요하다.
기존 파일을 삭제하거나 덮어쓰지 않으며 재실행에는 새 출력 폴더를 사용한다.

Workspace에서 보존된 두 run을 검산하는 명령은 다음과 같다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_full_refinement/evidence/verify_reference.py
```

관련 테스트는 `code/`에서 다음 명령으로 실행했다. 184개, 76.269초, 모두 통과했다.

```bash
PYTHONPATH=.:tests ../.venv/bin/python -m unittest \
  test_teacher_shell_full_refinement_audit test_teacher_shell_refinement_audit \
  test_teacher_shell_newmark_acceleration test_teacher_shell_precision_audit \
  test_teacher_shell_temporal_audit test_teacher_shell_dynamics test_teacher_shell_structure \
  test_teacher_plate_reference test_teacher_bending_mapping test_teacher_bending_audit \
  test_packaging_and_imports -v
```

## 결과의 범위

`teacher_eligible=false`, `convergence_status=not_assessed`다.
Full 응답 통과도 공간·probe/스펙트럼·work·감쇠·공력 검증이나 학습 dataset 발행을 대체하지 않는다.
고정 n=4·한 물성·한 초기 진동의 10,241개 공통 시각에 대한 시간 refinement 결과다.
모든 native 시각이나 연속 시간의 응답 최대 오차, 다른 mesh/material/하중의 정확도를 보장하지 않는다.
기존 공간/정적 에너지 진단의 실패도 그대로 남아 있다. 원격 fetch·설치·commit·push는 수행하지 않았다.
