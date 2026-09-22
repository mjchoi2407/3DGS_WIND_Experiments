# 고부하 FP64/FP32 연산별 고정 작업량 비교

2026-09-20. 스크립트·CPU 검증 완료, GPU 측정은 사용자 실행 대기다.
기존 M1/M2/운영 솔버를 수정하지 않고 원본 동결 runtime의 별도 사본에서 진단한다.

## 입력과 범위

원본은 `teacher_timestep_search/gpu_gtx1080ti_wind120_to200_reference_v1/comparison`이다.
완료된182–200(표시 기준)의 저장 시작 상태 중 시간 최대200, 남은 GMRES 최대194,
남은 중앙 시간190의 세 프레임을 선정한다. 목록과 원본 시간/반복 수는 selection.json에 보존한다.
이들은 검사한19프레임의 대표이며 전체 생성 범위의 최대 하중이라는 뜻은 아니다.

각 시작 상태의 **첫 substep**을 R64로 진단하여 최대 GMRES 반복 Newton 호출을 고르고,
같은 시작 상태로 그 substep만 다시 실행해 해당 uh/lo/a/RHS/P/방향을 저장한다.
P는 새 worker 초기화 상태다. 과거 실행의 P cache나 프레임 전체에서 가장 어려운
Newton 상태를 복원했다고 주장하지 않는다. 두 번째 실행의 선택 호출 및 잔차도 보존한다.
저장된 원본 held force를 그대로 사용하고 forcing index/phase time을 기록한다.
추출 시 첫 substep 실패/검산 결과는 그대로 남기며, 미승인 상태의 연산 진단을 teacher 성공으로 취급하지 않는다.
전체 프레임 재생·Gauss 복구·dt 정책 변경은 이번 연산 측정에 포함하지 않는다.

## 실행

workspace root, 기존 GPU 작업과 겹치지 않는 시점에 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_highload_precision_bench.sh
```

매번 새 `experiments/artifacts/runs/teacher_precision_v3/highload_fixed_<시각>`을 생성한다.
원본을 덮어쓰거나 중단 실행을 자동 재개하지 않는다. 출력 경로를 고정하려면:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_highload_precision_bench.sh \
  --out experiments/artifacts/runs/teacher_precision_v3/highload_fixed_1080ti_v1
```

5070에서는 메인컴이 추출한 같은 snapshot을 재사용하는 것이 장치 비교에 적합하다.
공유 경로가 보이면 코드 수정 없이 아래 명령을 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_highload_precision_bench.sh \
  --samples experiments/artifacts/runs/teacher_precision_v3/highload_fixed_1080ti_v1 \
  --out experiments/artifacts/runs/teacher_precision_v3/highload_fixed_5070_v1
```

`--samples` 생략 시 해당 PC에서 자체 추출한다. 이 경우 원본 시작 상태가 같아도 내부 Newton
snapshot의 정확 일치를 가정하지 않는다. snapshot 및 전처리 배열 hash를 비교해야 한다.
공통 기본 block은256/256/256이다. 첫 장치 대조에서는 이를 유지한다.
명시적으로 `--blocks 32 32 256`을 주면 별도 설정으로 기록하지만 기존256 결과와 순수 dtype 차이로 섞지 않는다.
GPU/라이브러리 환경을 자동 교체하지 않으며 Graph 실패 시 로그를 남기고 중단한다.

CPU 준비만 하려면 `--prepare-only`. 해당 폴더 실행 시 같은 설정과 `--prepared --out <폴더>`를 준다.
Ctrl+C 시 다른 실행은 건드리지 않고 현재 명령의 로그를 보존한다. 새 out으로 다시 시작한다.

## 무엇을 재는가

- `P_factor`: 원본 FP64 조립값의 동일 P를 FP64/FP32로 수치 분해. 조립 자체는 제외.
- `P_apply`: 분해 완료된 같은 P와 실제 저장 RHS를 고정 횟수 적용. 내부 copy/풀이/output은 유지.
- `A_hvp_mass`: 기존 A64 action과 기존 LowAction의 HVP·질량 연산. low 경로는 기존 uh-only 구현.
- `vector_subtract_with_reset`: 기존 GMRES `subtract_basis`의 FP64/FP32 버전. 실제 RHS/저장 방향,
  고정 계수0.5, 호출마다 원본 벡터 reset 포함. 내적·정규화·모든 Krylov 연산 전체를 대표하지 않는다.

FP32 low namespace는 동결된 기존 구현을 그대로 사용한다. 새 정밀도 보정/허용오차 변경 없음.
각 역할은 한 Graph 안에20호출을 캡처하고 warm-up 후6쌍을 측정한다. FP64/FP32 순서를 교대한다.
`FP32_with_conversion`은 호출별 입력 cast와 출력 widen까지 포함한다(P_factor는 행렬 cast).
HVP 상태 준비·모델 생성·기저 벡터 변환은 준비 비용이고 호출별 변환에는 포함되지 않는다.
동일 입력 복원/출력 덮어쓰기로 replay마다 값이 누적되어 workload가 변하지 않게 한다.
GPU event와 동기화 완료 wall을 모두 저장한다. GPU event를 순수 산술 시간으로 부르지 않는다.

`raw.csv`의 모든 표본, median/MAD/min/max, 실제 Graph inventory/launch 기록과 원시 출력 NPZ,
finite/cuDSS info/HVP status/최대절대·RMS·상대L2 차이를 남긴다.
분해 출력은 동일 RHS solve 결과로 검사한다. info/status/finite 실패 시 가속률을 비워 둔다.
출력 차이는 근사 연산 차이이며 Newton 참 잔차/teacher 정확도 판정이 아니다.

`report.md`는 프레임·연산별 FP64/FP32 및 변환 포함 가속률을 보여준다.
전체 시뮬레이션 가속률, FP32 전체 시간 비중, 생산 채택으로 일반화하지 않는다.
환경, 명령/process wall, snapshot/입력·source hash, 전처리 배열, changes.diff를 함께 보존한다.
원본 comparison manifest 검증 뒤 별도 사본을 만들고 부모에서는 CUDA를 import/초기화하지 않는다.

## 검증 상태

선정 규칙·부모 import 경계 CPU unit test2개와 실제 입력/hash 검증·runtime 준비,
수정 모듈의 Python 구문 및 shell 구문 검사를 통과했다. pytest 미설치로 표준 unittest를 사용했다.
GPU capture/분해/Graph 실행은 아직 실행하지 않았으며, 실측값을 미리 채우지 않았다.
production_enabled=false, training_eligible=false를 유지한다.
