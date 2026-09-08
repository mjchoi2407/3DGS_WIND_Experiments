# Shell 가속도 Newmark 짧은 구간 시간 refinement

- 날짜: 2026-09-08
- 범위: Wind3DGS experiments-side, R1 short 시간 해상도 개발 진단
- 상태: 관련 171개 검사·CPU 원본·독립 재실행·상태/벡터 검산 완료, short 응답 기준 통과
- 계약과 명령: [실험 README](../R1_teacher_shell_refinement/README.md),
  [code 설계·구현 기록](../../code/sessions/2026-09-08_03_teacher_shell_refinement_design.md)

사용자 “ㄱㄱ”로 구체적인 short refinement 기능과 실제 실행 범위를 승인했다.
Baseline N=10240 재사용, 신규 N=20480/40960 총 3,072 step/run,
원본과 독립 재실행·상태/벡터 검산을 진행한다. 기존 물리·solver source·tolerance는 유지한다.
Full/공간 refinement, 학습 Teacher 채택과 dataset 발행은 이번 기능 밖이다.

기존 dirty 변경과 원본 run은 보존하며 새 output 폴더만 사용한다.
구현 전 root·code·ideas·experiments의 로컬 status/HEAD와 비ignored 파일 597개의 hash를 확인했다.
Artifact/environment manifest는 정책·과거 관측으로 읽었고 현재 source/environment는 새 run에서 별도로 기록한다.
외부 조회·fetch·설치·stage·commit·push는 하지 않았다.

## 실행·판정

README의 명령으로 `artifacts/runs/teacher_shell_refinement/20260908_reference_v1`과
`20260908_reference_v1_replay`를 새로 실행했다. Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU다.
원본 세 개·reference·baseline의 검산을 통과한 뒤 각 run에서 신규 3,072 step을 완료했다.
관련 171개 검사가 52.228s에 통과했다. Dependency 변경·GPU 실행은 없다.

| N | 정규화 위치 차이 | 정규화 속도 차이 | native 최대 상대 energy drift |
| --- | ---: | ---: | ---: |
| 10240, 원본 재사용 | 4.97580173e-5 | 2.20619631% | 1.38046241e-9 |
| 20480, 신규 | 1.31977665e-5 | 0.61230757% | 3.59215768e-10 |
| 40960, 신규 | 3.35283019e-6 | 0.15404377% | 8.25424173e-11 |

같은 513개 시각의 위치·속도 차이 감소와 finest의 1%/1e-3 기준을 통과했다.
`source/reference/baseline/solver/short_response_check=passed`다.
관측 차수는 위치 1.91464/1.97684, 속도 1.84923/1.99092다.
Full refinement는 미실행이며 기존 full N=2560의 11.7491% 차이는 그대로 보존한다.
`full_response_check=not_assessed`, `convergence_status=not_assessed`, `teacher_eligible=false`다.

## 검산·보존

두 report의 semantic SHA-256:
`eb95b82ffaddf05a8c638925400621b9d32e26529a8a58612cd9c1e8b177c37b`.
Report와 모든 상태/modal/반복 벡터, runtime을 제외한 trace hash가 일치했다.
Run마다 source 23개·inventory 160개·신규 상태 3,074개·반복 벡터 33,792개,
trial 3,072묶음·선형 correction 6,144개·NPZ chunk 96개를 재검산했다.
EOM·힘·pin/반력·에너지·Newmark 갱신·state chain, iteration/trial·merit/Armijo,
correction의 선형 잔차·공통 시각 비교·CSV와 판정이 일치했다.
최대 nonlinear 잔차/bound 비는 0.0413108, 갱신 결함/bound 비는 0.0251813이었다.

Case runtime 합은 원본 54.5378s / 재실행 54.8366s이며 각 audit은 900초 상한 내 완료됐다.
전체 native 상태·벡터·trace·chunk는 ignored 원본 두 개에 유지했다.
Manifest 제외 raw inventory byte 수는 원본 91,940,477 / 재실행 91,940,506이다.
[Provenance](../R1_teacher_shell_refinement/provenance.json)는 선택 evidence 9개·311,813byte와
원본 위치·manifest/hash를 연결한다. [검산 결과](../R1_teacher_shell_refinement/evidence/verification.json)와
실제로 실행한 검산 파일의 동일 복사본도 포함한다. 재현 명령은 README를 따른다.

## 완료·다음 단계·Git

이번 short refinement 기능과 기록을 완료했다. 다음 검토는 한 주기 전체의 시간 refinement 해상도와 예산이다.
Short 통과만으로 학습 Teacher·dataset을 발행하지 않았다.
Experiments의 새 실험/evidence/session·README/index는 미commit·미push다.
Code의 구현·test·launcher·문서도 미commit·미push이며 root·ideas는 이번에 변경하지 않았다.

최종 QA에서 문서 로컬 링크 91개·공백·개인 경로/credential 패턴·두 저장소 diff·Bash 문법을 확인했다.
선택 evidence 9개와 원본 byte/hash, 실제 검산 파일/결과의 동일 복사,
새 두 run inventory 320개·runtime source 23개 및 기존 여섯 run inventory 1,426개의 보존 검사가 통과했다.
