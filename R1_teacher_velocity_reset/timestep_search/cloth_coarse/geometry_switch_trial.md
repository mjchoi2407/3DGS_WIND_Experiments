# 기하 경고만으로 Newmark/Gauss 전환 재시험

2026-09-15. 사용자가 요청하지 않은128분할 시간 오차 감시 비용을 제거하는 별도 시험이다.
선행 [시간 지표 시험](integrator_switch_trial.md)은 당시 결과로 보존한다.
물리식·FP64 hi/lo·공식 독립 검산 허용오차·학습 Gate·기본 생성기는 유지한다.

## 설정과 판정

- `newmark_geometry_switch_v2`의 입력은 선행 시험과 같은 직사각형1/500,384삼각형/1813 P3 노드다.
- 초기 처짐 프레임0 및 바람 프레임120의 원시 hi/lo 상태와 held 외력 각각에서1/60초를 계산한다.
- Newmark64단계(dt=1/3840초)를 한 번 계산하고 기존 `local_metric` 검산을 수행한다.
- 완료된 풀이의 기하 flag16 단독 실패만 같은 시작 상태의 Gauss6차512단계(dt=1/30720초) 재계산으로 연결한다.
- 다른 검사/솔버 실패가 있거나 재계산도 실패하면 상태를 채택하지 않는다. 기하 검사는 자기 충돌 검사가 아니다.
- 128분할 solver를 만들지 않으며 시간 오차 추정도 호출하지 않는다. 공통 config의 rtol/atol 항목은 이 모드에서 사용하지 않는다.
- 독립 Gauss 대조군은 비교용 추가 실행이다. 전환 프레임 시간에는 이 대조군 실행 시간을 합산하지 않는다.

## 재현과 근거

출력: `experiments/artifacts/runs/teacher_timestep_search/newmark_geometry_switch_v2/`.
`commands.json`은 실제 명령/종료 코드, `manifest.json`은 동결 입력/runtime,
`evidence_manifest.json`은 최종 근거 hash를 소유한다. `summary.json`, `analysis.json`,
각 seed의 `report.json`과 trace/audit NPZ를 보존한다. [compact evidence](geometry_switch_trial.json).

```bash
.venv/bin/python code/scripts/prepare_integrator_switch_trial.py --out <새 출력 경로>
# 환경/라이브러리 연결과 두 seed의 실제 실행 명령은 보존된 run_batch.py와 commands.json 참조
# 핵심 옵션: run_integrator_switch_trial.py --mode geometry --input <입력> --out <새 결과> --repeats 2
```

GTX1080Ti에서 두 seed를 순차 실행하며 각 seed는 전환→Gauss, Gauss→전환 순서로 두 번 반복한다.
타이머는 GPU 완료·상태 기록·검산·선택을 포함하고 초기화/워밍업/파일 저장을 제외한다.
Gauss 단계 기록과 검산도 포함한다. 장치 독점은 확인하지 못했으며 전체 데이터 생성 시간/다른 장치 성능으로 일반화하지 않는다.
메인컴의 국소 시험이며 sub_pc 경로는 기존 목록만 조회했다. 원격 fetch/download는 하지 않았다.

## 검증 범위

작은 GPU fixture에서 정상 단일 채택, 시간 추정 호출 금지, 기하 flag16 주입 후 원상 복원과
Gauss 단독 대조, 기하+힘 등 혼합 오류 및 솔버/질량/검산 시간 실패 배제를 확인했다.
주입 검사는 제어 분기 검증이며 실제 기하 실패를 고친 증거가 아니다.
실제 저장 상태의 수치 비교와 통과 범위는 아래 결과와 compact evidence를 따른다.
기존 검산 통과만으로 시간 적분 오차/장기 안정성/teacher 적격성이 해결됐다고 해석하지 않는다.

## 완료 결과

| 입력 | 기하 전용 전환 경로(2회) | 같은 실행의 Gauss 단독(2회) | 채택 |
| --- | --- | --- | --- |
| 초기 처짐 | 1.8716 / 1.8714초 | 42.0636 / 42.2519초 | Newmark64 |
| 바람2초 상태 | 10.2717 / 10.6447초 | 57.7623 / 52.1992초 | Newmark64 |

두 개의 물리 입력에서 각2회, 두 모드의 총8회 프레임 계산과2304단계 독립 검산을 통과했다.
정상 전환4회는 모두 한 번만 풀었고 자연 발생 기하 경고/재시도는0회다.
모든 trace의 시작 원시 hi/lo가 입력과 일치하며 초기 manifest194개 hash를 검증했다.
선행 전환 시험의 입력6개와도 hash가 일치한다. 작은 주입 fixture는 위2304단계 분모 밖이다.

이전1/500 preload 첫 로그는 계산·검산 포함1.674초였고 이번1.87초는 같은1~2초 범위다.
선행 v1의 Newmark 자체5.9초와 이번1.87초는 반복 수가 같아도 측정 조건이 달랐다.
Gauss 단독도 선행128초에서 이번42초로 달라졌으므로 v1→v2 전체 배속을 정책 변경 효과로 주장하지 않는다.
128분할 감시와 불필요한 Gauss 재계산을 제거한 사실은 실제 시도 수로 확인했다.

### 움직임/정확도

같은 프레임 공통65시각에서 Gauss512와 비교한 Newmark64의 consistent mass 가중
속도 상대 RMS 차이는 초기 처짐3.15%, 바람65.67%다. 최대 노드 위치 차이는
각1.78nm/1.31mm, 최대 노드 속도 차이는4.60µm/s/3.45m/s다.
이는 선행 시간 지표 시험에서 계산했던 Newmark 결과와 같은 수준이며 정확도 개선이 아니다.
프레임 끝점만 비교하면 속도 상대 질량 norm은3.95%/73.70%로, 전 구간 RMS와 구분한다.
Gauss512도 연속시간 정답으로 인증된 참조는 아니다.

기하 전용 정책의 실행/분기 비용은 확인했지만, 실제 기하 경고의 해결 성공률,
연속 전체 궤적, 장기 안정성과 teacher 정확도는 미완료다. 기본 생성기는 변경하지 않았다.

## 실제 실패 구간 후속 확인

[원본 기하 실패5건 재계산](logged_geometry_retry.md): 옛 투영 경고는 Newmark/Gauss 모두 재현됐고 Gauss 해결0/5건이다. 두 방법 모두 현행 국소·물리 검산은 통과했다. 현행 국소 인증 실패의 재시도 성공률과 구분한다.
