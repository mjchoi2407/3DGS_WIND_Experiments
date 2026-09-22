# 네 정밀도 경로의 진단 비교

## 현재 상태

후속 [굽힘1/100·4초 FP64 세 경로 비교](refine64_4s.md)을 준비했다. 기존 메인컴 결과와 종료 후 자동 비교한다.
기존1/100은4초 목표 중 기하 검사로 조기 중단되어 속도 비교는 공통 정상 저장 구간에 한정한다.

후속 [적응 FP32/FP64 비교](adaptive_report.md): 순·역방향10프레임 비교와 전체 단계 검산 완료.
혼합의 가속은 미확인, 같은 알고리즘의 FP64 대조군은28–30% 시간 감소. 기본 채택·장기 검증은 별도다.

2026-09-13. 사용자 요청에 따라 정확도 초과로 즉시 중단하지 않는 진단 모드를 준비했다.
네 경로를 같은 입력·장치에서 순차 실행하고 다음 두 쌍을 비교한다.

| 비교 | 기준 | 후보 |
| --- | --- | --- |
| hi/lo 유지 | `reference_hilo`: FP64/hi-lo | `fp32_hilo`: FP32/hi-lo |
| 순수 정밀도 | `fp64`: FP64 | `fp32`: FP32 |

준비된 기본은 굽힘1/100 손수건·초기 평면·속도0·기존 바람·Δt=1/3840초·60Hz·64substep,
각10프레임(1/6초)이다. 본 네 경로는 완료됐으며, 후속 식 재작성·선택적 보정 결과는
[FP32 개선 보고서](stable_strain_report.md)에 정리했다. 엄격 기준·학습 적격성은 미완료다.
이전 세 경로의 엄격 종료 실행·원본은 보존한다. [이전 조건과 검증](strict_v1.md).

## 실행

Workspace root에서 다음 명령 하나로4개 경로 생성과 독립 분석을 순차 수행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_compare.sh \
  --out experiments/artifacts/runs/teacher_precision_compare/20260913_four_precision_diagnostic_v2 --run-prepared
```

상태는 같은 명령의 `--run-prepared`를 `--status-only`로 바꿔 확인한다.
각 프레임의 시간·경고 단계 수·치명적 실패를 터미널에 출력한다. 상세 로그는 `<lane>.log`다.

다른 길이·메시는 새 경로로 준비한다. 아래는 **10초(600프레임)×4개**의 준비 예시이며,
이 명령만으로 계산을 시작하지 않는다. 큰 비용의 본 실행은 이번 작업에서 수행하지 않았다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_compare.sh \
  --out experiments/artifacts/runs/teacher_precision_compare/four_precision_10s_new \
  --case bend_001 --shape handkerchief --frames 600 --prepare-only
```

`--case`: `baseline`, `bend_010`, `bend_001`.
`--shape`: `reference_rectangle`, `triangular_flag`, `handkerchief`.
서브컴에서는 `--out experiments/artifacts/runs/sub_pc/<고유runID>`를 지정한다.
새 준비의 기본 `--mode diagnostic`은 경고 후 진행, `--mode strict`는 기존 엄격 종료다.
준비된 run에는 해당 설정이 동결되므로 변경하려면 새 출력으로 준비한다.
기존 출력·결과·controller lock은 덮어쓰지 않으며 자동 재개하지 않는다.
Ctrl+C는 전체 비교와 소유 worker를 종료한다. 확정 프레임은 보존하고 미저장 구간은 버린다.

## 정확도 초과 시 동작

기존 수치 허용오차 자체는 그대로 둔다. 진단 모드의 **진행/종료 정책**만 변경한다.

- Newton 반복 한도, 선형 미수렴, line search 한도, 유한한 행렬 검사·위치 업데이트 오차는 경고로 남긴다.
- 반복은 기존 유한 한도 안에서 수행한다. 미수렴이면 마지막 채택 후보(없으면 유한한 초기 예측 후보)를 사용해
  속도를 갱신하고 다음 substep으로 진행한다. 직전 상태로 되돌려 시간을 건너뛰거나 실패 상태를0으로 채우지 않는다.
- 경고 후 마무리 전에는 실제로 사용할 후보의 힘·잔차·에너지를 다시 평가해 거부된 trial 캐시를 사용하지 않는다.
- 비유한 값, 힘/기하 평가 불능, cuDSS/CUDA 오류는 계속 종료한다. 유한한 다음 상태를 계산할 수 없는 경우다.
- 단계별 `warnings` bitmask와 `failure` 치명적 코드는 별도 배열이다. 경고 코드1/2/3/7/8은 각각
  Newton 한도/선형 미수렴/line search 한도/행렬 검사/위치 업데이트 초과다.
- report는 `warning_steps`, `warning_counts`, `first_warning_step`(0기반), `first_warning_time_s`를 기록한다.
  한 단계에 여러 경고가 가능하므로 코드별 횟수 합계와 경고 단계 수는 다를 수 있다.

`complete`와 `completed_steps`는 **진단 궤적의 진행 완료**이지 엄격한 수렴 통과가 아니다.
경고 이후 궤적은 앞선 미수렴의 영향도 포함한다. `training_eligible=false`, R1 Gate는 유지한다.

## 정밀도 범위

GPU 기하·힘·HVP·공력·질량 행렬 작용·cuDSS 분해/풀이·Newton·GMRES·합산을 해당 FP32/FP64로 수행한다.
CPU 모델·구적·초기 행렬 전처리는 공통 FP64이고 GPU 업로드 시 변환한다. 독립 CPU 진단은 FP64/longdouble이다.
따라서 CPU 전처리까지 전부 FP32인 실험은 아니다.

hi/lo 경로는 각 자료형의 두 값으로 상태 누적과 일부 기하 연산을 보정한다. FP32 곱 분할 상수는4097,
FP64는134217729이며 재결합·암묵적 FMA fusion을 끈 기존 보정 구조를 유지한다.
FP32/hi-lo의 힘·행렬·선형 풀이 전체가 FP64 정확도를 갖는다고 가정하지 않는다.
순수 경로는 보정을 제거하고 호환 low 버퍼를0으로 유지한다. 자동 미분 dual 성분은 보정 low와 구분한다.

동결 runtime별 정밀도 변환을 사용하며 기본 솔버 소스에는 진단 정책을 적용하지 않는다.
기존 병렬 합산·current 우선·보조 풀이/채택 평가 재사용은 별도 프로세스에서 동일하게 유지한다.

## 결과와 솔버 오차

`comparison.json.trajectory`는 `fp32_hilo_vs_reference_hilo`, `fp32_vs_fp64` 두 쌍이다.
경고 포함 공통 진행 substep의 최대 위치·속도 성분 차이와 면적 가중 RMS 최대값,
`common_advanced_steps`, `moving_common_steps`, `common_warning_steps`를 기록한다.
모든 구간이 무풍이면 동적 일치로 해석하지 않는다. 치명적 실패 이후 구간은 비교하지 않는다.

`<lane>/frame_*.npz`는 원시 hi/lo 상태·후보·선형 입력·내부 잔차·반복 상태·경고를 모든 substep에 저장한다.
프레임 마지막 후보는 독립 CPU 계산으로 힘/선형 잔차·공력 차이·탄성 에너지·변형률을 재평가한다.
진행한 상태의 위치 업데이트·운동 에너지·에너지 장부·고정점도 표본 확인한다.
이 독립 분석은 모든 substep의 전체 teacher audit가 아니며, 기하 Bernstein 무접힘 인증도 부여하지 않는다.

입력·runtime·라이브러리·shim은 manifest로 동결하고 원시 결과는 hash로 확인한다.
생성 시간은 GPU 풀이·추가 진단 버퍼·프레임 동기화를 포함한다. 초기화·전송/저장·독립 분석은 분리한다.
첫 프레임 준비 비용, 미수렴 반복 증가, 진행 구간 차이를 제외하지 않은 시간을 단순 가속률로 해석하지 않는다.

## 검증 범위

[선별 근거](diagnostic_smoke_evidence.json)의 원본은
`artifacts/runs/teacher_precision_compare/20260913_four_diagnostic_smoke_v1`이다.
GTX1080Ti의 굽힘1/100 손수건에서 각2프레임/128단계를 요청했다.

- 4개 모두128단계 진행, 독립 분석 오류0. FP32 두 경로는 각각61개 경고 단계를 포함하여 끝까지 진행했다.
- FP32/hi-lo의 위치·속도 low part가 실제 비영이며, 순수 경로의 low는0인 것을 원시 기록에서 확인했다.
- 실제 Warp CPU 산술 검사에서 FP32 hi/lo의 합·곱 잔여 복원과 작은 증가량1000회 누적을 확인했다.
- 정밀도·경고 정책9개 CPU 검사 통과. 유한한 정확도 초과는 경고, 비유한 값은 치명적 실패로 구분했다.
- 위 smoke 검증은2프레임이다. 후속10프레임 검증은 [개선 보고서](stable_strain_report.md)를 따른다.
  10초 장기 안정성·성능 채택·모든 단계의 독립 검산·전체 step graph host-node 감사는 미완료다.

이 결과는 실행기 동작 검증이다. 이후 긴 구간의 차이는 승인된 진단 진행 정책의 영향도 포함한다.
로컬 snapshot만 사용했고 외부 fetch·다운로드·기존 결과 변경·commit·push는 하지 않았다.
