# 2026-09-01 02 샘플 mesh 상용 포맷 출력

## Context

`code/wind3dgs/teacher/sample_meshes.py`의 세 절차적 cloth fixture를 상용 DCC/CAD 도구에서
직접 확인할 수 있도록 개별 Wavefront OBJ로 발행했다. Attachment와 metadata 손실을 막기 위해
기존 exporter가 제공하는 NPZ sidecar도 함께 보존했다.

## Generation

`code/`에서 다음 명령을 실행했다.

```bash
PYTHONPATH=. ../.venv/bin/python -m wind3dgs.teacher.generate_sample_meshes \
  --shape all \
  --resolution 24 16 \
  --output-dir ../experiments/artifacts/packages/sample-cloth-meshes-v1_u24_v16 \
  --format both
```

출력 package:

- `artifacts/packages/sample-cloth-meshes-v1_u24_v16/rectangular_flag.obj`
- `artifacts/packages/sample-cloth-meshes-v1_u24_v16/triangular_flag.obj`
- `artifacts/packages/sample-cloth-meshes-v1_u24_v16/handkerchief.obj`
- 각 OBJ와 같은 stem의 `.npz` sidecar
- 같은 폴더의 상용 도구 import 주의사항 `README.md`

## Geometry 결과

| Shape | Vertices | Triangles | Pinned | Extent (m) |
| --- | ---: | ---: | ---: | --- |
| `rectangular_flag` | 425 | 768 | 17 | `1.2 x 0.0 x 0.75` |
| `triangular_flag` | 409 | 752 | 17 | `1.2 x 0.0 x 0.75` |
| `handkerchief` | 425 | 768 | 6 | `0.7 x 0.0 x 0.7` |

OBJ SHA-256:

- `rectangular_flag.obj`: `c5f7d7048016c536dca1b8af20cc161077fad0f32f20813c290e16549b544fd6`
- `triangular_flag.obj`: `66c8aaa394f4f9d507d5584057e8b9c359f0e4d7f20beefcd4ab031166629f57`
- `handkerchief.obj`: `597bc1998c3cea884c9e1e64896ed10bd83110b8b32d90bc73c0eefa6c049126`

## Validation

- `test_sample_meshes.py`의 7개 unit test 통과
- 독립 `trimesh` importer에서 세 OBJ를 `process=False`, `maintain_order=True`로 재로딩
- OBJ와 NPZ의 vertex/face 순서 및 개수 일치
- 모든 vertex의 UV 존재, 선언한 meter extent 일치
- 모든 triangle의 winding이 `+Y`이고 degenerate face 없음
- 세 형상이 watertight가 아닌 single open sheet인 것은 의도한 결과
- 생성물은 기존 `experiments/artifacts/` ignore 정책에 포함됨
- 네트워크 fetch나 새 dependency 설치는 수행하지 않음

## Commercial Tool Notes

OBJ는 meter, right-handed, `+Z` up, `+Y` front 계약을 사용한다. OBJ 표준에는 unit/up-axis가 없고
이 파일에는 `vn`, thickness, material/MTL이 없으므로 import 때 meter와 Z-up을 지정하고 필요하면
two-sided display 또는 normal 재계산을 사용한다. Pin group은 OBJ 주석과 NPZ에만 보존되며 일반
importer가 selection set으로 자동 복원한다고 가정하지 않는다.

이번 작업에서는 reusable code, public API와 dependency를 수정하지 않았다.
