# 2026-09-08 Shell Newmark 가속도 변수 정밀도 회귀

## 범위와 승인

Wind3DGS R1 Teacher 개발 검증. 사용자가 [code 설계](../../code/sessions/2026-09-08_02_teacher_shell_precision_design.md)의
가속도 변수 경로·실패 step 재현·최대 3,457 step 대조를 “진행해줘”로 승인했다.
기존 solver·물리 법칙·수렴 정책과 이전 실험의 실패 상태는 유지했다.
실험 조건·사전 판정·결과 표는 [실험 README](../R1_teacher_shell_precision/README.md)에 있다.

## 실제 실행

Workspace root 기준 명령이다. Launcher 안의 상대 경로는 `code/` 기준이다.

```bash
bash code/scripts/audit_teacher_shell_precision.sh \
  --dynamics-source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --temporal-source-run ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1
bash code/scripts/audit_teacher_shell_precision.sh \
  --dynamics-source-run ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1 \
  --temporal-source-run ../experiments/artifacts/runs/teacher_shell_temporal/20260908_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_precision/20260908_reference_v1_replay
```

Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU다. 각 audit 900초 상한 내 종료했다.
새 DOP853 계산은 하지 않았고 기존 source 검증 후 a/b 자체 대조를 재검산해 reference_b를 재사용했다.

## 결과

- 두 run 모두 legacy step 5의 `line_search_failed`가 저장된 기록과 일치했다.
- 같은 시작 state의 새 step 5와 독립 short/full 후보 5개 case, 총 3,457 step을 완료했다.
- Source/reference/legacy replay/solver/precision regression/prefix 검사가 통과했다.
- Short N=2560/5120/10240의 정규화 속도 차이는 6.91220 / 5.50795 / 2.20620%다.
  Finest가 1%보다 커 `short_response_check=failed`다.
- Full N=2560은 11.7491%로 `full_reference_error_check=failed`다.
  후보의 full ladder는 실행하지 않아 `full_response_check=not_assessed`다.

새 step 5의 잔차는 3.12274e-10m/s²로 기존 bound 1.34886e-8보다 작다.
같은 저장 위치에서 기존 위치 역산식을 쓰면 잔차가 2.45592e-8로 허용값을 초과한다.
새 경로의 위치/속도 갱신은 독립 roundoff 검사도 통과했다.
새 경로와 기존 경로의 full N=2560 정규화 속도 차이는 3.31711e-9로 매우 작다.
정밀도 때문에 중단되던 계산을 완료할 수 있게 됐지만 고주파 시간 오차는 별개로 남았다.
`teacher_eligible=false`, `convergence_status=not_assessed`를 유지한다.

## 검산·evidence

새 24개 + 기존 131개, 총 155개 검사가 최종 source에서 통과했다.
두 실제 run의 semantic report·상태/modal/반복 배열과 runtime을 제외한 trace hash가 일치했다.
Run마다 source 21개, inventory 198개, 저장 frame 3,463개, 반복 벡터 55,702개,
trial 벡터 묶음 5,982개, NPZ chunk 108개를 검사했다.
힘·반력·에너지·갱신·state chain, iterate/trial의 실제 변화·merit/Armijo와 모든 대조 수치·CSV를 재계산했다.
최대 잔차/bound 비 0.999232, 위치/속도 갱신 결함/bound 비 0.0290237이었다.

Semantic report hash:
`093fd1b440f61b7e604167abd25a902c1f0170071d018df3348245067c397be6`.
Case runtime 합은 120.953s / 121.730s이며 source 검산·case 최종 파일 저장 등은 제외한 값이다.

[Provenance](../R1_teacher_shell_precision/provenance.json)에 evidence 9개·430,310byte와 원본을 연결했다.
전체 inventory는 원본/재실행 각각 198개·142,905,367 / 142,905,457byte(manifest 제외)다.
Ignored 원본은 삭제·덮어쓰지 않았으며 상대 경로·byte/hash로 회수한다.
재검산 명령은 workspace root 기준이다.

```bash
PYTHONPATH=code .venv/bin/python experiments/R1_teacher_shell_precision/evidence/verify_reference.py
```

출력은 `/tmp/wind3dgs_shell_precision_verification.json`이다. 실제 실행한 보조 파일과
[검산 결과](../R1_teacher_shell_precision/evidence/verification.json)를 그대로 evidence에 복사했다.

## 변경·다음 판단·Git

`experiments/`에는 새 실험 README·provenance·evidence·본 session과 README/index를 반영했다.
`code/`에는 새 solver/audit/test/launcher 5개와 기존 승인 session·README/index를 반영했다.
두 저장소 모두 미commit·미push 상태이며 기존 dirty 변경을 stage하거나 정리하지 않았다.
Root·ideas는 이번 기능에서 변경하지 않았다. 설치·다운로드·외부 조회·fetch 없이 로컬 source로 실행했다.

다음 판단은 가속도 변수 경로의 남은 시간 해상도 문제를 검증할 범위다.
이번에 full ladder 확대·새 integrator·감쇠·공력·GPU/GUI·Registry 기본 채택·학습 dataset 발행은 하지 않았다.

최종 검사에서 기존 579개 파일 중 해당 README/index·code session 5개만 변경됐고,
code 새 파일 5개·experiment 기록 12개를 추가했다. Root·ideas의 Git status는 시작 때와 같다.
로컬 링크 86개·공백·개인 경로·credential 패턴, code/experiments `git diff --check`,
evidence 9개·source 21개 hash와 기존 temporal 원본 두 run inventory 906개 보존 검사가 통과했다.
