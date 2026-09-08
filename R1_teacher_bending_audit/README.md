# Teacher native bending mesh 의존성 감사

## 목표와 범위

같은 flat-rest cloth와 analytic 초기 변위를 각 mesh 해상도에 적용했을 때 native bending 에너지가
얼마나 달라지는지 확인한다. [GPU smoke의 자유감쇠 차이](../R1_teacher_smoke/README.md)를 계기로 수행하는
R1 개발 진단이다. 이번 단위는 NumPy 계산·검증·JSON/CSV 기록이며 material 보정이나 동역학 수렴 인증은 아니다.

입력은 1m×1m rectangular flag, 왼쪽 변 고정, `ΔY=A·(X/W)²`, A=0.01m, native `edge_ke=10 N`,
각 축의 mesh 구간 수 n=4/8/16/32다. Rest geometry와 requested/realized 초기 상태는 기존 Teacher API를 따른다.
질량, membrane, damping, 중력, 바람, timestep과 solver iteration은 이번 bending 에너지 계산에 들어가지 않는다.
Mesh/연결성은 training/evaluation privileged input이며 target runtime을 실행하지 않는다.
Dataset/object package/model/학습 split은 개발 geometry 감사이므로 `not_applicable`이다.

반증 기준은 평면·강체 불변성 또는 단일 hinge/strip 해석식 불일치다. 진단 코드의 수치 일치 검사와
Teacher 물리 수렴 acceptance threshold를 구분한다. 결과의 `convergence_status`는 `not_assessed`다.

## 계산 계약

Newton 1.3.0의 `evaluate_dihedral_angle_based_bending_force_hessian`에 있는
`k=edge_ke*edge_rest_length`, `dE_dtheta=k*(theta-rest_angle)`를 기준으로 다음 항을 평가한다.

```text
E_b = 0.5 * edge_ke * Σ_internal_edge(rest_edge_length * theta²)       [J]
K_energy(A) = 2 * E_b(A) / A²                                       [N/m]
```

Authored rest가 flat이므로 rest angle은 0이다. Boundary edge는 bending 항에서 제외한다.
`K_energy`는 지정한 quadratic 변형 패턴에 대한 **에너지 등가 강성**이다. 비선형 힘의 F(A)/A,
접선 강성 E''(A) 또는 전체 천의 강성으로 해석하지 않는다.
기존 float32 초기 위치와, 같은 rest 위의 반올림 전 float64 field를 각각 평가해 실현 오차를 분리한다.
기하학 계산은 모두 float64이며 Newton kernel 내부 float32 에너지 계측이 아니다.
Newton의 길이/법선 early-exit 범위에 들어가는 입력은 조용히 제외하지 않고 거부한다.

삼각형 단위 법선으로 계산한 값을 독립적인 strip 해석식과 대조한다. `x_j`는 실제 authored X 좌표이고,
`s_j=(y_{j+1}-y_j)/(x_{j+1}-x_j)`는 각 strip의 기울기다.

```text
E_analytic = 0.5 * edge_ke * H * Σ_j(atan(s_j) - atan(s_{j-1}))²
```

한 strip 안의 삼각형은 같은 평면이며, 굽힘은 X 내부 경계에서 생긴다. 그 경계를 따라 있는 Z 방향
edge 길이를 합하면 H가 되므로 이 식을 얻는다. 실제 float32 authored 좌표의 간격을 사용해
요청 치수의 반올림과 순수 기하학 오차를 섞지 않는다.

균일 간격의 작은 진폭 한계에서 이 패턴의 선형화 강성은 다음과 같다.

```text
K_linear = 4 * edge_ke * H / W² * (n-1) / n²
```

따라서 고정된 `edge_ke`에서 이 강성은 n을 늘리면 0으로 향한다. 이 식은 해당 grid와 변형 패턴의
성질을 설명하며, 임의 mesh의 물성을 보정하는 공식으로 채택한 것은 아니다.

## 재현 명령과 출력

프로젝트 root에서 실행한다. GPU와 Newton import가 필요하지 않으며 root `.venv`의 NumPy를 사용한다.
기존 출력 경로는 거부하므로 재실행할 때 새 폴더 이름을 지정한다.

```bash
bash code/scripts/audit_teacher_bending.sh \
  --resolutions 4 8 16 32 --width-m 1 --height-m 1 \
  --amplitude-m 0.01 --edge-ke-n 10 \
  --output ../experiments/artifacts/runs/teacher_bending_audit/20260907_default_a001
```

`--output`의 상대 경로는 `code/` 기준이다. JSON/CSV/환경 hash와 완료·실패 상태가 새 폴더에 남는다.

| 파일 | 역할 |
| --- | --- |
| `report.json` | 설정, geometry/초기 상태 identity, level별 에너지·강성·비율·수치 오차, report hash |
| `levels.csv` | 비교하기 쉬운 level별 수치 |
| `environment.json` | Python/NumPy, CPU NumPy 실행 표시, 이용 가능한 생산 source의 SHA-256 |
| `manifest.json` | running/completed/failed 상태와 파일 byte/SHA-256 inventory |

원본 출력은 ignored `artifacts/runs/teacher_bending_audit/20260907_default_a001/`에 보존하고,
선택한 compact report/CSV/환경/manifest는 이 폴더의 [evidence/](evidence/)에 복사해 보존했다.
재현 코드 진입점은 `code/wind3dgs/evaluation/teacher_bending_audit.py`다.
Source hash는 실행 당시 작업 파일의 snapshot이며 기존 Git HEAD가 새 코드를 포함한다고 가정하지 않는다.
기준 Newton 1.3.0 kernel/builder의 파일 hash와 실행 명령은 [provenance.json](provenance.json)에 있다.
이 파일들은 로컬 설치에서 읽었으며 이번 작업에서 fetch/download는 수행하지 않았다.

## 결과

2026-09-07 위 명령을 실행해 종료 코드 0, `status=completed`를 확인했다.
Python 3.12.3/NumPy 2.4.4에서 수행한 CPU 정적 기하학 계산이다.

| Mesh 구간 수 n | 굽힘 에너지 (J) | 에너지 등가 강성 (N/m) | 직전 해상도 대비 에너지 |
| --- | ---: | ---: | ---: |
| 4 | 0.000374910875186 | 7.498217504 | — |
| 8 | 0.000218695028197 | 4.373900564 | 0.583325 |
| 16 | 0.000117157161775 | 2.343143236 | 0.535710 |
| 32 | 0.000060531005436 | 1.210620109 | 0.516665 |

Mesh 32의 에너지는 mesh 4의 약 **16.15%**다. 같은 `edge_ke=10 N`과 같은 초기 변형을 사용해도
이 패턴의 굽힘 에너지·등가 강성이 mesh 해상도에 따라 달라진다.
Mesh 4/8 값은 앞서 보존한 GPU run 초기 위치의 기하학적 관찰과 일치한다.
해석식과 float64 기하학 에너지의 최대 상대 차이는 **1.792e-15 이하**다.
초기 위치의 float32 실현 최대 오차는 **3.353e-10m 이하**이고, 에너지 실현 상대 차이의 절댓값은
**3.799e-7 이하**다. 이번 에너지 감소는 이 작은 반올림 오차만으로 설명되지 않는다.

해당 bending 항은 timestep·solver iteration 없이 계산했다. 따라서 이 정적 에너지 차이를 설명하기 위해
먼저 material 이산화/매핑을 검토해야 한다. 전체 자유감쇠 응답에는 membrane/damping/time integration도
관여하므로 이번 결과만으로 앞선 동역학 오차의 기여율을 확정하지 않는다.

Report semantic SHA-256은 `c6f8c3cbc55fda1831e6f43496371979611302cdcf672d7b01a40f07aadea13b`다.
원본과 compact evidence의 JSON/CSV byte 및 manifest SHA-256을 대조했다.
검증은 평면·강체 운동의 에너지 0, 단일 hinge의 알려진 각도/길이, stiffness 선형성,
작은 진폭의 닫힌 식, 기존 초기 상태 수치, 입력 거부·무수정, JSON/CSV/hash, 실패 보존과 CLI를 포함한다.

다음 명령으로 compact evidence를 재계산할 수 있다. 결과 파일을 쓰거나 GPU를 실행하지 않는다.

```bash
PYTHONPATH=code .venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path
from wind3dgs.evaluation.teacher_bending_audit import TeacherBendingAuditSpec, audit_teacher_bending

root = Path('experiments/R1_teacher_bending_audit/evidence')
manifest = json.loads((root / 'manifest.json').read_text())
assert manifest['status'] == 'completed'
for name, entry in manifest['outputs'].items():
    data = (root / name).read_bytes()
    assert len(data) == entry['bytes']
    assert hashlib.sha256(data).hexdigest() == entry['sha256']
environment = json.loads((root / 'environment.json').read_text())
for name, expected in environment['sources_sha256'].items():
    assert hashlib.sha256((Path('code') / name).read_bytes()).hexdigest() == expected
saved = json.loads((root / 'report.json').read_text())
recomputed = audit_teacher_bending(TeacherBendingAuditSpec.from_dict(saved['spec']))
assert recomputed == saved
assert manifest['report_sha256'] == recomputed['report_sha256']
print('Bending 감사의 원본 hash와 재계산 결과 일치')
PY
```

## 후속 범위

이 감사는 물리 계수를 변경하지 않는다. 관찰된 bending 이산화의 mesh 의존성을 설명한 뒤,
연속체 물성에 대응하는 bending 계약/매핑의 설계가 필요하다. Solver iteration/time/mesh의 동역학 비교와
최종 acceptance threshold 동결, 학습 dataset 발행은 별도 기능 단위다.
설계 선택지와 완료 기록은 [code session](../../code/sessions/2026-09-07_08_teacher_bending_audit.md),
실험-side 이력은 [실험 session](../sessions/2026-09-07_02_teacher_bending_audit.md)을 따른다.
