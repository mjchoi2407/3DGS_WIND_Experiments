# 2026-09-08 Shell 모드·독립 시간 기준·시간 해상도 진단

## 범위

Wind3DGS R1 Teacher 개발 검증. 사용자가 [code 설계](../../code/sessions/2026-09-08_01_teacher_shell_temporal_design.md)를
“ㅇㅋ”로 승인한 기능의 CPU 실행·독립 재실행·원본 재검산과 compact evidence를 기록한다.
같은 E·ν·h·질량·고정점·내부 힘의 독립 시간 기준으로 기존 Newmark 응답을 비교했다.
Source solver·물리 법칙·수렴 정책은 그대로다. Dataset·GPU·GUI 실행은 포함하지 않았다.

## 실행

Workspace root에서 다음 두 명령을 실행했다. Launcher의 상대 경로는 `code/` 기준이다.

```bash
bash code/scripts/audit_teacher_shell_temporal.sh \
  --source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1
bash code/scripts/audit_teacher_shell_temporal.sh \
  --source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1_replay
```

Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU다. 설치·fetch·다운로드 없이 현재 환경과
로컬 source snapshot으로 실행했다. Source 18개 hash와 당시 code/experiments HEAD는 environment에 있다.
독립 reference는 각각 internal step 50,000/RHS 1,000,000회, 각 audit은 1,800초 상한으로 고정했다.

## 결과와 해석

[실험 README](../R1_teacher_shell_temporal/README.md)에 전체 조건·결과 표·판정 기준을 기록했다.
두 run 모두 source/modal/reference 검사를 통과했다. DOP853 a/b의 최대 정규화 차이는
x=1.24085e-11, v=6.93487e-9, 최대 에너지 drift는 4.88329e-10 / 8.06520e-11이었다.

Newmark full 640/1280/2560은 모두 계산됐지만 N=2560의 정규화 속도 차이는 11.7491%로
`full_response_check=failed`다. Short N=5120은 256 step 완료, 속도 차이 5.50795%다.
N=10240은 성공 4 step 뒤 5번째 `line_search_failed`로 중단됐다.
따라서 `newmark_solver_check=failed`, `short_response_check=not_assessed`다.
각 run은 7개 case 중 6개 완료·1개 실패, 새 Newmark 성공 4,740 step이다.

실패 직전 GMRES 선형 풀이는 통과했지만 비선형 잔차 1.51874e-8m/s²가 허용값 1.34886e-8보다 컸다.
전체 correction/L은 4.10444e-17, 좌표 ULP/(beta dt²)는 8.10559e-8m/s²였다.
21개 line-search trial 실패와 마지막 성공 상태를 그대로 보존했다.
절대 위치 차분의 반올림 한계를 의심할 근거이며 아직 원인 확정은 아니다.

속도 차이는 빠른 XY 모드에 집중됐다. 다음 기능 후보는 작은 dt의 위치 차분·잔차 정밀도 검토이며,
별도로 고주파의 시간 오차가 남아 있다. 에너지 보존이나 line search 통과만으로 시간 수렴을 선언하지 않는다.
이번 단위의 진단 구현과 기록 검증은 완료했으며 `teacher_eligible=false`, `convergence_status=not_assessed`다.

## 검증과 artifact

- 새 25개와 기존 106개, 총 131개 테스트 통과. 명령은 code 설계·구현 기록에 있다.
- 독립 재실행의 semantic report·모든 상태/모드 배열·runtime을 제외한 trace hash가 일치했다.
- Run마다 source 18개, inventory 453개, case 배열 72개·저장 frame 49,800개, NPZ chunk 248개 검산.
- Pin·반력·운동방정식·에너지·Newmark 갱신과 state chain, reference/full/short/원본 320 대조·CSV 재계산 일치.
- 성공 step의 최대 잔차/허용값 비 0.965412. 위치/속도 갱신식 오차 ≤2.19806e-16m / 4.33681e-19m/s.

Semantic report hash는 두 run 모두
`33ddc889a428d70a814d0e2df894a265f4469ab54c97e2260908137fd6a16579`다.
Case runtime 합은 451.723s / 455.850s이며 전체 wall time과 구분한다.

[Provenance](../R1_teacher_shell_temporal/provenance.json)에 선택 evidence 9개·749,815byte의 hash와
원본 두 run을 연결했다. 원본/재실행의 inventory는 manifest 자체를 제외한 각 453개이며,
190,075,838 / 190,075,917byte다. 전체 상태·modal basis·chunk·반복 기록은 ignored artifact로 유지했다.
회수할 때 provenance와 manifest의 상대 경로·byte/hash를 검증하고, 재실행에는 새 폴더를 사용한다.
기존 artifact는 삭제하거나 덮어쓰지 않았다.

실제로 실행한 원본 검산 보조 파일을 [evidence](../R1_teacher_shell_temporal/evidence/verify_reference.py)에 복사했다.
Workspace root에서 다음 명령으로 같은 검산을 수행할 수 있다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_temporal/evidence/verify_reference.py
```

새 결과는 `/tmp/wind3dgs_shell_temporal_verification.json`에 기록한다.
[선택 검산 결과](../R1_teacher_shell_temporal/evidence/verification.json)의 `passed`는
무결성·재현성 판정이며 Newmark 응답 통과를 뜻하지 않는다.

## 변경과 Git

`experiments/`: 새 실험 README·provenance·evidence, 본 session과 README/index를 갱신했다.
`code/`: 새 audit·launcher·test와 승인된 기존 session·README/index를 갱신했다.
두 저장소 모두 worktree의 미commit·미push 상태다. 기존 dirty 변경을 보존했고 stage하지 않았다.
Root·ideas는 이번 구현 단위에서 변경하지 않았다. 원격 fetch를 수행하지 않았으며 Git 상태는 로컬 기준이다.

기존 물리/구조·동역학 결과의 실패 상태도 그대로 유지한다. 다음 solver 수정은 별도의 기능 설계 범위다.

최종 검사에서 시작 시점 563개 기존 파일 중 이번 범위의 README/index·code session 5개만 변경됐다.
새 파일은 code 3개·experiments 12개이며 Root·ideas의 Git status는 시작 때와 같다.
문서 로컬 링크 85개, whitespace·개인 경로·credential 패턴, code/experiments `git diff --check`와
evidence 9개·원본 copy·provenance hash 검사를 통과했다.
