# 2026-07-09 나머지 crop 모델 mesh extraction

## 작업 배경

- `bonsai` crop 모델에서 GOF mesh extraction 경로를 먼저 검증했다.
- 이어서 같은 절차로 나머지 crop 모델(`flowers`, `garden`, `treehill`, `stump`)도 geometry-only mesh로 생성했다.
- 현재 목적은 wind response 적용 후보 영역의 proxy mesh를 빠르게 확보하는 것이므로, UV texture나 vertex color texture 옵션은 켜지 않았다.

## 추가한 공통 스크립트

- `M04_mesh_extraction/scripts/run_gof_crop_mesh_extraction.sh`
  - crop PLY가 가진 Gaussian 속성에 원본 GOF PLY의 `filter_3D` 값을 복원한다.
  - `cfg_args`, `cameras.json`, `input.ply`를 새 mesh extraction용 모델 폴더로 복사한다.
  - GPU 접근 가능 여부를 확인한 뒤 GOF `extract_mesh.py`를 실행한다.
- `M04_mesh_extraction/scripts/restore_gof_filter3d_from_reference.py`
  - crop PLY와 reference PLY의 XYZ 좌표를 매칭해서 crop PLY에 `filter_3D` property를 추가한다.

## 생성 결과

| scene | output model | mesh size | vertices | faces |
| --- | --- | ---: | ---: | ---: |
| `bonsai` | `gof_mip360_bonsai_crop_mesh_test` | 21.28 MiB | 586,200 | 1,174,944 |
| `flowers` | `gof_mip360_flowers_i30000_images_4_mid_crop_mesh_test` | 3.76 MiB | 103,095 | 208,354 |
| `garden` | `gof_mip360_garden_i30000_images_4_mid_crop_mesh_test` | 0.88 MiB | 24,195 | 48,610 |
| `treehill` | `gof_mip360_treehill_i30000_images_4_mid_crop_mesh_test` | 12.90 MiB | 353,658 | 714,058 |
| `stump` | `gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_test` | 39.60 MiB | 1,089,849 | 2,188,332 |

공통 mesh 경로:

```text
M04_mesh_extraction/models/<output model>/test/ours_30000/fusion/mesh_binary_search_7.ply
```

## 로그

- `M04_mesh_extraction/outputs/logs/bonsai_crop_mesh_extraction_20260709_183432.log`
- `M04_mesh_extraction/outputs/logs/gof_crop_mesh_gof_mip360_flowers_i30000_images_4_mid_20260709_184537.log`
- `M04_mesh_extraction/outputs/logs/gof_crop_mesh_gof_mip360_garden_i30000_images_4_mid_20260709_184719.log`
- `M04_mesh_extraction/outputs/logs/gof_crop_mesh_gof_mip360_treehill_i30000_images_4_mid_20260709_184841.log`
- `M04_mesh_extraction/outputs/logs/gof_crop_mesh_gof_mip360_stump_i30000_fullres_highplus2_20260709_185014.log`

## 확인 사항

- PLY 파일 생성과 header 기준 `vertex`/`face` element 수는 정상 확인했다.
- 실제 형상 품질은 아직 외부 뷰어에서 시각적으로 확인하지 않았다.
- GOF mesh extraction은 camera 정보를 읽어 alpha integration/visibility 기반으로 mesh 후보 영역을 해석한다. 따라서 crop Gaussian만 있더라도 `cameras.json`과 원본 scene 설정이 필요하다.
- 이번 결과는 geometry-only mesh다. GOF의 `--texture_mesh` 옵션은 일반적인 UV texture image 생성이 아니라 vertex color 계열 확인용에 가깝기 때문에 이번 배치에서는 제외했다.
