# 2026-08-13 02 실험 저장소 작업 지침 보강

## 목적

새 TD 실험에서 version-controlled evidence와 대형 working artifact를 분리하고, 읽기 전용 작업·Git·세션 기록의 안전한 경계를 명시한다.

## 결정

- 읽기 전용 확인·감사에는 session note를 만들지 않고, 같은 logical task는 기존 note를 계속 갱신한다.
- 새 TD heavy artifact는 ignored `artifacts/` hierarchy에 두고 compact evidence만 실험 디렉터리에서 추적한다.
- ignored artifact는 삭제 가능한 파일이 아니며 provenance, derivative, hash, retrieval rule과 승인을 확인한다.
- 기존 M01--M04 tracked output은 보존할 legacy 예외이며 새 TD 완료 근거로 승계하지 않는다.
- dirty worktree의 기존 변경을 사용자 소유로 취급하고 정확한 경로만 stage하며, destructive Git과 암묵적 push를 금지한다.
- 연구 문서는 현재 task에 관련된 section만 점진적으로 읽는다.
- `.env`와 `.env.*`는 제외하고 secret-free `.env.example`만 허용한다.

## 변경 파일

- `AGENTS.md`
- `.gitignore`
- `README.md`
- `sessions/README.md`
- `sessions/2026-08-13_02_workflow_policy_update.md`

## 검증

- Markdown과 ignore 규칙의 diff를 확인했다.
- `artifacts/`, `.env`, `.env.local`은 제외되고 `.env.example`과 compact report 경로는 추적 가능한 것을 확인했다.
- `git diff --check`가 통과했다.

## 다음 단계

새 TD 실험을 추가할 때 versioned experiment README와 ignored working run 사이의 manifest/hash 연결을 함께 검증한다.
