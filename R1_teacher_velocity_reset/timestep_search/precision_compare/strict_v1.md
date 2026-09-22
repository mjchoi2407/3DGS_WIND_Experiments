# 이전 세 경로 엄격 종료 비교 — 보존 기록

아래는 경고 후 진행 모드 도입 전 기록이다. 현행 실행은 [README](README.md)를 따른다.

# FP32·FP64 전역 GPU 연산 비교

## 현재 상태

2026-09-13. 별도 정밀도 실행기와 실패/오차 분석을 준비했다. 기존 천 실행·동결 결과는 변경하지 않는다.
본 비교 기본은 굽힘1/100 손수건, 초기 평면·속도0, 기존 바람,60Hz·64substep,
Δt=1/3840초,10프레임(1/6초)이다. 준비된 본 실행은 아직 계산하지 않았다.
FP32 장기 궤적을 만들기 위해 허용오차를 자동으로 낮추지 않는다.

## 실행

Workspace root에서 준비된 비교를 실행한다. 세 lane은 같은 GPU에서 순차 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_compare.sh \
  --out experiments/artifacts/runs/teacher_precision_compare/20260913_fp32_fp64_v1 --run-prepared
```

별도 조건은 새 출력 경로로 준비한다. 아래 예시는 삼각 깃발의10프레임이다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_precision_compare.sh \
  --out experiments/artifacts/runs/teacher_precision_compare/triangle_new \
  --case bend_001 --shape triangular_flag --frames 10 --prepare-only
```

`--prepare-only`를 생략하면 준비 후 실행한다. `--status-only`는 상태 파일만 읽는다.
서브컴 출력에는 `experiments/artifacts/runs/sub_pc/<고유runID>`를 지정한다.
`--frames 600`은10초의 요청 길이이며 완주 보장이 아니다. 이번 작업에서600프레임 비교는 실행하지 않았다.
기존 출력·lane·controller lock은 덮어쓰거나 자동 재개하지 않는다. Ctrl+C는 소유 worker를 종료하며
확정 프레임 파일을 보존하고 미저장 구간은 버린다. 재시작에는 새 출력 경로를 사용한다.

## 정밀도의 정의

| lane | GPU 반복 계산 | 상태 누적 |
| --- | --- | --- |
| `reference_hilo` | 기존 FP64 | 기존 두 FP64의 hi/lo 보정 유지 |
| `fp64` | FP64 | 보정 없는 순수 FP64, 호환용 low 버퍼는0 |
| `fp32` | FP32 | 보정 없는 순수 FP32, 호환용 low 버퍼는0 |

GPU 기하·힘·HVP·공력·질량 행렬 작용·cuDSS 분해/풀이·Newton·GMRES·합산을 대상으로 한다.
CPU 모델 생성·구적·초기 희소 행렬 준비는 공통 FP64이고 GPU 업로드 시 해당 정밀도로 변환한다.
따라서 CPU 전처리까지 순수 FP32로 수행하는 실험은 아니다. 독립 CPU 진단은 FP64/longdouble이다.
자동 미분용 dual 성분과 상태 반올림 보정용 low 성분은 구분하며, 전자의 미분 연산은 유지한다.

기존 개발 최적화 context를 별도 프로세스에서 동일하게 재사용한다. 소유 코드의 명시된 GPU 모듈을
lane별 동결 runtime으로 생성하고 원본 모듈을 수정하지 않는다. cuDSS dtype descriptor와 수치 자료형의
machine epsilon/tiny/sentinel도 변환한다. 물리·수렴 허용오차는 변환하지 않는다.
이 경로는 정밀도 영향 분리를 위한 개발 진단이며 새 production solver나 혼합 정밀도 채택이 아니다.

## 두 가지 분석 관점

1. **결과 차이:** `comparison.json.trajectory`에서 공통 성공 substep 전체의 위치·속도 최대 성분 차이와
   면적 가중 RMS 최대값을 확인한다. FP32–FP64 직접 비교와 각 lane–기존 hi/lo 비교를 제공한다.
   실패 후보를 정상 궤적에 포함하지 않으며, 무풍·무운동 구간만 같으면 동적 일치로 해석하지 않는다.
2. **솔버 오차:** 모든 substep의 내부 잔차·Newton/GMRES 상태·행렬 검증 오차·실패 코드를 저장한다.
   각 프레임 마지막 후보(실패 포함)는 독립 CPU 계산으로 힘 잔차, HVP 기반 선형 잔차, 공력 차이,
   탄성 에너지·변형률을 재평가한다. 정상 후보는 위치 업데이트·운동 에너지·에너지 장부·고정점도 확인한다.
   독립 진단은 모든 substep의 엄격 재검산이 아닌 표본 진단이다. 표본이 없는 값은 성공으로 간주하지 않는다.

`<lane>/frame_*.npz`는 모든 제출 단계 중 첫 실패까지의 원시 상태·실패 후보·선형 입력·진단을 보존한다.
`<lane>/report.json`은 실제 GPU 자료형·장치·완료 단계·프레임별 계산/전송/저장 시간과 파일 hash를 기록한다.
입력·runtime·cuDSS·native shim은 `manifest.json`으로 동결한다. 오류는 `<lane>.log`와 report에서 확인한다.

생성 시간은 GPU 풀이와 추가 진단 버퍼 기록·매 프레임 동기화를 포함한다. 초기화, 전송/저장/hash,
독립 CPU 분석은 분리한다. 첫 프레임에는 준비 영향이 있고 실패 lane은 실제 풀이 구간이 짧다.
실패 lane의 짧은 실행 시간이나 무풍 구간을 FP32 가속률로 해석하지 않는다. 기존 비동기 성능과 직접 비교하지 않는다.

기존 솔버의 힘/변위·선형·행렬 재구성·업데이트·유한성 기준을 유지한다. 기하 Bernstein 인증을
모든 단계에 적용한 기존 teacher audit를 대체하지 않으며, 이 진단에는 기하 인증 통과 판정이 없다.
원본 visual 기하 예외를 새 학습 승인으로 승계하지 않는다. `training_eligible=false`, R1 Gate 유지.

## 짧은 실제 검증

[선별 검증 결과](smoke_evidence.json). 원본은
`artifacts/runs/teacher_precision_compare/20260913_smoke_v2`다.
GTX1080Ti의 굽힘1/100 손수건,초기0–2프레임/128단계를 각 lane에 요청했다.
첫 프레임은 무풍이며 두 번째 프레임에 실제 바람이 들어온다.

- 기존 hi/lo와 순수 FP64는128단계 solver 완료. 두 결과의 최대 위치 성분 차이1.721e-17m,
  속도4.888e-13m/s. 독립 진단은 lane별2개 프레임 마지막 후보만 수행했다.
- FP32는 첫64개 무풍 단계 후 첫 유풍 단계에서 code7로 중단했다.
  보조 행렬 작용과 HVP 작용의 상대 차이는1.640e-7, 기존 허용치는1e-10이다.
  정상 움직임의 FP32 비교 구간은0개이며 FP32 장기 정확도·가속률을 얻은 것이 아니다.
- FP32 실패 후보의 독립 선형 상대 잔차는4.520e-6이다. 이는 해당 후보의 값이며 정상 수렴 결과가 아니다.
- 독립 분석 오류0, low part0·GPU 상태/힘/행렬/cuDSS/GMRES 자료형 기록 확인.
- 정밀도 변환3개 CPU 검사, 재사용한 종료 helper 관련3개 회귀 검사 통과.
- 전체10프레임/10초, 완화 허용오차, FP32 teacher 적격성, 새 정밀도 step graph 전체의 host-node 감사는 미완료다.

실험 입력·라이브러리는 기존 로컬 snapshot을 사용했다. 외부 fetch·다운로드·기존 결과 수정·commit·push 없음.
다음은 엄격 기준 실패 결과를 먼저 검토하고, FP32 전용 진단 허용오차를 별도 승인할지 결정하는 것이다.
