# 저해상도 세 메시의 굽힘 강성 비교

[두 GPU launch/정밀도 비교](dual_gpu_launch.md): 현행 풀이 유지, 각 PC 사용자 실행용 block sweep/cache/기존 FP32 fixed-work와 결과 취합.

[Teacher 성능 진단 실행](teacher_precision_profiling.md): 같은 checkpoint3회·별도 Nsight Systems. RTX 5070에서 사용자 직접 실행, 상위 연산 정밀도 비교는 후속.

[수렴 실패 시 Gauss6차8분할 재시도](newmark_gauss_retry.md): 현행 retry 스크립트, 실제 실패2프레임 복구와 세 씬 smoke 통과. 본 실행 미시작.

[Newmark 고정 dt / 수렴 실패 시 절반 dt 세 씬 비교](newmark_dt_suite.md): 로컬 실행 스크립트2개·본6개 설정 준비, 실제 실패 복구와 짧은 저장 검증 완료. 본 실행 미시작.

[기하 경고만 전환하는 재시험](geometry_switch_trial.md): 추가128분할 감시 없이 기존 검사와 조건부 재계산의 비용 비교.

[Newmark 우선·Gauss 재계산 비교](integrator_switch_trial.md): FP64 hi/lo 유지, 시간 분할 차이·물리 검산과 원상 복원 재계산의 실제 비용 비교.

[행·열 스케일링과 FP64 보정 비교](gauss_scaling_trial.md): FP32 단독 스케일링과 엄격한 FP64 잔차 보정의 비용·정확도 분리 시험.

[Gauss FP32 hi/lo 개발 비교](gauss_fp32_trial.md): 같은 실제 한 프레임의 정밀도·허용오차 대조와 원래 FP64 검산. 기본값 변경과 학습 채택은 별도다.

[Gauss6차·8분할·1/500 세 씬 실행](gauss6_bend500_three_scenes.md): 씬별/서브컴 독립 스크립트, 중력·무풍·바람 및60Hz 재생 기록.

[타임스텝과 수렴 비용 비교](gauss_timestep_sweep.md): 동일 구간24개 GPU 계산·검산 통과. Newmark는 dt절반에서 총 비용 감소, 속도 최소와 학습 정확도는 별도 판정.

[GPU Gauss6차·기존 솔버·세분 Newmark 비교](gauss_gpu_comparison.md): 1/500 깃발의두 국소 상태에서 GPU 적분/독립 검산 및 속도·정확도 대조 완료. 기본 FP64 hi/lo Newmark와 학습 Gate는 유지한다.

[중력 처짐 후 주름 비교](gravity_wrinkles.md): 손수건1/100에 중력 ramp 포함2초 처짐 준비 후,
속도를 유지한 동일 checkpoint에서 무풍/바람 각각4초로 나누는 초기 준비 문서다. 이후 깃발 실행과 확정 결과는 [구현·실험 인계](../../../sessions/2026-09-13_09_gravity_wrinkles.md)에서 찾는다.

2026-09-13에는 FP64 hi/lo로 고정했다. 2026-09-15 사용자 요청으로 별도 FP32 진단을 재개했으며 기본 솔버는 유지한다.
[국소 기하 검사 구현·샘플 통과](local_geometry_validation.md): 명시적 `local_metric` 옵션으로 적용 가능하다.
기존 strict 기본값은 보존하며 자기 교차 탐지/응답은 아직 별도 작업이다.
[10초 기하 경고 분석과 해결안](geometry_diagnosis.md): 초기 평면 투영 충분조건의 큰 회전 한계와
대표 상태의 실제 교차 표본 검사를 구분했다. strict/학습 Gate는 유지한다.

후속 [FP64 보정1/100·4초 실행과 자동 비교](../precision_compare/refine64_4s.md)는 별도 스크립트를 사용한다.
기존 실행·기본 strict 설정을 보존하며 정밀도 진단 결과를 별도 출력한다.

## 완료된 서브컴10초 결과 재생

`view_cloth_coarse_10s.sh`는 완료된 서브컴 run
`artifacts/runs/sub_pc/20260912T223433Z-aca6fc4223714a02a9fe8afe7f4edeef`를 기본으로 연다.
생성 스크립트의 메인컴 기본 출력 경로와 구분한다. 물리 재계산 없이 동결 뷰어를 사용하며,
2026-09-22 정리에서 3조건×3메시의 표시 cache를 모두 생성·검증하고 raw substep chunk를 제거했다.
캐시는 해당 run의 `playback/`에 있고 source report와 cache 파일 hash를 유지한다. 뷰어는 이 cache만 읽으며,
cache를 잃으면 남은 report에서 복구할 수 없으므로 아래 생성 스크립트로 새 output을 다시 계산해야 한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse_10s.sh bend_001 --shape handkerchief
bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse_10s.sh bend_010 --shape triangular_flag
bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse_10s.sh baseline
```

조건은 `baseline`, `bend_010`, `bend_001`, 메시는 `reference_rectangle`, `triangular_flag`,
`handkerchief` 중 선택한다. 메시 생략 또는 `both`는 직사각형·손수건을 함께 연다.
`--time 8`로 시작 시각, `--prepare-only`로 창 없이 캐시 생성, `--help`로 사용법을 확인한다.
완료 결과도 `visual_only`이며 엄격 기하 검산 통과나 학습 적격성을 뜻하지 않는다.
정리 범위와 보존 원본은 [artifact 보존 보고서](../artifact_retention_20260922.md)를 따른다.

## 현재 상태 — 2026-09-13

현행 기본 실행을 최적화 GPU 계산·GPU 독립 검산으로 연결했다. 신규 출력은
`20260913_cloth_coarse_4s_gpu_v6`이며 기존 하이브리드 출력·동결 코드는 보존한다.
3조건×3메시, 각각4초의 물성·해상도·바람·dt·검산 Gate는 동일하다.
짧은 실제 GPU 검증은 아래 근거를 따른다. 전체4초 완료·천다운 움직임은 미검증이며 학습 발행 보류를 유지한다.

## 목적과 비교 조건

[완료 궤적 분석](../evidence/cloth_motion_20260913/README.md)에서 관찰한 판 같은 움직임이
굽힘 저항을 낮추면 개선되는지 확인한다. 천처럼 늘어나기는 어렵고 구부러지기는 쉬운 조합을
시험하되, 특정 실제 직물의 보정값으로 간주하지 않는다. 각 저해상도에서 기존 물성도 다시 계산해
해상도 변경과 물성 변경의 영향을 구분한다.

| 메시 | 원래 → 비교 해상도 | 삼각형 수 | P3 계산점 수 | 고정 조건 |
| --- | --- | ---: | ---: | --- |
| 직사각형 | n32 → n16 | 384 | 1,813 | 기존과 같은 x=0.25m의 변 위치·법선 고정 |
| 수정된 삼각 깃발 | n24 → n12 | 144 | 703 | 왼쪽0.75m 변 위치·법선 고정 |
| 손수건 | 24×16 → 12×8 | 192 | 925 | 양쪽 집게 실제 폭 각각 약5.83cm 유지 |

삼각 깃발은 고른 삼각 격자를 새로 생성한다. 이전에 실패한752면 입력을 축소하지 않는다.
세 물성 조건에서 메시·고정점·질량·바람 입력은 동일하다.

| 조건 이름 | 굽힘 비율 | E (Pa) | 강성 계산 두께 h (m) | 굽힘 계수 (N·m) |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | 1 | 1,000,000 | 0.01 | 0.09157509 |
| `bend_010` | 1/10 | 3,162,277.660168 | 0.003162277660 | 0.009157509 |
| `bend_001` | 1/100 | 10,000,000 | 0.001 | 0.0009157509 |

막 강성 계수10989.010989N/m, ν=0.3, 독립 면밀도0.1kg/m²를 유지한다.
`h'=h√s`, `E'=E/√s`로 늘어남 저항을 유지하면서 굽힘과 경계 굽힘 penalty를 함께 s배로 만든다.
이 h는 이번 비교의 강성 매개변수이며 실제 천 두께를 측정한 값이 아니다.

- 각 씬 **0–4초, 60Hz·240프레임, 프레임당64단계**, Δt=1/3840초다. 기존 큰 움직임이 있었던3.35초를 포함한다.
- 조건마다 평면 rest·속도0에서 시작한다. 중력·초기 처짐·부착 방식·공력 모델·구조 감쇠는 변경하지 않는다.
- 기존v4와 같은 바람 파일의 첫240프레임을 사용한다. 힘·변위 허용오차, EW 내부 선형 풀이와64단계 보조 행렬 재사용 설정도 유지한다.
- 순서: `baseline` → `bend_010` → `bend_001`, 각 조건에서 직사각형 → 삼각 깃발 → 손수건. 동일 GPU에서 하나씩 실행한다.
- 물리 시간 합계36초이며 **실제 계산 시간은 미측정**이다. 기존v4의 씬별 실행 시간 한도 없음 정책을 유지한다. 자동 시간 간격 변경·재시도·고해상도 확장은 없다.
- `training_eligible=false`, `r1_complete=false`. 학습데이터 발행 보류와 연구 Gate는 유지한다.

## 실행과 로그

Workspace root에서 실행한다. 터미널을 닫을 가능성이 있으면 백그라운드 옵션을 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --background
```

현재 터미널에서 진행을 보려면 옵션 없이 같은 스크립트를 실행한다. 상태와 로그 확인은 별도 터미널에서도 가능하다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --status-only
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --logs
```

`--logs`의 Ctrl+C는 로그 보기만 끝낸다. 상태 조회는 파일을 읽기만 한다.
실행 시 시작 안내를 바로 출력하고 이후 약15초마다 진행을 표시한다.
전체 안내는 `batch.log`, 단계별 원본은 `<조건>/<메시>/worker.log`에 남긴다.

```bash
# 입력 준비·hash 확인만 수행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --prepare-only
# 물성 조건 하나만 실행: 해당 조건의 세 메시
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --case bend_010
```

출력은 `experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_4s_gpu_v6/`에 둔다.
각 조건의 `plan.json`, `inputs/`, `runtime/`를 동결하며 새 작업 코드가 바뀌어도 기존 동결본으로 실행한다.
묶음 전체 lock은 중복 실행을 막는다. 다른 기존 실험의 실행 상태를 제어하지 않으므로 같은 GPU에
다른 계산이 있다면 사용자가 실행 시점을 정한다.

전경 실행의 Ctrl+C는 worker를 종료하고 다음 씬도 시작하지 않는다. 저장 경계까지 기다리지 않으며 미저장 구간은 폐기한다. 확정 결과를 보존하고 `interrupted`로 표시한다. 저장 중 중단 흔적이 있을 수 있어 자동 재개하지 않는다. 새 실행은 새 `--out`으로 준비한다.
완료·수치 실패·검산 실패 조건은 보존하고 건너뛴다. 실패 뒤 다음 씬은 계속 실행한다.
강제 종료되어 report가 `running`으로 남으면 자동 초기화하지 않는다.
이때는 worker 생존·확정 파일·로그·비용을 먼저 확인해야 하며 흔적 파일을 임의 삭제하지 않는다.
백그라운드 종료·이어하기도 먼저 실행 상태를 확인한다.

## GPU 계산·검산과 저장

- 계산은 병렬 합산·첫 보조 풀이 재사용·current 우선·채택 평가 재사용을 적용한다.
- 매 프레임64개 substep 상태를 GPU 안에서 독립 검산기로 전달한다. 운동방정식·업데이트·에너지·전체 다항식 기하 검사와 고정점 검사를 유지한다.
- 검산 실패는 해당 프레임 끝에서 GPU 실패 상태로 전파하여 이후 본 계산의 상태 갱신을 막는다.
  CPU 확인 전 이미 제출한 후속 검산 작업은 남을 수 있으나 실패 이후 결과를 정상 데이터로 발행하지 않는다.
- 기본2초마다 원시 float64 hi/lo 위치·속도와 검사 결과를 무압축 저장한다. 매 substep 기록 해상도는 유지한다.
  검산·반복 판정의 수치 계산은 GPU에서 수행하며 Python은 순서대로 작업을 제출한다. 초기 준비와 저장 경계에서 CPU를 사용한다.
- GPU 상태 버퍼만 직사각형 약1.25GiB, 삼각 깃발0.48GiB, 손수건0.64GiB다. 솔버·검산 작업 공간은 별도다.
  전체9개 씬4초의 무압축 원시 상태는 약15.9GB이므로 디스크 여유도 필요하다. 씬은 순차 실행한다.
- [gpu_config.json](gpu_config.json)의 `save_interval_s` 또는 `save_interval_by_mesh_s`로 저장 간격을 지정한다.
  예: `"save_interval_by_mesh_s": {"handkerchief": 1.0}`. 준비한 설정을 바꾸려면 JSON 사본과 새 `--out`을 사용한다.
- 기존 하이브리드 실행/상태/재생은 스크립트 첫 옵션으로 `--legacy`를 지정한다.
  기존의 완료/실패 결과를 새 GPU 결과로 표시하거나 이어붙이지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --legacy --status-only
# 저장 간격을 바꾼 JSON으로 별도 준비
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse.sh --prepare-only --config /tmp/cloth_gpu_config.json --out experiments/artifacts/runs/teacher_timestep_search/cloth_gpu_custom
```

## 사용자 보고 기하 실패의 해석

아래 결과는 서브컴 실행 `sub_pc/20260912T162242Z-59eb2516b2124c6d997d086fcd6f86e6`의
config·plan·manifest·batch.log·report·failure 원본에서 확인했다. manifest393개 항목의 해시가 모두 일치한다.
메인컴 구실행만 확인했던 앞선 원본 부재 판단을 정정한다. [실패 수치·원본 hash](sub_pc_geometry_failure.json).
새 GPU 비교와 세 조건의 메시·바람은 바이트 단위로 같고 plan 차이는 `gpu_execution`, `audit_backend`뿐이다.

| 조건 | 직사각형 | 삼각 깃발 | 손수건 |
| --- | --- | --- | --- |
| baseline | complete240 | complete240 | complete240 |
| bend_010 | complete240 | geometry_bound_unresolved205 | geometry_bound_unresolved112 |
| bend_001 | geometry_bound_unresolved174 | geometry_bound_unresolved183 | geometry_bound_unresolved98 |

`geometry_bound_unresolved`는 원래 평면에 투영한 변위 기울기의 Bernstein 상한이
무접힘 충분조건 `r<1`을 만족하지 못했다는 뜻이다. 큰 회전·접힘이나 상한의 보수성 때문에
실제 면 교차가 없어도 발생할 수 있다. 굽힘을 낮춘 조건에서 먼저 발생한 경향은 이에 부합하지만,
다섯 실패의 마지막 단계는 기하 flag만 발생했다. 힘 잔차 비율은0.00463–0.02275로 기준1 미만,
위치 업데이트 오차는1.09e-19m 이하, 기록된 에너지 오차는0이다.
기하 상한은1.000066–1.001167로 기준1을 넘었다. 거부 상태NPZ도 확보했으나 실제 자기 교차 판정은 아직 수행하지 않았다.
[R1 기하 인증 계약](../../../../ideas/development/r1_teacher_probe_oracle.tex)의 현재 조건을 유지했다.
GPU 전환만으로 이 실패가 해결된다고 주장하지 않는다. 임계값 확대·검사 생략·물성 변경은 하지 않았다.

새 실행은 마지막 정상 **전체 프레임**까지 `chunks/*.npz`와 `*.audit.npz`에 확정한다.
실패 시 `failure_window.npz`에 미확정 후보 프레임의 상태, `failure.json`에 첫 실패의0기반 프레임·substep·상한값을 남긴다.
실패 구간은 학습/완료 궤적에 포함하지 않는다. 구실행의 `failure.json`, `audit_rejected_state.npz`,
`last_valid_state.npz`와 plan을 확보하면 실제 접힘과 보수적인 판정을 구분할 수 있다.
실제 교차 없이 상한만 보수적이면 인증 상한의 세분화 등 개선을 검토하고, 실제 자기 접촉이면
현행 무접촉 모델의 범위를 다시 결정해야 한다. 이러한 범위·인증 기준 변경은 별도 사용자 결정 대상이다.

## 완료 후 재생과 판정

```bash
# 1/10 조건의 직사각형·손수건을 함께 재생
bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse.sh bend_010
# 같은 조건의 삼각 깃발
bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse.sh bend_010 --shape triangular_flag
```

조건 이름을 `baseline`, `bend_001`로 바꿔 비교한다. 완료된 씬만 재생하며 표시 배율은1배다.
저해상도 직사각형의 계산점 수는 동결 plan에서 읽고, 재생 캐시는 각 조건별로 분리한다.

수치 통과는240프레임 완료, 모든 단계의 기존 운동방정식·기하 검사 통과로 판단한다.
`summary.json`, 각 씬 `report.json`의 실제 적용 물성 `effective_material`, 실패 시 `failure.json`을 확인한다.
천다운 움직임은 전체 기울어짐 외에 몸체가 분산해서 휘고 펄럭이는지 같은 시각에서 비교한다.
후속 분석에서는 전체 변위·최적 평면 잔차·고정부 굽힘 집중·늘어남을 함께 확인한다.
최적 평면 잔차 증가 하나만으로 개선을 확정하지 않으며 미세 주름은 저해상도에서 최종 평가하지 않는다.
심한 접힘·자기 접촉이 나타나면 현행 모델의 사용 범위 밖으로 분류한다.
유망한 조건만 원래 해상도로 재확인하고,10초 안정성을 주장하려면 별도10초 평가가 필요하다.

## 기존 하이브리드 준비의 재현 근거와 검증 범위

- [입력 구성](config.json), [준비·hash·정적 검사](preparation_checks.json).
- 원본은 기존 `20260912_three_scenes_10s_v4`의 로컬 동결 snapshot이다. 외부 조회·fetch·다운로드 없음.
- 실제9개 모델에서 동일 기하·고정점·질량·막 행렬, 굽힘 행렬·경계 penalty 비율을 확인했다.
- 작은 세 메시에서 경계 항을 포함하는 실제 rest 강성 행렬의 면내 성분 유지·법선 굽힘 성분 비율을 검사했다.
- 설정 전달, 이전 직사각형n32 호환, 해상도가 다른 prefix 거부, 실패 후 진행·중단·중복 lock,
  저해상도 저장 결과 재생을 포함한17개 CPU 검사 통과. Bash 두 스크립트 문법 검사 통과.
- 당시 준비에서는 GPU 적분이나 새 OpenGL 표시를 실행하지 않았다. 기존 실행·원본·동결 runtime은 수정하지 않았다.

```bash
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s code/tests -p 'test_teacher_cloth_sweep.py' -v
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s code/tests -p 'test_teacher_three_scene_run.py' -v
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s code/tests -p 'test_shell_recording_viewer.py' -v
```

## GPU 연결 검증

- [짧은 실행 근거](gpu_validation.json): 별도 `20260913_cloth_gpu_smoke_v2`에서9개 조건 각1프레임 통과.
  직사각형 baseline은 저장 후 추가1프레임 재개도 통과했다. 본4초 실행과 분리했다.
- GPU 검산 회귀8개(기존 대조·GPU 입력·실패 전파), CPU 굽힘 실행기6개·기존 실행기8개, 저장 뷰어4개 통과.
  뷰어 검증은 캐시 생성이며 새 OpenGL 창은 실행하지 않았다.
- GPU 전달 경로에서 CPU 배열 조회를 금지하는 검사와 graph 내부 host 전송0 확인.
- 새 본 실행은9개 씬 ready·0프레임으로 준비하며 기존 실행은 중단·재시작하지 않는다.
- 외부 fetch·다운로드 없음. 로컬 cuDSS0.7.1.6과 native workspace shim을 해시 검증/동결한다.

## 메인컴·서브컴 구간 속도 비교

현행 기본 `gpu_v3`는 매 저장 구간(기본0–2초,2–4초)의 시간을 씬별 `worker.log`와
`report.json.interval_timings`에 기록한다. 기존v2 동결 실행은 그대로 보존하며 자동으로 계측이 추가되지 않는다.
메인컴/서브컴 모두 새 코드로 새 run을 준비해야 한다. `--out`으로 서브컴의 고유 run 경로를 지정할 수 있다.

- `compute_audit_s`: GPU 계산·검산·상태 버퍼 기록의 실제 경과 시간. 기존 저장 경계의 GPU 완료 대기까지 포함한다.
  CPU 작업 제출·프레임 로그 비용도 포함하므로 순수 GPU kernel 시간과 구분한다. 첫 구간에는 지연 초기화·graph capture가 포함될 수 있다.
- `boundary_check_s`: 결과 요약의 CPU 전송, 상태·cuDSS·검산 결과 확인 시간.
- `transfer_write_hash_s`: 원시 상태 CPU 전송·NPZ 저장·해시 계산 시간. 공유 파일시스템 속도 영향을 포함한다.
- `window_s`: 위 구간의 전체 경과 시간. 마지막 구간 로그 출력과 report JSON 쓰기는 제외한다.
- 제출/정상 프레임·substep 수와 시뮬레이션 시작/끝 시각, dt, 정상 단계당 계산 시간을 함께 기록한다.
  실패 구간은 이미 제출된 작업과 정상 단계 수가 다르므로 단계당 속도를 null로 두고 비교에서 제외한다.
- `timing_launches`에는 재개별 초기화 시간·CPU/GPU 이름·plan/manifest 해시를 남긴다. 재개 시 기존 구간 기록을 유지한다.

같은 메시·물성·바람·dt·정확도·코드·시뮬레이션 구간·저장 간격·재개 조건끼리 비교한다.
서로 다른 장치의 전체 실행 속도를 비교할 때도 계산과 공유 저장 비용을 분리한다.
첫 구간과 후속 구간은 초기화 상태가 다르므로 서로 교차 비교하지 않는다.
기존 누적 시간만 있는 결과에서 동일 구간 시간을 추정해 확정하지 않는다.

검증: 별도 smoke에서 삼각 깃발1프레임과 재개1프레임을 실행해 구간 경계·시간 합계·단계당 시간·기존 기록 보존을 확인했다. [계측 검증 원본](timing_validation.json). 새 본 실행9개 씬은 ready0 상태다.

## Ctrl+C 종료 정책

현행 `gpu_v4`는 worker를 별도 프로세스 그룹으로 실행하고 controller가 SIGINT/SIGTERM을 받아
소유 worker에 종료 신호를 전달한다. 2초 내 종료하지 않으면 해당 worker만 강제 종료한다.
worker는 CUDA 정리·저장 경계를 기다리지 않고 종료한다. 반복 Ctrl+C도 종료 처리 중 worker를 남기지 않는다.
기존v2/v3 동결 코드는 변경하지 않았다. 확정 chunk·기존 결과는 삭제하지 않으며 저장 중 미완료 파일도 보존한다.
별도 테스트3개에서 실제 자식 종료, timeout 강제 종료, 다음 씬 미실행·확정 report 보존을 확인했다.
본4초 GPU 실행은 하지 않았다. 현재 호스트 조회에는 천 시뮬레이션이 없었으며 별도 cuDSS probe는 종료하지 않았다.
서브컴 프로세스는 공유 결과만으로 종료할 수 없으므로 원격 제어 없이 종료했다고 보고하지 않는다.

## 터미널 완료 구간 요약

현행 기본 `gpu_v5`는 controller가 확정된 `interval_timings`를 읽어 새 구간만 한 줄씩
터미널과 `batch.log`에 표시한다. 프레임 범위·완료/실패·계산 및 검산 시간·저장 시간·전체 시간을 남긴다.
기본 출력 주기는 매120프레임(시뮬레이션2초)이며 매 프레임마다 GPU 동기화하지 않는다.
보고서 확정 후 보통1초 이내 표시하고 worker 종료 직후 마지막 구간도 확인한다.
30초 동안 완료 구간이 없으면 계산 중 안내만 표시한다. 작업 제출 메시지는 상세 `worker.log`에 남는다.
재개 이전 구간은 다시 출력하지 않는다. 기존v4 이하 동결 실행은 변경하지 않는다.
검증: 기존 실제 smoke의 두 구간 출력·중복 방지 확인, Ctrl+C 회귀3개 통과. 새 GPU 시뮬레이션은 실행하지 않았다.

## 현행 터미널 출력 — 매1프레임

사용자 정정에 따라 `gpu_v6`는 매 프레임64개 substep 계산·검산 완료를 GPU synchronize로
확인하고 소요 시간을 출력한다. controller는 worker.log의 프레임 줄을 보통1초 이내 터미널·batch.log로 전달한다.
위v5의120프레임 요약 정책을 대체한다. `frame_timings.jsonl`에는0기반 frame·시뮬레이션 구간·
실제 계산/검산 시간·실패 여부·launch ID를 즉시 남긴다. 물리 상태 저장은 기존2초 간격을 유지한다.
프레임 계산 완료는 디스크 저장 완료와 다르다. `state_saved:false`는 프레임 로그 생성 시점의 상태이며
최종 저장 여부는 report의 확정 chunk를 따른다. 실패 프레임은 완료로 표시하지 않고 저장 경계 처리를 앞당긴다.
매 프레임 GPU 완료 대기·실패 상태 조회·소규모 로그 쓰기 비용이 추가되므로 기존v5 이하 시간과
직접 속도 비교하지 않는다. 메인컴·서브컴 모두 같은v6 조건을 사용한다. 첫 프레임은 graph 준비 비용을 포함할 수 있다.

검증: 별도 `20260913_cloth_frame_log_smoke_v1`에서 삼각 깃발2프레임 실제 GPU 계산·검산·프레임별 터미널 출력과 JSONL 기록 통과. Ctrl+C 회귀3개 통과. 새 본 실행은9개 씬 ready0 상태다.

## 10초 × 9회 비교 실행

현재 프레임별 GPU 완료 시간 출력·Ctrl+C 종료 정책을 사용하는 별도10초 실행이다.
직사각형·삼각 깃발·손수건 × baseline/굽힘1/10/굽힘1/100의9개 씬을 순차 실행한다.
각 씬은 평면 rest·속도0에서600프레임(60Hz)이며64substep과 기존 물리/검산 기준을 유지한다.
기존4초 결과를 이어붙이지 않는다. [설정](gpu_10s_config.json).

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse_10s.sh
# 상태 확인
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse_10s.sh --status-only
# 터미널을 닫아도 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse_10s.sh --background
```

기본 출력은 `experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_10s_gpu_v1`이다.
서브컴에서는 같은 스크립트에 `--out experiments/artifacts/runs/sub_pc/<고유runID>`를 추가한다.
기존4초 스크립트·동결 결과는 보존한다. 2초 저장 간격·매 프레임 시간 출력은 동일하며
원본 바람600프레임 범위와 준비된9개 plan·ready0 상태를 확인했다. GPU 본 계산은 미실행이다.
무압축 원시 상태는9회 합계 약39.6GB이며 부가 기록은 별도다. 저장 버퍼는2초 크기를 유지한다.
기하 오류를 포함한 기존 실패 Gate는 유지하므로 각10초는 목표 길이이며 모든 씬의 완주를 보장하지 않는다.
실패 씬은 보존하고 다음 씬으로 진행하며 사용자 Ctrl+C는 전체 실행을 종료한다.

## 현행10초 실행: 기하 중단 해제 시각 확인

사용자 승인에 따라 `run_cloth_coarse_10s.sh`의 기본을
`20260913_cloth_coarse_10s_visual_v1` / [시각 확인 설정](gpu_10s_visual_config.json)으로 변경했다.
이 실행만 `geometry_bound_unresolved` flag(16)를 중단 조건에서 제외한다. 기하 상한·원래 flag는
각 substep의 `chunks/*.audit.npz`에 그대로 기록하며 report에 경고 단계 수·최초 발생 시각을 남긴다.
힘 잔차·위치 업데이트·에너지·고정점·비유한 값 실패는 계속 중단한다. 솔버의 유효성 검사도 유지한다.
결과는 `visual_only:true`, `training_eligible:false`, `r1_complete:false`이며 complete는10초 계산 완료를
뜻할 뿐 엄격 기하 검산 통과가 아니다. 자기 접촉을 처리하는 물리 모델을 추가한 것은 아니다.
기존4초 및 엄격10초 동결 실행과 결과는 보존한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_coarse_10s.sh
# 완료 후 굽힘1/100 손수건 재생
bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse_10s.sh bend_001 --shape handkerchief
```

GPU 작은 입력7개로 기하 단독 경고는 계속 진행, 다른 flag 및 혼합 실패는 중단, strict 모드는 유지,
원본 flag 불변을 확인했다. 9개 씬 ready0으로 준비했으며 본 시뮬레이션/시각적 판정은 미실행이다.
