# 2026-09-09 02 변화 바람/도달 형상 속도 초기화 비교

## 현재 상태

2026-09-11 후속 상태: 사용자 실행 두 묶음이 종료되었다. 최신 결과·확인 범위는 [실험 인계](2026-09-10_02_teacher_timestep_search.md)를 따른다. 아래는2026-09-10 인계 시점의 근거다.

확인 기준: 2026-09-10 사용자 실행 완료 후 전체 성능 비교 결과와 원본 무결성을 확인했다.

- [전체 1.5초 비교 완료 결과](../R1_teacher_velocity_reset/p3_shell_random/profiling/full_run/README.md#완료-결과): 기존·개선 방식과 양쪽 검산·비교 모두 통과. CPU 풀이를 유지한 HVP/graph 개선의 전체 실행 근거를 확보했다.
- 저장 파일·동결 source identity와 재시작 경계를 확인했다. 속도는 단일 순차 비교 및 다른 부하·재시작 영향을 포함한 잠정값이다.
- 중단 → 저장 frame부터 사용자 재개 → 양쪽 전 구간 검산·비교 완료. 수식·허용오차는 변경하지 않았다.
- 사용자 결정: CPU 반복 풀이+HVP/graph 경로로 후속 물리 검증을 계속하며 추가 GPU 풀이 최적화는 보류한다. 장시간 계산은 사용자 실행으로 인계한다.
- [개선 경로 인계 준비](../R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/README.md): 사용자 선택1에 따라 기존 원본을 보존하는 동결 실행 묶음 준비 완료. CPU/CUDA 이어하기 전체 흐름과 경계·reset·재시작·원식 검산을 시험했다. 기본 v2 묶음은 사용자 실행 대기이며 긴 계산은 시작하지 않았다.
- CuPy GPU LU는 미채택이며 추가개발은 보류다. 다른 격자/velocity-reset 전체 검증, R1 전체·학습 적격성·추가 학습데이터 생성은 미완료다.

## 이전 단계의 결정과 근거

Wind3DGS experiments-side. 사용자가 선택한 rest-start 변화 바람과 중간 형상의 velocity-reset 탐색을
“작업 계속해줘” 요청으로 이어간다. [실험 README](../R1_teacher_velocity_reset/README.md)를 실행 전에
작성했고, 동일 기능의 구현 계약은 `code/sessions/2026-09-09_02_teacher_velocity_reset.md`에 기록했다.

## 사전 설정과 적용 범위

Seed20260909, 1.5 s/90 frame, native Newton CPU, mesh4/8/16 및 substeps8/16/32의 5조건.
Rest 원본, 무개입 재생, 0.3/0.7/1.1 s의 세 독립 reset을 비교한다. 실제 wind vector를 고정해 이후 입력을
일치시키고, 두 buffer의 velocity만 0으로 만든다. Solver 상태는 원본 prefix replay로 재구성한다.
원본·분기는 같은 source group이며, 학습 label/window나 target runtime 초기화 API는 발행하지 않는다.
P3 처방 압력 결과를 승계하지 않고 별도 demo 개발 schema와 training_eligible=false를 유지한다.

## 실행·검증

```bash
bash code/scripts/check_teacher_velocity_reset.sh \
  --output ../experiments/artifacts/runs/teacher_velocity_reset/20260909_velocity_reset_v1
```

실제 결과, 재검산·회귀·대표 그림과 판정은 아래 완료 절과 README에 기록했다.
개인 절대 경로·secret 없이 환경과 producer source hash를 기록한다. 기존 artifact는 덮어쓰지 않았다.

## 완료 결과

CPU 373.876초, 25 trace/2,250 interval/2,275 state/54,000 VBD substep을 실행했다.
다섯 독립 replay의 위치·속도·force/work 최대 차이0, 모든 reset 위치 보존/v0/kinetic 개입 검산 통과.
전체 finite/pin drift0/guard0이며 공력·work·event·보고서를 새 프로세스에서 재계산했다.
Producer source25개와 설치 Newton VBD source도 hash 대조했다. 신규8개+Newton 관련85개 회귀가 통과했다.
새 GPU 검사는 하지 않았다.

Raw inventory는 manifest 제외55파일/6,791,538 byte, manifest content hash는
`1a44df7a0605324e54c069041e99e385b87ab6d445509eb166169c15bfaaed87`이다.
[Compact evidence](../R1_teacher_velocity_reset/evidence/)에 원본 report/config/environment/manifest/run.log,
별도 verification/rotation diagnostic과 대표 응답·refinement PNG 두 장을 보존했다.
[Provenance](../R1_teacher_velocity_reset/provenance.json)에 각 evidence byte hash를 기록한다.
Raw를 삭제·덮어쓰지 않았으며 clone만으로 NPZ가 복구되는 것은 아니다.

물리 진단은 실패다. 자연 연속의 finest 공간 속도12.040068%, 시간 속도2.176690%가1% 기준을 넘었다.
모든 reset finest pair도 실패하며1.1 s reset은 공간81.148231%/시간17.756006%다.
작은 fine peak와 절대 차이도 README 표와 report에 함께 남겼다.

또한 현재 pin-line이 강체 회전을 허용하여0.7 s 형상의 총 probe 변위 RMS12.700918 mm 중 회전 잔차가
0.002380 mm뿐이었다. 단일 seed·짧은 구간·회전 위주 상태에서 굽힘 상태의 학습 적절성을 확정하지 않는다.
기울기 또는 동일한 물리 폭의 고정 영역으로 굽힘 상태를 확보하는 후속 후보와 먼저 시간 오차를 줄인 뒤
공간 비교를 다시 하자는 판단을 R1 본문에 기록했다. 현재 fixture/물성을 그 후보로 변경하지 않았다.
`training_eligible=false`, R1 미완료이고 새 학습 patch/window dataset은 발행하지 않았다.

정확한 재현/검산/그림 명령과 모델·진단 식은 [실험 README](../R1_teacher_velocity_reset/README.md)가 소유한다.
실험 README/index/session과 evidence를 갱신했고 기존 무관한 변경을 보존했다. Commit/push/fetch는 하지 않았다.

## 후속: 왼쪽0.25m 고정·시간 보완·공간 실패 분석

사용자는 굽힘 fixture의 BC로 왼쪽0.25m 영역 고정을 선택했다. 초기25 trace, 자연 연속 pilot3 trace,
추가 시간10 trace를 CPU로 실행했다. 모두 기존 rest/mass/material/바람/fps/horizon을 유지한다.
Raw 경로는 `artifacts/runs/teacher_velocity_reset/` 아래 다음 세 폴더다.

| 폴더 | 경과 [s] | manifest 제외 파일/byte |
| --- | ---: | ---: |
| 20260909_strip_initial_v2 | 320.758 | 55 / 5,039,317 |
| 20260909_strip_temporal_pilot_v2 | 110.384 | 8 / 450,485 |
| 20260909_strip_refined_v2 | 372.303 | 25 / 1,488,597 |

초기 자연 연속의 공간8→16 속도 차이140.233689%, 시간16→32는29.463330%였다.
Pilot의 iteration10→20은0.436875%, substeps32→64/64→128은1.799880%/1.257692%다.
추가 시간64→128의 자연/reset0.3/0.7/1.1 속도 차이는1.257692/1.252818/1.469637/0.974783%다.
마지막 분기는 변위1.005909%로 실패하므로 네 분기 모두 변위/속도1% 동시 기준을 통과하지 못했다.
기준을 바꾸지 않았고 추가 run에 spatial pair가 없음을 명시한다.

비평면 굽힘은 최적 평면 잔차로 확인했다. 별도 동일 해석 형상의 native 에너지는 n4/8/16/32에서
8.888856504/5.185163554/2.777765415/1.435178592 μJ다. n32/n4=0.16145817982468566이며
독립 strip slope 식과 최대 상대 차이1.7705802304e-15다. 정적 계산에 dt/iteration은 들어가지 않는다.
이는 native 이산화의 격자 의존성이 현재 BC에서도 남음을 뜻하며 전체 동역학 오차의 기여율 확정은 아니다.

[후속 보고서](../R1_teacher_velocity_reset/clamped_samples/README.md)에 정확한 실행·재계산 명령,
분모/절대값 표, 현재 실패/다음 선택과 figure를 기록했다. Compact evidence는 초기/추가 source
25/26개의 ZIP hash를 당시 environment와 대조했다. 두 raw의 전체 report 재계산과 pilot inventory 검산을
완료했다. 진단 wrapper의 pin 속성 오기(`pin_mask`)는 실제 `pinned`로 고친 뒤 재실행을 통과했다.
이 수정 전 진단은 결과 폴더 생성 전에 실패했으며 raw simulation은 변경하지 않았다.

사용자는 실패 개발 sample로 완료하는 안을 거절하고 원인 해결 후 생성을 선택했다.
새 sample 발행 수0, 관련 code17개 테스트 통과는 임시 데이터만 사용했다.
해결 범위로 기존 P3 작은 굽힘 연결(새 wind/BC 수렴 재검증 필요)과 Newton 비선형 굽힘 보완(범위 확대)을
질문했고 아직 결정 대기다. 물성/solver는 변경하지 않았다.
현재 evidence/원본을 유지하며 삭제·덮어쓰기·설치·새 GPU 실행·fetch/download·commit/push는 하지 않았다.

### 이번 후속의 최종 기록 검증

Sketch28쪽/master7쪽/R1 24쪽 PDF를 실제 XeLaTeX/latexmk로 빌드했다. 최종 log에 오류·미해결 참조·overfull이 없고, master/R1의2쪽 체크리스트0/8과3쪽 목차를 확인했다. 두 bundle3개/20개 항목의 source/PDF byte 동기화를 검산했다.
실험 evidence hash/producer snapshot 및 문서 링크, 네 저장소 diff 공백 검사를 통과했다. Root와 무관한 기존 dirty 파일의 hash 및 네 HEAD를 보존했다. Code/experiments/ideas는 현재 작업의 미commit 변경이 있고 새 commit/push/fetch는 없다.
현재 종료 상태는 물리 모델 선택 대기이며 sample 생성 완료가 아니다. 사용자가 선택하기 전에는 backend/물성 변경이나 실패 source의 sample 발행을 진행하지 않는다.

## 후속 완료: P3 작은 굽힘의 물리 검증과76개 sample 발행

사용자가 기존 P3 활용을 선택했다. 왼쪽0.25m 고정·변화 바람·도달 형상의 velocity-reset을 유지하며
기존 P3 물성/consistent mass와 작은 굽힘 wind상한.05m/s를 사용했다. 고정 경계의 slope0 처리와
full boundary moment, 독립 spline의 강한 경계를 각각 구현하여 동일 continuum 조건을 비교했다.

`R1_teacher_velocity_reset/p3_samples/README.md`에 입력·단위·에너지/공력/시간 식, scope와 반증 기준,
실제 실행/재검산/reader 예제, 격자·대각선·구적·독립 기준 표와 대표 PNG 두 장을 보존했다.
P3 8→16의 최대 속도 연속 시간 상대 상한은.882329%, 대각선.224285%, 구적.197062%,
spline16→32 .505603%, P3/spline .386575%로1% 이내다. Coarse4→8의1.423535% 실패는 보존한다.
끝점 sampled 비교와 전체 면적의 시간 상한을 구분하며, 모든 상태에서 전체 모드를 유지했다.

| Raw (artifacts/runs/teacher_velocity_reset/) | CPU초 | manifest 제외 파일/byte |
| --- | ---: | ---: |
| 20260909_p3_wind_initial_v1 | 77.781 | 54 / 167,584,586 |
| 20260909_p3_wind_verified_v1 | 91.145 | 54 / 167,594,035 |
| 20260909_p3_wind_replay_v1 | 91.445 | 54 / 167,594,035 |

Initial은 첫 paired 비교다. 이후 추가한 continuous envelope·직접 consistent M/K ledger·독립 expm을
포함한 verified/replay가 최종 채택 근거다. 각36trace/3,240interval/3,276state이며618개 배열,
44,291,978개 scalar 및 물리 report가 정확히 일치했다. 이 비교에 elapsed/log를 동일하다고 요구하지 않는다.
원본 manifest file SHA-256은6127bc9f4a895225b5c45de36dd337b18314d89c320d485194701ee2d17d69ef다.
실제 지점 변위 최대.109697mm와 모든 위치·시간 상한.421778mm미만을 구분해 기록했다.
기준1mm/기울기.01을 통과했다. Modal ledger와 직접 M/K의 roundoff 잔차도 따로 기록했다.

실제 dataset은 `artifacts/datasets/teacher_p3_reset_samples/20260909_small_bending_v1/`다.
19window/76patch, manifest 제외99파일/376,077byte다. 자연7window, reset6/4/2window이며
각12interval/13state/9probe다. Native 실패 source는 발행하지 않았다.
새 프로세스의 원본 배열/probe map/wind/work 검산과 batch8의10개 batch(마지막4개)를 통과했다.
Code의 신규11개 검사도 통과했다. 무관한 원본·artifact를 삭제/덮어쓰지 않았다.

Compact config/report/environment/manifest/log, verified/replay 대조, dataset manifest,
최초/최종 physics 및 sample producer ZIP, 대표 그림을 evidence에 보존했다. Producer source hash는
Git HEAD와 구분하며 raw NPZ는 clone만으로 복구되지 않는다. 정확한 retrieval 위치와 명령은 README에 있다.
공식 FEniCS-Shells 페이지를 웹 조회했으며 Git fetch·dependency 설치/다운로드·새 GPU 실행은 없다.
이번 결과는 작은 굽힘 한 객체/seed/풍속/60Hz scope의 sample 적격성이다. 큰 변형·장기 실행·새 입력,
independent GS/oracle 및 student 학습 이득·R1 전체 완료는 주장하지 않는다.

### P3 후속 산출물 최종 검증

Compact evidence26개 새 경로의 생성 및 당시 source ZIP/hash, 그림·문서 링크를 확인했다.
원본과 재실행을 비교한 source verification을 dataset에 함께 보존했고 sample manifest/원본 map·상태·풍장·work,
NumPy batch를 별도 프로세스로 검산했다. Raw와 dataset의 큰/작은 작업 payload는 원래 ignored 위치에 유지한다.
초기native 실패와 initial P3 진단을 최종통과로 덮어쓰지 않았다. Root/무관한 기존 파일과 네 HEAD를 보존했고
현재 code/experiments/ideas 변경은 미commit이다. Stage/commit/push/Git fetch·원본 삭제/덮어쓰기는 하지 않았다.

## 후속 진행: 물리 수식 구현 후 데이터 생성

사용자의 최신 지시에 따라 추가 학습데이터를 생성하지 않고 P3의 공통 3D 요소 수식을 검증했다.
기존 76개와 source/replay는 변경하지 않았다. 아직 전역 구조식 선택에 대한 답변을 기다린다.

- 새 재현 보고서: `R1_teacher_velocity_reset/p3_surface/README.md`.
- 정적 run: `artifacts/runs/teacher_p3_surface/20260909_geometry_v1/report.json`.
- Compact evidence: 동일 report, 신규 10개 검사 log, 기존을 포함한 21개 회귀 검사 log,
  4개 정적 대조 완료 log. Report에 7개 producer/dependency source SHA-256와 환경이 있다.
- n4/n8 × 두 대각선 4/4, 총240개 요소의 mass/3D 상대풍/가상 일 대조 통과.
  사전 상대 기준 1e-10, 최대 관측 차이 1.76425e-15 미만, 자유 영역 질량 0.075kg.
- 새 시간 rollout/학습 sample/GPU 검사는 수행하지 않았다.
- 강체 회전·Green strain/곡률의 1·2차 변화, 응력 virtual work와 공력 passive power는 요소 검사다.
  이것을 전역 nonlinear physics acceptance나 시간·공간 수렴으로 승계하지 않는다.
- 미해결: 유한 회전 shell/von Kármán/선형 P3 범위의 사용자 선택.
  전역 요소 연결·고정 경계·재료 응력·접선/solver는 그 선택 후 진행한다.
- 자료 확인: Verhelst et al. (2024) §2.1–2.3 웹 원문을 조회했다. 외부 코드 다운로드,
  Git fetch/commit/push는 수행하지 않았다. Experiments worktree 변경은 미commit이다.

공식 재실행 명령은 위 README를 따른다. 기존 sample 보고서에도 최신 추가 발행 보류 원칙을
표시했으며 이전 immutable manifest의 eligibility를 소급 변경하지 않았다.

## 후속 결정: P3 유한 회전 shell의 독립 수식·동적 검사

사용자 선택은 **1번 유한 회전 shell**이다. 모델 선택 대기는 해소되었고 추가 학습데이터는0개다.
새 보고서는 `R1_teacher_velocity_reset/p3_shell/README.md`, raw는 `artifacts/runs/teacher_p3_shell/`이다.
Koiter/StVK 막·굽힘, normal-jump/full boundary flux, consistent mass, 비선형 Newmark의 같은 식을 검증한다.
처음부터 static/time/wind run의 `training_eligible=false`, `r1_complete=false`를 기록한다.

- Static v1: n4/8/16 × 대각선2 × curvature1.2/2 × angle0/±45도,36개. Finest 에너지 차이.00747187%.
- Temporal v1: rest/bent-preloaded,0.0005s, 두 DOP853 기준과 Newmark32/64/128. 두 계열 통과.
  Bent의 초기 형상을 유지하는 manufactured preload가 포함된다. 자유 release나 동적 공간 기준은 아니다.
- Wind v1: 60Hz3 frame, [0,.5,0]→[.25,.35,-.25]→[0,0,0] m/s. Zero ambient drag 유지.
  n4/n8의sub64→128 속도 차이.275331%/.471643%; n8→16 at sub128은1.357196% 실패.
- Bent release v2: 초기 analytic cylinder1.2 m^-1, 최대 회전.9rad, preload 없이 같은 바람을 가한다.
  n4 sub128/256 실행·원본 운동방정식 검산은 통과했지만 속도 차이13.313118%로 시간 진단 실패.
  기존 임계1%를 유지한 후속 시간/공간 refinement를 진행한다.
- v2는 지지 모멘트와 실패 prefix/reset 이벤트 기록을 보완했다. v3는 substep 상한/진행 로그를 확장했다.
  CLI/로그 차이는 보고하고, mechanical source가 다른 결과끼리 자동 수렴 비교하지 않는다.
- 각 run config에14개 source hash와 CPU/Python/NumPy/SciPy/policy가 있다. v1/v2/v3 source ZIP 보존.
  오래 실행되는 추가 v1 비교는 고정된 v1 source 사본에서 수행하여 초기 source identity를 유지한다.

수치/상태/manifest 검산, complete/failed 구분과 reproducible command는 보고서에서 관리한다.
개입 에너지와 frame-force 재계산을 포함한 raw validator를 추가했다. Hard-kill 복구를 보장하는
checkpoint 시스템은 아니며 Python 예외에서 완료 prefix를 남기는 범위다. Raw는 ignored local artifact다.
Noels (2009) 저자 저장소의 primary 논문을 웹 조회했다. 외부 checkout/의존성 다운로드·설치/Git fetch는 없다.
현재 변경은 미commit·미push며 기존 sample/manifests와 네 repository HEAD는 변경하지 않는다.

### 유한 회전의 release 진단과 wind-reached reset을 구분한 후속 검산

원통 release n4는 sub1024→2048에서 속도.762185%, 변위 증분.00455078%로 시간 기준을 통과했다.
Sub128→256의13.313118%, sub256→1024의7.737815%와 거친 공간 n4→8/sub256의85.250331%는
그대로 남겼다. 원통의 자유단 moment=0 조건 불일치, 격자에 따라 커지는 초기 가속도와
초기 접선 기저의500–1000Hz 시간 오차를 별도 JSON에 보존했다. 이 초기 접선은 nonlinear 시스템의
고정 spectrum이 아니며, canonical spectrum 상태를 발행하지 않는다.

사용자의 원래 순서에는 별도5m/s peak의 rest-start/frame2-reset 진단을 추가했다. n16/sub128에서
약7.3cm 변형, 최대 법선 회전.262665rad와 reset 제거 kinetic .179405469J를 확인했다.
Frame2 reset 뒤 마지막 zero-ambient frame의 held force는0이므로 자유 응답이며,
유한 변형 중 바람 변화의 응답은 앞의 두 frame에서 발생한다. 데이터 풍속 범위는 아직 동결하지 않았다.
N8의 시간 sub128→256 .304620%, n8→16/sub128의 공간1.849529%를 분리해 보고하고 n32로 세분한다.

`p3_shell_bounds.py`의 Bernstein 검산을 모든 원본 interval에 적용했다. 공간 P3·시간 quadratic
수치 보간에 한정한 전역 단사성 충분조건, mid-surface strain, engineering curvature와 선형 두께
보간의 표면 strain 상한을 기록한다. n16/sub128 큰 바람의 r상한.034625438, J하한.931948045,
mid-surface strain상한.001136284, 선형 표면 strain상한.017044350이다.
Float64 누적 여유를 밝히고 연속 ODE·3D hyperelastic strain의 엄밀한 인증으로 승계하지 않는다.

최종 raw validator는 support torque를 운동방정식과 normal-frame couple로 다시 계산하고,
실제 검산 source16개/producer 차이를 함께 저장한다. 최종 신규23개 테스트는13.329s 통과이며,
기존P3 21개를 포함한 중복 없는 범위는44개다. 전체 repository suite는 아니다.
Source/tests20개 snapshot `p3_shell_validator_v5.zip`의 SHA-256은
`a9f6983d6116bcd2d285be28623c2404650293ea250e0b473d8f12eda1243a72`다.

실험 전용 wrapper `R1_teacher_velocity_reset/p3_shell/render_development_evidence.py`로
n16/sub128의 실제 중앙 P3 단면과 reset 양쪽 시각을 보존한 에너지 그래프를 만들었다.
`figures_v5/`에 PNG·벡터 PDF·원본/검산/wrapper 해시를 저장했고 시각적으로 확인했다.
이 그림은3 frame 수식 진단이며 장기 trajectory·학습데이터·GUI 기능이 아니다.

```bash
MPLCONFIGDIR=/tmp/wind3dgs_plot_cache PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/p3_shell/render_development_evidence.py --run experiments/artifacts/runs/teacher_p3_shell/20260909_strong_reset_m16_s128_v4 --verification experiments/artifacts/runs/teacher_p3_shell/verification_final_v5/20260909_strong_reset_m16_s128_v4.json --output experiments/R1_teacher_velocity_reset/p3_shell/new_figures
```

본 producer에 채택하지 않은 inexact forcing/회전 preconditioner의12step CPU 진단도 보고서에 범위와
결과를 적었다. 최종 수렴 실행은 원래 solver/tolerance/재료/penalty를 유지한다.

### 후속 선택에 따른 실제 GPU 수식 진단

사용자는 CPU 계산 비용을 설명한 뒤 제시한 선택지에서 **GPU 이식 우선**을 선택했다.
기존 CPU 수렴 run은 끝까지 확인하며 별도 `artifacts/runs/teacher_p3_shell_gpu/`에 새 원본을 만들었다.
GTX1080Ti/11GiB/sm61, Warp1.17.0의 float64로 같은 기하·constitutive·gradient/HVP·공력·조립을 실행한다.
Newton 제어·희소 mass/rest-K 풀이·마지막 에너지 합산은 CPU에 남는다. 관련 기록은
[`p3_shell_gpu/README.md`](../R1_teacher_velocity_reset/p3_shell_gpu/README.md)에 있다.

12개 상태의 CPU/CUDA 연산자 검사가 통과했다. Warm5회 n32 energy/force/HVP/조립/host 복사는
CPU .497249s, GPU .00845958s로58.779배였다. 전체 solver 가속 비율로 쓰지 않는다.
N16 strong-reset/n32 weak의 full trajectory 속도 상대 차이는7.17524e-13/6.62087e-12였다.
N16의 독립 GPU replay는17개 배열/4,228,422 scalar와 step diagnostics가 정확히 일치했다.

Same v3의 n16→32/sub128 strong-reset은 전체 수치 보간 속도 상한.3917943%,
n32/sub128→256은.2437471%로1%를 통과했다. 원래 거친 공간1.849529%와 원통 release 실패는 보존한다.
Fine 시각·reset 좌극한·구간 사이 변위 상한을 추가한 helper와 실제 CPU raw 검산을 manifest로 연결했다.
N32/sub256에서 제거 kinetic.179406992697J, 누적 energy integration residual−2.5314274e-8J였고,
support torque 재계산 차이는2.929e-15N·m 미만이다.
전체 수치 보간의 projected gradient상한.034156968, J하한.932852763,
mid-surface strain상한.001006379, 선형 표면 strain상한.017308061이었다.
동일4개 실제 상태의 volume/edge6/4 대10/8 구적 자체 비교는 force mass-dual 차이 최대.000959886%였다.

의도적으로 CPU device를 지정한 실행은 exit1/failed와 로그·manifest를 보존했다.
GPU source22개의 v1/v2/v3, CPU 검산/보간/helper21개와 package bootstrap40개를 별도 ZIP으로 남겼다.
Bootstrap은 수식 snapshot의 package 초기화 dependency 누락을 보완하며,
격리 복사본의37개 project import가 모두 그 복사본 안에 있음을 확인했다. 제3자 dependency는 포함하지 않는다.
관련 GPU5개/보간3개를 선행44개에 더한 고유 테스트 범위는52개다. 학습데이터 추가 생성은0개다.

기존 작은 굽힘 sample의99개 출력/376,077byte와 producer run의54개 출력/167,594,035byte는
기존 manifest와 다시 대조해 일치를 확인했다. 이전76개 sample의 적격성 범위를 승격하지 않았다.
Finest 방향/공간의 추가 결과, 격리 replay 및 CPU 최종 완료는 종료 절에 함께 기록한다.

### 단기 결과 확정과 긴 랜덤 바람 착수

Finest strong n16→32/sub256 속도 상한.4000651%, strong/weak n32/sub256 방향 상한
.0406189%/.0397466%로 통과했다. 격리 bootstrap의 full n16 replay도17개 배열/4,228,422 scalar와
step diagnostics가 정확히 같았고 별도 CPU raw 검산을 통과했다.
원래 CPU n32 strong은7255.413s에 끝났고 v5는 wind24개/비교20개를 모두 마쳤다.
같은 n32의 CPU/GPU 속도 상대 차이는2.89993e-12, 변위9.52711e-16로 통과했다.
HVP14329/14330회라는1회 차이도 기록한다. CPU26개/GPU13개 run의 metadata와
완료된 verification JSON을 각각 compact evidence에 추가했으며 원본 NPZ는 그대로 보존한다.

사용자는 다음1.5초를 기존0.25–0.5m/s knot부터 검증한 뒤 필요에 따라 확대하도록 선택했다.
`p3_shell_random/README.md`에 seed/clock, natural과18/42/66 reset, parent identity,
프레임별 저장 및 원식 검산 범위를 명시했다. 새 raw root는 `artifacts/runs/teacher_p3_shell_random/`다.
실제 CUDA n4/sub8의3 frame smoke가 완료됐고, 동일 원본의 전 상태 CPU 검산 및
CUDA+frame별 CPU3상태 대조가 각각 통과했다. Natural n8/sub128과 n16/sub128을 시작했다.
완료 원본은 실험 wrapper가 원식 검산→checkpoint42 무초기화 재시작→reset18/42/66 전진·검산 순으로
처리한다. 추가 학습데이터는0개이며 긴 구간 수렴 결과는 아래에 이어 기록한다.

### 첫1.5초 묶음과 보고서 정규화 기준

N8/sub128의 natural·reset18/42/66을 완료하고29,952 interval을 모두 원식·에너지·기하로 검산했다.
Natural639.729s, 최대 nodal 변위9.064782mm, strain 상한3.995235e-6,
reset 제거 kinetic4.196144/7.372056/16.385619µJ다. 마지막0.3초 zero ambient의 일은−1.380223µJ다.
N16/sub128 natural도847.078s에 완료·검산했다. 두 grid의 checkpoint 재시작은9개 배열과
각각369,848/1,409,474 scalar·step diagnostics가 정확히 같았다.
Source46개를 격리한 n8 checkpoint도 같은 배열·원식 검산을 통과했다.
N8의 실제 입력/자유단 변위/자유 영역 RMS 속도/kinetic4-panel PNG·PDF와 provenance를 만들고
직접 이미지로 확인했다. 초기 Matplotlib cache 권한 경고는 임시 cache로 자동 복구되어 출력에 실패하지 않았다.

Natural n8→16/sub128 수치 보간 상한은 속도.6990798%, 변위/증분.0714174%,
reset18 속도.9109530%로1% 아래다. 나머지 reset, n16/sub128→256 및 n16/sub256 방향 비교는 진행 중이다.
초기 RMS 점검의 단위 오류 해석은 선행 README의 전체1m² 평균 정의를 확인한 뒤 철회했다.
기존 전체 영역 RMS와 새 law v2의 자유0.75m² RMS를 명시적으로 구분하며 절대값 변환1/sqrt(.75)와
상대값 일치를 실제90 frame 보고서로 확인했다. 관련 sidecar는 `p3_shell/evidence/metric_units_v6.json` 및
random raw의 `verification/normalization_crosscheck_v1.json`이다.
비교 wrapper3개만 제어 중단한 v1의 failed/KeyboardInterrupt를 보존했다. 물리 전진·검산은 중단하지 않았다.
새 v2 비교 폴더에서 이어가며 원본26개 source와 solver 허용오차·1% 기준은 유지했다.
Runtime46개 ZIP v1/v2/v3와 manifest, Python3.12.3/NumPy2.4.4/SciPy1.18.1/Warp1.17.0 환경 기록을 추가했다.

### 1.5초 약한 랜덤 바람의 최종 검증 완료

사용자가 선택한0.25–0.5m/s knot, 기존 seed/방향/시각/물리 law를 유지했다.
N8/sub128, n16/sub128, n8/sub256, n16/sub256 forward/backward의5조건에서 natural과
세 독립 reset을 끝냈다. Primary20개 원본/239,616 interval/1,170 frame의 원식·에너지·고정 조건·
Bernstein 검산을 통과했다. CUDA 전 interval 검산과 별도로 CPU 상태3,510회(경계 중복 포함),
공력1,170회를 대조했다. Checkpoint5개·격리 재시작·smoke는 이 primary 합계에서 제외한다.

| 속도 수치 보간 상한 (%) | Natural | Reset18 | Reset42 | Reset66 |
|---|---:|---:|---:|---:|
| 공간8→16/sub128 | 0.699079818 | 0.910952981 | 0.848094674 | 0.720627912 |
| 공간8→16/sub256 | 0.694414320 | 0.904299033 | 0.842757344 | 0.711992708 |
| 시간128→256/n8 | 0.108164309 | 0.136702936 | 0.119953292 | 0.169299080 |
| 시간128→256/n16 | 0.096663827 | 0.119147052 | 0.096074463 | 0.148473407 |
| 방향/n16/sub256 | 0.044940356 | 0.055049300 | 0.045901233 | 0.063805441 |

20개 비교의 변위/증분/속도 모두 기존1%를 통과했다. 변위 최대.071417445%, 증분.072494201%다.
공간 차이가1%에 가까워 n8/sub256을 추가했으며, 시간 간격을 절반으로 줄인 후에도 공간 최대 속도
상한.910952981%→.904299033%로 유지됐다. 이번 약한 바람 범위에서는 n32 장기 계산을 추가하지 않았다.
허용오차·수식·재료·기준을 완화하지 않았다. 독립 비선형 공간 기준의 통과로 승계하지 않는다.

Finest n16/sub256 natural의 최대 nodal 변위9.067314262mm, 면적비 하한.99971002732,
mid-surface strain 상한3.580886766e-6, 선형 표면 strain 상한.000308814685다.
Reset18/42/66 제거 kinetic은4.196988109/7.363603640/16.355722756µJ다.
Finest natural 마지막0.3초 외력 일은−1.378832651µJ이며20개 원본의 tail 모두 음수다.
추가 구조 감쇠 없이 상대풍 drag가 순 에너지를 제거했다. 전체 힘 잔차/허용오차 최대 비는.0238135532다.
다섯 checkpoint 재시작은9개 배열과 step diagnostics가 정확히 같았다.
Sub256 n8/n16의 scalar 수는735,416/2,802,626개다.

도달한 위치·시각을 보존하고 속도만0으로 제거한 뒤 같은 미래 바람으로 이어가는 절차는
이번 약한 바람에서 수치적으로 성립했다. 약9mm 변위이므로 큰 변형 장기 coverage는 남는다.
다음 풍속 확대는 사용자 선택을 받은 뒤 시작하며, 추가 학습데이터는0개다.
개발 검증 true와 training_eligible/r1_complete false를 함께 보존한다.

`R1_teacher_velocity_reset/p3_shell_random/evidence/verification/final_summary_v1.json`은
20개 원본 manifest와 검산·20개 비교 입력·checkpoint·선택 구적의 해시를 연결한다.
`aggregate_random_v1.py`는 완결성/producer26개와239,616 interval을 요구하고 기존 요약을 덮어쓰지 않는다.
`collect_random_v1.py`로27개 완료 원본(20 primary+5 checkpoint+smoke+격리)의 작은 metadata와
검산·source/log205개 파일을 보존했다. NPZ는 ignored raw에 그대로 둔다.
`inventory_v1.json`은 각 작은 파일의 크기·SHA를 기록한다. 중단했던 비교 wrapper v1의
failed/KeyboardInterrupt는 제어 중단 기록으로 보존하며 물리 실패와 구분한다.

Runtime v4는47개 source, SHA `84a1ebb8b4b38958f242e79610b7feabb3ac34dd67c2480cfe1041e2faffebca`다.
CPU 선행 inventory v2는 원래146개를 바꾸지 않고 RMS 정의 sidecar를 더한147개다.
GPU 짧은 검사 inventory v1의100개와 이전 raw/sample은 유지했다.
최종 `figures_m16_s256_v1/random_reset.png/.pdf`는 실제 substep의 바람/자유단 변위/자유 영역 RMS 속도/
kinetic을 그렸고 이미지로 확인했다. Provenance에 원본·검산·wrapper hash와 제거 kinetic을 남겼다.
재실행 시 `MPLCONFIGDIR=code/outputs/matplotlib-cache`를 사용해 cache 경고를 피했다.

### 최종 보존 확인과 다음 결정 대기

최종 무결성 확인을 실제 실행해 통과했다. Runtime v4의47개 source와 현재 파일·ZIP member,
실험 wrapper3개와 snapshot, 문서 bundle3/20개 member의 byte 일치를 확인했다.
CPU/GPU/긴 랜덤 바람의 작은 근거 inventory147/100/205개가 각각 SHA와 크기에 맞았다.
기존 작은 굽힘 sample99개 output/376,077 byte와 원본54개 output/167,594,035 byte의
manifest 및 모든 output 해시도 이전 보존 기록과 같았다. 공유 후보 텍스트585개에서 개인 절대 경로를 발견하지 않았다.

Root는 작업 시작 전 상태를 그대로 보존했다. Code는 구현·문서, ideas는 canonical source/PDF/bundle·기록,
experiments는 실행/검산·그림·작은 근거·기록의 미커밋 변경이 있다. 네 저장소 HEAD와 기존 무관 변경은
보존했으며 diff --check를 통과했다. 이번 작업의 stage/commit/push/fetch는 모두0건이다.
원격 최신성은 조회하지 않았고 origin 비교는 로컬 remote-tracking ref에 한정한다.

다음 사용자 질문을 제시했다: 동일 방향·시각의 바람 파형을4배(목표 knot1–2m/s, 권장)로
단계적으로 키울지,10배(2.5–5m/s)로 바로 큰 변형을 확인할지 선택한다.
전자는 실패 원인 추적이 쉽지만 변형이 부족하면 추가 확대가 필요하다. 후자는 큰 변형을 적극적으로
확인하지만 수렴 실패·계산 비용 위험이 크다. 답변을 받기 전에는 새 풍속 실행을 시작하지 않는다.
약한 바람의 완료 검증과 다음 확대 선택을 분리하며 학습데이터 추가 생성은 계속 보류한다.

## 4배 바람: 사용자 승인 범위 1–3단계

사용자가 제시된 다음 순서의3번까지 진행하도록 요청했다. 권장4배 파형(목표 knot1–2m/s)의
1.5초 rest natural,0.3/0.7/1.1초 독립 velocity-reset, 원식·공간/시간/방향1% 검증을 수행한다.
4번의 후속 확대·재료/학습 적격성 채택이나 학습데이터 생성은 이번 범위에 포함하지 않는다.
기존 물리 law22개 source와 허용오차는 유지하며 저장/검산에 명시적 wind scale을 연결한다.

## 병목 진단

### 병목 진단 결과

- [진단 보고서](../R1_teacher_velocity_reset/p3_shell_random/profiling/README.md)에 실제 명령·시간·호출 수·정확한 재생·한계와 개선 우선순위를 정리했다.
- 일반 sandbox의 GPU 차단은 승인 실행으로 해결했다. GPU 실시간 커널/전송 분리는 미측정이며 CPU wall-time으로 해석한다. 다른 GPU 부하를 배제하지 못한다.
- 변경 범위는 experiments의 새 profiling 폴더와 이 기존 note다. code/ideas/root 파일, 기존 물리식·허용오차·원본·진행 중 snapshot은 수정하지 않았다.
- 진단 실행 exit 0, 세 구간의 위치·속도 차이 0, 비계측/계측 정확 일치, 원본 HVP 수 일치, profiler SHA 대조를 확인했다.
- GPU 이식 및 긴 검증 재개는 수행하지 않았다. experiments 변경은 미커밋이며 stage·commit·push·fetch하지 않았다.

## GPU 성능 개선 1–4단계

사용자는 CuPy 추가와 기존 풀이 구조 유지를 선택했다. 초기 행렬 분해 CPU 유지 가능성을 질문에서 명시했다. 기존 원본·기준 runtime은 보존하고 opt-in 별도 모듈에서 구현한다.

추가 관측: CuPy 단위 검사는 73.836초에 통과했다. n32 benchmark의 CuPy 준비/실행과 시간대가 일부 겹쳤으므로 해당 시제품 시간은 독점 성능 값이 아니다. 이전 두 backend 측정은 해당 단위검사 시작 전 완료했다.

중단 stack은 CuPy `SuperLU.solve -> cusparse.spsm -> spSM_analysis`였다. 반복 수 증가 외에도 희소 삼각 풀이의 구조 분석 비용을 함께 조사해야 한다. GPU 실제 kernel 시간 분해로 확정한 것은 아니다. `compare_backends`의 검산 인수에서 load_frame의 반환이 list임을 확인해 수정했다. 중단 run은 해당 지점에 도달하지 않았으며 독립 검산 wrapper에서 올바른 계약을 사용한다.

사용자는 CuPy 위 직접 반복 제어를 선택했다.

질문: 느린 희소 풀이만 CPU 유지(권장) 또는 GPU 친화적 전처리 추가 개발. 답 대기 중에는 기존 CPU 풀이를 유지한 HVP/graph 경로의 독립 검증을 계속한다.

### GPU 성능 개선 현재 판정

- 1번 HVP 전용 연산 및 3번 선택적 CUDA graph: CUDA 단위3건과 n32 전체frame2개(512 interval) 원식·기하·CPU 대조 검산, n32 velocity-reset4 step 기준 비교 통과.
- 2번 CuPy GPU 반복 풀이: 작은 격자 물리1건/선형풀이2건, n32 단일step 기준 비교 통과. 기본 GMRES 반복 증가→직접 조기 종료, 매번 구조 분석→고정 분석 재사용, null stream capture 실패→공유 전용 stream으로 수정했다. 그러나 실제 GPU LU가 느려 채택하지 않았다.
- n32 같은 상태 3회 중앙값: 기준0.655261초, HVP/graph0.587796초, GPU 반복 풀이13.085003초. 모두 HVP40회. 전체run 배속이나 무간섭 벤치마크로 해석하지 않는다.
- 같은 희소 풀이 분리 측정: CPU6.7–9.7ms, GPU event177–178ms. 희소 풀이CPU유지(권장)와 GPU친화적 전처리 추가개발 중 질문 답 대기.
- 4번 I/O·검산 비용 분리: 기존frame39 압축2.214초/검산12.813초. 새fast frame39계산130.168초/검산14.281초, frame79계산103.110초/검산10.825초. 검사 생략/허용치 완화 없음.
- 구현: `code/wind3dgs/teacher/p3_shell_warp_fast.py`, `_fast_kernels.py`, `p3_shell_cupy.py`, `_cupy_linalg.py`; optional extra `teacher-gpu-solver`와 관련3개 test파일. CuPy13.6.0/fastrlock0.8.3 설치, pip check 통과. SciPy/CuPy 파생 알고리즘의 license를 새 linalg 모듈에 보존했다.
- 원본과 기존기준backend는 유지, 새backend는opt-in. 긴검증 재개/학습데이터/R1전체완료는 수행·선언하지 않았다.
- [상세 성능 보고](../R1_teacher_velocity_reset/p3_shell_random/profiling/README.md)는 실패·보완·수치·명령·한계·정확한 source snapshot을 포함한다.
- code와experiments만 변경. 기존dirty변경 보존, stage·commit·push·fetch는 수행하지 않았다.
