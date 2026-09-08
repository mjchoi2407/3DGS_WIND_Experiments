# 곡률 기반 선형 판 굽힘 기준 모델 검사

## 목표와 반증 기준

주변 정점의 quadratic fit으로 곡률을 복원하는 선형 판 모델이 재료 D·ν에 맞는
방향별 굽힘 에너지를 갖는지 확인한다. 강성에 불필요한 영모드가 생기거나,
일반 변형의 에너지 오차가 세분화에 따라 줄지 않는 경우도 반증 대상으로 둔다.
계약과 고정 검사 정책은 [code 설계·구현 기록](../../code/sessions/2026-09-07_10_teacher_bending_alternatives_design.md)을 따른다.

입력은 training/evaluation 전용 synthetic flat mesh와 법선 변위다. Target runtime은 실행하지 않는다.
Dataset/object package/model/split은 `not_applicable`, seed는 `null`이다.
Membrane·질량·감쇠·공력·시간 적분·pin을 실행하지 않으며, R1 물리 수렴이나 dataset acceptance로 승계하지 않는다.

## 입력과 재현 명령

1m×1m 영역의 float64 평가 격자, n=4/8/16/32, forward/backward/checkerboard 삼각분할을 사용한다.
D=1 N·m에서 ν=0과 0.3을 각각 명시한다. 이 값은 진단용이며 실물 물성이나 native 계수와의 대응이 아니다.
원통 축 0~165도/15도 간격의 12개, twist/dome/saddle, quartic/sine으로 mesh마다 17개 변형을 계산한다.
한 실행은 204개, 두 실행은 총 408개 사례다. Quadratic 곡률은 0.02 m⁻¹, 일반 변형 진폭은 0.001m다.

Workspace root에서 실행한다. GPU는 필요 없고 상대 출력 경로는 launcher의 `code/` 기준이다.
이미 실행된 원본 경로는 덮어쓰지 않으므로 재실행할 때 새 폴더명을 사용한다.

```bash
bash code/scripts/audit_teacher_plate_reference.sh \
  --plate-rigidity-n-m 1 --poisson-ratio 0 \
  --resolutions 4 8 16 32 --width-m 1 --height-m 1 \
  --curvature-inv-m 0.02 --amplitude-m 0.001 \
  --output ../experiments/artifacts/runs/teacher_plate_reference/20260907_nu000

bash code/scripts/audit_teacher_plate_reference.sh \
  --plate-rigidity-n-m 1 --poisson-ratio 0.3 \
  --resolutions 4 8 16 32 --width-m 1 --height-m 1 \
  --curvature-inv-m 0.02 --amplitude-m 0.001 \
  --output ../experiments/artifacts/runs/teacher_plate_reference/20260907_nu030
```

## 계산·검사 계약

각 중심 삼각형에서 최대 4 ring까지 edge-adjacent face를 확장하며, 최초로 rank 6·condition ≤1e8인
patch 전체를 동일 가중 least-squares에 사용한다. 상대 SVD cutoff는 1e-12다.
중심 삼각형의 rest 면적으로 `E=0.5 Σ A (Cw)ᵀ Db (Cw)`를 적분하고 복원력은 `−Kw`다.
경계에도 실제 정점을 사용하며 면적 누락·가상 정점·penalty가 없다.
곡률 복원이 정확하다는 사실만으로 경계값 문제나 비선형 shell 해의 수렴을 주장하지 않는다.

| 개발 진단 | 고정 기준 |
| --- | --- |
| Quadratic 에너지와 곡률 | 정규화 에너지 오차 및 곡률 상대 L2 오차 ≤1e-9 |
| 원통 방향 | 각 mesh 12방향 max(E)/min(E)−1 ≤1e-9 |
| 강성·영공간 | n=4/8에서 대칭·반양정치, affine 영공간 3개; 정규화 cutoff 1e-9 |
| Quartic/sine 에너지 | 각 refinement 단계에서 상대 오차 감소, finest 오차 ≤5% |

Quadratic 에너지의 정규화 분모는 `0.5 D area κ²`다. 일반 변형의 에너지는 독립 해석 영역 적분과
비교하며, 곡률 L2 진단은 각 face 중심의 해석 Hessian과 비교한다. Float32 변위 양자화의 에너지 차이는
별도 기록하며 float32 solver 검증으로 간주하지 않는다. D와 ν는 CLI의 필수 인자다.

## 출력과 완료 gate

- 원본: 위 `artifacts/runs/teacher_plate_reference/` 두 폴더에 보존한다.
- 검토용 evidence: `evidence/nu000/`, `evidence/nu030/`에 선택한 결과 파일을 보존한다.
- `report.json`: spec·정책·mesh/operator identity·사례·방향/영모드/일반 변형 검사·semantic hash.
- `cases.csv`: 사례별 에너지·곡률 오차·float32 차이·복원력 norm.
- `environment.json`: Python/NumPy, 로컬 HEAD와 실제 실행 source의 파일 hash.
- `run.log`, `manifest.json`: 한국어 단계 로그, 실행 상태·명령 template·파일 byte/hash inventory.

계산의 `completed`와 각 모델 검사 결과를 분리한다. `teacher_eligible=false`,
`convergence_status=not_assessed`를 유지한다. 성공 종료는 학습 데이터 발행 승인이 아니다.

## 실행 결과

2026-09-07 위 두 명령을 실행했다. 각각 종료 코드 0, 204개 사례 `completed`,
총 **408개 사례**를 보존했다. 두 실행 모두 quadratic·방향·영모드·일반 변형 검사가 통과했다.
Python 3.12.3 / NumPy 2.4.4의 CPU 계산이다.

| 전체 사례의 최댓값 | ν=0 | ν=0.3 |
| --- | ---: | ---: |
| Quadratic 정규화 에너지 오차 | 6.476e-13 미만 | 8.419e-13 미만 |
| Quadratic 곡률 상대 L2 오차 | 4.892e-13 미만 | 4.892e-13 미만 |
| 원통 방향 max/min−1 | 5.709e-13 미만 | 5.518e-13 미만 |
| Float32 변위 양자화에 따른 에너지 상대 차이 | 8.662e-6 미만 | 1.125e-5 미만 |

강성 검사는 재료별로 삼각분할 3개×n=4/8의 6개 mesh에서 수행했다.
12개 검사 모두 affine `{1,u,v}`에 해당하는 영모드 3개만 관측했고, 대칭·반양정치 검사를 통과했다.
n=16/32에 대한 전체 영공간 검사나 모든 mesh에서의 안정성을 증명한 것은 아니다.

다음은 해석적인 영역 에너지 적분에 대한 **상대 오차(%)**다.
모든 행에서 n=4→8→16→32의 각 단계마다 오차가 줄었고, finest 오차는 0.77% 이내였다.

| ν | 삼각분할 | 변형 | n=4 | n=8 | n=16 | n=32 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 0 | forward | quartic | 30.7880 | 10.1544 | 2.8802 | 0.7651 |
| 0 | backward | quartic | 29.1139 | 9.2128 | 2.5598 | 0.6732 |
| 0 | checkerboard | quartic | 27.6703 | 9.2198 | 2.6498 | 0.7096 |
| 0 | forward | sine | 25.4829 | 5.8472 | 1.1247 | 0.2244 |
| 0 | backward | sine | 25.4829 | 5.8472 | 1.1247 | 0.2244 |
| 0 | checkerboard | sine | 3.3883 | 0.6794 | 0.4095 | 0.1323 |
| 0.3 | forward | quartic | 28.9098 | 9.6252 | 2.7395 | 0.7287 |
| 0.3 | backward | quartic | 26.7573 | 8.4145 | 2.3276 | 0.6105 |
| 0.3 | checkerboard | quartic | 26.0000 | 8.6448 | 2.4766 | 0.6618 |
| 0.3 | forward | sine | 27.6553 | 7.2119 | 1.5807 | 0.3535 |
| 0.3 | backward | sine | 27.6553 | 7.2119 | 1.5807 | 0.3535 |
| 0.3 | checkerboard | sine | 10.6895 | 0.5696 | 0.2361 | 0.1098 |

오차 감소는 지정 변형의 정적 에너지 비교 결과다. 경계값 문제의 변형 해나 시간 응답을 계산한 것이
아니므로 물리 수렴은 여전히 `not_assessed`다. 특정 수렴 차수를 모든 mesh에 일반화하지 않는다.
또한 [기존 면적 가중 후보](../R1_teacher_bending_mapping/README.md)의 유한 dihedral 에너지와
현재 선형 판 모델의 값이 같은 물성을 뜻하지 않는다.

## 보존·재계산과 완료 gate

원본의 다섯 파일씩을 [evidence/nu000/](evidence/nu000/)와 [evidence/nu030/](evidence/nu030/)에
그대로 복사했다. 총 740,157 bytes다. 파일별 byte/hash와 원본 연결은 [provenance.json](provenance.json)을 따른다.

- ν=0 report semantic SHA-256: `1ba40066067ef2350476f1936dfab3d58487b283823007f14c8f278d0826f1fe`
- ν=0.3 report semantic SHA-256: `dbe011ca1f775eff8a16197ee24ef68b38cb9ccaf161a3fbe95b0d6f0412896d`

두 run은 code HEAD `7010682`, experiments HEAD `61d972e`에서 실행했으며 새 구현은 미commit 상태다.
실행 source는 각 environment의 파일 hash 9개로 특정한다. Local HEAD는 원격 최신성이나
미commit 구현의 보존을 보장하지 않는다. 이번 구현·실행에서는 network fetch/download를 수행하지 않았다.

다음 명령을 workspace root에서 그대로 실행해 두 report의 전체 재계산 일치를 확인했다.
출력 파일은 생성하지 않는다.

```bash
PYTHONPATH=code .venv/bin/python - <<'PY'
import json
from pathlib import Path
from wind3dgs.evaluation.teacher_plate_reference import (
    TeacherPlateReferenceSpec, audit_teacher_plate_reference,
)
base = Path('experiments/R1_teacher_plate_reference/evidence')
for name in ('nu000', 'nu030'):
    saved = json.loads((base/name/'report.json').read_text())
    actual = audit_teacher_plate_reference(TeacherPlateReferenceSpec.from_dict(saved['spec']))
    assert actual == saved
    print(name, '전체 결과 재계산 일치')
PY
```

- [x] 두 report의 전체 재계산·semantic hash 일치
- [x] CSV의 모든 필드와 JSON, manifest의 파일 byte/hash, 실행 source 9개 확인
- [x] 원본과 선택한 evidence 10개의 byte 일치
- [x] 사전 고정한 방향·영모드·일반 변형 진단 및 관련 58개 검사 통과
- [x] 실패·중단·부분 파일·출력 폴더 재사용 거부를 코드 검사로 확인

## 실패 사례와 다음 결정

| 사례 | 관찰 | 해석·다음 결정 |
| --- | --- | --- |
| n=4/8만 사용하는 축소 검사 | 실행은 완료되지만 일반 변형의 5% 기준은 일부 실패 | 실패 상태를 보존하고 finer mesh 검사와 구분 |
| rank 부족·매우 좁은 patch | `plate_stencil` 오류 | 계수 조정이나 regularization으로 숨기지 않고 거부 |
| 현재 전체 ladder | 지정된 개발 진단 모두 통과 | 회전·막 탄성·경계조건·solver 연결을 후속 설계 |

이 기능은 선형 기준 계산과 개발 검증까지 완료했다. Newton·GPU·GUI·Registry와 학습 dataset은
이번 범위에서 변경하지 않았다.
