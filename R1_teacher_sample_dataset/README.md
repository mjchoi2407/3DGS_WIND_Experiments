# Teacher 개발용 샘플 데이터

2026-09-08, Wind3DGS. 사용자의 샘플 생성·검증까지 연속 진행 요청에 따른 작은 response 데이터다.
기존 Newton/Registry/raw trajectory/probe 경로로 생성하며 새 CPU shell 물성 경로를 채택한 데이터가 아니다.

본 학습용 Teacher는 아직 공간 수렴을 통과하지 못했다. 이번 샘플은 저장·원본 대조·재생·batch loader를
확인하는 **development 전용**이며 `training_eligible=false`다. Loader에서 `allow_development=True`가
필요하고 모든 wind/초기 변형 파생물은 같은 source object group의 development split에 둔다.
독립 GS·GS mapping·oracle·FRF·R1/R2 학습 완료를 주장하지 않는다.

입력은 1m×1m 사각 깃발, n=8, M_ref=0.1kg, 60fps, 16 substeps, 10 iterations와 기존 native 물성이다.
중력은 0이다. 0.5m/s 바람 펄스(0.2초)+정지 공기(0.8초), 바람 0.5초 on/off,
공력 off·초기 ΔY=0.01x² 자유감쇠 각 1초를 독립 실행한다.
25개 probe의 변위·속도와 입력 바람·외력 work를 12 interval/13 state 단위로 나눈다.
외력은 frame-start sample을 hold하는 기존 계약을 유지한다. 자유감쇠의 native material damping은 유지한다.

```bash
bash code/scripts/generate_teacher_sample_dataset.sh \
  --output ../experiments/artifacts/runs/teacher_sample_dataset/my_new_run \
  --dataset ../experiments/artifacts/datasets/teacher_samples/my_new_dataset
```

Launcher가 code로 이동하므로 인자는 code 기준이다. CPU에서 실행하고 Warp cache는 code/outputs 내부에 둔다.
기존 출력 덮어쓰기·자동 재시도는 없으며 600초 상한 내에 세 원본·probe·독립 재생·dataset·batch 검사를 수행한다.
보존된 실제 결과는 다음 절에 기록했다.

## 생성·검증 결과

**15개 개발용 sample 생성·검증이 완료됐다.** 세 원본의 180 interval/183 state를 보존했다.
원본 값 대조, CPU 독립 재생, 재로드와 배치 크기 [4,4,4,3] 검사가 통과했다.
각 sample의 정답 배열은 [13,25,3], 첫 batch는 [4,13,25,3]이다.
세 재생 모두 위치·속도·공력 힘·work 최대 차이가 0이다. 모든 원본에서 pin drift=0, guard=0이다.

| 시계열 | 최대 nodal speed [m/s] | 외력 work 절댓값의 합 [J] |
| --- | ---: | ---: |
| wind_pulse | 0.202946126 | 0.000789484374 |
| step_on_off | 0.471042246 | 0.006596602165 |
| aero_off_decay | 0.133365527 | 0 |

마지막 열은 순 외력 일이나 구조 에너지 drift가 아닌 interval별 외력 work 절댓값의 합이다.
Pulse/step의 바람 off 구간도 air drag가 켜져 있으므로 정지 공기에서 저항이 남는다.
Free-decay는 공력을 끄지만 기존 material damping은 유지하며, 보존계 진동이라고 표시하지 않는다.

생성·원본 대조·세 replay·배치 검증에 48.370초가 걸렸다. 실제 환경은 [environment](evidence/environment.json)를 따른다.
추가 독립 프로세스에서 원본 inventory와 producer source 24개, 모든 sample label/input/work를 다시 대조했다.
신규 dataset 검사 11개와 공간/기존 회귀 228개를 합친 관련 **239개 검사**를 확인했다.
이는 이번에 실행한 관련 범위이며 repository 전체 test discovery 결과는 아니다.

- 데이터: `artifacts/datasets/teacher_samples/20260908_sample_v1/` — manifest 포함 20개 파일, **125,293byte**.
- 원본: `artifacts/runs/teacher_sample_dataset/20260908_sample_v1/` — 최상위 manifest 제외 93개 inventory, 1,150,138byte.
- [생성 보고서](evidence/report.json), [데이터 manifest](evidence/dataset_manifest.json),
  [검산 결과](evidence/verification.json), [provenance](provenance.json), [설정](evidence/config.json).

Dataset manifest SHA-256:
`1ab229207fa8ec60c282aa433c49d7a5f8a288deb1575688794b72b2afdae8f5`.
Raw registry/content hash와 probe manifest를 sample case마다 연결한다.
Compact evidence만으로 NPZ를 복원할 수 없으므로 raw와 dataset을 함께 보존한다.
원본 삭제·덮어쓰기·commit·push·fetch·설치는 하지 않았다.

## 열어보기

Workspace root에서 실행한다. Torch·Newton·Warp 없이도 저장한 dataset을 읽고 NumPy batch를 만들 수 있다.
`allow_development=True`가 없으면 본 학습용으로 오인해 사용하지 않도록 거부한다.

```bash
PYTHONPATH=code .venv/bin/python - <<'PY'
from wind3dgs.teacher.sample_dataset import TeacherSampleDataset

samples = TeacherSampleDataset.open(
    'experiments/artifacts/datasets/teacher_samples/20260908_sample_v1',
    allow_development=True,
)
for batch in samples.iter_batches(batch_size=4):
    print(batch['sample_ids'])
    print(batch['arrays']['rest_displacements_m'].shape)
PY
```

`static.npz`는 rest probe·면적·M_ref 질량·attachment mask,
세 registry JSON은 물리 설정, 15개 NPZ는 window별 절대 시각·초기 변위·변위/속도·바람·공력 flag·외력 work다.
인접 window의 공유 state를 유지하고 interval을 중복하거나 case 사이를 연결하지 않는다.
Sample 입력은 response loader 개발용이며 target static GS를 대신하지 않는다.

[움직임 확인 그래프](evidence/sample_response.png)는 (1,0,0) 끝점의 Y 변위·속도를 그린다.
[검산·그래프 스크립트](evidence/verify_and_plot.py)는 다음처럼 재현한다.
그래프에는 로컬에 이미 설치된 Matplotlib과 Noto Sans CJK 글꼴을 사용했다.

```bash
PYTHONPATH=code MPLCONFIGDIR=/tmp/wind3dgs_sample_matplotlib \
  .venv/bin/python experiments/R1_teacher_sample_dataset/evidence/verify_and_plot.py
```

## 본 학습용 채택까지 남은 조건

기존 native bending의 mesh 의존성과 [새 shell의 공간 검사 미달](../R1_teacher_shell_linear_spatial/README.md)이 남아 있다.
공간/시간·공력·spectrum의 accepted Teacher 설정, independent GS/common-valid mapping과 oracle 계약을
충족해야 본 학습용 데이터로 채택할 수 있다. 이번 실행은 R2 학습을 수행하거나 이 조건을 완료 처리하지 않았다.
