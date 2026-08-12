# 2026-06-27 GOF 중간 density 남은 scene batch 스크립트

## 배경

`stump images_8_mesh`는 빠르고 안정적으로 끝났지만 viewer에서 다소 뿌옇게 보였다. 원인은 Gaussian 수가 너무 적고 `images_8` 입력 해상도도 낮은 점으로 판단했다. 사용자는 입력 이미지를 더 높은 해상도인 `images_4`로 두고 density를 조금 높이는 설정을 `flowers`, `garden`, `treehill`에도 적용하고 싶다고 요청했다.

## 변경 내용

- `M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh` 임시 wrapper를 추가했다.
- 기본 실행 대상은 `flowers garden treehill`이다.
- 기본 학습 설정:
  - `iterations=30000`
  - `images=images_4`
  - `checkpoint-every=1000`
  - `resume=1`
  - `densify_until_iter=5000`
  - `densify_grad_threshold=0.001`
  - `densification_interval=200`
  - `opacity_reset_interval=100000`
- 출력 model은 `models/gof_mip360_<scene>_i30000_images_4_mid`로 분리한다.
- 각 scene 학습 후 `iteration_sibr_safe/point_cloud.ply` 변환을 자동 실행한다.
- `flower` 입력은 `flowers`로 자동 보정한다.
- `--dry-run`, `--scenes`, `--continue-on-error`, `--skip-train-if-ready`, density override, viewer-safe 변환 옵션을 지원한다.
- README에 사용법과 기본 출력 경로를 기록했다.

## 검증

다음 문법 검사를 통과했다.

```bash
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh
```

다음 dry-run을 확인했다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh --dry-run
```

dry-run 결과 `flowers`, `garden`, `treehill` 각각에 대해 `images_4`, `30000` iterations, 중간 density 옵션, `..._images_4_mid` model 디렉터리, `iteration_sibr_safe` 변환 command가 출력되는 것을 확인했다.

## 실행 명령

전체 실행:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh
```

특정 scene만 실행:

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh \
  --scenes "flowers treehill"
```
