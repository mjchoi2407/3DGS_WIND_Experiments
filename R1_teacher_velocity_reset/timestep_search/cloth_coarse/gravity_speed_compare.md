# 깃발 중력 조건의 최초 하이브리드/현재 풀이 비교

## 현재 상태

2026-09-14 상태 확인. 최초 하이브리드 경로의 preload는 완료했으며 calm은 사용자가 직접 종료했다.
확정 저장120프레임을 보존한다. Hybrid wind와 resident 세 단계는 미실행이다. 추가 비교/재개는 보류하며
완주 성능비나 전체 궤적 동등성을 주장하지 않는다. CPU8개 통과는 준비 당시 검증이다.
기본 출력 `artifacts/runs/teacher_timestep_search/gravity_flag_hybrid_compare_v1`은 interrupted 상태이므로
아래 기본 실행 명령으로 자동 재개되지 않는다. 향후 다시 요청할 경우 새 `--out`이 필요하다.

## 실행

기존 GPU 실행이 끝난 뒤 짧은 검증부터 수행한다. 같은 GPU에서 다른 시뮬레이션과 동시에 실행하면 속도 비교가 왜곡된다.

```bash
# 별도 짧은 연결 검증: 각 단계2프레임, 양쪽 합계768substep
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_speed_compare.sh --smoke --out experiments/artifacts/runs/teacher_timestep_search/gravity_flag_hybrid_smoke_v1
# 전체 비교: 최초 하이브리드 → 현재 GPU, 각각 중력2초+무풍4초+바람4초
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_speed_compare.sh
# 읽기 전용 상태
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_speed_compare.sh --status-only
# 완료 결과 재분석
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_speed_compare.sh --compare-only
```

완료 시 출력 루트에 `comparison.md`·`comparison.json`이 생성된다. interrupted/실패 실행은 자동 재개하지 않는다. Ctrl+C는 현재 소유 worker를 종료하며 다음 lane을 시작하지 않는다. 확정 청크를 보존한다.

## 비교 계약

- 직사각형 깃발(`reference_rectangle`) 왼쪽 고정, 해상도16·384삼각형·1813노드, 굽힘1/100. FP64 hi/lo 계열,60Hz·64substep,dt1/3840초.
- 중력−Z, 처음1초 ramp 포함2초 준비. 각 lane의 준비 끝 hi/lo 위치·속도를 자체 무풍4초/바람4초에 그대로 전달한다. 양쪽 최초 rest는 동일하지만 바람 분기 시작에는 각 preload의 수치 차이가 포함된다. 결과 비교도 이 누적 차이를 포함하며 강제로 같은 checkpoint를 주입하지 않는다.
- 최초 하이브리드 기준은 `20260913_gpu_resident_10frames_v1`의 `P3ShellWarpPrecisionStepper` + `AdaptivePreconditionerStepper`다. CPU 적분/반복 제어·CPU 보조 풀이·GPU 힘 평가, rest 우선·32반복 전환·기존 EW 정책을 유지한다. 선택한 핵심8파일은 과거 manifest·보존 원본·현재 파일 SHA256 일치를 준비 시 확인하고 기록한다.
- 현재 경로는 GPU 상주·병렬 합산·첫 보조 풀이 재사용·current 우선·채택 평가 재사용을 적용한다. 두 경로의 원시 위치/속도는 동일한 f64 hi/lo 배열 형태로 기록하되 최초 하이브리드의 내부 상태는 기존 longdouble 기반 방식이다.
- 양쪽에 같은 중력 추가, **공통 GPU 독립 검산·국소 기하 정책·무압축2초 저장**을 연결한다. 따라서 과거 CPU 검산·압축 저장까지 포함한 프로그램 전체 복원 비교가 아니다. 과거7.378배 기록과 직접 비교하지 않는다. 셀프컬리전·학습 적격 판정 없음.
- 새 lane 모두 입력·코드·라이브러리를 별도로 동결한다. 기존 실행 결과는 사용하거나 변경하지 않으며 새로 순차 측정한다.

## 시간과 정확도 해석

`solve_record_s`는 프레임 외력·64단계 풀이·공통 GPU 기록 버퍼 전달을 GPU 완료까지 측정한다. 하이브리드의 공통 기록기 업로드 비용도 포함한다. `audit_s`는 GPU 독립 검산 및 완료 대기, `compute_audit_s`는 앞 항목에 속도/중력 에너지 진단까지 포함한다. 분리를 위한 GPU 완료 확인을 양쪽 같은 위치에 둔다.
`save_s`는 청크 읽기·무압축 저장·hash 및 저장 경계 검사, `setup_s`는 모델 구성 이후 솔버·검산 준비, `worker_s`는 setup부터 최종 checkpoint 생성까지다. 입력 hash·모델 구성은 worker 타이머 밖이며 controller 전체 시간에는 포함된다. 따라서 이 항목들을 임의로 합쳐 중복 계산하지 않는다.

자동 분석은 저장 파일 hash·외력 입력 일치·청크 시간축·완료 프레임을 검사하고 모든 저장 substep의 위치/속도 성분 최대 차이와 검산 flag 수를 기록한다. 양쪽 물리 검산 통과만으로 두 궤적이 동등하다고 자동 채택하지 않는다. 단일 순차 실행의 관측 시간비이며 부하/클록 변동을 통제한 통계적 벤치마크는 아니다.

## 재생

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh wind --out experiments/artifacts/runs/teacher_timestep_search/gravity_flag_hybrid_compare_v1/hybrid
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh wind --out experiments/artifacts/runs/teacher_timestep_search/gravity_flag_hybrid_compare_v1/resident
```

`preload`·`calm`도 같은 방식으로 선택한다. 로컬 snapshot만 사용했고 외부 fetch·commit·push 없음.
