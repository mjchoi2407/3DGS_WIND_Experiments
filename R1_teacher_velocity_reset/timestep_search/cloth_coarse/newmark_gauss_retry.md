# Newmark 수렴 실패 시 Gauss6차8분할 재시도

## 현행 실행

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_newmark_gauss_retry.sh
```

기존 `run_newmark_dt_retry.sh`도 이제 위 Gauss 재시도 스크립트로 연결된다.
고정 dt 스크립트는 그대로다. 과거 half-dt 실행과 동결 runtime/result는 보존했다.
옛 half-dt 설정을 새로 재현하려면 `teacher_newmark_dt_suite --mode retry --out <새 경로>`를 명시한다.

현재 출력은 `artifacts/runs/teacher_timestep_search/newmark_dt_gauss_retry_bend500_v1/<shape>/`다.
직사각형→손수건→삼각형 순차 실행, 굽힘1/500·FP64 hi/lo·중력2초 후 무풍/바람4초씩 분기한다.
`--prepare-only`, `--status-only`, `--out <새 경로>`, `--smoke`를 지원한다.

- 정상: Newmark64substep/프레임, dt1/3840초.
- 수렴 실패: 직전 정상 상태와 원래 held 외력에서 그 한 구간만 Gauss3stage6차·8단계(dt1/30720초)로 다시 계산.
- 성공: 다음 기본 구간은 Newmark로 복귀. 실패 반복 시 고차 적분을 유지하는 정책은 이번에 추가하지 않았다.
- Gauss도 실패하거나 물리/기하 검산이 실패하면 중단. 추가 half/quarter step 없음.
- 현재 수렴 실패 조건은 유한 통계의 code1 Newton/2 GMRES/3 line search와 정상 prefix 검산이다.
  옛 투영 기하 경고는 전환 조건이 아니다. 기본 정확도 기준은 유지한다.

## 검산·기록

Gauss는 stage/끝점/에너지/cubic 기하의 자체 GPU 독립 검산을 사용한다.
Newmark 식으로 Gauss를 검사하지 않는다. [구현 계약](../../../../code/docs/newmark_gauss_retry.md).
상태는60Hz 원시 hi/lo로 저장하며, 모든 채택 단계의 검산과 dt·method를 저장한다.
`method=0`은 Newmark,1은 Gauss다. `gauss_checks`에는 Gauss 단계의 원래11열 검산을 별도로 보존한다.
flags 비트의 의미도 method별이므로 기존 Newmark용 해석기를 그대로 적용하지 않는다.
`frame_timings.jsonl`은 half_dt_retries=0과 gauss_retries를 구분하고 모든 실패/재시도 비용을 포함한다.

## 재생

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_newmark_gauss_retry.sh reference_rectangle wind
```

다른 씬/phase/`--out` 선택은 기존 뷰어와 같다. 과거 `view_newmark_dt_retry.sh`는 과거 half-dt 결과 재생용으로 유지한다.
새 실행이 확정 chunk를 저장한 뒤 재생 가능하다. 실패/미완료 실행도 저장된 prefix만 표시한다.

## 검증 근거와 한계

출력 근거는 `artifacts/runs/teacher_timestep_search/newmark_gauss_retry_validation_v1/`이며
fixture/actual/smoke 명령·로그, 실제 입력 hash, 저장 상태와 method별 검산을 보존한다.
완료된 고정 dt run의 failure_state는 프레임 시작 상태다. 같은 프레임 외력을 재구성해 원본 held와 일치함을 확인했다.

실제 실패 프레임 두 곳의 결과:

| 씬·바람 frame(0기반) | 기본 Newmark 실패 | Gauss 재시도 | 프레임 전체 |
| --- | --- | --- | --- |
| 직사각형103 | 기본 substep37, line search code3 | 해당 구간8단계1회 | 64기본 구간/71채택 단계 검산 통과 |
| 삼각형120 | 기본 substep60, line search code3 | 해당 구간8단계1회 | 64기본 구간/71채택 단계 검산 통과 |

각 프레임의 실패 시도+복구+나머지 계산·검산은78.721초/17.585초였다.
과거 half-dt의 다른 장치/입력/실행 시간과 배속을 계산하지 않는다. 성공한 두 프레임은 장기 가속 근거가 아니다.
작은 GPU fixture에서 정상 단일 Newmark, 실패 직전 raw hi/lo 복원, Gauss8단계 dt/방법 기록과 자체 검산,
Gauss 재실패 시 프레임 시작 상태 보존을 확인했다.

전체3씬 본 실행, 잦은 전환 시 시간/안정성, 순간속도·에너지 장기 정확도와 teacher 적격성은 미완료다.
Gauss 재시도 성공을 전체 Gauss 단독 실행과 동일한 궤적/정확도라고 해석하지 않는다.

### 완료 검증

실제2프레임/142채택 단계와 세 씬×3phase 각1프레임/576단계의 독립 검산·저장 hash·시간 합·분기 검증을 통과했다.
[선별 근거](newmark_gauss_retry.json). 본3씬은 ready0이며 긴 실행은 시작하지 않았다.
CPU 중력 회귀6개, Python/shell 구문 검사, 변경 경로 diff 검사 통과.
R1에 적분기별 검산과 개발 범위를 반영했고 canonical PDF/bundle을 실제 빌드·검증했다.
기존 고정/half/Gauss 단독 결과와 실행 중 프로세스는 변경하지 않았다. stage/commit/push 없음.
