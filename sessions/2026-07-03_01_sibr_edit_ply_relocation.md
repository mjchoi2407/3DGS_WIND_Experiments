# 2026-07-03 01 SIBR edit PLY relocation

## Context

사용자가 SuperSplat 등 GUI에서 편집한 `point_cloud_edit.ply` 파일들을 각 모델의 `iteration_sibr_safe` 폴더에 넣어두었고, SIBR viewer가 읽을 수 있도록 폴더를 만들어 이동해 달라고 요청했다.

## 변경 내용

SIBR viewer의 `--iteration edit` 규칙에 맞게 다음 파일들을 `point_cloud/iteration_edit/point_cloud.ply`로 이동했다.

- `gof_mip360_flowers_i30000_images_4_mid`
- `gof_mip360_stump_i30000_fullres_highplus2`
- `gof_mip360_garden_i30000_images_4_mid`
- `gof_mip360_treehill_i30000_images_4_mid`
- `gof_mip360_bonsai_i30000_images_2`

## 수행 명령

```bash
find experiments/M04_mesh_extraction/models -type f -name 'point_cloud_edit.ply' -print
```

각 `point_cloud_edit.ply`에 대해:

```bash
mkdir -p <model>/point_cloud/iteration_edit
mv <model>/point_cloud/iteration_sibr_safe/point_cloud_edit.ply \
  <model>/point_cloud/iteration_edit/point_cloud.ply
```

## Verification

- `find experiments/M04_mesh_extraction/models -type f -name 'point_cloud_edit.ply' -print` 결과가 비어 있음을 확인했다.
- 다음 5개 산출물이 존재함을 확인했다.
  - `experiments/M04_mesh_extraction/models/gof_mip360_flowers_i30000_images_4_mid/point_cloud/iteration_edit/point_cloud.ply`
  - `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2/point_cloud/iteration_edit/point_cloud.ply`
  - `experiments/M04_mesh_extraction/models/gof_mip360_garden_i30000_images_4_mid/point_cloud/iteration_edit/point_cloud.ply`
  - `experiments/M04_mesh_extraction/models/gof_mip360_treehill_i30000_images_4_mid/point_cloud/iteration_edit/point_cloud.ply`
  - `experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i30000_images_2/point_cloud/iteration_edit/point_cloud.ply`

## Next

SIBR 확인 시 각 scene에 대해 다음 형식으로 실행한다.

```bash
code/scripts/run_sibr_gaussian_viewer.sh <model_path> <source_path> edit
```
