# Teacher bending 매핑 후보의 기본 변형 검사

## 목표와 반증 기준

Rest 면적 가중치로 bending 계수를 환산한 후보가 해상도와 굽힘 방향에 따라 어떤 에너지를
갖는지 확인한다. [기존 native 감사](../R1_teacher_bending_audit/README.md)와
[매핑 설계](../../code/sessions/2026-09-07_09_teacher_bending_mapping_design.md)를 잇는 R1 개발 진단이다.
기하학 에너지가 독립 strip 해석식과 다르면 계산 실패이며, 계산이 정확해도 cylinder 방향별
에너지 차이가 크면 후보의 방향 검사는 실패다. 두 상태를 분리해 저장한다.

입력은 training/evaluation 전용 synthetic rest mesh와 지정 quadratic 변위다. Target runtime은
실행하지 않는다. Dataset/object package/model/split/seed는 synthetic 정적 감사이므로
`not_applicable` 또는 `null`이다. Pin 조건·membrane·damping·바람·시간 적분을 실행하지 않는다.
초기 변위를 실제 자유감쇠 run에 사용하거나 이 결과를 학습 데이터로 발행하지 않는다.

## 입력과 계산 계약

- 1m×1m flat rest, n=4/8/16/32, 현재 대각선 `forward`와 반대 대각선 `backward`.
- 후보 `B_h=1 N·m`, 별도 native 기준 `edge_ke=10 N`. 두 값은 진단용이며 동등한 재료라는 뜻이 아니다.
- 곡률 κ=2⁻¹² 및 0.02 m⁻¹. `w=0.5*κ*(a*u²+2*b*u*v+c*v²)`, `u=X-Xmin`, `v=Zmax-Z` [m].
- Field는 u/v/±45도 cylinder, twist, dome, saddle의 7개다. 총 2×4×2×7=112개 사례다.
- Poisson ratio는 지정하지 않는다. ν가 필요한 twist/dome/saddle의 연속체 대조 값은 `null`이다.

후보의 식은 `k_e=B_h*l_e/(A_left+A_right)`,
`E=0.5*B_h*sum_internal(l_e²/(A_left+A_right)*theta_e²)`다.
길이와 면적은 실제 authored rest에서 계산하고 boundary 계수는 0이다.
`B_h`는 아직 등방성 plate rigidity로 검증되지 않았다.

계산은 float64다. Float32 위치만 적용한 에너지, float32 계수만 적용한 에너지와 두 실현을 함께
적용한 에너지를 분리한다. 이는 Newton kernel의 float32 실행을 재현했다는 뜻이 아니다.
법선으로 계산한 기하학 에너지를 실제 Cartesian 축 간격의 독립 slope 식과 대조한다.

실행 전에 코드에 고정한 개발 진단 정책은 다음과 같다. R1의 물리 acceptance 기준이 아니다.

| 대상 | 정책 |
| --- | --- |
| u/v strip의 정확한 atan 에너지 | 상대 오차 ≤ 1e-10 |
| 작은 곡률의 선형화 에너지 | 상대 오차 ≤ 1e-5 |
| float32 위치·계수의 합성 실현 에너지 | 상대 차이 절댓값 ≤ 5e-5 |
| 첫 곡률의 크기 | abs(κ)×max(W,H) ≤ 2⁻¹⁰ |
| Cylinder 방향 진단 | 각 대각선에서 finest 작은 곡률의 4방향 max(E)/min(E)−1 ≤ 0.05 |

유한 mesh의 방향 진단이 통과하더라도 continuum 수렴을 증명하지 않는다.
현재 후보의 방향 반례는 사전 설계에서 이미 예측했고, 이를 재현하는 것이 이번 검사의 목표다.

## 재현 명령

Workspace root에서 실행한다. GPU가 필요 없으며 출력은 새로운 폴더여야 한다.
상대 출력 경로는 launcher가 사용하는 `code/` 기준이다.

```bash
bash code/scripts/audit_teacher_bending_mapping.sh \
  --hinge-bending-scale-n-m 1 --edge-ke-n 10 \
  --resolutions 4 8 16 32 --width-m 1 --height-m 1 \
  --curvatures-inv-m 0.000244140625 0.02 \
  --output ../experiments/artifacts/runs/teacher_bending_mapping/20260907_default
```

실행기: `code/scripts/audit_teacher_bending_mapping.sh`.
재사용 구현: `code/wind3dgs/evaluation/teacher_bending_mapping.py`.
새 dependency는 없고 root `.venv` 또는 `WIND3DGS_PYTHON`을 사용한다.

| 파일 | 용도 |
| --- | --- |
| report.json | Spec/정책, rest·map·위치 identity, 112개 사례와 방향 검사, semantic hash |
| cases.csv | 사례별 에너지·정밀도·해석식 오차 |
| environment.json | Python/NumPy와 실행 source hash, 로컬 Git HEAD 관찰 |
| run.log | 한글 진행·계산 완료·방향 판정 로그 |
| manifest.json | 실행 명령 template/spec hash, 상태·실패 코드와 파일 byte/hash inventory |

환경에 남은 HEAD는 실행 source가 전부 commit됐다는 뜻이 아니다. 실제 source snapshot은 파일
SHA-256을 따른다. Manifest의 `<new-output-dir>`는 덮어쓰기를 방지하기 위한 재실행 placeholder이며
위 명령이 이번 원본의 정확한 경로를 기록한다. 원본은 ignored `artifacts/runs/`에 보존한다.

## 실행 결과

2026-09-07 위 명령을 실행해 종료 코드 0, **112개 사례 `completed`**를 확인했다.
Python 3.12.3 / NumPy 2.4.4의 CPU 계산이며, 후보의 `isotropic_cylinder_check=failed`,
`teacher_eligible=false`, `convergence_status=not_assessed`다.

다음은 현재 `forward` 대각선, 작은 곡률에서 `0.5*B_h*area*kappa²`로 나눈 에너지다.

| n | u 방향 | v 방향 | +45도 | -45도 |
| --- | ---: | ---: | ---: | ---: |
| 4 | 0.750000 | 0.750000 | 1.000000 | 2.500000 |
| 8 | 0.875000 | 0.875000 | 1.000000 | 2.750000 |
| 16 | 0.937500 | 0.937500 | 1.000000 | 2.875000 |
| 32 | 0.968750 | 0.968750 | 1.000000 | 2.937500 |

Mesh 32의 `E_minus45/E_plus45`는 **2.9375001853**이다. 대각선을 반대로 한 `backward`에서는
**0.3404255442**로 우세 방향이 바뀐다. 4방향 전체의 `max/min` 비율은 약 3.032258이므로
±45도 두 방향의 비율과 구분한다. 현재 격자에서 u/v 방향의 유한한 에너지 극한이 보이는 것만으로
등방성 bending 물성을 인정할 수 없다.

| 수치 진단 | 전체 사례의 최댓값 |
| --- | ---: |
| 후보 exact strip 상대 오차 | 9.296e-16 미만 |
| Native exact strip 상대 오차 | 9.916e-16 미만 |
| 작은 곡률 linearization 상대 오차, native/후보 | 7.000e-8 미만 |
| Float32 합성 실현 에너지 상대 차이 절댓값 | 3.799e-7 미만 |
| Float32 위치 실현 오차 | 8.941e-10 m 미만 |

방향 편향은 이 수치 오차보다 훨씬 크다. 이는 사전 설계의 기하학 반례를 실제 배열에서
재현한 결과이며, 전체 동역학/감쇠 오차의 기여율이나 다른 shell 모델의 실패를 의미하지 않는다.

선택한 5개 파일은 [evidence/](evidence/)에 원본 그대로 복사해 보존했다. 총 크기는 273,757 bytes다.
Report semantic SHA-256은 `d3a2e65a6ae7d9700377d398475c1e020371f246104d6a346b1c278ad24fdd02`다.
Code HEAD `7010682`, experiments HEAD `61d972e`에서 실행했으며 새 검사기/결과는 미commit 상태다.
Network fetch/download를 수행하지 않았고, 환경의 Git 값은 로컬 snapshot이다.

다음 명령으로 evidence 파일과 source hash, report 재계산을 대조할 수 있다.
새 출력이나 GPU simulation을 실행하지 않는다.

```bash
PYTHONPATH=code .venv/bin/python -B - <<'PY'
import hashlib
import json
from pathlib import Path
from wind3dgs.evaluation.teacher_bending_mapping import (
    TeacherBendingMappingSpec, audit_teacher_bending_mapping,
)

root = Path('experiments/R1_teacher_bending_mapping/evidence')
manifest = json.loads((root / 'manifest.json').read_text())
assert manifest['status'] == 'completed'
assert manifest['isotropic_cylinder_check'] == 'failed'
for name, entry in manifest['outputs'].items():
    data = (root / name).read_bytes()
    assert len(data) == entry['bytes']
    assert hashlib.sha256(data).hexdigest() == entry['sha256']
environment = json.loads((root / 'environment.json').read_text())
for name, expected in environment['sources_sha256'].items():
    assert hashlib.sha256((Path('code') / name).read_bytes()).hexdigest() == expected
saved = json.loads((root / 'report.json').read_text())
recomputed = audit_teacher_bending_mapping(TeacherBendingMappingSpec.from_dict(saved['spec']))
assert saved == recomputed
assert manifest['report_sha256'] == recomputed['report_sha256']
print('Bending 매핑 감사의 파일/source hash와 재계산 결과 일치')
PY
```

## 완료와 후속 범위

새 단위 검사 19개, 기존 native 감사 14개와 packaging/import 4개를 합쳐 **37개 통과**를 확인했다.
기하학 불변성·단일 hinge·독립 해석식, 비이진 크기·음의 곡률·명시적 ν,
float32 오차 분리, 입력 거부, hash/실패 prefix/CLI와 optional dependency 분리를 검증했다.
원본과 evidence byte/hash 및 source를 확인하고 위 재계산 명령도 실행했다.

이번 완료는 검사기의 계산·기록 기능에 대한 것이다. 후보의 방향 검사 실패를 보존하며 Teacher의
물성·solver·기존 GPU 결과를 바꾸지 않았다. 이후에는 같은 기본 변형 검사로 대조할 수 있는
삼각분할/굽힘 구성식 대안의 설계가 필요하다.

[Code 구현 기록](../../code/sessions/2026-09-07_09_teacher_bending_mapping_design.md)과
[실험 session](../sessions/2026-09-07_03_teacher_bending_mapping.md)에 인수인계를 남겼다.
