# 2026-06-27 GOF Mip-NeRF 360 고퀄 batch 스크립트

## 배경

스모크 학습으로 `bonsai` viewer 확인이 정상 동작하는 것을 확인했다. 이후 연구용 고퀄 3DGS 모델을 한 번에 생성하기 위해 학습, SIBR 호환 변환, render를 묶은 wrapper가 필요했다. Mesh extraction은 3DGS 품질 확인 뒤 별도 단계로 진행하기로 했다.

## 변경 내용

- `M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh`를 추가했다.
- 기본값은 전체 Mip-NeRF 360 준비 scene, `30000` iterations, official factors이다.
- official factors는 현재 보유 scene 기준 `bonsai=images_2`, `flowers/garden/stump/treehill=images_4`로 적용한다.
- 각 scene마다 기존 단일 학습 wrapper를 호출해 학습을 수행한다.
- 학습 point cloud를 `wind3dgs.m04_mesh_extraction.filter_viewer_safe_ply`로 SIBR 호환 `iteration_sibr_safe` copy로 변환한다.
- 기본으로 render까지 실행하며, `--no-render`, `--no-convert`로 각 단계를 끌 수 있게 했다.
- mesh extraction 관련 옵션은 고퀄 학습 wrapper에서 제거했다. 추후 3DGS 품질 확인 뒤 별도 mesh extraction wrapper를 만든다.
- `--skip-train-if-ready`, `--backup-existing`, `--continue-on-error`, `--dry-run` 옵션을 지원한다.
- `M04_mesh_extraction/README.md`에 고퀄 batch 사용법과 산출물 경로를 추가했다.

## 검증

다음 명령으로 문법 검사를 통과했다.

```bash
bash -n experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh
```

다음 명령으로 전체 실행 계획 dry-run을 확인했다.

```bash
experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh --dry-run
```

dry-run 결과, 5개 scene의 학습 command, SIBR 호환 변환 command, render 후처리 command, viewer 확인 command가 모두 생성됐다.

## 사용 메모

전체 고퀄 run은 시간이 길 수 있으므로 먼저 `--dry-run`으로 경로와 옵션을 확인한다. 특정 scene만 먼저 확인하려면 `--scenes "bonsai"`처럼 범위를 줄인다.

현재 render 단계는 이미지 산출물을 생성하는 단계이며, 자동 수치 평가나 contact sheet 비교는 포함하지 않는다. 자동 비교가 필요하면 별도 평가 wrapper를 만든다.
