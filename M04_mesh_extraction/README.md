# M04 Mesh Extraction Data Preparation

> **현재 역할:** 이 폴더는 GOF/SuGaR/TSDF를 이용한 offline GS reconstruction·mesh preprocessing과 mesh-based baseline을 보존한다. 추출 mesh는 training privilege, oracle/debug 자료 또는 비교군으로만 사용하며 target runtime의 필수 입력이 아니다.

이 실험 폴더는 GOF를 기존 주 extractor로, SuGaR와 TSDF 계열을 비교군으로 사용했던 테스트 데이터와 실행 기록을 관리한다.

## 목적

기존 목표는 mesh extraction algorithm 자체를 새로 제안하는 것이 아니라 공식 extractor를 이전 Wind3DGS pipeline에 안정적으로 연결하는 것이었다. 현재 방법에서는 이 자산을 offline teacher/preprocessing 및 mesh baseline으로 제한한다.

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

## 기존 M04 진행 순서와 기록

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

Mesh extraction을 목표로 할 때는 Gaussian이 지나치게 조밀하지 않아도 된다. `flowers`, `stump`처럼 densification 이후 VRAM 사용량이 11GB 근처까지 올라가는 scene은 먼저 `images_8`과 저밀도 preset을 같이 사용한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene stump \
  --iterations 30000 \
  --images images_8 \
  --model-dir experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_images_8_mesh \
  --checkpoint-every 1000 \
  --resume \
  --density-preset mesh
```

`--density-preset mesh`는 densification을 `2500` iteration까지만 수행하고, gradient threshold와 densification interval을 보수적으로 잡으며, opacity reset을 사실상 끈다. 그래도 VRAM이 계속 빠듯하면 다음처럼 더 강한 preset을 쓴다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene stump \
  --iterations 30000 \
  --images images_8 \
  --model-dir experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_images_8_safe \
  --checkpoint-every 1000 \
  --resume \
  --density-preset safe
```

Density preset 요약:

- `default`: GOF 기본 densification 설정을 유지한다.
- `mesh`: mesh extraction용 저밀도 우선 설정이다. 품질과 VRAM 사이의 첫 시도값으로 쓴다.
- `safe`: VRAM이 계속 부족하거나 학습 속도가 급격히 느려질 때 쓴다.
- `off`: densification을 끈다. geometry가 너무 빈약할 수 있으므로 최후 확인용으로만 쓴다.

`--model-dir`를 직접 지정하지 않으면 `mesh`, `safe`, `off` preset은 기본 model 디렉터리 끝에 각각 `_mesh`, `_safe`, `_off` suffix를 붙인다. 기존 default density checkpoint를 실수로 이어받지 않기 위한 분리 규칙이다.

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

### 2026-06-27 GOF Mip-NeRF 360 연구용 고퀄 batch 스크립트

연구용 고퀄 3DGS 모델을 한 번에 생성하려면 다음 wrapper를 사용한다. 기본값은 전체 준비 scene, `30000` iterations, 공식 factor, SIBR viewer 호환 변환, render까지 실행한다. Mesh extraction은 3DGS 품질을 확인한 뒤 별도 스크립트로 진행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh --dry-run
```

계획이 맞으면 실제 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh
```

기본 실행 대상과 출력 model 경로:

```text
bonsai   -> models/gof_mip360_bonsai_i30000_images_2
flowers  -> models/gof_mip360_flowers_i30000_images_4
garden   -> models/gof_mip360_garden_i30000_images_4
stump    -> models/gof_mip360_stump_i30000_images_4
treehill -> models/gof_mip360_treehill_i30000_images_4
```

각 scene마다 생성되는 주요 산출물:

- 3DGS point cloud: `point_cloud/iteration_30000/point_cloud.ply`
- checkpoint: `chkpnt5000.pth`, `chkpnt10000.pth`, ... `chkpnt25000.pth`
- SIBR 호환 viewer copy: `point_cloud/iteration_sibr_safe/point_cloud.ply`
- SIBR 변환 요약: `point_cloud/iteration_sibr_safe/point_cloud.viewer_safe_summary.json`
- render 결과: `train/ours_30000/`
- batch 로그: `outputs/logs/gof_mip360_quality_i30000_official_factors_<timestamp>.log`

기본값은 `5000` iteration마다 GOF checkpoint를 저장하고, 기존 model 디렉터리에 checkpoint가 있으면 최신 checkpoint에서 자동 재개한다. 학습 중단 뒤 같은 명령을 다시 실행하면 scene별 최신 `chkpnt*.pth`를 찾아 이어서 학습한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --scenes "bonsai"
```

checkpoint 간격을 바꾸려면 다음처럼 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --checkpoint-every 2500
```

checkpoint 저장과 자동 재개를 끄려면 다음 옵션을 사용한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --no-checkpoint \
  --no-resume
```

주의: checkpoint 옵션을 추가하기 전에 이미 생성된 model 디렉터리에 `chkpnt*.pth`가 없다면 그 run은 중간부터 이어갈 수 없다. 이 경우 새 model 디렉터리를 지정하거나 `--backup-existing`으로 기존 디렉터리를 백업하고 처음부터 다시 시작한다.

### 2026-06-27 GOF density 제어 옵션

GOF 학습 중 VRAM 사용량은 iteration 수 자체가 메모리에 누적되어 증가한다기보다, densification으로 Gaussian 수가 늘어나면서 증가한다. `flowers`, `stump`, `garden`처럼 입력 사진 수와 sparse point가 많은 scene은 해상도를 `images_8`로 낮춰도 densification 이후 GPU memory가 계속 커질 수 있다.

Mesh extraction용 3DGS를 먼저 확보하는 단계에서는 다음 순서로 낮은 밀도 run을 권장한다.

1. `images_8 + --density-preset mesh`
2. 그래도 VRAM이 10.5GB 이상에서 오래 머물면 `images_8 + --density-preset safe`
3. geometry 연결성만 빠르게 확인하려면 짧은 iteration에서 `--density-preset off`

전체 batch에서도 같은 옵션을 전달할 수 있다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --scenes "stump treehill flowers garden" \
  --images images_8 \
  --density-preset mesh \
  --checkpoint-every 1000 \
  --no-render
```

이 경우 출력 model은 예를 들어 `models/gof_mip360_stump_i30000_images_8_mesh`처럼 density preset suffix가 붙은 별도 디렉터리에 생성된다.

Scene별로 더 보수적인 값을 직접 지정할 수도 있다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene flowers \
  --iterations 30000 \
  --images images_8 \
  --model-dir experiments/M04_mesh_extraction/models/gof_mip360_flowers_i30000_images_8_custom_density \
  --checkpoint-every 1000 \
  --resume \
  --densify-until-iter 1200 \
  --densify-grad-threshold 0.002 \
  --densification-interval 400 \
  --opacity-reset-interval 100000
```

`stump images_4_mid`에서 확인한 중간 density 설정을 `flowers`, `garden`, `treehill`에 반복 적용하려면 다음 임시 wrapper를 사용한다. 기본값은 `images_4`, `30000` iterations, `checkpoint-every=1000`, `densify_until_iter=5000`, `densify_grad_threshold=0.001`, `densification_interval=200`, `opacity_reset_interval=100000`이며, 학습 후 `iteration_sibr_safe` 변환까지 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh --dry-run
```

계획이 맞으면 실제 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh
```

기본 출력 model:

```text
flowers  -> models/gof_mip360_flowers_i30000_images_4_mid
garden   -> models/gof_mip360_garden_i30000_images_4_mid
treehill -> models/gof_mip360_treehill_i30000_images_4_mid
```

특정 scene만 실행하려면 다음처럼 지정한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh \
  --scenes "flowers treehill"
```

특정 scene만 먼저 고퀄로 확인하려면 다음처럼 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --scenes "bonsai"
```

학습과 SIBR 변환만 먼저 끝내고 render를 나중에 돌리고 싶다면 다음처럼 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --scenes "bonsai flowers" \
  --no-render
```

이미 point cloud가 있는 scene에서 변환과 후처리만 이어서 실행하려면 다음 옵션을 붙인다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --skip-train-if-ready
```

일부 scene이 실패해도 나머지 scene을 계속 진행하려면 다음 옵션을 사용한다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --continue-on-error
```

현재 render 단계는 predicted image와 GT image를 저장하는 단계이며, PSNR/SSIM/LPIPS 같은 수치 평가나 contact sheet 생성은 이 wrapper 안에서 자동 실행하지 않는다. 자동 비교가 필요하면 별도 render-evaluation 스크립트로 분리한다.

### 2026-07-10 stump crop 수정 후 r05 주변 mesh sweep

`stump` crop PLY에서 노이즈를 수정한 뒤에는 기존 variation model 폴더를 재사용하지 말고, filter_3D 복원부터 다시 수행한 새 sweep을 만든다. 다음 wrapper는 `iteration_crop`과 `iteration_edit` 중 더 최근 `point_cloud.ply`를 자동 선택해 `filter_3D`를 다시 붙이고, 이전 시각 확인에서 가장 좋았던 `r05_alpha_only` 주변 6개 후보를 생성한다.

실행 전 경로와 파라미터만 확인한다.

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh --dry-run
```

계획이 맞으면 실제 실행한다.

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh
```

기본 후보:

```text
r05a_a081_g070 alpha=0.81 tetra=1.50 gaussian=0.70
r05b_a082_g065 alpha=0.82 tetra=1.50 gaussian=0.65
r05c_a082_g070 alpha=0.82 tetra=1.50 gaussian=0.70
r05d_a082_g075 alpha=0.82 tetra=1.50 gaussian=0.75
r05e_a083_g070 alpha=0.83 tetra=1.50 gaussian=0.70
r05f_a084_g070 alpha=0.84 tetra=1.50 gaussian=0.70
```

실행이 끝나면 결과 `.ply`, `summary.tsv`, `manifest.tsv`, `sweep.log`, `README.md`가 다음 형식의 폴더에 모인다.

```text
experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_r05_local_<timestamp>
```

자동 선택 대신 특정 crop PLY를 쓰고 싶으면 다음처럼 지정한다.

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh \
  --crop-iteration edit
```

GOF의 `filter_mesh` 효과만 비교할 때는 `r05c`, `r05e`, `r05f` 세 후보로 축소한 샘플 preset을 사용한다. 이 preset은 `--filter-mesh`를 자동 적용하며 기존 결과와 구분되는 새 폴더에 모은다.

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh \
  --preset r05-filter-sample
```

수집 폴더 형식:

```text
experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_r05_filtermesh_sample_<timestamp>
```

2026-07-10 실제 생성 결과:

```text
experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_r05_filtermesh_sample_20260710_221227
```

세 후보 모두 정상 완료됐으며, 같은 파라미터의 무필터 결과보다 vertex는 약 `5.8~6.1%`, face는 약 `11.0~11.5%` 감소했다. 시각 비교는 `fm_r05c`, `fm_r05e`, `fm_r05f` 순서로 진행한다.

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
