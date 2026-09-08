# 곡률 기반 선형 판 기준 모델 검증

- 범위: Wind3DGS experiments-side, R1 개발 진단
- 상태: 두 CPU 실행·재계산·compact evidence 보존 완료
- 계약과 구현: [code 기록](../../code/sessions/2026-09-07_10_teacher_bending_alternatives_design.md)
- 정확한 명령·수치·원본 연결: [실험 README](../R1_teacher_plate_reference/README.md)

## 실행과 결과

사용자가 승인한 선형 판 기준 모델 기능에 따라 D=1 N·m, ν=0/0.3 두 run을 실행했다.
각 run은 세 삼각분할, mesh 4/8/16/32, 17개 변형으로 204개 사례다.
`artifacts/runs/teacher_plate_reference/20260907_nu000/`과 `20260907_nu030/`에서
총 408개 사례, 종료 코드 0과 `completed`를 확인했다.

Quadratic·방향·영모드·일반 변형 진단은 모두 통과했다.
원통 방향 에너지 max/min−1은 최대 5.709e-13 미만, 일반 변형의 최종 에너지 상대 오차는
0.76514% 미만이다. 작은 mesh 12개 강성 검사에서 affine 영모드 3개만 관측했다.
이는 정적 기준 모델 검증이며 `teacher_eligible=false`, `convergence_status=not_assessed`다.

## 보존과 검증

두 원본에서 report/CSV/environment/log/manifest를 선택해
`R1_teacher_plate_reference/evidence/nu000/`, `evidence/nu030/`에 그대로 복사했다.
10개 파일은 740,157 bytes이며 원본 파일과 byte 단위로 일치한다.
`provenance.json`에 파일별 hash와 원본 상대 경로를 보존했다.

각 report를 저장된 spec으로 전체 재계산해 일치를 확인했고, semantic hash,
CSV의 모든 필드와 JSON, manifest의 파일 byte/hash, source 9개를 검증했다.
Code의 관련 58개 검사도 통과했다. Source·이전 GPU/bending 결과는 보존했다.
Python 3.12.3 / NumPy 2.4.4의 CPU 계산이며 dependency 설치나 GPU 실행은 없었다.

## 저장소와 다음 단계

- `experiments/`: 새 실험 README·provenance·compact evidence와 본 session, index 변경이 worktree에 있다.
  미commit·미push이며 기존 dirty 변경과 이전 원본은 보존했다.
- `code/`: 승인된 기준 계산·검사·launcher·문서를 구현했다. 상세 검증은 code 기록을 따른다.
- Root/ideas는 이번 작업에서 변경하지 않았다. Network fetch/download를 수행하지 않았다.

다음은 회전·막 탄성·경계조건을 포함한 backend/적분기 연결 설계다.
현재 결과를 실제 동역학 Teacher의 공간·시간 수렴 근거로 승계하지 않는다.
