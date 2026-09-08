# 2026-09-07 02 Teacher native bending 감사

## Context

Wind3DGS experiments-side. 사용자가 다음 단계 진행을 요청해 앞서 제안된 bending mesh 의존성 감사
기능을 구현하고 기본 fixture를 실행했다. [code 기록](../../code/sessions/2026-09-07_08_teacher_bending_audit.md)을 따른다.
GPU 검사 이후의 정적 기하학 진단이며 새로운 GPU simulation이나 material 보정은 아니다.

## 실행과 출력

Workspace root에서 실행했다.

```bash
bash code/scripts/audit_teacher_bending.sh \
  --resolutions 4 8 16 32 --width-m 1 --height-m 1 \
  --amplitude-m 0.01 --edge-ke-n 10 \
  --output ../experiments/artifacts/runs/teacher_bending_audit/20260907_default_a001
```

Python 3.12.3/NumPy 2.4.4, 종료 코드 0, `status=completed`다.
원본 4개 JSON/CSV/manifest/environment는 ignored 경로에 보존하고, 동일 byte의 compact evidence를
`R1_teacher_bending_audit/evidence/`에 복사했다. [README](../R1_teacher_bending_audit/README.md)에
계산 계약·명령·수치·해석을, `provenance.json`에 로컬 Newton 기준 파일 hash를 남겼다.
Experiments README와 session index도 갱신했다.

## 관찰과 검증

- 동일 초기 변위에서 mesh 4→32 에너지는 0.000374911→0.000060531 J, 에너지 등가 강성은
  7.498→1.211 N/m로 줄었다. 마지막 에너지는 첫 mesh의 16.15%다.
- 반올림 전 field의 삼각형 법선 계산과 strip 해석식 최대 상대 차이는 1.792e-15 이하다.
- 새 모듈/packaging 총 18개 검사 통과. README의 재계산 명령을 실행하고 JSON/CSV/source/manifest hash를 대조했다.
- 기존 GPU artifact를 삭제·덮어쓰기하지 않았다. Newton 기준 source는 로컬 snapshot에서 읽었고
  fetch/download는 하지 않았다.

## 해석과 Git 상태

고정 native bending 계수에 mesh 의존성이 있음을 이 변형 패턴에서 확인했다.
전체 cloth stiffness나 동역학 수렴, 수렴 오차의 기여율을 확정하지 않는다. 상태는 `not_assessed`다.
다음 제안은 해상도에 일관된 bending 물성 매핑 설계이며, 계수·solver를 자동 변경하지 않았다.

이번 실험/code 변경은 미commit/미push다. 기존 `.gitignore`, `AGENTS.md`, 정책 문구와 다른 session은
보존했으며 root/ideas를 변경하지 않았다.
