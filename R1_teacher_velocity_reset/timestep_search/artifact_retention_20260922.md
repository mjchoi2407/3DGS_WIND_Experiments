# 실험 artifact 보존·정리

## 2026-10-01 정리

사용자 승인으로 물리 솔버 중간 자료와 과거 사진 기반 mesh extraction 자료를 정리했다.
현재 원본 mesh → 렌더 이미지 → 3DGS 생성 경로에 필요한 mesh·학습 도구와 물리 비교 원본은 보존했다.
연구 수치·판정·완료 기준은 바꾸지 않았다. 아래 원시 자료의 보관 방식만 변경했다.

| 대상 | 삭제 파일 수 | 회수한 파일 할당량 |
| --- | ---: | ---: |
| 재생성 가능한 컴파일 캐시 | 10,642 | 2.304 GiB |
| 보존 ZIP과 SHA256이 같은 중복 파일 | 4,289 | 2.527 GiB |
| 과거 적분기·정밀도 중간 trace/stages | 36 | 4.645 GiB |
| M04 사진·학습 모델·다운로드·중간 산출물 | 1,092,444 | 239.053 GiB |
| 합계 | 1,107,411 | 248.529 GiB |

GiB는1024³ bytes다. 위 합계는 파일의 실제 할당량이며 제거한 빈 디렉터리와 파일시스템 metadata 공간은 별도다.
물리 자료의 회수량은9.476 GiB다. 삭제 전 목록 전체의 경로·크기·수정시각·inode를 대조했고,
ZIP 중복본은 삭제 전 SHA256 동일성과 보관 ZIP의 불변성을 확인했다. 양 PC에 실행 중 계산·전송이 없음을 확인했다.

- [삭제 명세](../../artifacts/retention/20261001_cleanup/cleanup_manifest.jsonl.gz): workspace 상대 `path`, `group`, 삭제 전 `signature`; ZIP 중복본은 `sha256`, `archive`, `archive_entry` 포함.
- [완료 요약](../../artifacts/retention/20261001_cleanup/summary.json): `status`, `groups`, `deleted_files`, 보존·검증 판정. [실행 기록](../../artifacts/retention/20261001_cleanup/execution.jsonl)은 실제 삭제 진행과 완료를 기록한다.
- 삭제 명세 SHA256: `2bccfa07c8406fbcd0f95eda74a699fdc68937902435a627bb4036e89f7792c1`. 이 목록과 완료 요약은 ignored retention artifact이며 Git에 원시 대용량 자료를 추가하지 않는다.

### 보존한 비교 원본

- v12 세 씬과 서브 v13 세 씬의 연속 완주, 감쇠24의 같은 RTX5070 64/128 비교.
- 막5ms 기준, 막5ms·굽힘20ms·기하 재사용 추천안, 같은 시작점의 비용 대조, 바람 reference/smooth/local 비교.
- 초기 hi/lo·forcing·후속 실행이 사용하는 프레임과 기존 geometry 실패,1/500 선택 원본, 과거 playback-only 결과.
- 최근 핵심 묶음 11,215개 파일은 삭제 전후 크기·수정시각·inode 동일성을 확인했다. `bundle_cached`는 과학적 결과 묶음이므로 삭제하지 않았다.
- M04의 [대표 추출 mesh 모음](../../M04_mesh_extraction/outputs/collected_meshes) 28개 파일과 스크립트·설정·작은 로그를 남겼다. [mesh hash 목록](../../artifacts/retention/20261001_cleanup/preserved_meshes.json)의 모든 SHA256이 삭제 전후 일치한다. 원본 cloth mesh와 mesh 후보 데이터셋은 M04 밖에 보존한다.

### 압축 보관과 재생성

`teacher_precision_v3`의 `completed_dual_gpu_20260916_compact.zip`,
`bounded_closeout_20260916.zip`, `frozen_line_search_20260917.zip`을 보존했다.
압축본과 같은 4,289개 파일만 확장 폴더에서 제거했고 고유 파일은 남겼다.
각 폴더의 `retention_status.json`과 삭제 명세의 archive member로 위치를 확인한다.
필요하면 ZIP을 **새 복원 경로**에 풀어 사용한다. 현재 확장 폴더를 완전한 원본 실행으로 취급하지 않는다.

`teacher_timestep_search`의 `newmark_gauss_switch_v1`, `newmark_geometry_switch_v2`,
`gauss_scaling_trial_v1`, `gauss_fp32_trial_v1`에서 선별한36개 중간 trace/stages NPZ를 제거했다.
동결 실행기·입력·보고서·설정·나머지 NPZ는 남겼으며 `retention_status.json`으로 부분 보관을 표시했다.
해당 배열이 필요하면 보존된 명령과 입력으로 새 경로에 재계산한다. 과거의 정확한 wall-clock 재현은 주장하지 않는다.
기존 실패 분모·compact 보고서와 과거 검증 결과를 성공으로 바꾸지 않는다.

M04 사진/모델은 현재 경로에서 퇴역했다. 남긴 다운로드·학습 스크립트와 과거 README는 당시 재현 경로이며,
외부 원본의 현재 다운로드 가능성을 이번 작업에서 재확인하지 않았다. 새 촬영 자료나 모델을 받지 않았다.

### 정리 후 검증

[뷰어 준비 검사](../../artifacts/retention/20261001_cleanup/viewer_validation.json)의 네 호출이 모두 통과했다:
바람3종, 전체wind 감쇠 추천안, 감쇠24의64와128이다. `--prepare-only`로 기존 raw/hash/시간/연결을 확인했으며
새 시뮬레이션이나 시각 품질 판정을 수행한 것이 아니다. 보존 ZIP3개와 대표 mesh 모음의 hash도 유지됐다.

## 2026-09-22 당시 정리

사용자 승인으로 시각 확인·성능 비교가 끝난 raw 궤적을 playback-only 또는 report-only로 정리했다.
물리식·솔버·검산 기준과 추적된 결과 수치는 변경하지 않았다.

## 결과

- `experiments/artifacts`: 378,361,958,400 → 51,054,505,984 bytes.
- 회수 공간: 327,307,452,416 bytes.
- 디스크 사용률: 71% → 39%.
- 삭제 작업: 3,257개 경로.
- 원본 삭제 목록·이유·보존 경로: `artifacts/retention/20260922_cleanup/cleanup_manifest.json`.

## 보존 범위

- 기하 실패 원본 `sub_pc/20260912T162242Z-59eb2516b2124c6d997d086fcd6f86e6`.
- 최근 RTX5070 적응형 실행 `sub_pc/20260919T194142Z-4d98ab0f6f2a40d18a91eaf77e62a872`.
- 최근 GTX1080Ti 적응형 실행 `teacher_timestep_search/gpu_gtx1080ti_adaptive_integrator_bend500_v1`.
- 선택한 1/500 visual 원본 `teacher_timestep_search/gravity_wrinkles_flag_bend500_v1`.
- 입력·wind·config·report·summary·manifest·checkpoint·linear snapshot.
- v2를 직접 참조하는 158–163 frame.
- P3 reset66 미달 비교의 n16/n32 대표 66·67·89 frame.
- precision v3 compact/closeout/frozen-line-search ZIP.

완료된 서브컴 10초 3조건×3메시는 9개 playback cache로 보존했다. 각 cache의 source report hash와
`positions.npy`·`geometry.npz` hash를 확인한 뒤 38GB substep chunk를 제거했다. 원본 삭제 후
`view_cloth_coarse_10s.sh`의 9개 `--prepare-only` 조합이 모두 통과했다.

## 재생성 계약

삭제한 visual/physics 배열은 남은 실행기·config·입력·source identity를 사용해 새 output 경로에서
처음부터 계산한다. 과거 wall-clock은 장치 상태와 환경에 의존하므로 보존 report가 authority이며 동일 시간
재현을 요구하지 않는다. 중간 상태에서 시작하는 진단은 남긴 checkpoint/snapshot을 사용한다.
`prepared_not_run`과 최신 결과로 대체된 중단 prefix는 재생성 대상이 아니다.

기존 완료 폴더에 누락 frame을 이어 쓰지 않는다. report-only 폴더의 전체 궤적이 필요하면 새 폴더에서
재실행하고, 현재 compact 폴더를 완전한 raw 실행으로 해석하지 않는다.
