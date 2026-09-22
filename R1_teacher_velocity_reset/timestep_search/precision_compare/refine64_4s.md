# 굽힘1/100·4초 FP64 세 경로 비교

기존 메인컴 `20260913_cloth_coarse_4s_gpu_v6/bend_001`의 입력·물성·고정 조건·바람·dt를
그대로 동결해 **Pure FP64 기존 풀이와 FP64 보정**을 모두 실행한다. FP64 hi/lo는 기존 결과를 재사용한다. [짧은 비교에서 검증한 후보](adaptive_report.md)의
보정 상한4회·잔차 수축0.5·원래 EW 목표·실패 시 같은 RHS의 FP64 GMRES 전환을 사용한다.
hi/lo ↔ Pure FP64는 상태 산술 변경, Pure FP64 ↔ FP64 보정은 선형 풀이 변경 효과를 비교한다. 두 새 경로의 진단·저장 조건은 같다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_refine64_4s.sh
```

직사각형 → 삼각 깃발 → 손수건 순서로 각 메시의 Pure FP64 기존 풀이 → FP64 보정을 같은 GPU에서 순차 실행한다. 새 계산은 총6회다. 각240프레임·4초,
60Hz·64substep·dt=1/3840초다. 매 프레임 GPU 완료·계산 시간을 출력하고 기본2초마다
모든 substep의 상태를 무압축 저장한다. 상태 low 배열은 파일 호환성을 위해0으로 보관한다.
두 경로의 전체 원시 상태는 약10.2GB이며 검산·작은 솔버 진단 기록은 별도다.

기본 출력은 `artifacts/runs/teacher_timestep_search/20260913_cloth_three_fp64_4s_v2`이다.
종료하면 이 폴더에 **`comparison.md`, `comparison.json`을 자동 생성**한다. 개별 실행은 `fp64/bend_001/`, `refine64/bend_001/`에 저장한다. 이전 단일 후보 동결본 `20260913_cloth_bend001_refine64_4s_v1`은 보존한다.

```bash
# 한 메시만 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_refine64_4s.sh --shape handkerchief
# 백그라운드 실행 / 상태 / 기존 저장 결과 재분석
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_refine64_4s.sh --background
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_refine64_4s.sh --status-only
bash experiments/R1_teacher_velocity_reset/timestep_search/run_cloth_refine64_4s.sh --compare-only
```

`--prepare-only`는 입력·코드·native library를 동결하고 계산하지 않는다. `--out`으로 별도 실행을
만들 수 있다. 동결 후 작업 코드 변경을 자동 반영하지 않는다. Ctrl+C는 전체 비교와 소유 worker를
종료하며 확정 파일을 보존한다. interrupted/running/paused 결과는 자동 재개하지 않는다.
기존 완료 메시를 보존한 채 아직 ready인 메시만 실행할 수 있다.

## 비교 구간과 정확도 정책

| 기존 메인컴1/100 메시 | 정상 확정 프레임 | 정상 구간 | 종료 원인 |
| --- | ---: | ---: | --- |
| reference_rectangle | 174 | 2.9000초 | 기하 충분조건 실패 |
| triangular_flag | 183 | 3.0500초 | 기하 충분조건 실패 |
| handkerchief | 98 | 1.6333초 | 기하 충분조건 실패 |

이전 실행은 **4초 목표**였으며1/100은4초 완료 결과가 없다. 실패 프레임과 미저장 구간을 빼고
공통 정상 저장 프레임의 시간·궤적을 비교한다. **두 새 풀이끼리는 모두 완료하면4초 전체를 비교**한다. 기준보다 새 실행이 먼저 중단되면 교집합을 더 줄인다.
서브컴 완료10초 run `sub_pc/20260912T223433Z-aca6fc4223714a02a9fe8afe7f4edeef`는
RTX5070으로 계산했으므로 이 메인컴 GTX1080Ti 시간비의 분모로 사용하지 않는다.

앞서 승인한 **정밀도 diagnostic 정책**을 적용한다. 허용오차 수치는 유지하면서 유한한 미수렴·힘·업데이트·
에너지 장부·기하·고정점 오차 초과를 원래 flag/시각/횟수로 남기고 진행한다. 비유한 값·질량 풀이 오류·
계산 불능은 중단한다. 기하 검사는 독립 FP64/hi-lo 원본 모듈을 사용한다. 이 정책은 기본 strict 모드나
10초 visual 예외의 범위를 바꾸지 않으며 `diagnostic_only=true`, `training_eligible=false`다.
완료240프레임은 엄격 teacher 검산 통과를 뜻하지 않는다. 셀프컬리전·주름/바람 모델은 변경하지 않았다.

## 자동 비교 항목과 타이머

- 공통 정상 구간: 매 프레임의 계산·독립 검산 시간 합, 최대/RMS 위치·속도 차이, 힘 잔차 비율·업데이트·
  에너지 장부·변형률/곡률 상한, 검사 경고 수, 새 풀이의 보정·GMRES 전환 횟수.
- 새 전체 저장 구간: 같은 검산 요약, 보정/전환 누적 횟수, 솔버 경고. 총 에너지·선형 잔차 기록은
  `chunks/*.diagnostic.npz`에 남긴다. 마지막 선형 풀이 값이므로 Newton 풀이가 없는 단계에서는 이전 값일 수 있다.
  기존 결과에는 같은 에너지 기록이 없으므로 총 에너지 궤적 차이까지 계산했다고 해석하지 않는다.
- CPU/GPU·플랫폼이 다르면 속도비를 내지 않는다. 같아도 과거/현재 GPU 부하·클록은 통제하지 않은 관측 시간비다.
  새 진단 기록 비용도 계산 시간에 포함한다. 정확도 경고가 생기면 같은 정확도에서의 가속으로 해석하지 않는다.
- `preparation.json`: 입력·동결본 준비. `pre_setup_s`: worker 시작부터 모델·입력 준비까지.
  `setup_s`: 기존과 같은 솔버·독립 검산기·상태 버퍼 초기화. `diagnostic_setup_s`: graph 검사·추가 진단 버퍼.
  `compute_audit_s`: 계산·검산·GPU 기록·프레임 동기화와 구간 제출.
  `boundary_check_s`: 저장 경계의 상태·factor 확인. `write_s`: CPU 전송·무압축 쓰기·hash.
- `worker_function_s`는 위 하위 구간과 정리를 포함한다. `worker_process_s`는 프로세스 시작·종료 확인까지,
  `controller_timing.json`은 선택한 worker들과 관리 시간을 포함한다. `comparison_wall_s`는 최종 원본 검증·비교 시간이다.
  포함 관계가 있는 시간을 중복 합산하지 않는다. 이전에 없는 전처리/프로세스 시간은 null로 남긴다.
  서로 다른 전체 구간의 총 소요 시간을 나눠 전체4초 가속률로 표시하지 않는다.

묶음과 각 경로의 `config.json`·`manifest.json`, 각 경로의 `reference/` 보고서 사본으로 원본과 새 설정을 식별한다.
원본 코드·입력·보고서·프레임 로그 및 확정 NPZ hash를 확인하고 비교한다. 큰 상태 NPZ는 프레임 단위로
읽어 서로 다른 저장 청크 경계도 대조한다. 기존 산출물은 수정하지 않는다.

## 준비 검증

[검증 근거](refine64_4s_validation.json): CPU5개·소유 worker 중단3개 검사 통과.
`20260913_cloth_refine64_smoke_v2`는 세 메시 각각2프레임/128단계, 이후 초기 모듈 load 위치를
정리한 `smoke_v3`는 손수건2프레임을 실제 GPU에서 확인했다. 독립 물리/기하 경고0,
조건부 graph의 host 전송/콜백0, 저장 원본과 자동 비교 통과다.
후속 세 경로 묶음은 두 풀이×세 메시 각각2프레임·128단계의 실제 GPU 계산, 독립 검산 경고0, 세 쌍 자동 비교를 확인했다. [준비/검증 근거](three_fp64_4s_validation.json). 본4초 실행은 사용자가 위 명령으로 시작한다.
짧은 검증은 실행 연결·독립 검산·자동 비교 확인이며4초 속도나 장기 안정성의 근거가 아니다.

진단 NPZ 열: `counts[:,0:17]` 기존 solver control, `[:,17:27]` adaptive counter 순서
(`resident_adaptive_precision.COUNTER_NAMES`), `[:,27]` solver warning bitmask, `[:,28]` fatal code.
`values`는 단계 시작 총 에너지·에너지 장부 오차·외력이 한 일, 마지막 선형 RHS norm·목표 norm·참 잔차 norm 순서다.
단계 끝 총 에너지는 앞의 세 값을 더해 얻는다.

Pure FP64 기존 풀이의 adaptive counter 열은 미사용0이다. GMRES 반복 작업량은 기존 solver control 기록으로 확인한다.
