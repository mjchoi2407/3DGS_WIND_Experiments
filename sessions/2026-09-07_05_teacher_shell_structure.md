# 3D shell 구조 연산자 개발 진단

- 날짜: 2026-09-07
- 범위: Wind3DGS experiments-side R1 구조 연산자 검증
- 상태: 승인된 구조 기능의 네 CPU run·재계산·compact evidence 보존 완료. 일부 후보 진단 실패.
- 계약/구현: [code session11](../../code/sessions/2026-09-07_11_teacher_shell_solver_design.md)
- 재현 명령/결과/해석: [실험 README](../R1_teacher_shell_structure/README.md)

사용자가 승인한 E·ν·h 기반 3D 구조 연산자의 결과를 보존했다. 1m×1m synthetic flat mesh에서
E=1e6 Pa, ν=0/0.3, h=0.01/0.001 m, n=4/8/16/32, 세 삼각분할과 κ=0.2/0.6 m⁻¹를 썼다.
Dataset/object/model/split은 해당하지 않으며 무작위 미분 방향의 seed는 20260907이다.
질량·구속·시간 적분·감쇠·공력·GPU·GUI·Registry와 dataset 발행은 이번 범위에 없다.

## 실행과 결과

`artifacts/runs/teacher_shell_structure/20260907_{nu000_h010,nu030_h010,nu000_h001,nu030_h001}_final/`
네 폴더에 각각 300개 사례, 총 1,200개를 계산했다. 모든 명령은 종료 코드 0,
`status=completed`다. Python 3.12.3 / NumPy 2.4.4의 CPU 계산이다.

- 회전·합력/토크·정확한 미분·선형 극한·affine 에너지·rest 강성/6개 영모드 진단은 네 run 모두 통과했다.
- h=0.01은 ν=0과 0.3 각각 4/66개의 refinement ladder가 실패했다.
  양수 막 오차와 음수 굽힘 오차가 상쇄돼 n=16보다 n=32의 총오차가 크다.
  Finest 최대 오차는 각각 0.21793%, 0.21794%로 5% 조건을 충족하지만 단조 감소 조건을 실패했다.
- h=0.001은 네 조합 중 해당 두 run의 전체 개발 진단이 통과했다.
  Finest 최대 오차는 ν=0에서 4.45319%, ν=0.3에서 3.16342%다.
  Isometric 막/굽힘 비는 n=4에서 최대 185.069, n=32에서 최대 0.0447088이다.
  얇은 재질의 거친 mesh 한계는 별도 결과로 남긴다.

이 결과는 prescribed shape의 정적 에너지와 미분 검사다. 동역학 해, 공간·시간 수렴과
학습 Teacher 적격성을 뜻하지 않는다. `convergence_status=not_assessed`, `teacher_eligible=false`를 유지한다.

## 검증과 보존

- 최종 네 report를 독립 호출로 전체 재계산해 dict/semantic hash가 일치했다.
- 모든 CSV 필드와 JSON, manifest 필수 항목과 byte/hash, 실행 source 12개를 확인했다.
- `R1_teacher_shell_structure/evidence/`의 20개 파일, 2,737,903 bytes가 원본과 같다.
  원본 연결·hash·preliminary run inventory는 [provenance](../R1_teacher_shell_structure/provenance.json)에 있다.
- 구현 중 preliminary 4개 run도 그대로 보존했다. 최초 manifest의 빈 models 목록과
  C/anchor 미분 계산 표현을 정리한 뒤 최종 source의 네 run을 별도 폴더에서 실행했다.
- 새 24개와 기존 58개를 합친 82개 코드 검사가 통과했다. 실패·중단·부분 파일도 보존하는지 확인했다.
- 기존 GPU/native 217개 파일, 기존 판 source 9개와 원본/evidence 10개가 유지됐다.

## Git과 다음 단계

실행 시 로컬 HEAD는 code `7010682`, experiments `61d972e`다. 새 구현과 이 결과는 미commit이므로
실행 snapshot은 environment의 source hash로 특정한다. Fetch·다운로드·설치·push는 수행하지 않았다.
`experiments/`의 새 실험·본 session/index와 `code/`의 구현/문서는 각각 worktree에 있으며
미commit·미push다. Root와 ideas의 기존 작업에는 이번 변경이 없다.

다음은 총에너지 오차 상쇄와 얇은 재질의 mesh 요구 조건을 검토해 동역학 연결 범위·검증 기준을
정하는 것이다. 현재 실패한 정책을 바꾸거나 solver·dataset을 자동 연결하지 않았다.
