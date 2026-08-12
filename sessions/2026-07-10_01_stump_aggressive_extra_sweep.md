# 2026-07-10 stump crop mesh aggressive-extra sweep

## 배경

기존 `v05_aggressive` mesh가 가장 디테일이 살아 있었지만 아직 부족하다는 판단이 있었다. 따라서 같은 `stump` crop 모델을 대상으로 더 얇고 촘촘한 파라미터 후보 5개를 추가 생성했다.

## 변경 사항

- `experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh`에 `--preset aggressive-extra` 옵션을 추가했다.
- 기존 `default` preset은 유지하고, 추가 preset은 `v06`부터 `v10`까지 더 높은 `alpha_threshold`, 더 작은 `tetra_scale_multiplier`, 더 작은 `gaussian_scale_multiplier`를 사용한다.

## 실행 명령

```bash
experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh \
  --base-model experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2 \
  --preset aggressive-extra \
  --output-prefix experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_extra
```

## 검증

- `bash -n experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh`: 통과
- `/home/choi/conda-envs/wind3dgs/gof/bin/python -m py_compile experiments/M04_mesh_extraction/scripts/extract_mesh_parametric.py`: 통과
- CUDA 사전 확인: `NVIDIA GeForce GTX 1080 Ti`, CUDA 사용 가능
- 전체 sweep 종료 상태: `status: OK`

## 결과

요약 파일:

- `experiments/M04_mesh_extraction/outputs/mesh_param_sweeps/gof_mip360_stump_i30000_fullres_highplus2_20260710_001527.tsv`

로그 파일:

- `experiments/M04_mesh_extraction/outputs/logs/gof_crop_mesh_param_sweep_gof_mip360_stump_i30000_fullres_highplus2_20260710_001527.log`

| label | alpha | tetra | gaussian | mesh bytes | vertices | faces |
|---|---:|---:|---:|---:|---:|---:|
| v05_aggressive | 0.80 | 1.50 | 0.70 | 54,063,206 | 1,419,249 | 2,848,615 |
| v06_a082_g065 | 0.82 | 1.40 | 0.65 | 53,130,062 | 1,396,737 | 2,797,615 |
| v07_a085_g060 | 0.85 | 1.30 | 0.60 | 53,291,629 | 1,401,739 | 2,805,426 |
| v08_a088_g055 | 0.88 | 1.20 | 0.55 | 54,386,374 | 1,427,438 | 2,865,915 |
| v09_a090_g050 | 0.90 | 1.10 | 0.50 | 55,753,367 | 1,458,374 | 2,942,512 |
| v10_a092_g045 | 0.92 | 1.00 | 0.45 | 56,255,941 | 1,467,935 | 2,972,346 |

## 해석

- `v06`과 `v07`은 `v05`보다 파라미터는 더 공격적이지만 최종 mesh 크기와 vertex 수는 오히려 약간 낮다. 표면 선택이 얇아지면서 일부 blob이 줄었을 가능성이 있다.
- `v08`부터는 `v05`보다 vertex/face 수가 증가한다. 디테일 개선을 기대할 수 있는 1차 후보는 `v08`, `v09`, `v10`이다.
- `v10`은 이번 sweep에서 가장 촘촘하지만, 과도하게 얇아진 부분의 구멍이나 끊김이 생길 수 있으므로 시각 확인이 필요하다.

## 다음 확인

- Blender 또는 mesh viewer에서 `v08`, `v09`, `v10`을 우선 비교한다.
- 디테일은 `v10`이 가장 좋지만 연결성이 나쁘면 `v09`, 구멍이 많으면 `v08`을 후보로 둔다.
- 그래도 디테일이 부족하면 현재 mesh extractor 파라미터보다 crop 범위, 원본 3DGS 학습 품질, 또는 후처리 remeshing/decimation 전략을 같이 봐야 한다.

## 후속 판단

사용자 시각 확인 결과, `aggressive-extra` 후보들은 기존 `v05_aggressive`보다 전반 품질이 좋지 않았다. vertex/face 수가 늘어도 품질이 좋아지지 않았으므로, 문제는 단순 밀도 부족이 아니라 높은 `alpha_threshold`와 낮은 `gaussian_scale_multiplier`가 필요한 표면을 과하게 깎아내는 방향으로 작용한 것으로 본다.

따라서 `aggressive-extra`를 더 밀지 않고, `v05`를 기준으로 한 번에 한 축만 조정하는 `v05-refine` preset을 추가했다.

추가된 후보:

| label | alpha | tetra | gaussian | 의도 |
|---|---:|---:|---:|---|
| r01_v05_dense | 0.80 | 1.25 | 0.70 | `v05`에서 tetra만 소폭 촘촘하게 한다. |
| r02_v05_dense_plus | 0.80 | 1.00 | 0.70 | `v05`에서 tetra만 강하게 줄인다. |
| r03_soft_dense | 0.78 | 1.25 | 0.75 | 표면 소실을 줄이고 tetra를 소폭 촘촘하게 한다. |
| r04_soft_dense_plus | 0.78 | 1.00 | 0.75 | 표면을 덜 깎으면서 tetra를 강하게 줄인다. |
| r05_alpha_only | 0.82 | 1.50 | 0.70 | `v05`에서 alpha만 살짝 올려 원인을 분리한다. |

Dry-run:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh \
  --base-model experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2 \
  --preset v05-refine \
  --output-prefix experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine \
  --dry-run
```

검증:

- `bash -n experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh`: 통과
- `v05-refine` dry-run: 통과

## v05-refine 실제 실행 결과

사용자 요청에 따라 `v05-refine` sweep을 실제 실행했고, 결과 `.ply` 파일을 한 폴더로 모았다.

실행 명령:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh \
  --base-model experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2 \
  --preset v05-refine \
  --output-prefix experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine
```

실행 시간:

- 시작: 2026-07-10 02:26:38 KST
- 종료: 2026-07-10 03:05:39 KST
- 상태: `OK`

요약 파일:

- `experiments/M04_mesh_extraction/outputs/mesh_param_sweeps/gof_mip360_stump_i30000_fullres_highplus2_20260710_022638.tsv`

로그 파일:

- `experiments/M04_mesh_extraction/outputs/logs/gof_crop_mesh_param_sweep_gof_mip360_stump_i30000_fullres_highplus2_20260710_022638.log`

수집 폴더:

- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_v05_refine_20260710_022638`

수집 폴더에는 5개 `.ply`, `summary.tsv`, `sweep.log`, `README.md`를 함께 넣었다.

| label | alpha | tetra | gaussian | mesh bytes | vertices | faces |
|---|---:|---:|---:|---:|---:|---:|
| r01_v05_dense | 0.80 | 1.25 | 0.70 | 55,731,830 | 1,460,177 | 2,939,191 |
| r02_v05_dense_plus | 0.80 | 1.00 | 0.70 | 54,969,694 | 1,435,306 | 2,903,523 |
| r03_soft_dense | 0.78 | 1.25 | 0.75 | 55,919,709 | 1,463,944 | 2,950,166 |
| r04_soft_dense_plus | 0.78 | 1.00 | 0.75 | 53,883,667 | 1,406,648 | 2,846,436 |
| r05_alpha_only | 0.82 | 1.50 | 0.70 | 55,306,747 | 1,450,059 | 2,915,832 |

검증:

- 5개 변형 모두 `mesh_binary_search_7.ply` 생성 완료
- `summary.tsv`에서 5개 변형 모두 `OK`
- 수집 폴더 총 용량: 약 264MB
- PLY 헤더에서 `element vertex`, `element face` 확인 완료

해석:

- `r03_soft_dense`가 이번 `v05-refine` 후보 중 vertex/face 수가 가장 많다. 표면을 덜 깎는 방향이라 이전 `aggressive-extra`보다 우선 확인할 만하다.
- `r04_soft_dense_plus`는 tetra를 더 촘촘하게 했지만 결과 크기와 face 수가 가장 낮다. tetra 해상도만 올린다고 디테일이 단조롭게 증가하지 않음을 보여준다.
- `r05_alpha_only`는 alpha만 올린 분리 실험으로, 시각적으로 더 깎인 느낌이 있으면 높은 alpha가 품질 저하 원인임을 확인하는 후보가 된다.
- 다음 시각 확인 우선순위는 `r03`, `r01`, `r05`, 그 다음 `r02`, `r04`로 둔다.

## v05-refine 시각 확인 메모

사용자가 수집된 결과를 확인한 결과, `r05_alpha_only_mesh_binary_search_7.ply`가 가장 품질이 좋아 보인다고 판단했다.

의미:

- vertex/face 수가 가장 많은 `r03_soft_dense`보다 `r05_alpha_only`가 더 좋아 보였으므로, 단순히 더 조밀한 tetra 설정이 시각 품질을 보장하지 않는다.
- 이번 `stump` crop에서는 `tetra_scale_multiplier=1.50`, `gaussian_scale_multiplier=0.70`을 유지하고 `alpha_threshold=0.82`로 표면을 정리한 조합이 가장 유망하다.
- 다음 sweep은 `r05_alpha_only` 주변에서 `alpha_threshold`를 0.81-0.84 범위로 좁게 흔들고, `gaussian_scale_multiplier`를 0.65-0.75 범위에서 비교하는 방향이 적절하다.

## 수정 crop 기준 r05-local 스크립트 준비

사용자가 `stump` crop 모델의 노이즈를 수정했다고 알려주었다. 수정된 crop PLY를 반영하려면 이전 variation model 폴더를 재사용하지 않고, `filter_3D` 복원부터 다시 수행해야 한다.

현재 확인한 stump model의 crop 관련 PLY:

| iteration | 파일 크기 | 수정 시각 |
|---|---:|---|
| `iteration_crop` | 17,008,874 bytes | 2026-07-10 03:28:21 KST |
| `iteration_edit` | 17,002,674 bytes | 2026-07-10 03:33:23 KST |
| `iteration_30000` | 179,728,460 bytes | 2026-06-30 21:38:28 KST |

`iteration_crop`과 `iteration_edit`가 모두 오늘 갱신되어 있어, 새 wrapper의 기본 입력은 `--crop-iteration auto`로 둔다. `auto`는 `iteration_crop`과 `iteration_edit` 중 더 최근 `point_cloud.ply`를 선택한다. 특정 파일을 강제로 쓰려면 `--crop-iteration crop` 또는 `--crop-iteration edit`를 지정한다.

변경한 스크립트:

- `experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh`
  - `r05-local` preset 추가
  - `--stamp` 옵션 추가
- `experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh`
  - stump 전용 wrapper 추가
  - 기본 `--crop-iteration auto`로 최근 crop/edit PLY 자동 선택
  - `--force-prepare`로 수정 crop PLY에 `filter_3D`를 다시 복원
  - `r05-local` 후보 6개 실행
  - 결과 `.ply`, `summary.tsv`, `manifest.tsv`, `sweep.log`, `README.md`를 하나의 수집 폴더에 복사

`r05-local` 후보:

| label | alpha | tetra | gaussian | 의도 |
|---|---:|---:|---:|---|
| r05a_a081_g070 | 0.81 | 1.50 | 0.70 | 기존 best보다 alpha를 살짝 낮춘다. |
| r05b_a082_g065 | 0.82 | 1.50 | 0.65 | 기존 best에서 Gaussian proxy를 더 얇게 본다. |
| r05c_a082_g070 | 0.82 | 1.50 | 0.70 | 이전 best `r05_alpha_only`와 같은 기준점이다. |
| r05d_a082_g075 | 0.82 | 1.50 | 0.75 | 기존 best에서 Gaussian proxy를 덜 얇게 본다. |
| r05e_a083_g070 | 0.83 | 1.50 | 0.70 | alpha를 한 단계 높여 표면 정리를 강화한다. |
| r05f_a084_g070 | 0.84 | 1.50 | 0.70 | alpha를 더 높였을 때 디테일 소실 여부를 본다. |

내일 실행 전 dry-run:

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh --dry-run
```

실제 실행:

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh
```

검증:

- `bash -n experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh`: 통과
- `bash -n experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh`: 통과
- `experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh --dry-run --stamp 20260710_testdryrun`: 통과
- `experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh --dry-run --stamp 20260710_autodryrun`: 통과, 현재 최신 PLY인 `iteration_edit` 자동 선택 확인

Dry-run에서 확인된 기본 수집 폴더 형식:

```text
experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_r05_local_<timestamp>
```

## 의미 없는 대용량 결과 정리

사용자 요청에 따라 오늘 생성한 대용량 결과 중 의미가 낮은 결과를 삭제했다. 판단 기준은 다음과 같다.

- `aggressive-extra` 5개 후보는 사용자 시각 확인에서 기존보다 품질이 나빠 보인다고 판단했다.
- `v05-refine`에서는 `r05_alpha_only_mesh_binary_search_7.ply`가 가장 좋아 보인다고 판단했다.
- 따라서 최종 대표 PLY는 수집 폴더에 남기고, 비교용 PLY와 중간 variation model 폴더는 삭제했다.

삭제한 대용량 model 폴더:

- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_extra_v06_a082_g065`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_extra_v07_a085_g060`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_extra_v08_a088_g055`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_extra_v09_a090_g050`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_extra_v10_a092_g045`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine_r01_v05_dense`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine_r02_v05_dense_plus`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine_r03_soft_dense`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine_r04_soft_dense_plus`
- `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2_crop_mesh_param_v05_refine_r05_alpha_only`

삭제한 수집 PLY:

- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_v05_refine_20260710_022638/r01_v05_dense_mesh_binary_search_7.ply`
- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_v05_refine_20260710_022638/r02_v05_dense_plus_mesh_binary_search_7.ply`
- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_v05_refine_20260710_022638/r03_soft_dense_mesh_binary_search_7.ply`
- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_v05_refine_20260710_022638/r04_soft_dense_plus_mesh_binary_search_7.ply`

보존한 대표 결과:

- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_v05_refine_20260710_022638/r05_alpha_only_mesh_binary_search_7.ply`
- 같은 폴더의 `summary.tsv`, `sweep.log`, `README.md`

정리 후 확인:

- `stump_v05_refine_20260710_022638` 수집 폴더 크기: 약 54MB
- 남은 `crop_mesh_param*` model 폴더는 2026-07-09 기본 sweep `v01-v05`뿐이다.
- filesystem 여유 공간: 약 642GB

## 수정 crop 기준 r05-local 실제 실행

사용자 요청에 따라 준비해둔 `stump cropfix r05-local` variation 6개를 실제 실행했다.

처음 일반 sandbox에서 실행했을 때 CUDA가 보이지 않아 실패했다.

```text
cuda_available: False
오류: 이 터미널에서 CUDA를 사용할 수 없습니다.
```

이후 GPU 접근 권한으로 다시 실행했고 정상 완료했다.

실행 명령:

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh
```

실행 정보:

- 시작: 2026-07-10 17:55:41 KST
- 종료: 2026-07-10 18:20:30 KST
- 상태: `OK`
- GPU: `NVIDIA GeForce GTX 1080 Ti`
- 입력 crop: `experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2/point_cloud/iteration_edit/point_cloud.ply`
- crop vertices: `68,553`

요약 파일:

- `experiments/M04_mesh_extraction/outputs/mesh_param_sweeps/gof_mip360_stump_i30000_fullres_highplus2_20260710_175541.tsv`

로그 파일:

- `experiments/M04_mesh_extraction/outputs/logs/gof_crop_mesh_param_sweep_gof_mip360_stump_i30000_fullres_highplus2_20260710_175541.log`

수집 폴더:

- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_r05_local_20260710_175541`

Windows 탐색기 경로:

```text
\\wsl.localhost\Ubuntu\home\choi\projects\2026_paper_work\Wind_Deformable_3DGS\experiments\M04_mesh_extraction\outputs\collected_meshes\stump_cropfix_r05_local_20260710_175541
```

결과:

| label | alpha | tetra | gaussian | mesh bytes | vertices | faces | status |
|---|---:|---:|---:|---:|---:|---:|---|
| r05a_a081_g070 | 0.81 | 1.50 | 0.70 | 54,660,967 | 1,434,048 | 2,880,936 | OK |
| r05b_a082_g065 | 0.82 | 1.50 | 0.65 | 52,160,770 | 1,372,452 | 2,745,471 | OK |
| r05c_a082_g070 | 0.82 | 1.50 | 0.70 | 55,239,848 | 1,448,292 | 2,912,317 | OK |
| r05d_a082_g075 | 0.82 | 1.50 | 0.75 | 55,721,714 | 1,458,814 | 2,939,671 | OK |
| r05e_a083_g070 | 0.83 | 1.50 | 0.70 | 55,685,023 | 1,459,248 | 2,936,448 | OK |
| r05f_a084_g070 | 0.84 | 1.50 | 0.70 | 56,031,525 | 1,467,672 | 2,955,326 | OK |

검증:

- `summary.tsv`: 6개 후보 모두 `OK`
- `manifest.tsv`: 6개 collected PLY 모두 vertices/faces 확인
- 수집 폴더 크기: 약 315MB
- 중간 variation model 폴더 크기: 후보별 약 129-132MB

해석 메모:

- 수정 crop 기준에서도 `r05c_a082_g070`은 이전 best였던 `r05_alpha_only`와 같은 기준점이다.
- 수치상 가장 큰 mesh는 `r05f_a084_g070`이며, alpha를 높일수록 vertex/face 수가 약간 증가했다.
- `r05b_a082_g065`는 Gaussian proxy를 더 얇게 본 후보이고, 이번 6개 중 vertex/face 수와 파일 크기가 가장 작다. 시각적으로 노이즈가 줄었는지, 또는 디테일이 사라졌는지 확인해야 한다.
- 우선 시각 확인 순서는 `r05c`, `r05e`, `r05f`, `r05d`, `r05a`, `r05b`로 둔다.

## stump mesh 노이즈와 정리 단계 확인

GOF 논문과 로컬 구현을 대조한 결과, 학습 완료 PLY를 별도로 uniform resampling하는 표준 후처리 단계는 없다. 논문에서 말하는 더 균일한 Gaussian 분포는 학습 중 densification의 clone 위치를 부모 중심에 그대로 복제하지 않고 Gaussian 분포에서 sampling하는 전략이다. 현재 로컬 `GaussianModel.densify_and_clone()`에도 이 sampling이 적용되어 있다.

GOF 학습에는 다음 geometry 정규화와 density 정리가 포함되어 있다.

- depth distortion loss와 depth-normal consistency loss: 기본값으로 iteration 15,000부터 적용
- densification과 opacity 기반 pruning: `densify_until_iter` 전까지 반복
- `filter_3D`: 카메라 거리와 focal length를 이용해 화면 공간 aliasing을 제어
- opacity reset: 설정된 주기마다 opacity를 낮춰 다시 최적화

현재 stump `fullres_highplus2` 학습 설정은 `densify_until_iter=16000`, `densify_grad_threshold=0.0006`, `densification_interval=120`, `opacity_reset_interval=100000`이다. 따라서 GOF의 sampling 기반 densification과 geometry loss는 적용됐지만, 30,000 iteration 동안 opacity reset은 사실상 꺼진 설정이다.

오늘 생성한 `r05-local` 로그에서는 `filter_mesh: 0`이었다. GOF의 `--filter_mesh`는 marching tetrahedra의 교차 edge 길이가 양 끝 scale 합보다 긴 경우 해당 vertex와 face를 제거한다. 따라서 멀리 떨어진 Gaussian 사이를 잇는 늘어진 면이나 일부 bridge 노이즈를 줄일 수 있지만, 작은 독립 component를 면적 기준으로 제거하거나 mesh를 smoothing하는 기능은 아니다.

수정 crop PLY 수치 점검:

- Gaussian 수: `68,553`
- opacity `< 0.2`: `2.322%`
- max scale 중앙값: `0.0128563`
- max scale이 중앙값의 5배 초과: `2.136%`
- max scale 최댓값: `0.6863213`, 중앙값의 약 53배
- 원본 GOF PLY의 `filter_3D`는 `68,553/68,553` 전부 정확히 복원됨

다음 검증 순서:

1. 같은 `r05c/r05e/r05f` 후보에 `--filter-mesh`를 켜 전후 비교한다.
2. 남는 작은 독립 조각은 connected-component 면적/face 수 threshold sweep으로 제거한다. 나뭇가지와 잎을 보존해야 하므로 largest component만 남기는 방식은 피한다.
3. 여전히 표면 돌기와 덩어리가 남으면 crop Gaussian에 opacity 하한과 과대 scale 상한을 적용한 전처리 variation을 비교한다.
4. uniform downsampling은 얇은 가지와 표면 디테일을 직접 줄이므로 우선순위에서 제외한다.

참고:

- GOF 논문: https://arxiv.org/abs/2404.10772
- GOF 공식 저장소: https://github.com/autonomousvision/gaussian-opacity-fields

## filter_mesh 비교 샘플 생성

노이즈 원인을 분리해서 보기 위해 기존 수정 crop과 `r05c/r05e/r05f` 파라미터는 그대로 두고, GOF `--filter_mesh`만 켠 세 샘플을 생성했다.

스크립트 변경:

- `run_gof_crop_mesh_param_sweep.sh`에 `r05-filter-sample` preset 추가
- `run_stump_cropfix_r05_mesh_sweep.sh`에 `--preset` 선택 기능 추가
- `r05-filter-sample` 선택 시 `filter_mesh=1` 자동 적용
- 결과 이름에 `fm_` 접두사를 사용해 무필터 결과와 구분

실행 명령:

```bash
experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh \
  --preset r05-filter-sample \
  --stamp 20260710_221227
```

실행 결과:

- 시작: 2026-07-10 22:12:41 KST
- 종료: 2026-07-10 22:25:40 KST
- 상태: `OK`
- 입력 crop: `iteration_edit`, Gaussian `68,553`개
- `filter_mesh`: `1`
- 수집 폴더 크기: 약 `145MB`

수집 폴더:

- `experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_r05_filtermesh_sample_20260710_221227`

Windows 탐색기 경로:

```text
\\wsl.localhost\Ubuntu\home\choi\projects\2026_paper_work\Wind_Deformable_3DGS\experiments\M04_mesh_extraction\outputs\collected_meshes\stump_cropfix_r05_filtermesh_sample_20260710_221227
```

| label | vertices | faces | mesh bytes | vertex 감소 | face 감소 | 파일 크기 감소 |
|---|---:|---:|---:|---:|---:|---:|
| fm_r05c_a082_g070 | 1,363,825 | 2,593,009 | 50,075,240 | 5.832% | 10.964% | 9.349% |
| fm_r05e_a083_g070 | 1,371,853 | 2,606,951 | 50,352,822 | 5.989% | 11.221% | 9.576% |
| fm_r05f_a084_g070 | 1,377,486 | 2,616,007 | 50,538,146 | 6.145% | 11.482% | 9.804% |

해석:

- `filter_mesh`가 모든 후보에서 vertex 약 6%, face 약 11%를 일관되게 제거했다.
- 먼저 `fm_r05c`와 기존 `r05c`를 시각 비교해 bridge/늘어진 면이 줄었는지 확인한다.
- 디테일 손실이 허용 범위면 `fm_r05e`, `fm_r05f` 순으로 alpha 효과를 비교한다.
- 여전히 작은 독립 노이즈가 많을 때만 다음 단계인 connected-component threshold sweep을 진행한다.
