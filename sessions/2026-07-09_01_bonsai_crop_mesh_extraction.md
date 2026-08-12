# 2026-07-09 01 bonsai crop mesh extraction

## 목적

bonsai에서 viewer로 crop한 작은 3DGS subset을 GOF `extract_mesh.py`에 넣어 실제 mesh extraction까지 이어지는지 확인했다.

## 입력

- 원본 GOF 모델: `experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i30000_images_2`
- crop PLY: `point_cloud/iteration_crop/point_cloud.ply`
- crop Gaussian 수: `50,257`
- 원본 reference PLY: `point_cloud/iteration_30000/point_cloud.ply`
- reference Gaussian 수: `1,076,336`

## 처리

`iteration_crop` PLY는 SIBR/viewer 호환 PLY라 `filter_3D` 필드가 빠져 있었다. GOF `extract_mesh.py`는 `GaussianModel.load_ply()`에서 `filter_3D`를 필수로 읽기 때문에, 원본 GOF PLY의 동일 XYZ Gaussian을 찾아 `filter_3D`를 복원한 임시 모델을 만들었다.

추가한 스크립트:

- `experiments/M04_mesh_extraction/scripts/restore_gof_filter3d_from_reference.py`
- `experiments/M04_mesh_extraction/scripts/run_bonsai_crop_mesh_extraction_test.sh`

임시 모델:

- `experiments/M04_mesh_extraction/models/gof_mip360_bonsai_crop_mesh_test`
- 복원 PLY: `point_cloud/iteration_30000/point_cloud.ply`
- 복원 결과: `50,257 / 50,257` vertices matched
- property 수: `62 -> 63`

## 실행 결과

첫 실행은 Codex sandbox 안에서 `torch.cuda.is_available() == False`라 GPU 사전 확인에서 중단됐다. GPU 접근 권한으로 다시 실행하자 정상 완료됐다.

- GPU: `NVIDIA GeForce GTX 1080 Ti`
- 시작: `2026-07-09 18:34:32 KST`
- 종료: `2026-07-09 18:40:05 KST`
- 로그: `experiments/M04_mesh_extraction/outputs/logs/bonsai_crop_mesh_extraction_20260709_183432.log`
- mesh: `experiments/M04_mesh_extraction/models/gof_mip360_bonsai_crop_mesh_test/test/ours_30000/fusion/mesh_binary_search_7.ply`
- mesh 크기: `22,308,894` bytes
- mesh vertex 수: `586,200`
- mesh face 수: `1,174,944`

## 메모

crop 모델 수준에서는 GOF mesh extraction 경로가 정상 작동한다. 아직 mesh 품질의 시각 검사는 하지 않았으므로, 다음 단계는 mesh viewer 또는 Blender/MeshLab에서 형태와 불필요한 floating surface를 확인하는 것이다.
