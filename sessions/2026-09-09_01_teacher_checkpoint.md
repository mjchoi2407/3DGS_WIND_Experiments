# 2026-09-09 01 Teacher 실험·샘플·공간 보완 누적 checkpoint

## 요청과 판정

Wind3DGS experiment-side. 이 채팅의 모든 구현·실험을 논문 작성용 문서와 Git에 보존한다.
[아이디어 연구 기록 TeX](../../ideas/development/r1_teacher_implementation_record.tex) /
[PDF](../../ideas/development/r1_teacher_implementation_record.pdf)에 수식·단위·경계, 실패·수정 이유,
분모·수치·재현 경로와 claim 경계를 통합했다. [Code checkpoint](../../code/sessions/2026-09-09_01_teacher_checkpoint.md)가 구현 계보를 소유한다.

**개발 sample 15개 생성·검증 완료, 본 학습 Teacher 미승인.** P3 처방 압력은 공간/방향/독립 기준의
연속 시간 상계까지 1%를 통과했지만 원래 x² 초기 변위의 속도 실패와 nonlinear wind 미검증은 남아 있다.
오래된 실험 README/session의 “미구현/미커밋/다음 작업”은 해당 작성 시점이며 최신 상태는 이 문서를 따른다.

## 전체 evidence 연결

| 단계 | 보존한 결과와 해석 | 재현 명령·config·hash·raw 위치 |
| --- | --- | --- |
| 사용자 GPU | GTX 1080 Ti smoke 12/12, temporal 11.41%·decay spatial 193.25%, 수렴 미판정 | [GPU smoke](../R1_teacher_smoke/README.md) |
| Native bending | n32/n4 energy-equivalent stiffness 비 0.161454, 해석식 일치와 mesh 의존성 | [Bending](../R1_teacher_bending_audit/README.md) |
| Area hinge | 112개 사례, ±45도 방향 에너지 비 n32에서 2.9375, isotropic 후보 실패 | [Mapping](../R1_teacher_bending_mapping/README.md) |
| Quadratic patch KL | 408개 정적 사례 통과, 이후 동적 수렴을 보장하지 못함 | [Plate](../R1_teacher_plate_reference/README.md) |
| Nonlinear shell 구조 | 1,200개, objectivity/미분 통과, 8개 total-energy ladder 실패와 thin locking | [Structure](../R1_teacher_shell_structure/README.md) |
| Dynamics | 19 rollout/2,105 step, 수치 계약 통과·velocity temporal 11.394% 실패 | [Dynamics](../R1_teacher_shell_dynamics/README.md) |
| Temporal reference | DOP853 자체 비교 통과, full 11.7491%, short step 5 line-search 실패 | [Temporal](../R1_teacher_shell_temporal/README.md) |
| Acceleration precision | 기존 실패 재현·3,457 step 완료, short 2.20620%, full 오차 유지 | [Precision](../R1_teacher_shell_precision/README.md) |
| Short refinement | 속도 2.20620→0.612308→0.154044%, 원본/replay 각각 새 3,072 step | [Short](../R1_teacher_shell_refinement/README.md) |
| Full refinement | 속도 6.059758→2.974723→0.868281%, 각각 143,360 step 및 전체 vector 검산 | [Full](../R1_teacher_shell_full_refinement/README.md) |
| Linear spatial | 각각 92,169 frame, 공간 velocity 22.7–23.2%, 방향 최대 51.5% 실패 | [Spatial](../R1_teacher_shell_linear_spatial/README.md) |
| Sample | 세 source/15 window [13,25,3], 모든 CPU replay 차이 0, development 전용 | [Dataset](../R1_teacher_sample_dataset/README.md) |
| Spatial remediation | 내부 weak-force 반례·mass/ring 진단, P2 실패, P3 pressure 통과·x² velocity 실패 유지 | [Remediation](../R1_teacher_spatial_remediation/README.md) |

원래 실패를 새 결과로 덮어쓰지 않았다. GPU fine-run RMS, 고정 A/Aω scale, sampled maximum와
continuous upper의 분모·의미 차이는 통합 연구 기록에 명시했다. 시간/공간은 동일 backend여야 한다.

## 원본과 저장 정책

- Full temporal 원본/replay: 각 inventory 2,262개, 약 2.183 GB, 560 chunk, 1,576,960 trial/iteration vector.
- Linear spatial 원본/replay: 각 inventory 1,509개, 약 266 MB. Runtime 외 1,508개 byte-identical.
- Sample raw: inventory 93개/1,150,138 byte. Dataset: manifest 포함 20개/125,293 byte.
- Remediation reference 원본/replay: 각 inventory 55개/약 45.16 MB. Runtime 외 54개 일치.
- P3 원본/replay: 각 inventory 16개/146,317,681 byte. Runtime 외 15개 일치.
- Git에는 compact report/config/environment/manifest/provenance/검산 스크립트와 선택한 PNG만 둔다.
  Ignored raw의 state/trace/vector/modal array 및 dataset NPZ는 별도 보존이 필요하다.
  Git clone이나 compact evidence만으로 전체 NPZ를 복원할 수 없다.
- 원본 report/config/source snapshot을 이번 문서 갱신에 맞춰 다시 쓰지 않는다.
  Run 시점 content hash와 checkpoint commit ID를 구분한다.

## 검증과 Git

Code에서 누적 관련 **234개 테스트 / 95.133초 / OK**를 재실행했다. 실제 GPU 검사는 과거 사용자 실행이며
이번 checkpoint에서 GPU나 대규모 full temporal 실험을 재실행하지 않았다.
Semantic report/manifest의 대표 SHA-256은 통합 연구 기록과 각 README에 보존한다.
최종 파일별 무결성·source snapshot 및 문서 링크/JSON/whitespace 검사를 수행해 stage 전 확인한다.

실제 checkpoint 검사에서 **source hash 271개 항목, compact hash 60개 항목, JSON 91개**를 확인했다.
Full temporal/linear spatial의 각 원본·replay, sample 원본, remediation 네 run의
**9개 run / inventory 7,777개 / 5,283,975,129 byte**가 byte/SHA-256과 일치했다.
저장된 15개 dataset을 다시 열어 raw/probe의 모든 label/input/work를 대조하고 batch [4,4,4,3]을 확인했다.
원본을 바꾸지 않은 읽기 검산이며 전체 simulation을 새로 실행한 것으로 세지 않는다.
CSV writer의 원래 CRLF는 content hash를 유지하기 위해 보존했다.
`git -c core.whitespace=trailing-space,space-before-tab,cr-at-eol diff --cached --check`로
정상 CRLF와 실제 trailing space를 구분해 통과했고, index에 올린 evidence byte도 worktree 원본과 대조했다.

시작 HEAD는 `61d972ece9e183786d03434f8df5360d9d3d7fdf`였다.
관련 구현은 code commit `894993c5d44533938fb1f360acd27da880d5fb71`에 보존했다.
이 commit은 실행 당시 source snapshot의 후속 보존점이며 frozen environment의 이전 HEAD 값을 변경하지 않는다.
GPU 이후 12개 R1 experiment folder와 관련 session/README를 명시 경로로 커밋한다.
기존 `.gitignore`, `AGENTS.md`, 08-13/09-01의 무관한 note와 session index 정책 문단은 제외한다.
Fetch/push는 이번에 수행하지 않으며 원격 최신성을 주장하지 않는다.

## 다음 실험

P3 nonlinear wind backend와 고차 probe/registry를 연결한 뒤 동일 물리/입력의 공간·시간·tip/work/spectrum을 검증한다.
첫 accepted 입력군의 범위는 미결정이며 기존 displaced free-decay 요구를 삭제하지 않는다.
Development sample은 accepted 데이터와 별도 identity로 유지한다.
