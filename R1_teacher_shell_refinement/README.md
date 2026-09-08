# Shell 가속도 Newmark 짧은 구간 시간 refinement

[승인한 설계](../../code/sessions/2026-09-08_03_teacher_shell_refinement_design.md)에 따른 R1 개발 진단이다.
초기 T1/20에서 적분 간격을 두 번 줄여 고정된 513개 시각의 위치·속도 차이가 감소하는지 검사한다.
기존 short N=10240을 검증 후 재사용하고 N=20480/40960을 각각 frame zero부터 계산한다.
세 단계에서 차이가 감소하지 않거나 finest 정규화 x/v 차이 >1%, native energy drift >1e-3이면 응답 검사는 실패다.

## 입력·실행 범위

Training/evaluation 전용 n=4 forward 1m 평판, E=1e6Pa, ν=0.3, h=0.01m, M_ref=0.1kg,
A=0.001m 첫 normal 모드, 외력·감쇠 0, seed=20260907이다.
Dataset·object package·model checkpoint는 `not_applicable`, target runtime은 실행하지 않는다.
기존 가속도 변수 Newmark의 힘·질량·pin·β/γ·잔차/correction tolerance를 유지한다.
Full/공간 refinement, 공력·감쇠·GPU/GUI와 학습 데이터 발행은 포함하지 않는다.
항상 `teacher_eligible=false`, `convergence_status=not_assessed`, `full_response_check=not_assessed`다.

Workspace root에서 실행하며 launcher의 상대 경로는 `code/` 기준이다.

```bash
bash code/scripts/audit_teacher_shell_refinement.sh \
  --dynamics-source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --temporal-source-run ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1 \
  --precision-source-run ../experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_refinement/20260908_reference_v1
```

독립 재실행은 output 끝에 `_replay`를 붙인다. Output은 새 폴더여야 하며 세 입력과 겹칠 수 없다.
CPU NumPy/SciPy에서 실행한다. 각 audit의 wall-clock 상한은 900초이며 `--max-wall-time-s`로 낮출 수 있다.
기존 source 21개를 유지하고 신규 audit/launcher를 포함한 runtime 23개의 hash와 환경을 기록한다.

## 비교·보존 계약

| 사례 | T1당 적분 N | 실제 step | 비교 stride | 비교 frame | 출처 |
| --- | ---: | ---: | ---: | ---: | --- |
| acceleration_short_10240 | 10240 | 512 | 1 | 513 | precision 원본 재사용 |
| acceleration_short_20480 | 20480 | 1024 | 2 | 513 | 신규 |
| acceleration_short_40960 | 40960 | 2048 | 4 | 513 | 신규 |

실행당 신규 성공 step 상한은 3,072개다. Reference는 자체 대조를 재검산한 기존 DOP853 reference_b다.
새 DOP853 실행은 없다. Baseline도 원본 state/trace/vector identity, 힘·반력·에너지·Newmark 갱신과
state chain을 검산한 뒤 재사용한다. 세 입력의 연결·semantic hash·inventory·현재 runtime hash가 맞아야 한다.

비교 시각은 `T1*k/10240, k=0..512`이며 후보와 기준을 보간하지 않는다.
Primary는 free mass RMS의 공통 시각 최대값을 위치 A, 속도 Aω1로 정규화한 값이다.
XY/Z·SI·tip·고정 rest modal projection은 보조 지표다. 위상/ωdt는 실제 적분 N을 사용한다.
Energy drift는 모든 native frame에서 검사하며 공통 시각의 drift도 별도로 기록한다.
공통 시각 사이의 위치·속도 오차나 연속 시간 최대값을 인증하지 않는다.

64 frame 이하 chunk와 최종 case에 모든 native state·성공/실패 iteration/trial 벡터·trace를 보존한다.
풀이 실패 시 다음 case를 실행하지 않고, 미완료 series는 `not_assessed`로 기록한다.
원본·재실행과 기존 입력 run을 덮어쓰거나 삭제하지 않는다.
Raw NPZ/JSONL은 ignored run에 유지하고 compact report/config/environment/manifest/log와 검산 기록만 선택한다.

## 2026-09-08 실제 실행 결과

Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU에서 원본과 독립 재실행을 완료했다.
두 run 모두 새 3,072 step을 완료했고 `source/reference/baseline/solver/short_response_check=passed`다.
신규 16개와 기존 155개를 합친 **171개 테스트가 통과**했다(52.228s).

| T1당 적분 N | 정규화 위치 차이 | 정규화 속도 차이 | 모든 native frame의 최대 상대 energy drift |
| --- | ---: | ---: | ---: |
| 10240, 재사용 | 4.97580173e-5 | 2.20619631% | 1.38046241e-9 |
| 20480, 신규 | 1.31977665e-5 | 0.61230757% | 3.59215768e-10 |
| 40960, 신규 | 3.35283019e-6 | 0.15404377% | 8.25424173e-11 |

세 단계에서 위치·속도 차이가 각각 감소하고 finest의 1%/1e-3 조건도 통과했다.
관측 차수는 위치 1.91464 → 1.97684, 속도 1.84923 → 1.99092로,
이 short fixture의 finest 두 level은 2차 시간 오차 감소와 가까운 결과다.
기준 자체 차이의 noise floor를 넘은 비교이며 모든 상황의 2차 정확도 증명으로 해석하지 않는다.
분모는 A=0.001m 및 Aω1이고 T1=1.0719083180935054s, 비교 구간은 약 0.0535954s다.

한 주기 전체는 이번에 실행하지 않았다. 기존 full N=2560의 11.7491% 차이는
[선행 결과](../R1_teacher_shell_precision/README.md)에 그대로 남는다.
Short 통과만으로 full/공간 convergence나 학습 Teacher를 채택하지 않는다.
다음 기능은 full refinement의 해상도·실행 예산 설계다.

두 report의 semantic SHA-256은
`eb95b82ffaddf05a8c638925400621b9d32e26529a8a58612cd9c1e8b177c37b`로 일치한다.
신규 case runtime 합은 원본 54.5378s / 재실행 54.8366s다.
이는 입력 검산과 최종 case 저장 등을 포함한 전체 wall time과 구분하며 각 audit은 900초 상한 내 완료됐다.
각 run의 manifest 제외 inventory는 160개, 원본 91,940,477byte / 재실행 91,940,506byte다.

## 검산·재현성과 artifact 회수

원본·독립 재실행의 semantic report, 모든 native 상태/modal/iteration/trial 배열과 runtime을 제외한 trace hash가 일치했다.
각 run에서 source 23개·inventory 160개, 저장 상태 3,074개, 반복 벡터 33,792개,
trial 묶음 3,072개·선형 correction 6,144개와 NPZ chunk 96개를 검산했다.
재사용 baseline의 512 step도 세 입력 검증에 포함했다. 신규 step 수와 재사용 step 수는 구분한다.

Pin·반력·힘·에너지·Newmark 갱신·state chain, 모든 iterate와 trial의 가속도·위치·실제 위치 변화,
correction·merit/Armijo와 상태 연결을 다시 계산했다. 저장 correction에 HVP를 적용해 질량 스케일 선형 잔차도 검산했다.
후자는 저장 벡터에서 선형 변수를 복원하는 산술의 roundoff 항을 별도로 포함한다.
실제 solver의 GMRES rtol=1e-10과 기록된 원래 잔차 bound 통과를 함께 확인했으며 solver 기준을 완화하지 않았다.
Native energy, 공통 시각의 primary/보조 비교·CSV와 short 판정도 다시 계산했다.

성공 step의 최대 nonlinear 잔차/허용값 비는 0.0413108, Newmark 갱신 결함/roundoff bound 비는 0.0251813이었다.
검산 `passed`는 기록의 정확성·재현성이다. Short 응답 통과와 full/공간 수렴 미평가를 구분한다.

[Provenance](provenance.json)는 선택 evidence **9개·311,813byte**를 원본 위치와 byte/hash로 연결한다.
모든 raw 상태·벡터·trace·chunk는 원본과 독립 재실행의 ignored run에 유지했다.
회수 시 provenance의 manifest hash와 각 manifest의 상대 경로·byte/hash를 확인한다.

실제 실행한 검산 파일을 byte 단위로 동일하게 evidence에 복사했다. 세 입력 run, 이번 두 run과
environment에 기록된 source snapshot이 필요하다. Workspace root에서 재검산한다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_refinement/evidence/verify_reference.py
```

출력은 `/tmp/wind3dgs_shell_refinement_verification.json`이다.
[선택 검산 결과](evidence/verification.json), [수치 report](evidence/reference/report.json),
[CSV](evidence/reference/comparisons.csv), [실험 session](../sessions/2026-09-08_03_teacher_shell_refinement.md)을 함께 확인한다.
Dependency 설치·외부 조회·fetch·commit·push는 수행하지 않았다.
