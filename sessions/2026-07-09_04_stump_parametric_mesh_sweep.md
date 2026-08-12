# 2026-07-09 stump crop parametric mesh sweep

## 목적

- crop mesh 내부 디테일이 alpha field에서 뭉쳐 보이는 문제를 줄일 수 있는지 확인하기 위해 GOF mesh extraction 파라미터 sweep을 수행했다.
- 현재 `fusion/mesh_binary_search_7.ply` 경로는 voxel grid가 아니라 marching tetrahedra 기반이므로, voxel size 대신 다음 파라미터를 열었다.
  - `alpha_threshold`: 표면으로 잡을 alpha 등가면
  - `tetra_scale_multiplier`: Gaussian 주변 tetra sampling 범위
  - `gaussian_scale_multiplier`: proxy mesh용 Gaussian actual scale multiplier
  - `filter3d_multiplier`: GOF `filter_3D` multiplier

## 추가 스크립트

- `M04_mesh_extraction/scripts/extract_mesh_parametric.py`
  - GOF `extract_mesh.py`를 기반으로 실험용 인자를 추가했다.
  - 기존 GOF 원본 파일은 수정하지 않았다.
- `M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh`
  - crop PLY에 `filter_3D`를 복원한 뒤, variation별 output model 폴더를 분리해서 mesh를 생성한다.
  - 기본 5개 variation을 순차 실행한다.

## 실행 대상

- base model: `M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2`
- crop PLY: `point_cloud/iteration_crop/point_cloud.ply`
- reference PLY: `point_cloud/iteration_30000/point_cloud.ply`

실행 명령:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh \
  --base-model experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2
```

## 결과

| label | alpha | tetra | gaussian | filter3d | mesh size | vertices | faces |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v01_base` | 0.50 | 3.00 | 1.00 | 1.00 | 41,526,727 bytes | 1,089,849 | 2,188,332 |
| `v02_alpha60` | 0.60 | 3.00 | 1.00 | 1.00 | 43,036,646 bytes | 1,128,243 | 2,269,039 |
| `v03_balanced` | 0.70 | 2.50 | 0.90 | 1.00 | 47,220,612 bytes | 1,237,943 | 2,489,621 |
| `v04_thinner` | 0.75 | 2.00 | 0.80 | 1.00 | 51,243,278 bytes | 1,344,233 | 2,700,943 |
| `v05_aggressive` | 0.80 | 1.50 | 0.70 | 1.00 | 54,063,206 bytes | 1,419,249 | 2,848,615 |

summary:

```text
M04_mesh_extraction/outputs/mesh_param_sweeps/gof_mip360_stump_i30000_fullres_highplus2_20260709_230336.tsv
```

log:

```text
M04_mesh_extraction/outputs/logs/gof_crop_mesh_param_sweep_gof_mip360_stump_i30000_fullres_highplus2_20260709_230336.log
```

## 해석

- baseline variation은 기존 stump crop mesh와 같은 크기/vertex/face 수로 재현되었다.
- `alpha_threshold`를 올리고 Gaussian/tetra scale을 줄일수록 mesh 파일 크기와 face 수가 증가했다.
- 이는 단순히 표면이 축소되는 것이 아니라, 기존에 뭉쳐 있던 alpha field가 더 복잡한 등가면으로 분리되거나 표면 후보가 늘어나는 방향으로 작동했을 가능성이 있다.
- 실제 품질 판단은 뷰어에서 구멍, 과분할, leaf/branch 분리 정도를 비교해야 한다.

## 다음 확인

- `v03_balanced`, `v04_thinner`, `v05_aggressive`를 우선 시각 비교한다.
- `v05_aggressive`에서 구멍이 과하면 `alpha=0.75`, `gaussian=0.75~0.85` 주변을 더 촘촘히 탐색한다.
- 반대로 아직도 blob이 심하면 `alpha=0.85`, `gaussian=0.60` 쪽을 추가로 테스트한다.
