# 2026-06-27 GOF Mip-NeRF 360 전체 스모크 batch 스크립트

## 배경

사용자가 Mip-NeRF 360 준비 scene 전체를 한 번에 스모크 테스트할 수 있는 스크립트를 요청했다. 기존 `run_gof_mip360_smoke.sh`는 단일 scene만 실행하므로, 전체 진행률과 scene별 요약을 보기 편하게 출력하는 batch wrapper가 필요했다.

## 추가한 파일

```text
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
```

## 동작 방식

- 기본 scene 목록:
  - `bonsai`
  - `flowers`
  - `garden`
  - `stump`
  - `treehill`
- 각 scene에 대해 기존 단일 스모크 스크립트 `run_gof_mip360_smoke.sh`를 순차 실행한다.
- 기본값은 `1000` iterations, `images_4`, GPU `0`이다.
- scene별 port는 `6009`부터 1씩 증가한다.
- batch 로그는 `experiments/M04_mesh_extraction/outputs/logs/`에 남긴다.

## 진행도 출력

batch 로그와 터미널에 다음 정보를 출력한다.

- 전체 진행률: `[현재/전체]`, percent, scene 이름
- scene별 시작/종료 시각
- scene별 실행 command
- scene별 exit status
- scene별 소요 시간
- batch 누적 시간
- 현재까지 성공/실패 요약

GOF 학습 중 출력되는 외부 학습 로그와 `tqdm` progress는 원문 그대로 터미널과 로그에 함께 남긴다.

## 주요 옵션

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --dry-run
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --continue-on-error
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --run-render --run-mesh
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --skip-train-if-ready --run-render --run-mesh
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --scenes "bonsai flowers"
```

품질용 run으로 넘어갈 때는 다음 조합을 사용할 수 있다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh \
  --iterations 30000 \
  --official-factors
```

현재 `--official-factors`는 보유 scene 기준으로 `bonsai=images_2`, `flowers/garden/stump/treehill=images_4`를 사용한다.

## 검증

다음 검증을 수행했다.

```bash
chmod +x experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --help
experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --dry-run
```

`--dry-run`에서 5개 scene의 command가 정상적으로 출력되는 것을 확인했다. 실제 GPU 학습은 사용자가 직접 실행할 예정이므로 시작하지 않았다.
