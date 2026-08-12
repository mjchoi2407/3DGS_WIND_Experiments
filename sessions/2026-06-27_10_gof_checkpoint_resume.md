# 2026-06-27 GOF checkpoint 재개 기능 추가

## 배경

사용자가 고퀄 GOF/3DGS 학습을 중단했을 때 이어서 실행할 수 있는지 확인했다. 기존 wrapper는 최종 point cloud가 완성된 경우만 `--skip-train-if-ready`로 건너뛸 수 있었고, 중간 iteration checkpoint 재개는 연결되어 있지 않았다.

## 변경 내용

- `M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh`에 checkpoint 옵션을 추가했다.
- 추가 옵션:
  - `--checkpoint-every N`
  - `--checkpoint-iterations "LIST"`
  - `--resume`
  - `--no-resume`
  - `--start-checkpoint PATH`
- `--resume`이 켜져 있고 model 디렉터리에 `chkpnt*.pth`가 있으면 가장 큰 iteration 번호의 checkpoint를 자동 선택한다.
- model 디렉터리가 비어 있지 않은데 checkpoint가 없으면 실제 실행은 중단한다. `--dry-run`에서는 경고만 출력하고 command를 보여준다.
- `M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh`는 기본으로 `--checkpoint-every 5000 --resume`을 단일 scene wrapper에 전달한다.
- README에 checkpoint 산출물, 재실행 방법, 기존 checkpoint 없는 run의 한계를 기록했다.

## 검증

다음 문법 검사를 통과했다.

```bash
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh
```

다음 dry-run을 확인했다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh \
  --scene bonsai \
  --iterations 30000 \
  --images images_2 \
  --checkpoint-every 5000 \
  --resume \
  --dry-run
```

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh \
  --dry-run \
  --scenes "bonsai"
```

dry-run 결과, 고퀄 batch command에 `--checkpoint-every 5000 --resume`이 포함되는 것을 확인했다.

## 주의

checkpoint 기능 추가 전에 이미 만들어진 model 디렉터리에 `chkpnt*.pth`가 없다면 중간 iteration부터 이어갈 수 없다. 이 경우 새 model 디렉터리를 지정하거나 `--backup-existing`으로 기존 디렉터리를 백업하고 처음부터 다시 시작한다.
