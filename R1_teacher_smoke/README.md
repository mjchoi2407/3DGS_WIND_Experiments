# R1 Teacher GPU smoke 검토

## 목표와 판정 범위

Teacher의 CUDA 실행→trajectory 저장→공통 probe 추출→공간·시간 비교→같은 GPU에서 replay 경로를 검증한다.
2026-09-07 사용자의 GTX 1080 Ti 실행은 **12/12단계 통과**했다. 물리 수렴 판정은
`convergence_status=not_assessed`이며, 이 결과는 R1 완료나 학습 dataset 품질 인증이 아니다.
CUDA 미지원, incomplete inventory, 원본/hash 불일치, non-finite state, pin drift/guard 발생이나
replay 허용치 초과는 이 smoke 검사의 실패 조건이다. 수렴 지표 자체의 허용 오차는 아직 동결하지 않았다.

현행 연구 계약은 [ideas index](../../ideas/README.md), 누적 구현은 [code 인수인계](../../code/sessions/2026-09-07_07_teacher_gpu_checkpoint.md)를 따른다.
이 폴더는 R1 개발용 지원 검증의 compact evidence다. 기존 TD## milestone 완료 상태와 연결하지 않는다.

## 실행·입력과 환경

Workspace root에서 사용자가 실행한 명령은 다음과 같다. 다시 실행하면 새 timestamp 폴더가 생긴다.

```bash
bash code/scripts/check_teacher_gpu.sh
```

- 실행: 2026-09-07 04:25:24–04:26:18 KST, 검사 소요 53.912114초, child exit 0.
- 장치: `cuda:0`, NVIDIA GeForce GTX 1080 Ti, 11 GiB, `sm_61`.
- 환경: Python 3.12.3, Newton 1.3.0, Warp 1.17.0, NumPy 2.4.4.
  Warp 로그의 CUDA Toolkit 12.9/Driver API 13.0, `nvidia-smi` driver 582.28.
- 설정: 실행기의 고정 `CASE_PLAN`, seed 0. 1m×1m rectangular flag, 왼쪽 변 고정, M_ref=0.1kg.
  fps=60, 12 interval/13 state, 총 0.2초, structural iterations=10.
- Wind: 처음 6 interval은 0.5m/s, 나머지 6개는 ambient wind off/0m/s이며 relative air drag는 유지한다.
  `gravity_off` 초기 정책으로 실제 중력은 0이다. Mesh 2/4/8과 substeps 4/8/16을 사용한다.
- Free decay: mesh 4/8, substeps 4, `displaced_gravity_off`, ΔY=0.01m·(X/1m)², 초기 속도·실제 중력 0,
  air drag off. Wind sample이 기록돼 있어도 공력과 외력 work는 0이다.
- Native material: tri_ke=1000 N/m, tri_ka=1000 N/m, tri_kd=0.1 s,
  edge_ke=10 N, bending damping off. 연속체 물성 대응/mesh 보정은 미확정이다.
- 공통 probe: 5×5 rest grid, trapezoidal 면적 가중치, 총 면적 1m², 총 질량 0.1kg, tip=`tip_center`.
- Privilege: mesh/연결성/pin과 solver state는 training/evaluation Teacher 입력이다.
  Student runtime은 실행하지 않았다. Dataset/model/object package는 `not_applicable`: 개발 fixture이며
  split reference는 `development-smoke-only`다. 실제 source-object train/validation/test split이 아니다.

## 보존한 evidence와 원본

- 원본: `experiments/artifacts/runs/teacher_gpu_check/20260907_042524_687651/`.
- [review.json](review.json): 원본 summary/checks/environment/cuda, 비교 report의 metadata와 source binding,
  추가 읽기 전용 bending 관찰을 보존한다. 자체적인 R1PreflightReport schema나 완료 marker는 아니다.
- [artifact_inventory.json](artifact_inventory.json): 원본 191개 파일의 상대 경로·byte 수·SHA-256.
  원본 report의 semantic hash와 파일 byte hash는 구분한다.
- 실행 당시 코드는 미commit 상태였다. `environment.sources_sha256`의 24개 파일이 실제 실행 snapshot이며,
  이 파일들이 모두 일치하는 후속 code commit을 `review.json`의 `source_checkpoint`에 기록한다.
  후속 commit이 실행 당시 HEAD였다고 주장하지 않는다.
- 원본 trajectory/NPZ/cache는 Git에서 제외된 경로에 그대로 보존한다. Compact evidence만으로 원본을 복원할 수 없다.
  다른 환경에서는 소유자가 보존한 원본 폴더를 가져와 inventory로 대조하거나 위 명령으로 별도 run을 생성한다.
  이번 작업에서 원격 fetch/download, 원본 삭제·덮어쓰기 또는 GPU simulation 재실행은 하지 않았다.

## 확인한 결과

7개 raw/probe 쌍, 비교 3개와 replay 2개가 모두 통과했다. 모든 run은 `cuda:0`, pin drift=0,
guard count=0이며 유한한 비영 운동을 보였다. Free-decay 외력 work는 정확히 0이다.
Wind/decay replay의 position·velocity 최대 절대 차이는 0이다. Wind force 차이는
2.3283e-10 N, work 차이는 1.6589e-13 J이고 decay의 기록된 차이는 모두 0이다.
허용치는 rtol=5e-5, position atol=1e-6m, velocity=1e-5m/s, force=1e-6N, work=1e-9J다.

Agent는 사용자 GPU 실행 후 원본을 연결해 비교 3개를 NumPy로 다시 계산했고 report hash가 일치했다.
이 경로는 raw/probe 원본과 고정 조건도 검증한다. Source SHA-256 24개가 현재 구현과 일치했고,
검토 전후 원본 191개 파일의 SHA-256도 변하지 않았다. GPU replay는 사용자가 실행한 결과의 기록을 검토했다.

| 비교 | 인접 level | 속도 RMS 차이 (m/s) | Fine 속도 대비 상대 RMS |
| --- | --- | ---: | ---: |
| Spatial wind | mesh 2→4, substeps 4 | 0.0084417774 | 10.07% |
| Spatial wind | mesh 4→8, substeps 4 | 0.0216475230 | 24.90% |
| Temporal wind | substeps 4→8, mesh 8 | 0.0206361883 | 23.99% |
| Temporal wind | substeps 8→16, mesh 8 | 0.0097397137 | 11.41% |
| Spatial free decay | mesh 4→8, substeps 4 | 0.0323283472 | 193.25% |

RMS는 probe mass/M_ref 공간 가중치와 전체 T+1 state의 시간 trapezoidal 적분을 사용한다.
상대값의 분모는 fine run의 같은 질량·시간 RMS 속도다. 193.25%는 변위 비율이나 발산 판정이 아니다.
공간 wind의 속도 관측 order는 -1.3586(`not_decreasing`), 시간 wind는 1.0832다.
Free decay는 2단계 smoke만 있어 관측 order가 없다. 시간 velocity 차이가 줄어도 band PSD 차이는
두 대역 모두 `not_decreasing`이며, velocity 하나로 spectrum 수렴을 인정하지 않는다.
0.2초 구간의 FFT bin 간격은 5 Hz이고 대역은 [0,15), [15,30] Hz다. 장기·대역 수렴과 peak 판정은 미완료다.

## Bending에 대한 추가 관찰

Free-decay mesh 4/8의 초기 probe 변위는 같고 quadratic mapping noise는 0이다.
동일 analytic field의 float32 실현·sampling 최대 오차는 두 경우 모두 2.2352e-10m다.
따라서 이 fixture의 큰 응답 차이를 초기 probe 입력 불일치로 설명하기는 어렵다.

Newton 1.3.0의 `newton/_src/solvers/vbd/particle_vbd_kernels.py`에 있는
`evaluate_dihedral_angle_based_bending_force_hessian`은 `k=stiffness*edge_rest_length`와
`dE_dtheta=k*(theta-rest_angle)`을 사용한다. Flat authored rest의 내부 edge에 대해
`E_b = 0.5 * edge_ke * sum(rest_edge_length * theta²)`를 기존 초기 위치로 계산하면 다음과 같다.

| 초기 상태 | Native bending 에너지 (J) |
| --- | ---: |
| decay mesh 4 | 0.00037491087518633757 |
| decay mesh 8 | 0.00021869502819702775 |

Mesh 8/4 에너지 비율은 약 0.583325다. 이는 membrane을 제외한 bending 항의 **기하학적 읽기 전용 계산**이며,
Newton 내부 에너지 측정이나 동역학 응답 차이의 인과 증명은 아니다. Mesh 의존성 감사의 동기이며,
계수 자동 보정이나 최종 물성 결정으로 승격하지 않는다.

## 읽기 전용 재검증 명령

다음은 workspace root에서 실행하며 기존 GPU run을 다시 simulation하지 않는다.
첫 블록은 원본 inventory/source hash와 비교 결과를 대조한다. 원본이 없으면 실패한다.

```bash
PYTHONPATH=code .venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path
from wind3dgs.evaluation import TeacherConvergenceReport, TeacherRefinementRun

evidence = Path('experiments/R1_teacher_smoke')
inventory = json.loads((evidence / 'artifact_inventory.json').read_text())
root = Path(inventory['artifact_root'])
actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
assert actual == set(inventory['files'])
for name, item in inventory['files'].items():
    data = (root / name).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
env = json.loads((root / 'environment.json').read_text())
for name, expected in env['sources_sha256'].items():
    assert hashlib.sha256((Path('code') / name).read_bytes()).hexdigest() == expected
for axis in ('spatial', 'temporal', 'decay_spatial'):
    path = root / 'comparisons' / axis
    metadata = json.loads((path / 'report.json').read_text())
    runs = [TeacherRefinementRun(level['level_id'],
            root / 'runs' / level['level_id'] / 'raw',
            root / 'runs' / level['level_id'] / 'probe') for level in metadata['levels']]
    report = TeacherConvergenceReport.open(path, runs=runs)
    assert report.source_verified
    print(axis, report.report_hash)
print('원본 inventory, 실행 source와 비교 결과 검증 통과')
PY
```

다음은 보존한 flat-rest fixture에 한정한 bending 관찰 재현이다. 내부 edge의 두 face 단위 법선 사이
각도를 float64로 계산한다. Authored rest angle은 0이며 각도 부호는 제곱 에너지에 영향을 주지 않는다.
새 bending 감사 기능이나 arbitrary shell의 에너지 API를 대신하지 않는다.

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import numpy as np

root = Path('experiments/artifacts/runs/teacher_gpu_check/20260907_042524_687651/runs')
for resolution in (4, 8):
    raw = root / f'decay_mesh{resolution}_sub4' / 'raw'
    with np.load(raw / 'mesh.npz', allow_pickle=False) as data:
        rest = data['rest_positions_m'].astype(np.float64)
        faces = data['faces']
    with np.load(raw / 'initial.npz', allow_pickle=False) as data:
        q = data['positions_m'].astype(np.float64)
    normals = np.cross(q[faces[:, 1]] - q[faces[:, 0]], q[faces[:, 2]] - q[faces[:, 0]])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    neighbors = {}
    for index, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            neighbors.setdefault(tuple(sorted((int(a), int(b)))), []).append(index)
    energy = 0.0
    for (a, b), adjacent in neighbors.items():
        if len(adjacent) != 2:
            continue
        n1, n2 = normals[adjacent]
        angle = np.arctan2(np.linalg.norm(np.cross(n1, n2)), np.dot(n1, n2))
        energy += 0.5 * 10.0 * np.linalg.norm(rest[b] - rest[a]) * angle**2
    print(resolution, energy, 'J')
PY
```

## 남은 문제와 다음 제안

- Native bending/material의 mesh 의존성 확인이 우선이다. 이어서 solver iteration, temporal timestep,
  spatial mesh를 분리해 검증하고 필요한 공력 sampling·장기 run도 확인한다.
- Threshold, accepted mesh/timestep/iterations, material/damping 대응, spectral window/band는 미확정이다.
  현재 결과는 개발 진단으로 보존하고 최종 acceptance 설정은 별도로 사전 동결한다.
- GS common-valid mask/mapping noise와 oracle/transport, source-object split과 품질 gate를 정한 뒤
  학습 데이터 pilot을 발행한다.
- 다음 bending 감사 기능은 제안 상태이며 아직 구현하거나 새 실험을 실행하지 않았다.

검토와 Git 정리 이력: [2026-09-07 실험 session](../sessions/2026-09-07_01_teacher_gpu_check_review.md).
