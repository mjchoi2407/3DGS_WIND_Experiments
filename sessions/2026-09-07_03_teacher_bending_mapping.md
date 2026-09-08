# 2026-09-07 03 Teacher bending 매핑 후보의 기본 변형 검사

## Context와 승인 범위

Wind3DGS experiments-side, 현행 R1의 정적 물성 검증 지원.
사용자가 [code 설계](../../code/sessions/2026-09-07_09_teacher_bending_mapping_design.md)의
NumPy 기본 변형 검사기 구현에 “응 진행해줘”라고 승인했다. 구현·검증 후 실제 실행을 수행하고
실험 README와 compact evidence를 보존했다. Continuum 물성 채택·Teacher 연결은 이 범위에 없다.

## 실행과 산출물

정확한 명령·입력·수치 정책·재계산 명령은
[실험 README](../R1_teacher_bending_mapping/README.md)에 있다.
1m×1m rest, native 기준 10N와 후보 B_h=1N·m, n=4/8/16/32,
두 대각선·두 곡률·7개 field의 총 112개 사례다. Nu는 지정하지 않았다.
Python 3.12.3 / NumPy 2.4.4에서 CPU 계산을 실행했다. GPU/동역학 solver와 target runtime은 실행하지 않았다.

- 원본: `artifacts/runs/teacher_bending_mapping/20260907_default/`, 기존 폴더를 덮어쓰지 않았다.
- Compact evidence: `R1_teacher_bending_mapping/evidence/`의 JSON/CSV/environment/manifest/run.log 5개.
- Report SHA-256: `d3a2e65a6ae7d9700377d398475c1e020371f246104d6a346b1c278ad24fdd02`.
- Source는 code worktree의 8개 파일 hash로 묶었다. 실행 HEAD는 code `7010682`, experiments `61d972e`이며
  이 HEAD가 새 구현을 포함한다고 주장하지 않는다. 이번에는 fetch/download를 수행하지 않았다.

## 결과와 검증

종료 코드 0, 계산 `completed`, 후보의 방향 검사 `failed`, `teacher_eligible=false`,
`convergence_status=not_assessed`를 확인했다. Mesh 32의 ±45도 에너지 비율은 forward에서
2.9375001853, backward에서 0.3404255442로 우세 방향이 뒤집혔다.
4방향 전체 max/min은 약 3.032258이며 두 방향의 비율과 구분한다.

최대 exact strip 상대 오차는 9.916e-16 미만, 작은 곡률 linearization 상대 오차는 7.000e-8 미만,
float32 실현 에너지의 상대 차이는 3.799e-7 미만이다. 현재 후보의 방향 편향은 이 오차보다 훨씬 크다.
사전 설계의 반례가 재현됐으며, 다른 mesh family/구성식의 실패나 전체 동역학 수렴 판정으로 확대하지 않는다.

신규/관련 code 검사 총 37개 통과, 원본/evidence byte와 manifest/source hash 일치,
report 재계산 일치, JSON/CSV/로그와 문서 링크를 확인했다. 이번 계산에 데이터 학습은 없다.
이전 GPU 원본과 native 감사 evidence 및 기존 사용자 파일은 보존했다.

## 저장소 상태와 후속 범위

- `experiments/`: 새 실험 폴더·evidence·이 session과 README/index 변경이 미commit/미push 상태다.
- `code/`: 새 검사기·검사·launcher와 문서가 미commit/미push 상태다. 상세 내역은 code session을 따른다.
- Root/ideas는 이번 변경 대상이 아니다. 기존 dirty 정책/연구 파일을 유지했다.

승인한 검사기 실행·기록은 완료했다. 현 후보를 Teacher에 자동 적용하지 않으며,
다음 제안은 같은 기본 변형 검사 기준으로 삼각분할/굽힘 구성식 대안을 설계하는 것이다.
