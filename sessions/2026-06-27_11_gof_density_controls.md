# 2026-06-27 GOF density 제어 옵션 추가

## 배경

`flowers`와 `stump`를 `images_8`로 낮춰도 GOF 학습 중 GPU memory가 계속 커지는 현상이 확인됐다. 원인은 해상도만이 아니라 densification으로 Gaussian 수가 증가하는 구조에 있다고 판단했다. 연구의 다음 단계가 mesh extraction이므로, 매우 조밀한 3DGS보다 안정적으로 mesh를 뽑을 수 있는 중간 밀도 모델을 먼저 확보하는 쪽이 적합하다.

## 변경 내용

- `M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh`에 density 제어 옵션을 추가했다.
- 추가 옵션:
  - `--density-preset default`
  - `--density-preset mesh`
  - `--density-preset safe`
  - `--density-preset off`
  - `--densify-until-iter N`
  - `--densify-grad-threshold VALUE`
  - `--densification-interval N`
  - `--opacity-reset-interval N`
  - `--percent-dense VALUE`
- `mesh` preset은 densification을 `2500` iteration까지만 수행하고 `densify_grad_threshold=0.001`, `densification_interval=200`, `opacity_reset_interval=100000`을 사용한다.
- `safe` preset은 더 보수적으로 densification을 `1500` iteration까지만 수행하고 `densify_grad_threshold=0.0015`, `densification_interval=300`, `opacity_reset_interval=100000`을 사용한다.
- `off` preset은 densification을 끄는 확인용 설정이다.
- `M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh`에서도 같은 density 옵션을 단일 scene wrapper로 전달하도록 연결했다.
- `--model-dir`를 직접 지정하지 않은 경우 non-default density preset은 기본 model 디렉터리에 `_mesh`, `_safe`, `_off` suffix를 붙이도록 했다.
- 정수형 옵션과 실수형 옵션의 입력 검증을 추가했다.
- README에 mesh extraction 목적의 저밀도 실행 예시와 권장 순서를 기록했다.

## 검증

다음 문법 검사를 통과했다.

```bash
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh
```

다음 dry-run을 확인했다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene stump \
  --iterations 30000 \
  --images images_8 \
  --model-dir experiments/M04_mesh_extraction/models/_dryrun_stump_density_mesh \
  --checkpoint-every 1000 \
  --resume \
  --density-preset mesh \
  --dry-run
```

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene stump \
  --iterations 30000 \
  --images images_8 \
  --model-dir experiments/M04_mesh_extraction/models/_dryrun_stump_density_safe \
  --checkpoint-every 1000 \
  --resume \
  --density-preset safe \
  --dry-run
```

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --dry-run \
  --scenes stump \
  --density-preset mesh
```

dry-run 결과 `mesh` preset에서는 `--densify_until_iter 2500 --densify_grad_threshold 0.001 --densification_interval 200 --opacity_reset_interval 100000`이 학습 command에 포함되는 것을 확인했다. `safe` preset에서는 `--densify_until_iter 1500 --densify_grad_threshold 0.0015 --densification_interval 300 --opacity_reset_interval 100000`이 포함되는 것을 확인했다.

## 권장 실행

현재 11GB급 GPU에서는 `stump`, `flowers`, `garden`을 바로 `images_4` 고퀄 설정으로 돌리기보다 `images_8 + mesh preset`으로 먼저 3DGS와 viewer 품질을 확인한다.

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

이 설정도 GPU memory가 계속 한계에 가까우면 같은 scene을 새 model 디렉터리로 `--density-preset safe`로 다시 시작한다.
