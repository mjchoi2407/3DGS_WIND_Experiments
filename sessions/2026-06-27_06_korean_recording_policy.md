# 2026-06-27 한국어 기록 원칙 반영

## 배경

사용자가 앞으로 프로젝트의 모든 기록을 한국어로 남기도록 요청했다. 대상에는 session 기록, README, 실험 보고서, 작업 로그, 스크립트가 직접 남기는 설명성 로그가 포함된다.

## 변경 내용

- `../AGENTS.md`에 프로젝트 전체 기록 언어 규칙을 추가했다.
- `AGENTS.md`에 실험-side 기록 언어 규칙을 추가했다.
- 새로 작성하거나 갱신하는 실험-side 기록은 한국어를 기본 언어로 사용하도록 명시했다.
- `M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh`의 도움말과 사람이 읽는 상태 로그를 한국어로 바꿨다.

## 예외

- 명령어, 파일 경로, 코드 식별자, API 이름, 논문/데이터셋/방법론의 공식 영문 명칭은 원문을 유지한다.
- GOF 학습 로그, CUDA/PyTorch 에러, 외부 라이브러리 로그처럼 원문 보존이 필요한 출력은 번역하지 않아도 된다.
- 사람이 덧붙이는 요약과 해석은 한국어로 작성한다.

## 검증

다음 검증을 수행했다.

```bash
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --help
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --dry-run --run-render --run-mesh
```

`--help`와 `--dry-run` 출력에서 스크립트 도움말과 상태 메시지가 한국어로 표시되는 것을 확인했다. 실제 GPU 학습은 실행하지 않았다.

## 비고

기존 영문 기록은 별도 요청이 없는 한 소급 번역하지 않는다.
