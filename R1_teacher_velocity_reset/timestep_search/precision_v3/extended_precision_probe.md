# 고부하 M2와 추가 FP32 후보 비교

2026-09-20. 사용자 실행 스크립트 준비. GPU 실행 미검증.

## 목적과 범위

최근 benchmark의 표시190/194/200프레임 **시작 상태**에서 첫 substep을 동일한
FP64 held force로 실행한다. 내부 선형계를 고정한 이전 microbenchmark와 달리,
Newton 반복/line search/독립 검산까지 포함한다. 각 후보·각 표본3회, AB/BA/AB 순서의18 worker다.
각 worker는 별도 초기화 후1회 워밍업하고 원본 상태로 복원하여1회 측정한다.
전체 프레임/Gauss 복구/전체 씬 비교는 아니다. 실패한 substep을 승인하거나 새 dt로 진행하지 않는다.

- `M2`: 기존 동결 M2의 수식/정밀도 유지.
- `M2_extended32`: 추가로 현재 P 조립, inner 내적/norm/Hessenberg/Givens/backsolve를 FP32로 수행.
- 유지: 힘/에너지/line search/hi-lo 상태 갱신, master 누적, 원래 A64 참 잔차·EW,
  독립 audit와 FP64 fallback. 모든 FP64 항목을 무조건 바꾸는 실험은 아니다.
  후자의 FP64 authority는 동일 기준 오차 비교에 필요하며, 독립 FP32 실패를 입증한 항목이라는 뜻도 아니다.
- outer correction의6회/정체 기준과 inner rtol0.01/반복 한도는 변경하지 않는다.
  inner dtype 변경 외에 원본 machine-epsilon 상수/반복 조건을 별도 튜닝하지 않는다.

## FP32 조립 검사와 복귀

원본 coloring groups/희소 구조, 원본 시각의 uh에서 기존 LowAction을 사용한다.
조립 후 P32 값을 FP64로 올려 **원래 FP64 probe, 원래 A64, 원래 조립 check_error**로 검사한다.
상대 제곱오차1e-20 판정·비유한 검사를 그대로 유지한다.
검사 실패 시 원래 FP64 조립 후 기존 M2처럼 P32로 cast·분해한다. 버린 FP32 조립 비용도 포함한다.
이는 허용오차 완화가 아니며, 많은 조립이 복귀하면 'FP32 조립 성공'으로 보고하지 않는다.

조립이 통과하면 해당 세대의 원래 P64는 아직 조립하지 않은 상태이므로 FP64 fallback 시
**P가 만들어진 당시 uh를 복원**해 원래 P64를 재조립한다. 현재 Newton 상태로 fresh P를 만들지 않는다.
실험 밖 전역 rebuild/생산 정책은 변경하지 않는다.

## 실행

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_extended_precision_probe.sh
```

매번 `experiments/artifacts/runs/teacher_precision_v3/extended32_<시각>`을 새로 만든다.
기존 결과는 덮어쓰거나 자동 재개하지 않는다. 다른 GPU에서는 같은 명령을 실행할 수 있다.
기본 `--source`는 메인 highload_fixed_20260920T012954이며 동일 raw 시작 상태를 쓴다.
사용자 서브 결과로 바꾸려면 `--source <benchmark 폴더>`를 명시한다.
기본 block256/256/256을 양쪽 유지해야 정밀도 효과를 분리하기 쉽다.

```bash
# 명시적 출력 폴더
bash experiments/R1_teacher_velocity_reset/timestep_search/run_extended_precision_probe.sh \
  --out experiments/artifacts/runs/teacher_precision_v3/extended32_main_v1

# CPU 입력 준비만
bash experiments/R1_teacher_velocity_reset/timestep_search/run_extended_precision_probe.sh \
  --out experiments/artifacts/runs/teacher_precision_v3/extended32_ready_v1 --prepare-only

# 위 폴더를 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_extended_precision_probe.sh \
  --out experiments/artifacts/runs/teacher_precision_v3/extended32_ready_v1 --prepared
```

`--pairs`로 반복 수를 조정할 수 있다. 준비/실행의 pairs·blocks는 같아야 한다.
후속 집계는 `--out <결과> --collect-only`. 누락/실패 쌍의 가속률을 만들지 않는다.
GPU 실행은 순차다. 기존 시뮬레이션을 중단하지 않는다.

## 터미널과 파일 출력

- 전체 실행 번호/표시 frame/후보/반복을 출력한다.
- 입력 준비 → 모델 준비 → GPU buffer/JIT/Graph → 워밍업 → 계산+검산 → 결과 저장 → 정리 → 집계의
  시작·완료와 해당 wall time을 즉시 출력한다. solver 내부 각 kernel 뒤의 추가 계측 동기화는 넣지 않는다.
- 외부 worker process wall은 별도로 저장한다. setup/워밍업/저장을 계산+검산과 합산하지 않는다.
- 각 worker 전체 stdout/stderr를 터미널에 전달하며 별도 log에도 저장한다.
- Ctrl+C는 이 스크립트가 생성한 worker process group에 전달한다. 다른 프로세스는 종료하지 않는다.

`report.md`, `raw.csv`, `pairs.csv`, `differences.csv`: 시간·통과·성공 쌍 가속률,
위치/속도/힘/탄성·운동에너지 차이. 차이는 M2 대비이며 참해 오차가 아니다.
각 result에는 dtype, A64 마지막 참 잔차/목표, inner/correction/fallback,
FP32 조립 승인/거부, GMRES/rebuild, audit flag와 timing을 기록한다.
NPZ는 승인 상태와 실패 후보 상태를 구분한다. 실패 후보를 학습 데이터로 발행하지 않는다.
manifest/동결 runtime/changes.diff/환경/전처리 배열/Graph inventory/실제 명령을 보존한다.

## 검증

- CPU unittest3개: dtype 변환/정책 보존, 실패 쌍 가속률 제외, hi-lo 합성 후 상태 차이 검증.
- 실제 입력 hash 검증/준비, Python 및 shell 구문 검사 통과.
- 새 inner FP32·제어 Warp kernel의 CPU 컴파일 통과.
- 도구 환경의 GPU 접근 제한으로 GPU Graph/cuDSS 실행 검증은 미실행. 사용자 GPU 실행 대기.
- 기존 솔버/운영 설정은 수정하지 않았고 production_enabled/training_eligible은 false 유지.

## 항목별 누적 시간 계측 (후속)

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_extended_precision_breakdown.sh
```

같은3표본×2경로×3회이며, 결과는 별도 `extended32_breakdown_<시각>`에 저장한다.
`role_report.md`가 요청한 **항목별 M2/확장32 누적 초와 전체 wall 비중 표**다.
행 합계가 전체 시간과 대응하도록 반복 평균을 표시하고 각 반복은 `role_times.csv`에 남긴다.
`device_regions.json`은 중첩 경로별 호출 수/inclusive/exclusive 원시값이다.

기존 검증된 GPU globaltimer marker로 conditional Graph 안의 실행 구간을 계측한다.
P 조립에 포함된 HVP를 내부 반복 HVP에 다시 더하지 않고, 참 잔차의 A64도 별도로 분류한다.
독립 검산은 기존 host 제출/완료 경계 전체를 측정하며 내부 Graph에 중복 marker를 넣지 않는다.
FP64 fallback은 각 연산 행에 포함하고 참고용 inclusive 합계를 별도 표시한다. Gauss는 이번 시험에 없다.
미분류 wall에는 제출/전송/대기/기록 경계 등이 남으며 이를 순수 CPU 시간으로 해석하지 않는다.
음수 exclusive나 root합계가 wall을 넘는 경우 raw를 숨기거나0으로 자르지 않고 accounting_valid=false로 보류한다.

이것은 **계측 실행 시간**이다. marker·scheduling·일부 host 대기 비용을 포함하므로
이전 일반 실행의 약6.3% 개선 수치와 혼합하지 않는다. 프로파일러 설치/드라이버 변경은 하지 않는다.
추가 kernel별 synchronize는 없고 batch 완료 경계에서 GPU 완료를 확인한다.

CUDA load가 반복된 이유: 기존 worker가18개의 독립 프로세스로 생성되기 때문이다.
확인한 기존 로그에서 최초에는 compiled가 있고 후속은 주로 cached였다.
워밍업/측정 중에는 다시 load하지 않았고, GPU 준비 시간은 계산+검산 분모 밖이었다.
이번에도 입력·후보별 독립 초기화 조건을 유지한다. 부모 CUDA 초기화는 없다.
모듈 load와 전체시뮬레이션의 frame/substep을 혼동하지 않는다.

후속 검증: CPU 회계/분류/보고서 테스트4개와 기존3개 통과, 실제 준비/hash·구문 검사 완료.
GPU 계측 실행은 사용자 실행 대기다.

## 전체 프레임 항목별 누적 비교

첫 substep 계측은 표시190/194/200프레임의 전체 비용과 Gauss 복구를 대표하지 않는다.
전체 프레임 비교에는 다음 별도 스크립트를 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_extended_precision_frame_breakdown.sh
```

각 checkpoint에서 원본 wind/gravity를 복원하고 Newmark64개 기본 구간을 끝까지 수행한다.
기본 구간이 실패하면 기존 정책과 같은 FP64 Gauss6차8분할로 해당 구간을 복구하며,
실패한 Newmark 시도와 Gauss 계산·검산 비용을 모두 포함한다. 기본은 비용을 고려해
표시190/194/200프레임, M2/확장FP32 각1회인6 worker를 순차 실행한다.

`role_report.md`는 각 계산 항목의 한 프레임 누적 시간을 나란히 표시한다.
FP32 시도 뒤 원래 FP64 선형 풀이 또는 FP64 보조 행렬 조립으로 돌아간 시간은 해당 항목
누적값에 포함하고, 같은 칸에 `(FP64 전환 ...초)`로 비가산 표시한다. Gauss 복구는
정밀도 fallback과 다른 적분기 복구이므로 별도 `Gauss6차8분할 복구(FP64)` 행에 기록한다.
터미널에는 base/Gauss attempt별 완료 구간과 wall time, 종료 후 항목별 누적값을 출력한다.
반복되는 Warp 초기화 banner와 CUDA module load/cache 정보는 터미널에서 숨긴다.
오류·경고와 프로젝트 단계 로그는 그대로 출력하며, 숨긴 정보도 worker별 원본 log에는 보존한다.

기존 첫 substep 결과는 범위가 잘못된 전체 프레임 비교로 승계하지 않는다. GPU marker의
항목 합계와 host wall 불일치가 있었으므로 전체 합계·비중을 항목별 판정에 사용하지 않고,
각 항목의 원시 계측값과 FP64 전환 overlay를 보존한다. 생산/학습 설정은 변경하지 않는다.
