# 3D shell 구조 연산자 개발 검사

## 목표와 고정 진단 기준

Flat rest mesh에서 E·ν·h로 막/굽힘 에너지, 3D 힘과 정확한 Hessian-vector product를 계산한다.
현재 법선의 미분까지 포함한 구조 계산을 독립 차분, 회전 대조, 선형 판 극한과 비교한다.
계약은 [승인된 구조 설계](../../code/sessions/2026-09-07_11_teacher_shell_solver_design.md)를 따른다.
현재 모델은 프로젝트의 discrete 에너지 후보이며 표준 비선형 shell 해법으로 검증됐다고 표시하지 않는다.

Synthetic training/evaluation 전용 flat mesh를 사용한다. Dataset/object package/model/split은
`not_applicable`이며 무작위 진단 방향의 seed는 `20260907`이다. Target runtime은 실행하지 않는다.
이번 단위는 구조의 정적 에너지·미분 검사다. 질량·위치 구속·시간 적분·감쇠·공력·GPU·GUI·
Registry/trajectory와 학습 데이터 발행은 후속 기능이다.

| 진단 | 변경하지 않는 기준 |
| --- | --- |
| Rest·rigid/변형 상태 회전 | 에너지·힘·tangent 및 합력·토크 정규화 오차 ≤1e-9 |
| 독립 차분 | 무차원 step 1e-3~1e-7에서 감소 구간 존재, 최저 오차 ≤1e-6 |
| 선형 판 tangent | Rest의 법선 tangent와 기존 K의 상대 오차 ≤1e-8 |
| Rest 강성 | n=4/8의 scaled congruence H 대칭·반양정치·영모드 6개, cutoff 1e-9 |
| Affine extension/shear | 독립 해석 에너지와 정규화 오차 ≤1e-9 |
| Graph·isometric cylinder | 단계별 총에너지 상대 오차 감소, finest 오차 ≤5% |
| 연속체 적분 | Graph Gauss 32/64점 적분 대조 상대 오차 ≤1e-9 |

길이는 `L_diag=√A_ref`, 막 에너지 단위는 `E h A_ref`, 굽힘은 `D A_ref/L_diag²`다.
힘은 각각 에너지/길이로 정규화한다. 막이 큰 얇은 재질에서 굽힘 오차를 가리지 않도록 나눈다.
회전은 x/y/z/(1,2,3)축, 30/90/170도와 translation을 사용한다. n=4/8에서 rest·graph dome·
isometric 45도 세 pose의 회전/균형 검사와 graph dome의 차분 검사를 수행한다.
Rest의 선형 힘 접근은 법선 진폭 1e-2/1e-3/1e-4에서 확인한다.
전체 변형 상태의 H는 음의 고유값을 가질 수 있고 이를 잘라내지 않는다.

## 명시적 입력과 실행

1m×1m float64 격자, n=4/8/16/32와 forward/backward/checkerboard의 세 삼각분할을 쓴다.
E=1e6 Pa, ν=0/0.3, h=0.01/0.001 m는 진단용 조합이며 실물 재료나 학습 preset이 아니다.
곡률은 κL_diag=0.2/0.6이다. Mesh마다 rest 1개, affine 2개, 곡률별 graph 7개와
isometric cylinder 4개로 25개 사례다. 한 run은 300개, 네 run은 1,200개 사례다.
Graph는 원통 방향 0/90/45/135도, twist/dome/saddle을 포함한다.
Isometric cylinder는 0/90/45/135도 방향이다.

Graph 기준은 현재 법선에 투영한 reference-coordinate 이차 미분의 연속체 영역 적분이다.
Current metric의 principal curvature와 같은 정의라고 가정하지 않는다.
Isometric cylinder의 해석 막 에너지는 0이다. P1 삼각형의 chord 근사에 따른 인공 막 에너지는
별도로 기록하며 `membrane_to_bending_ratio`로 굽힘을 지배하는지 확인한다.
Float32 현재 위치의 양자화 차이와 입력 hash도 기록한다. 이는 float32 solver 검증이 아니다.

Workspace root에서 다음을 실행한다. 상대 output은 launcher가 이동한 `code/` 기준이다.
출력 폴더는 배타적으로 생성하므로 재실행에는 새 이름을 사용한다.

```bash
bash code/scripts/audit_teacher_shell_structure.sh \
  --young-modulus-pa 1000000 --poisson-ratio 0 --thickness-m 0.01 \
  --resolutions 4 8 16 32 --curvatures-times-length 0.2 0.6 \
  --output ../experiments/artifacts/runs/teacher_shell_structure/20260907_nu000_h010_final

bash code/scripts/audit_teacher_shell_structure.sh \
  --young-modulus-pa 1000000 --poisson-ratio 0.3 --thickness-m 0.01 \
  --resolutions 4 8 16 32 --curvatures-times-length 0.2 0.6 \
  --output ../experiments/artifacts/runs/teacher_shell_structure/20260907_nu030_h010_final

bash code/scripts/audit_teacher_shell_structure.sh \
  --young-modulus-pa 1000000 --poisson-ratio 0 --thickness-m 0.001 \
  --resolutions 4 8 16 32 --curvatures-times-length 0.2 0.6 \
  --output ../experiments/artifacts/runs/teacher_shell_structure/20260907_nu000_h001_final

bash code/scripts/audit_teacher_shell_structure.sh \
  --young-modulus-pa 1000000 --poisson-ratio 0.3 --thickness-m 0.001 \
  --resolutions 4 8 16 32 --curvatures-times-length 0.2 0.6 \
  --output ../experiments/artifacts/runs/teacher_shell_structure/20260907_nu030_h001_final
```

## 보존할 결과와 완료 gate

각 원본 run의 `report.json`, `cases.csv`, `environment.json`, `run.log`, `manifest.json`을
`evidence/`의 대응 폴더에 선택 보존하고 `provenance.json`에 원본·byte/hash를 기록한다.
Report에는 재료·law·mesh/operator/input identity, component 에너지/힘·오차, 작은 mesh의
정확한 미분/회전·영공간, refinement ladder와 semantic hash를 담는다.
Environment에는 Python/NumPy, 로컬 HEAD와 미commit 실행 source의 hash를 기록한다.
Manifest는 실행 명령 template·seed·입출력 inventory와 실패/중단 상태를 보존한다.

계산 완료와 모델 진단 통과를 분리한다. 물리 진단에서 실패해도 계산은 `completed`일 수 있다.
기준을 사후 완화하지 않으며 `teacher_eligible=false`, `convergence_status=not_assessed`를 유지한다.
완료 gate는 실제 실행, 원본/evidence byte 일치, report 재계산과 CSV·manifest·source hash 대조다.

## 2026-09-07 실행 결과

최종 source로 위 네 명령을 실행했다. 각각 종료 코드 0, 300개 사례 `completed`로
총 **1,200개 사례**를 보존했다. Python 3.12.3 / NumPy 2.4.4의 CPU 계산이다.
모든 run에서 회전·독립 미분·rest 강성/선형 극한·affine 에너지·독립 적분 진단이 통과했다.
Rest 강성은 총 24개 작은 mesh에서 rigid 영모드 6개를 확인했다. 회전 대조는 864개 변환이다.
전체 mesh의 영공간이나 경계값 문제의 안정성을 증명한 것은 아니다.

| ν | h [m] | finest 총에너지 상대 오차 최댓값 | refinement 실패/전체 | 후보 진단 |
| --- | ---: | ---: | ---: | --- |
| 0 | 0.01 | 0.21793% | 4/66 | failed |
| 0.3 | 0.01 | 0.21794% | 4/66 | failed |
| 0 | 0.001 | 4.45319% | 0/66 | passed |
| 0.3 | 0.001 | 3.16342% | 0/66 | passed |

회전/균형 오차의 전체 최댓값은 9.762e-13 미만, 각 차분 ladder의 최저 오차 중 최댓값은
1.798e-8 미만, 선형 판 tangent와의 상대 차이는 6.031e-11 미만이었다.
원래 H의 작은 음수 고유값도 report에 보존한다. Scale을 분리한 cutoff 1e-9에서
rest 반양정치/영공간 검사에 통과했으며 물리 H의 고유값을 clipping하지 않았다.

### 실패: 막/굽힘 오차가 상쇄되는 총에너지

h=0.01에서 두 ν 모두 forward의 isometric 45도와 backward의 isometric 135도가
κ=0.2/0.6에서 실패했다. 합계 8개 ladder다. Finest 5% 조건은 충족하지만
n=16→32에서 총에너지 절대 오차가 증가해 사전 고정한 단계별 감소 조건에 실패한다.

예를 들어 ν=0, h=0.01, κ=0.6, forward 45도의 총에너지 오차는 다음과 같다.

| n | 총에너지 상대 오차 |
| --- | ---: |
| 4 | 6.85093% |
| 8 | 0.34055% |
| 16 | 0.0006843% |
| 32 | 0.0055359% |

연속체의 막 에너지는 0인데 discrete 막 에너지는 양수이고, 굽힘 에너지는 기준값보다 작다.
두 성분의 부호가 반대인 오차가 n=16에서 우연히 상쇄된다. 각각의 크기는 줄어도
합의 절대 오차가 매 단계 줄어든다는 보장은 없다. 이 해석은 report의 두 component 값으로 확인했다.
계산/미분 오류와 구분되는 현상이지만, 이 이유로 검사 기준이나 `failed`를 사후 변경하지 않았다.

### 얇은 재질의 인공 막 에너지

Isometric 사례 전체에서 관측한 막/굽힘 에너지 비의 최댓값이다. 비율 1은 두 에너지가 같다는 뜻이다.

| ν | h [m] | n=4의 최대 비 | n=32의 최대 비 |
| --- | ---: | ---: | ---: |
| 0 | 0.01 | 1.85069 | 0.00044709 |
| 0.3 | 0.01 | 1.31880 | 0.00031834 |
| 0 | 0.001 | 185.069 | 0.0447088 |
| 0.3 | 0.001 | 131.880 | 0.0318335 |

두께가 1/10이면 같은 기하학의 막/굽힘 비는 100배가 된다. 얇은 재질의 거친 mesh에서는
실제로 굽힘보다 인공 막 에너지가 훨씬 크다. Finest에서 지정한 기준을 통과했다는 사실만으로
거친 mesh·다른 두께·다른 변형 범위를 허용할 수 없다. 이것은 prescribed shape의 에너지 검사이며,
locking이 동역학의 변형 해에 미치는 영향이나 공간·시간 수렴은 아직 평가하지 않았다.

## 재계산·보존 확인

네 run의 다섯 파일씩, 총 **20개 / 2,737,903 bytes**를 `evidence/`에 원본과 동일하게 복사했다.
원본 연결, 파일 byte/hash, 각 report의 semantic SHA-256은 [provenance.json](provenance.json)을 따른다.
각 environment에는 로컬 code HEAD `7010682`, experiments HEAD `61d972e`와
실제 실행 source 12개의 SHA-256이 있다. 현재 구현은 미commit이므로 HEAD만으로 재현하지 않는다.
이번 구현·실행에서는 dependency 설치·다운로드·Git fetch를 수행하지 않았다.

구현 중 생성한 preliminary run 4개도 원본 폴더에 보존하고 provenance에 inventory를 기록했다.
최초 run의 manifest에 빠진 `models: []`를 보완했고, 에너지의 `C(x−x_anchor)`와
그 미분의 `C_hat`이 설계와 직접 대응하도록 계산 표현을 정리한 뒤 최종 source로 네 조합을 실행했다.
이전 run을 덮어쓰거나 실패 진단을 성공으로 바꾸지 않았다. 위 결과 표는 `_final` run만 사용한다.

Workspace root에서 다음 명령으로 네 report 전체를 재계산해 일치를 확인했다.
출력 파일을 만들지 않는다.

```bash
PYTHONPATH=code .venv/bin/python - <<'PY'
import json
from pathlib import Path
from wind3dgs.evaluation.teacher_shell_structure_audit import (
    TeacherShellStructureSpec, audit_teacher_shell_structure,
)
base = Path('experiments/R1_teacher_shell_structure/evidence')
for label in ('nu000_h010', 'nu030_h010', 'nu000_h001', 'nu030_h001'):
    saved = json.loads((base/label/'report.json').read_text())
    actual = audit_teacher_shell_structure(TeacherShellStructureSpec.from_dict(saved['spec']))
    assert actual == saved
    print(label, '전체 결과 재계산 일치')
PY
```

- [x] 전체 report 재계산·semantic hash, 모든 CSV 필드와 JSON 일치
- [x] Manifest 필수 필드·byte/hash·source 12개 대조, 원본/evidence 20개 일치
- [x] 새 24개 및 기존 58개, 관련 82개 테스트 통과
- [x] 실패·중단·부분 파일과 출력 폴더 재사용 거부 검사
- [x] 기존 GPU/native 보존 대상 217개, 판 source 9개와 원본/evidence 10개 보존

구조 연산자 구현과 진단·결과 보존은 완료했다. 후속 solver를 연결하기 전에 오차 상쇄와
얇은 재질의 mesh 요구 조건을 검토해야 한다. 학습 Teacher 채택이나 물리 수렴은 완료하지 않았다.
