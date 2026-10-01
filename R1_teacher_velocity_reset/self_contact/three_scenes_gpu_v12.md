# GPU 세 씬 v12 연속 10초

## 현재 상태

2026-09-28 후속: 무풍 처짐 시각 개선을 위해 [v13 초기 굽힘·1/4/5초](three_scenes_gpu_v13.md#현재-상태)를 별도로 준비했다. v12 원본과 아래 완주 근거는 당시 설정으로 보존하며 v13로 승계하지 않는다.

2026-09-28 저장 원본 분석: GTX1080Ti에서 사각형·손수건·삼각 깃발 모두
preload 2초(120프레임) → calm 4초(240프레임) → wind 4초(240프레임),
60Hz 연속10초·각600프레임을 완료했다. 사각형 wind는113프레임을 GPU dt/2로 복구했고
손수건·삼각 깃발은 복구0회다. 사각형의 기본 dt 최초 실패113회는 성공 분모와 함께 보존한다.
manifest296개 파일, 채택 프레임1,800개, 복구 증거113개와 여섯 raw hi/lo 구간 연결을
대조했고 불일치0건이다. 채택122,432 substep의 저장 검산 flags는 모두0이다.
이는 실행 중 검산 기록의 사후 무결성 확인이며 이번 분석에서 물리 잔차·CCD를 재계산하지 않았다.
[완주·검산·복구·비용과 원본 위치](#v12-사용자-실행-결과),
[사후 검사 근거 JSON](three_scenes_gpu_v12_audit.json)의 `scenes`, `issues`를 따른다.
연속10초 뷰어를 연결하고 실제 세 씬 표시를 확인했다. [실행·조작·표시 검증](#연속10초-뷰어).
미완료: 전체 궤적의 사용자 시각 판정, RTX5070 v12, 시간·공간 수렴·접촉 응답 검증과 학습 적격성.
후속 기준은 [CG 개발용 민감도·스크립트 계획](cg_development_checks.md#현재-상태)으로 확정했다.
이번 v12는 새 민감도·학습 진입 조건의 통과 전이며 추가 계산은 사용자가 직접 실행한다.

## 실행

프로젝트 루트에서 세 씬을 GPU 순차 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
```

이 명령으로 만든 현재 로컬 결과는 완료됐다. 새 환경에서는 먼저 같은 스크립트의 `--action prepare`를 실행한다.
상태 확인은 `--action status`다. 기존 출력은 덮어쓰지 않으며 재실행은 새 `--out`으로 준비해야 한다.

실행 묶음: [v12 suite.json](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/suite.json).
`trajectory_mode=serial`, `phase_start_s={preload:0,calm:2,wind:6}`,
`retry_newton_limit=true`가 동결됐다.
[manifest](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/manifest.json) SHA256:
`0be6397195b505b314fa8b8913aa41b28c2249593f366ea2c05529f5536c994e`.

## 연결과 복구 계약

- preload 끝 raw hi/lo 위치·속도 → calm 초기 상태 → calm 끝 상태 → wind 초기 상태.
  속도 초기화 없이 전달하며 앞 phase 실패 시 뒤 phase는 시작하지 않는다.
- 원본 물성·외력 배열·dt·허용오차는 유지한다. wind의 기존 바람 ramp는 전체 시간6초부터 시작한다.
  calm에도 움직이는 천의 공기 저항은 남는다. 기존 v11 wind와 초기 상태가 다르므로
  과거 실패 프레임이나 완주 결과를 새 궤적에 그대로 승계할 수 없다.
- 유한한 code1/code2와 기존 접촉·시간축·prefix 검사 조건을 만족한 경우에만
  프레임 시작에서 GPU dt/2 한 번 재시도한다. 실패 증거 보존·독립 검산·rollback은 유지한다.
  swept 후보2M 및 cuDSS 결정성1도 유지한다.
- 프레임 NPZ의 `phase_time_s`는 구간 시간, `trajectory_time_s`는 전체 시간이다.
  phase report의 `phase_start_s`와 `trajectory_mode`도 기록한다.
- 기존 v11 bundle·결과·6초 표시용 뷰어는 변경하지 않았다. 기존 뷰어를 v12의
  10초 뷰어로 간주하면 안 된다. 후속 v12 전용 연결은 [연속10초 뷰어](#연속10초-뷰어)를 따른다.

## 검증과 한계

현재 구현 보존 revision은 code commit `a5e4d8e`다. 이미 준비한 v12의 실제 실행 소스는
위 manifest의 runtime 파일 hash가 식별하며 후속 commit ID로 대체하지 않는다.

2026-09-27 commit 전 진단·CPU 동결·뷰어·실행기 관련 회귀33개가 통과했다.
GPU 본 실행이나 체크포인트 재생을 추가로 수행하지 않았다.

실행기 단위 검사8개 통과: 준비/hash, 순차 hi/lo 전달, preload/calm 실패 중단,
복구 옵션 전달, 전체 시간 기록, 실패 증거 보존 등.
세 씬의 동결 입력120/240/240프레임과 phase 시작0/2/6초 및 총10초를 확인했고
manifest 검증과 셸 구문 검사를 통과했다. 당시에는 GPU 본 실행·장기 완주를 검증하지 않았으며,
2026-09-28 GTX1080Ti 완주 결과는 아래에 별도로 기록한다.
code1 복구의 이전 단일 프레임 GPU 근거는
[v11 사각형 진단](three_scenes_gpu_v11.md#사각형-wind-code1-dt2-격리-진단)에 있다.

## v12 사용자 실행 결과

### 식별과 재현

2026-09-28 분석 대상은 위 manifest SHA256의 로컬 v12 실행이며 모든 phase의 장치명은
`NVIDIA GeForce GTX 1080 Ti`다. 세 씬 모두 `status=complete`,
`full_trajectory_verified=true`; `training_eligible=false`, `production_enabled=false`를 유지한다.
후속 commit이나 v11 결과를 v12 실행 근거로 대체하지 않는다. 관련 실행 프로세스는 종료됐다.

- [사각형 원본 report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/reference_rectangle/outputs/report.json)의 `phases`, `elapsed_s`;
  [wind report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/reference_rectangle/outputs/wind/report.json)의 `frames[].recovery`, `stage_timings`.
- [손수건 원본 report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/handkerchief/outputs/report.json)의 `phases`, `elapsed_s`;
  [wind report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/handkerchief/outputs/wind/report.json)의 `frames`.
- [삼각 깃발 원본 report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/triangular_flag/outputs/report.json)의 `phases`, `elapsed_s`;
  [wind report](../../artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12/triangular_flag/outputs/wind/report.json)의 `frames`.
- [작은 사후 분석 근거](three_scenes_gpu_v12_audit.json): `scenes.<shape>.phases.<phase>`에
  원본 report/checkpoint SHA256, 복구113개의 frame·원인·원본 증거 hash와 전체 통계;
  `issues=[]`, `passed=true`는 아래 사후 검사 범위에만 적용한다.
- [전체 분석 JSON](../../artifacts/analysis/p3_self_contact/v12_20260928/audit.json)의 `series`에는
  60Hz 상태 요약과 비용 추세가 있다. [추세 그래프](../../artifacts/analysis/p3_self_contact/v12_20260928/summary.png)는
  노드 단순 RMS 변위·속도, 힘 잔차 비율, 프레임 계산+검산 시간을 나타낸다.
  RMS는 면적/질량 가중 물리 metric이 아니며 메시 간 수렴 판정에 사용하지 않는다.

[분석 스크립트](../../artifacts/analysis/p3_self_contact/v12_20260928/audit_saved_results.py)는
NumPy로 저장 파일만 읽고 GPU를 사용하지 않는다. 새 JSON 경로를 지정해 재현한다.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  experiments/artifacts/analysis/p3_self_contact/v12_20260928/audit_saved_results.py \
  experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v12 \
  /tmp/wind_v12_audit_recheck.json
```

### 완주와 사후 검산

| 씬 | preload/calm/wind 승인 | dt/2 복구 | 채택 substep | 전체 elapsed |
| --- | --- | ---: | ---: | ---: |
| 사각형 | 120/120 · 240/240 · 240/240 | 113 | 45,632 | 6,596.45초 (109.94분) |
| 손수건 | 120/120 · 240/240 · 240/240 | 0 | 38,400 | 1,131.98초 (18.87분) |
| 삼각 깃발 | 120/120 · 240/240 · 240/240 | 0 | 38,400 | 3,862.99초 (64.38분) |

- 총1,800/1,800프레임·9/9 phase 완료. 미복구 실패0회, 기본 dt의 폐기 시도113회다.
  채택122,432 substep과 폐기113개 증거를 구분하며 폐기 시도를 성공 단계로 합산하지 않는다.
- 동결296개 파일, 모든 채택 frame과 initial/checkpoint 및 폐기 증거의 SHA256을 대조했다.
  누락/추가 frame·pending·실패 tail 없음. 원본 report/frame 요약도 일치한다.
- preload→calm와 calm→wind의 여섯 경계 모두 네 raw hi/lo 배열이 byte 단위로 같다.
  checkpoint와 다음 initial NPZ의 SHA256도 같다. 경계 속도는0이 아니며 그대로 전달됐다.
- 모든 frame의 `phase_time_s`, `trajectory_time_s`, 동결 중력/바람 배열,
  `dt * substeps = 1/60초`를 대조했다. 마지막 전체 시간은 각10초다.
- 채택 flags는 모두0, frame의 solver/contact/path/mass 오류0, 모든 저장 배열은 유한하다.
  복구 전 승인 prefix의 flags도0이며 최초 오류의 유한성·접촉·시간축 조건을 확인했다.

| 씬 | 최대 힘 잔차/허용량 (한도1) | 최소 국소 면적비 하한 | wind 최대 노드 변위 | wind 최대 노드 속력 |
| --- | ---: | ---: | ---: | ---: |
| 사각형 | 0.299919 | 0.279093 | 1.31672m | 9.72525m/s |
| 손수건 | 0.299921 | 0.980540 | 0.391514m | 2.40336m/s |
| 삼각 깃발 | 0.299974 | 0.475955 | 1.78081m | 12.4287m/s |

국소 면적비 하한은 퇴화하지 않았다는 충분조건의 하한이며 실제 최소 면적이나 허용 변형률이 아니다.
모든 채택 단계는 추가 공간/시간 기하 분할 없이 통과했다(`refined_substeps=0`).
위치 coupling 최대 오차는1.589e-18m(검사 한도2e-14m), 에너지 ledger의 두 검산값 간
최대 차이는2.776e-17J다. 후자는 에너지 drift나 물리 해 정확도 수치가 아니다.

### 사각형의 복구와 남은 부담

wind240프레임 중113개(47.08%)가 기본 dt에서 실패한 뒤 같은 프레임 시작 상태·외력으로
한 번의 dt/2·128 substep 재계산을 통과했다. Code2 선형 실패111개,
code1 Newton15회 한도2개(표시 wind158·170, 0-based157·169)다.
최초 복구는 표시 wind118, 전체7.9500–7.9667초다.
복구한 표시 프레임은118,122–131,133–137,139–146,148–152,154–155,157–158,
160–165,167–240이며 마지막74프레임은 모두 복구했다.
원본113개 `frame_XXXX_discarded.npz`를 유지했다. 미완료 tail의 flag14를
승인 prefix 오류나 최종 채택 상태의 실패로 집계하지 않는다.

따라서 이번 GTX1080Ti 궤적에서 code1/code2 복구와 연속 완주는 확인됐지만,
기본 dt만으로 전체 구간을 안정적으로 통과했다고 주장하지 않는다.
잦은 복구가 시간 정확도나 적정 기본 dt를 증명하지도 않는다. 재검토는 동일 초기 상태·
물리·외력의 시간 수렴 비교와 사전 계산 예산 확정 후 진행한다. 자동 설정 변경은 하지 않았다.

### 실제 비용과 해석

| 씬 | preload / calm / wind elapsed (초) | wind 계산+검산 중앙값 / p95 / 최대 (초/프레임) | wind collision 비율 |
| --- | --- | --- | ---: |
| 사각형 | 298.40 / 542.27 / 5740.80 | 16.51 / 73.64 / 107.64 | 4.00% |
| 손수건 | 185.82 / 361.36 / 582.46 | 2.20 / 3.55 / 3.88 | 14.42% |
| 삼각 깃발 | 175.59 / 346.08 / 3339.34 | 12.77 / 30.01 / 41.94 | 4.41% |

씬 report elapsed 합계는11,591.42초(약3시간13분11초)다. Setup·저장과 실패 시도 비용을
포함하는 각 씬의 wall이며 worker 시작 등 전체 셸 실행 시간을 별도로 측정한 것은 아니다.
프레임 통계는 `frame_wall_s`, collision 비율은 같은 phase의 `collision_s` 합계를
프레임 wall 합계로 나눈 값이다. Solver/audit inclusive와 collision은 중첩되므로 합산하지 않는다.

사각형 wind의 폐기된 기본 dt 시도만1,671.98초(27.87분; wind 프레임 wall의29.18%)다.
복구 재계산1,112.80초도 총시간에 포함된다. 사각형·삼각 깃발의 wind solver inclusive는
각97.75%·98.37%, 접촉을 제외한 solver 부분은 각94.39%·94.42%다.
이번 계측에서 직접적인 collision kernel 시간이 주된 비용은 아니지만 접촉 결합이
Newton/선형 풀이 난도에 미친 간접 영향까지 분리한 결과는 아니다.
반복/유휴 조건 대조를 새로 실행하지 않았으며, v11 대비 가속이나 장치 간 성능을 주장하지 않는다.

### 완료 범위와 다음 작업

GTX1080Ti에서 v12 세 씬의 연속 완주와 저장 검산 무결성을 확인했다. 이 결과는
v11 분기 실패를 소급 해결한 것이 아니며 RTX5070 v12의 직접 근거도 아니다.
접촉 검산은 고정 선형 proxy와 채택 quadratic 시간 경로 계약의 범위다.
실제 최소 접촉 간격·활성 접촉 개수는 이 frame 저장 형식에서 독립 집계하지 못했고,
원래 P3 곡면의 전역 비접촉·접촉 응답 공간 수렴은 미완료다.
시각 확인, 전체 궤적 시간/공간 수렴, GS 매핑·oracle·R1 학습 적격성은 승격하지 않는다.

다음은 [채택된 CG 개발용 스크립트 순서](cg_development_checks.md#스크립트-단위-구현과-사용-순서)의
v12 뷰어 연결·시각 확인과 대표 사각형 두 해상도 민감도 검사다.
새 시뮬레이션·추가 최적화의 실행 승인은 아니다. R1에는
[GPU 접촉 개발 근거](../../../ideas/development/r1_teacher_probe_oracle.tex)의
`sec:r1-gpu-self-contact`, `sec:r1-v12-completion`으로 결과 범위만 반영한다.

## 연속10초 뷰어

2026-09-28 사용자 요청으로 [v12 전용 셸](view_gpu_v12.sh)을 연결했다.
사각형·손수건·삼각 깃발의 preload→calm→wind를 같은0–10초 타임라인으로 나란히 표시한다.
명령은 프로젝트 root에서 실행하며 처음에는 정지 상태다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v12.sh
# 사각형만, 바람 구간부터 확인
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v12.sh --shape reference_rectangle --time 6
# 창을 열지 않고 표시 캐시만 검증·준비
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v12.sh --prepare-only
```

Space 재생/정지, Time 슬라이더로0–10초 이동, Playback speed 조절,
마우스 왼쪽 드래그 회전·휠 확대를 지원한다. 파랑 사각형·주황 손수건·초록 삼각 깃발이며
Fixed points로 고정점 표시를 켜고 끈다. UI에 preload0–2/calm2–6/wind6–10 구간을 표시한다.
세 씬 배치는 전체 저장 궤적의 표시 범위를 기준으로 잡고 실제 물체 크기는 유지한다.

모델 입력/코드·suite·frame/report/checkpoint hash, 완료·승인 상태, raw hi/lo 상태 연결과
`phase_time_s`/`trajectory_time_s`를 확인해 별도 float32 캐시를 만든다.
모든 씬은 초기 상태1개+600프레임으로601개 표시 시각을 가지며 끝은10초다.
기존 v11의 preload→분기 동작을 유지하고, 기본 캐시는 source와 뷰어 코드 버전별 새 경로로 분리한다.
기존 결과·캐시를 덮어쓰지 않으며 `--cache`로 지정한 경로의 불일치/미완료 캐시는 오류로 보존한다.

검증: 뷰어 관련 CPU 검사15개 통과(v11 호환, v12 세 씬/사각형, 상태 연결, 속도 초기화·시간 오류·
원본 변조 거절 포함), 셸 구문 통과. 실제 세 씬 각600프레임 캐시 준비 및8.5초 headless1프레임 표시 성공.
[검증 report](../../artifacts/runs/shell_playback/p3_self_contact_v12/verification_20260928/report.json)의
`scenes`에 캐시 경로·manifest hash·반올림 오차, `headless`에 표시 조건을 기록했다.
[8.5초 확인 이미지](../../artifacts/runs/shell_playback/p3_self_contact_v12/verification_20260928/wind_8p5.png)에서 세 메시가 잘리지 않고 표시됨을 확인했다.
표시 반올림 최대 오차는 사각형5.9602e-8m·손수건2.9803e-8m·삼각 깃발5.9594e-8m 미만이다.

첫 PNG 저장은 준비 명령에 시스템 Python을 사용해 폴더 생성이 실패한 탓에 거절됐으며,
프로젝트 환경으로 폴더를 준비한 뒤 동일 표시 검사가 성공했다. WSL의 CUDA/OpenGL interop 경고는
copy 표시 경로로 처리됐고 화면 출력이 확인됐다. 이전 Warp 캐시는 삭제하지 않았다.
표시는 P3 계산점을 잇는 삼각형과60Hz 경계 상태이며3DGS/물리 재계산/내부 substep 표시가 아니다.
뷰어 동작 확인은 전체 궤적의 시각 품질이나 CG 학습 진입 판정을 대신하지 않는다.
