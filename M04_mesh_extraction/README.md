# M04 Mesh Extraction Data Preparation

이 실험 폴더는 GOF를 main mesh extractor로, SuGaR와 TSDF 계열을 비교군으로 쓰기 위한 테스트 데이터를 관리한다.

## 목적

첫 목표는 mesh extraction algorithm 자체를 새로 제안하는 것이 아니라, 공식 extractor를 Wind3DGS pipeline에 안정적으로 연결하는 것이다. 따라서 테스트 데이터는 다음 조건을 우선한다.

- GOF와 SuGaR가 모두 읽기 쉬운 COLMAP/3DGS 계열 포맷일 것
- 너무 큰 데이터로 시작하지 않을 것
- 나중에 논문 비교군으로 설명 가능한 공개 데이터일 것
- adapter smoke test와 실제 quality check를 분리할 수 있을 것

## 확인한 공개 데이터 후보

### 1. Official 3DGS T&T+DB COLMAP dataset

- URL: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip
- 확인 크기: 682,628,995 bytes, 약 651 MiB
- 성격: original 3D Gaussian Splatting repository에서 제공하는 Tanks and Temples + Deep Blending COLMAP data
- 장점: COLMAP 구조라 SuGaR/GOF 양쪽의 공통 입력으로 가장 무난하다.
- 단점: object-centric deformable asset은 아니고 scene reconstruction dataset이다. 첫 extractor smoke/adapter test에는 좋지만, bunny/paper plane/kite류 object deformation 평가와는 별도이다.
- 추천 용도: 첫 공개 데이터 기반 mesh extraction 연동 테스트

### 2. GOF official TNT_GOF dataset

- URL: https://huggingface.co/datasets/ZehaoYu/gaussian-opacity-fields/tree/main
- 확인 크기: 8,004,621,817 bytes, 약 7.45 GiB
- 성격: GOF README에서 안내하는 preprocessed Tanks and Temples dataset
- 장점: GOF 논문/공식 코드 기준의 main baseline dataset에 가깝다.
- 단점: 지금 단계의 adapter 개발용으로는 크다. 다운로드, 압축 해제, training/extraction 시간이 모두 무겁다.
- 추천 용도: GOF adapter가 안정화된 뒤 main quality check

### 3. Official 3DGS pre-trained models

- URL: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/pretrained/models.zip
- 확인 크기: 14,660,630,999 bytes, 약 13.65 GiB
- 장점: pre-trained Gaussian model을 바로 써서 rendering/evaluation 확인이 가능하다.
- 단점: 너무 크고, SuGaR/GOF extraction pipeline은 source scene 및 각 method의 optimization output 구조를 같이 요구하는 경우가 있다.
- 추천 용도: 지금은 보류

### 4. NeRF Synthetic / Blender-style data

- 성격: synthetic object dataset
- 장점: object-centric shape test에 유리하다.
- 단점: GOF는 Blender synthetic loader를 갖고 있지만, SuGaR README는 full pipeline의 기본 입력을 COLMAP dataset으로 설명하고 synthetic dataset support를 TODO로 둔다. 공통 baseline으로 쓰기에는 흔들린다.
- 추천 용도: GOF-only quick test 또는 별도 object-centric 추가 실험

## 권장 진행 순서

1. Local synthetic COLMAP-style smoke fixture를 만든다.
   - 목적: adapter path, camera parsing, output path, mesh file discovery가 정상인지 빠르게 확인한다.
   - 데이터 크기: 매우 작게 유지한다.
   - 품질 평가는 하지 않는다.

2. Official 3DGS T&T+DB COLMAP dataset을 받는다.
   - 목적: 실제 공개 COLMAP scene에서 GOF/SuGaR adapter가 돌아가는지 확인한다.
   - 다운로드 크기: 약 651 MiB
   - 다운로드 스크립트: `scripts/download_official_3dgs_tandt_db.sh`

3. GOF official TNT_GOF dataset은 후순위로 둔다.
   - 목적: GOF main quality comparison
   - 다운로드 크기: 약 8 GB

## 실행 기록

### 2026-06-24 GOF playroom 3DGS smoke

- Dataset: `raw/db/playroom`
- Input images: 225
- Command:

```bash
cd external/gaussian-opacity-fields
MPLCONFIGDIR=/tmp/mpl-gof ../miniforge3/bin/conda run -n gof python train.py \
  -s ../../experiments/M04_mesh_extraction/raw/db/playroom \
  -m ../../experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8 \
  -r 8 \
  --iterations 1000 \
  --test_iterations 1000 \
  --save_iterations 1000 \
  --data_device cpu
```

- Result: training completed.
- Train metric at iteration 1000: `L1 0.03587201423943043`, `PSNR 25.656330490112307`.
- Output 3DGS PLY: `models/gof_playroom_i1000_r8/point_cloud/iteration_1000/point_cloud.ply`
- Output vertex count: `123060`
- Output size: about `30 MiB`

### 2026-06-24 GOF playroom render preview

- Command:

```bash
cd external/gaussian-opacity-fields
MPLCONFIGDIR=/tmp/mpl-gof ../miniforge3/bin/conda run -n gof python render.py \
  -m ../../experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8 \
  --iteration 1000 \
  --skip_test
```

- Render output:
  - `models/gof_playroom_i1000_r8/train/ours_1000/test_preds_8`
  - `models/gof_playroom_i1000_r8/train/ours_1000/gt_8`
- Rendered images: `225` prediction images and `225` GT images.
- Preview command:

```bash
external/miniforge3/bin/conda run -n gof python \
  experiments/M04_mesh_extraction/scripts/make_render_preview.py \
  --render-root experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/train/ours_1000 \
  --output-dir experiments/M04_mesh_extraction/outputs/gof_playroom_i1000_r8_preview \
  --scale-label 8
```

- Preview sheet:
  - `outputs/gof_playroom_i1000_r8_preview/contact_sheet_gt_vs_pred.jpg`
- Visual note: at `1000` iterations the reconstruction is recognizable, but some views are still blurry or incomplete. This is acceptable for smoke testing; quality-oriented mesh extraction should use a longer run.

### 2026-06-25 SIBR viewer-safe PLY

The `iteration_1000` GOF smoke model contains a small number of very large or far-away Gaussian outliers. They are acceptable for a quick training smoke test, but they can dominate SIBR's interactive viewer on GTX 1080 Ti / WSLg fallback mode.

The GOF PLY also contains one method-specific property, `filter_3D`, after the standard 3DGS fields. GraphDeco/SIBR's Gaussian viewer reads the binary vertex payload as a fixed `RichPoint` struct rather than by property name, so the extra property shifts every record after the first one. For SIBR, use the `iteration_sibr_safe` copy below.

Viewer-safe filtering command:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m04_mesh_extraction.filter_viewer_safe_ply \
  --input experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/point_cloud/iteration_1000/point_cloud.ply \
  --output experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/point_cloud/iteration_viewer_safe/point_cloud.ply \
  --max-radius 12 \
  --max-scale 1.0
```

Filtering result:

- Input vertices: `123060`
- Output vertices: `122612`
- Dropped by radius: `389`
- Dropped by scale: `59`

Run SIBR with the filtered copy:

```bash
SIBR_DEFAULT_ITERATION=viewer_safe code/scripts/run_sibr_gaussian_viewer.sh
```

SIBR-compatible filtering command:

```bash
PYTHONPATH=code .venv/bin/python -m wind3dgs.m04_mesh_extraction.filter_viewer_safe_ply \
  --input experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/point_cloud/iteration_1000/point_cloud.ply \
  --output experiments/M04_mesh_extraction/models/gof_playroom_i1000_r8/point_cloud/iteration_sibr_safe/point_cloud.ply \
  --max-radius 12 \
  --max-scale 1.0 \
  --sibr-compatible
```

SIBR-compatible result:

- Input vertices: `123060`
- Output vertices: `122612`
- Dropped by radius: `389`
- Dropped by scale: `59`
- Input property count: `63`
- Output property count: `62`
- Dropped property: `filter_3D`
- Output stride: `248` bytes, matching `62` float values

Run SIBR with the compatible copy:

```bash
SIBR_DEFAULT_ITERATION=sibr_safe code/scripts/run_sibr_gaussian_viewer.sh
```

The original `iteration_1000` PLY remains unchanged and should be used for method-side evaluation unless a viewer-specific diagnostic explicitly needs a filtered or converted copy.

### 2026-06-26 CO3D kite category download

CO3D category links were provided in `/mnt/h/co3d_links.txt`. For a first object-centric aerodynamic asset, `kite` was chosen over `plant` and `teddybear` because it is much smaller and still has a thin, wind-relevant surface.

Checked category archive sizes:

- `kite.zip`: `12,453,472,106` bytes, about `11.60 GiB`
- `plant.zip`: about `49.12 GiB`
- `teddybear.zip`: about `48.55 GiB`
- `umbrella.zip`: about `39.06 GiB`

Download command:

```bash
wget -c --progress=dot:giga \
  -O experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip \
  https://dl.fbaipublicfiles.com/co3d/kite.zip
```

Integrity and extraction commands:

```bash
unzip -tq experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip
unzip -q -n \
  experiments/M04_mesh_extraction/downloads/co3d/category_zips/kite.zip \
  -d experiments/M04_mesh_extraction/raw/co3d
```

Result:

- Archive: `downloads/co3d/category_zips/kite.zip`, `12G`
- Extracted category: `raw/co3d/kite`, `12G`
- Zip integrity check: no errors detected
- CO3D category metadata: `sequence_annotations.jgz`, `frame_annotations.jgz`, `set_lists.json`
- Sequence count: `163`
- Frame annotations: `16,358`
- Extracted file count under `raw/co3d/kite`: `65,600`
- Candidate preview sheet: `outputs/co3d_kite_candidate_preview/kite_top_sequence_contact_sheet.jpg`

Recommended first mesh-extraction candidate:

- Sequence: `414_56867_109917`
- Path: `raw/co3d/kite/414_56867_109917`
- Size: `168M`
- Files: `409`
- Frames: `102`
- Valid mask frames: `102 / 102`
- CO3D point cloud: `840,238` points
- CO3D point-cloud quality score: `-0.535`
- CO3D viewpoint quality score: `1.499`
- Visual note: wide triangular kite, the most directly relevant shape for a wind/aerodynamics asset among the inspected candidates.

Backup candidates:

- `402_52522_102936`: `82M`, `102` valid-mask frames, `338,343` point-cloud points, good metadata score.
- `398_50636_99350`: `55M`, `102` valid-mask frames, `641,671` point-cloud points, clean square kite texture.

### 2026-06-27 CO3D object category batch extraction

The remaining object-centric CO3D categories were downloaded, extracted under `raw/co3d`, checked through their CO3D metadata files, and the verified zip archives were removed.

Final extracted categories:

| Category | Size | Sequences | Frame annotations | Files |
| --- | ---: | ---: | ---: | ---: |
| `broccoli` | `28G` | `405` | `39,148` | `157,001` |
| `frisbee` | `8.6G` | `133` | `12,911` | `51,782` |
| `kite` | `12G` | `163` | `16,358` | `65,600` |
| `plant` | `51G` | `574` | `56,936` | `228,323` |
| `teddybear` | `50G` | `749` | `72,865` | `292,215` |
| `toyplane` | `18G` | `250` | `24,446` | `98,039` |
| `umbrella` | `40G` | `503` | `48,372` | `193,997` |

Final raw root:

```text
experiments/M04_mesh_extraction/raw/co3d
```

Final raw size:

```text
205G
```

`umbrella.zip` required an interrupted range-download recovery. The completed archive was verified with:

```bash
unzip -tq experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip
```

and returned:

```text
No errors detected in compressed data
```

After successful extraction and metadata checks, category zip archives were deleted. Only small download/recovery logs remain under:

```text
experiments/M04_mesh_extraction/downloads/co3d/category_zips
```

### 2026-06-27 Mip-NeRF 360 H-drive extraction

The Mip-NeRF 360 archives were kept on the H drive and extracted directly into the WSL experiment raw folder to avoid copying unnecessary zip archives into the WSL VHDX.

Source archives:

- `/mnt/h/360_v2.zip`: selected scenes only, `bonsai`, `garden`, `stump`
- `/mnt/h/360_extra_scenes.zip`: intended scenes, `flowers`, `treehill`

Extraction commands used:

```bash
ionice -c2 -n7 nice -n 10 unzip -q -n /mnt/h/360_v2.zip \
  'bonsai/*' 'garden/*' 'stump/*' \
  -d experiments/M04_mesh_extraction/raw/mipnerf360

ionice -c2 -n7 nice -n 10 unzip -q -n /mnt/h/360_extra_scenes.zip \
  'treehill/*' \
  -d experiments/M04_mesh_extraction/raw/mipnerf360

ionice -c2 -n7 nice -n 10 unzip -q -n /mnt/h/360_extra_scenes.zip \
  'flowers/*' \
  -d experiments/M04_mesh_extraction/raw/mipnerf360
```

Usable extracted scenes:

| Scene | Source archive | Size | Files | Status |
| --- | --- | ---: | ---: | --- |
| `bonsai` | `360_v2.zip` | `1.4G` | `1,172` | ready |
| `garden` | `360_v2.zip` | `2.9G` | `744` | ready |
| `stump` | `360_v2.zip` | `1.5G` | `504` | ready |
| `flowers` | `360_extra_scenes.zip` | `2.5G` | `696` | ready |
| `treehill` | `360_extra_scenes.zip` | `1.8G` | `568` | ready |

The first copy of `/mnt/h/360_extra_scenes.zip` was corrupt or incomplete around the `flowers` entries. After redownloading the archive, `flowers/*` passed:

```bash
unzip -tq /mnt/h/360_extra_scenes.zip 'flowers/*'
```

and returned:

```text
No errors detected in /mnt/h/360_extra_scenes.zip for the 703 files tested.
```

The previous partial extraction was preserved but quarantined as:

```text
experiments/M04_mesh_extraction/raw/mipnerf360/flowers_incomplete_from_corrupt_zip
```

It contains only `80` files and should not be used for training or mesh extraction. Use `raw/mipnerf360/flowers` for the valid scene.

### 2026-06-27 GOF Mip-NeRF 360 smoke 3DGS script

Use this wrapper to train a small GOF/3DGS smoke model from the ready Mip-NeRF 360 scenes:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
```

Default behavior:

- Scene: `bonsai`
- Images: `images_4`
- Iterations: `1000`
- Output model: `models/gof_mip360_bonsai_i1000_images_4`
- Log: `outputs/logs/gof_mip360_bonsai_i1000_images_4_<timestamp>.log`

Recommended first check:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --dry-run
```

Then run the actual smoke training:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
```

To smoke test another ready scene:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene flowers \
  --iterations 1000 \
  --images images_4
```

The script checks CUDA availability in the user terminal, prints progress to the terminal, and mirrors the output to a log file. It does not overwrite an existing non-empty model directory unless `--backup-existing` is passed.

Optional one-pass checks:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --run-render --run-mesh
```

If the smoke training already finished and the `point_cloud.ply` exists, run post steps without retraining:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --skip-train-if-ready \
  --run-render \
  --run-mesh
```

For higher-quality runs after smoke succeeds, use the same script with more iterations and the official image factor, for example `bonsai` with `--images images_2 --iterations 30000`.

### 2026-06-27 GOF Mip-NeRF 360 전체 스모크 batch 스크립트

Mip-NeRF 360 준비 scene 전체를 순차로 스모크 테스트하려면 다음 wrapper를 사용한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
```

기본 실행 대상:

```text
bonsai flowers garden stump treehill
```

기본값:

- 각 scene `1000` iterations
- 모든 scene `images_4`
- GPU `0`
- scene별 port는 `6009`부터 1씩 증가
- batch 로그: `outputs/logs/gof_mip360_all_i1000_images_4_<timestamp>.log`

먼저 전체 실행 계획을 확인한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --dry-run
```

문제가 없으면 실제 전체 스모크 학습을 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
```

실행 중 터미널과 batch 로그에 다음 정보가 계속 표시된다.

- 전체 진행률: `[현재/전체]`, percent, scene 이름
- scene별 시작/종료 시각
- scene별 command
- scene별 exit status
- scene별 소요 시간과 batch 누적 시간
- 현재까지 성공/실패 요약

일부 scene이 실패해도 나머지를 계속 확인하려면 다음 옵션을 사용한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --continue-on-error
```

학습 후 render와 mesh extraction까지 한 번에 확인하려면 다음처럼 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh \
  --run-render \
  --run-mesh
```

이미 학습된 point cloud가 있을 때 후처리만 이어서 확인하려면 다음처럼 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh \
  --skip-train-if-ready \
  --run-render \
  --run-mesh
```

특정 scene만 묶어서 돌릴 수도 있다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh \
  --scenes "bonsai flowers"
```

스모크가 성공한 뒤 품질용 run으로 넘어갈 때는 `--iterations 30000`과 `--official-factors`를 사용한다. `--official-factors`는 현재 보유 scene 기준 `bonsai=images_2`, 나머지 scene은 `images_4`를 사용한다.

## 로컬 데이터 배치 규칙

대용량 데이터는 git에 넣지 않는다. 이 폴더의 `.gitignore`는 다음 경로를 무시한다.

- `downloads/`: 원본 archive
- `raw/`: 압축 해제된 공개 dataset
- `models/`: external extractor training/checkpoint output
- `outputs/`: extracted mesh, logs, reports

## 참고한 공식 문서

- 3DGS official repository: https://github.com/graphdeco-inria/gaussian-splatting
- GOF official repository: https://github.com/autonomousvision/gaussian-opacity-fields
- GOF HuggingFace dataset: https://huggingface.co/datasets/ZehaoYu/gaussian-opacity-fields/tree/main
- SuGaR official repository: https://github.com/Anttwo/SuGaR
