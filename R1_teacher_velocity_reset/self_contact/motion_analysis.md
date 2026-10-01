# 저장 궤적의 처짐·움직임 분석과 공통 표면 매핑

## 현재 상태

- 확인일2026-09-28. 사용자 요청 명령 `analyze_gpu_v13_sub.sh`로 서브 RTX5070 v13 세 씬을 CPU 재분석했다.
- 세 씬 각600프레임·600개 진행 상태/초기 포함601개 상태의 입력 hash·구간 연결·외력·시간·저장 검산을 확인했다.
- [완료 v13 분석과 해석](three_scenes_gpu_v13.md#완료-v13-재분석)에 처짐·무풍 후반 움직임·사각형 복구466개와 한계를 정리했다.
- [새 HTML 보고서](../../artifacts/runs/p3_self_contact/motion_analysis/v13_sub_20260928T103705982406210Z/index.html)와 [재분석 증거 JSON](motion_analysis_v13_checks.json)을 생성했다. 이전 분석과 원본을 보존했다.
- 사각형·삼각형의 처짐과 잔운동이 모두 남는다. 완료/저장 검산 확인을 자연스러운 천 움직임이나 학습 적격성으로 승격하지 않는다.
- 이번에는 분석기·solver를 수정하거나 GPU 시뮬레이션을 실행하지 않았다. 실제 물리 잔차/CCD의 재계산도 아니다.
- 기존 CPU 분석기13개 검사·공통 매핑 검증은 당시 구현 기록이다. 이번 검증은 실결과 분석과 산출물31개 hash 확인이다.
- 공통512점 비교기는 준비됐지만 실제 두 정밀도/메시 민감도 비교·GS 전달·학습은 미완료다.
- 다음은 [짧은 감쇠 비교 샘플](damping_sample.md#현재-상태)의 사용자 실행·시각 비교다. 기존 v12 근거는 [당시 compact JSON](motion_analysis_v12_checks.json)에 보존한다.

## 실행 명령

완료된 원본은 읽기만 하며 `--out`은 원본 run 밖의 **존재하지 않는 새 경로**여야 한다.
실패/진행 중 결과는 전체 분석으로 승인하지 않고 새 출력의 report에 거절 사유를 남긴다.
일부 씬이 거절되면 요청한 씬 목록과 각각의 상태를 보존하며 전체 report는 incomplete다.

```bash
# 기본 원본은 완료된 v12. 이 예시 출력은 이번에 이미 생성했다.
bash experiments/R1_teacher_velocity_reset/self_contact/analyze_gpu_motion.sh \
  --out experiments/artifacts/runs/p3_self_contact/motion_analysis/v12_20260928_01

# 입력만 동결됐으면 공통점/map 준비 가능. 이 예시 출력은 아직 만들지 않았다.
bash experiments/R1_teacher_velocity_reset/self_contact/prepare_gpu_surface_samples.sh \
  --run experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_drape_v13 \
  --out experiments/artifacts/runs/p3_self_contact/motion_analysis/v13_maps_01

# 사용자 실행이 실제 완료된 뒤 사용. --run은 실제 결과가 있는 경로로 지정한다.
bash experiments/R1_teacher_velocity_reset/self_contact/analyze_gpu_motion.sh \
  --run <완료된_v13_run_경로> \
  --out experiments/artifacts/runs/p3_self_contact/motion_analysis/v13_01
```

서브 컴 결과가 `artifacts/runs/sub_pc/.../simulation`에 있다면 그 실제 경로를 `--run`에 넘긴다.
로컬 준비 묶음에 서브 컴 결과가 자동 복사됐다고 가정하지 않는다.
`--shape reference_rectangle` 등으로 한 씬만 선택할 수 있다. 기본은 세 씬이며
CPU 스레드1로 실행한다. GPU·solver·새 시뮬레이션·외부 다운로드를 호출하지 않는다.
출력이 이미 있으면 덮어쓰지 않으므로 재실행할 때 새 출력 이름을 사용한다.

## 출력과 지표 의미

| 출력 | 내용 |
| --- | --- |
| `index.html` | 세 씬 분석 화면과 상세 JSON/CSV 링크 |
| `report.json` | 원본 hash, 요청 씬·실패 분모, 구현 hash, 산출물 hash, 분석 상태 |
| `<shape>/report.json` | phase별 통계·마지막1초 움직임·매핑 식별·복구 횟수 |
| `<shape>/metrics.csv` | 전체 시각별 처짐·속도·비평면성·고정점 오차 |
| `<shape>/motion.png`, `calm.png` | 전체 시간과 무풍 구간 확대 곡선 |
| `<shape>/snapshots.png`, `snapshots.npz` | 시작·preload 끝·calm 끝·wind 중간·끝의 메시와 고정 카메라3방향 |
| `<shape>/samples.npz` | 601시각×512점의 FP64 위치/변위/저장 속도, 기준 위치·면적 가중치·외력·경계점 |
| `<shape>/mapping/` | `points.npz`, `surface_map.npz`, `boundary_map.npz` |

아래 지표는 **rest 면적 가중**의512점 표본 통계이며 실제 연속 표면 극값/정확한 질량 중심을 주장하지 않는다.

- 처짐: 평균 Z 감소를 양수로 표시한다. 평면 rest 대비와 실제 시작 모양 대비를 둘 다 기록한다.
- 평면 밖 거리: rest 평면까지 거리의 RMS다. 강체 회전·평행 이동도 포함한다.
- 비평면성: 매 시각 가장 잘 맞는 평면까지 거리의 RMS다. 평평한 천의 강체 회전을 굽힘으로 세지 않는다.
- 속도: raw `v_hi+v_lo`를 동일한 P3 map으로 옮긴 RMS다. 프레임 위치 차분으로 대체하지 않는다.
- 마지막1초 위치 변화: 그 구간의 시간 평균 모양 주위 RMS다. 진동과 느린 이동을 모두 포함하므로 자동 안정화 판정이 아니다.
- 고정점: 원본 모든 고정 DOF의 변위/속도 최대를 별도로 기록한다. 표면512점 분모에 끼워 넣지 않는다.

위치·속도 단위는 m/m·s⁻¹, 면적 가중치는 m²다. Material 좌표는 기존 P3의 `(x, 0.5-z)`다.
FP32 뷰어 캐시 대신 원본 FP64 hi/lo를 합산해 분석한다. `samples.npz`의 시각0 외력 행은
placeholder0이고 `frame_force_valid=False`다. 이후 외력 행은 저장된 프레임 입력이다.
스냅샷은 P3 노드의 표시용 삼각분할이며 엄밀한 연속 표면/접촉 검산이 아니다.

## 공통 표면512점

사각형·손수건은 rest 바운딩 박스의32×16 cell 중심을 사용한다. 삼각형은 같은 정규 격자를
세 꼭짓점으로 정의한 삼각형에 면적 보존 변환한다. 가중치는 모두 양수이고 합은 기준 면적이다.
이것은 고정된 표면 표본 규칙이며 정확한 적분 구적법이라는 주장은 아니다.
기하 크기가 같은 서로 다른 메시에서 ordered material 좌표·면적 가중치와 `probe_hash`가 같다.

각 점이 포함된 **원래 삼각형**을 찾아10개 signed P3 shape 값을 쓴다. 보간 계수의 음수를 자르거나
최근접 노드로 대체하지 않는다. 원래 표면 밖의 점·비유한 값·constant/affine 재현 실패는 거절하며
유효점만 남겨512점 분모를 줄이지 않는다. 공유 변에서는 결정적인 첫 요소를 고른다.
모서리 꼭짓점·변 중간점과 원본 고정 노드 ID는 보조 데이터로 별도 저장한다.

`mapping_hash`는 메시마다 달라지고 `probe_hash`는 같은 표면에서 동일하다.
이 map은 표면 위치/속도용이며 GS covariance/SPD·proper rotation·힘/일 전달 검사는 포함하지 않는다.

## 구현과 검증

재사용 구현은 [매핑](../../../code/wind3dgs/evaluation/p3_common_surface.py)의
`common_points` / `interpolation_map`, [원본 읽기](../../../code/wind3dgs/evaluation/gpu_contact_recording_io.py)의
`bundle` / `load_completed`, [분석](../../../code/wind3dgs/evaluation/analyze_gpu_contact_recording.py)의
`motion_metrics` / `phase_summary` / `analyze_shape`가 소유한다.

1. CPU 검사13개 통과: 세 씬4/8 해상도의 동일 표본·삼차장 재현, 기존 사각형 map과 대조,
   바깥 점 거절, 해석 가능한 이동/회전 지표, 속도 단위, bent 시작 상태, 전체 연속 시간,
   timestamp/상태 경계/검산 flag/hash 오류·미완료 결과 거절, 출력 보존을 확인했다.
2. v12 실제 세 씬의 각600프레임/601상태·512점을 분석했다. 전체 요청 분모3씬/1,800프레임,
   사각형 복구/폐기113개와 다른 씬0개를 보존했다. 원본 manifest 전체·모델 코드·raw 상태/시간/외력·
   phase 경계·저장 승인 flag와 폐기 증거 hash를 확인했다. 물리 잔차나 CCD를 다시 계산한 것은 아니다.
3. 대표 사각형의 생성된3방향 스냅샷을 열어 배치·시간·고정점 표시를 확인했다.
   전체 궤적의 사용자 시각 통과를 대신하지 않는다.
4. [사각형16/32 정적 map 근거](../../artifacts/runs/p3_self_contact/motion_analysis/mapping_16_32_20260928_01/report.json)의
   `maps`는1813/7081노드에서 같은512점과 삼차장 최대 오차4.44e−16을 확인한다.
   이는 **정적 보간 검증**이고16/32 시뮬레이션이나 계획된16/24 민감도 비교가 아니다.
5. 최초16/24 확인에서는 [24 생성 거절 기록](../../artifacts/runs/p3_self_contact/motion_analysis/mapping_16_24_20260928_01/report.json)을 남겼다.
   `rectangular_mesh`가4/8/16/32만 허용한다. 기존 코드·동결 실행은 유지했으며 계획24는 runner 구현 때 지원·검증이 필요하다.

## v12 관찰 수치

| 씬 | calm 끝 평균 처짐 (mm, 시작 대비) | calm 마지막1초 RMS 속력 (m/s) |
| --- | ---: | ---: |
| 사각형 | 0.07238 | 5.37e−5 |
| 손수건 | 0.05231 | 1.22e−5 |
| 삼각 깃발 | 0.10263 | 5.07e−5 |

이는 표면 면적 가중 평균 처짐이다. 앞선 v12 노드 변위 RMS와 정의가 다르므로 숫자를 동일시하지 않는다.
무풍 중 시각 변화가 매우 작다는 관찰과 부합하지만 v13의 처짐·완주를 예측하거나 승인하지 않는다.

## 남은 작업

v13 완료 후 실제 결과 경로로 분석·시각 확인한다. 이 분석은 다른 초기 상태의 v12/v13을
수렴 비교로 묶거나 자동 학습 적격으로 바꾸지 않는다. CG 계획의 T/S 입력·비교기·예산 실행기,
24 해상도 지원, GS 매핑과 작은 network-free 응답 검사는 후속 작업이다.
R1의 공통 매핑 부분 구현만 동기화하며 정식 Gate·수치 허용량·학습 승인 상태는 유지한다.
