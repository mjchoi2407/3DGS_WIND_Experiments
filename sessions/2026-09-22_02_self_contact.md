# P3 셀프 접촉 CPU/GPU 비교·실행 준비

## 현재 상태

- 확인일: 2026-09-22. v8 직사각형112번째 프레임을 같은 저장 상태·동결 runtime으로 재현해 최초 GMRES code2를 확인했다. cycles6도 실패했고 dt절반은128단계 전체 승인됐다.
- 실제 GPU 자동 복구도 통과했다. 버린 실패 시도와 재시도 비용을 모두 포함하며 단일 프레임 해결을 장기 완주/성능비로 일반화하지 않는다.
- 원본/config/코드 hash·상세 수치는 [같은 입력의 실패·복구 비교](../R1_teacher_velocity_reset/self_contact/frame112_recovery.md#같은-입력-비교)가 소유한다. 관련 고유 회귀54개 통과, 세 씬 스크립트는 새 `manual_v10` 준비·본 실행 미시작이다.
- 메인 v8의108프레임 외부 종료라는 과거 추정은 정정한다. 서브컴 공유 저장 원본도 확인했으나 해당5070 실패 프레임의 실제 복구는 미검증이다.
- 기존 원본·사용자 중단 실행을 수정/재개하지 않았다. 다음은 사용자 v10 본 실행 확인이며 시간 수렴·R1/학습 적격성은 미완료다. 푸시 전 원격 동기(HEAD...origin/main `0/0`)와 code 집중 GPU 회귀 `54 passed in 60.02s`를 확인했다.

- 상세 위치: [실행·재현 명령](../R1_teacher_velocity_reset/self_contact/frame112_recovery.md#재현), [접촉 비용·병렬화 분리](../R1_teacher_velocity_reset/self_contact/idle_performance.md#같은-실행기에서-분리한-접촉-비용과-병렬화-효과), [기하 인증으로 해결한 이유](../R1_teacher_velocity_reset/self_contact/refined_geometry.md#왜-해결됐는가).

## 이전 구현과 검증 — 당시 상태

- 확인일: 2026-09-22. BVH v5 수치 기준에 자동 시간 보정과 제한적 code2 복구를 더한 `manual_v9`을 세 씬 사용자 실행 기준으로 준비했다. 추가 수치 최적화 종료, 장기 완주·R1 미완료.
- GTX1080Ti v8의 내부 raw 시간이 frame wall보다 약6%, RTX5070 저장 결과는 약11.1% 크게 표시된 문제를 graph 전체 marker 기반 프레임별 배율로 보정한다. Raw와 배율은 report에 보존한다.
- V5 실패는 GMRES720 한도 code2가 audit99로 덮인 것으로 진단했다. v9은 원래 code를 보존하고 code2·contact/path0만 cycles3→6으로 한 번 GPU 재실행한다. 다른 오류와 재실패는 계속 거절한다.
- 동결 cuDSS 관련 GPU 회귀113개 통과. v9 suite/manifest hash 확인, 세 씬 준비 완료·미실행. 과거 실패 frame 실제 복구와 장기 완주는 아직 근거가 없다.
- 프레임마다 GPU 프레임, solver 전체, collision 합계와 solver/audit 분할, audit 전체 및 GMRES 누적을 터미널과 run log에 출력한다. 구간은 중첩되므로 합산하지 않는다.
- 관련 GPU 회귀140개 skip0/fail0, 동결v8 세 씬6프레임384단계 smoke 통과. v5 대비 상태 오차는 기존 허용 범위이고 여섯 프레임 시간 변화 중앙값+0.95%였다.
- v5 직사각형 본 실행은 preload120·calm240 완료 후 wind104프레임을 승인하고 다음 프레임에서 code99/flags[0,14]로 rollback 종료했다. 원본을 보존하고 장기 완주로 세지 않는다.
- BVH 순회/정밀 거리 분리의 제한 프레임 추가 단축을 같은 입력·GPU의 순서 교대 측정으로 확인했다. 예열 제외54프레임2,472단계와 상태 대조 통과.
- 이전139개 회귀와 동결v5 국소6사례56단계·세 씬6프레임384단계 근거를 유지한다. Fresh v9 본 outputs는 없고 v8 부분 실행은 별도 보존한다.
- 이전v4의121개 회귀(skip0/fail0), 국소6사례56단계·세 씬6프레임384단계 통과. CPU oracle·GPU host copy/callback0 확인.
- 후보 공통 항·제한 worker·GPU CCD 작업 큐와 기존 경로의 동치를 확인했다. 후속 유휴 재측정에서 전체 개선과 불확실한 마지막 병렬화 이득을 구분했다.
- 작은2단계3경로 측정 도구 기능 검사를 완료했다. 공유 GPU에서 항상 빨라진 것은 아니며 성능 수치는 미채택이다.
- 중복 힘 평가/보조 RHS 재사용, GMRES 초기화 병렬화, 빈 접촉 분기, 검산 Hessian 제거를 검증했다. 물리·승인 기준 유지.
- 같은 v2 상태와 허용오차 내 동치이며 손수건 wind의 선형 반복1회 차이는 보고서에 보존했다.
- 접촉 Hessian 배열만 약50% 감소했다. 총 VRAM 감소율이나 최종 가속 배수로 일반화하지 않는다.
- 기존 bend500 입력 hash·재료·외력·공식 허용오차를 유지한 GPU 전용 개별 세 스크립트를 준비했다.
- 정밀 기하 v2로 초기3씬 검사와 중력/최대풍6프레임384단계 GPU 검산을 통과했다. 활성 접촉 없는 연결 시험이다.
- 같은 GPU에서 순차 실행하고 계산/검산·setup·저장을 구분했다. 원본과 코드/native를 hash로 동결했다.
- 국소 barrier1,000/10,000×3사례를 비교했다. 총56개 GPU 시간 경로와 CPU IPC 대조가 통과했다.
- 사용자 승인 후 GPU 정밀 기하 인증으로 기존4사례12구간 미인증을 해결했다. 같은6사례56단계가 전체 검산을 통과했다.
- 물성·barrier·dt·비퇴화 요구는 유지했다. v1 실패 원본·기존 scalar flags를 보존하고10,000을 자동 채택하지 않았다.
- 초기 CPU OFF/LBVH/BruteForce·강도 비교·FP32 입력 양자화와 약한100 고속 실패는 기존 보고서에 보존한다. 당시 힘/CCD 통과와 후속 기하 승인을 구분한다.
- 관련106개 검사 통과·skip0·GPU graph host copy/callback0. 실제/거의 퇴화·한도 초과를 계속 거절함도 확인했다.
- 사용자 요청으로 v2 본 실행의 부모/worker만 종료했다. 저장 prefix·종료 전 report를 보존하고 중단 상태를 기록했다. 후속 씬 미실행·삭제 없음.
- 기존 manual_v2/v3를 보존하고 세 스크립트를 새 `manual_v4`로 갱신했다. 동결 source244개·native/입력 검증, 본 outputs 없음.
- 공유 부하에서 중간 후보의4조건 비교만 완료하고600초 제한으로 종료됐다. 동시 GPU 작업을 사용자에게 확인했으며 수치는 성능 근거로 미채택·보존했다.
- 사용자 유휴 확인 후 통제 ON/OFF/재사용/병렬과 실제 동결v1/v4를 새로 측정했다. 예열 제외135프레임7,164단계 모두 승인·상태 대조 통과. 다른 GPU 작업은 중단하지 않았다.
- 과거 최초 측정에도 부하가 있었을 가능성을 사용자에게 확인했다. 이전 배수는 순수 접촉 비용으로 채택하지 않고 원본을 보존한다.
- R1 접촉 절에 후속 구현·성능 보류를 반영하고 XeLaTeX PDF·bundle을 갱신했다. Gate/학습 적격성은 유지한다.
- 다음: 사용자 v9 본 실행에서 복구와 비용·세 씬 완주를 확인한다. calibration·proxy 공간 수렴은 미완료이며 기존 출력 덮어쓰기·자동 재개는 없다.

명령·raw/hash·상세 수치: [v2 보고](../R1_teacher_velocity_reset/self_contact/refined_geometry.md), [v1 보존](../R1_teacher_velocity_reset/self_contact/gpu.md).
비용 분모·source/hash·메모리 산술값: [비용 보고](../R1_teacher_velocity_reset/self_contact/cost.md).
최종v3 코드·검증 snapshot·공유 부하 판정: [성능 점검](../R1_teacher_velocity_reset/self_contact/performance.md).
현재v4 실행·병렬 구조·검증·메모리: [병렬 개선](../R1_teacher_velocity_reset/self_contact/parallel_v4.md).
새 속도·비용·변동·동결 source/hash: [유휴 조건 재측정](../R1_teacher_velocity_reset/self_contact/idle_performance.md).
추가 개선·현행 실행·정확한 비교 분모: [BVH v5](../R1_teacher_velocity_reset/self_contact/broadphase_v5.md).
기본 진행 출력·v5 장기 실패·v8 검증: [프레임 계측](../R1_teacher_velocity_reset/self_contact/frame_timing_v8.md).
자동 보정·solver code 보존·v9 준비: [v9 보고](../R1_teacher_velocity_reset/self_contact/frame_timing_v9.md).
CPU 초기 근거: [기준 비교](../R1_teacher_velocity_reset/self_contact/README.md).
구현 계약: [code 기록](../../code/sessions/2026-09-22_01_self_contact.md).
서브컴의 이 GPU 접촉 run은 발견되지 않았고 RTX5070 검증으로 일반화하지 않았다. 원격 fetch·commit·push 없음.
