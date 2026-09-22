# 10초 P3 시간 간격 탐색 인계

## 현재 상태

- **최신 검증(2026-09-12):** 같은 어려운 4프레임에서 수렴 여유 3조건 비교 완료, 각 256단계 원식 검산 통과. 내부 30% 목표+EW 상한 1e-4는 최대 잔차가 공식 허용치의 2.075%, 현재 EW보다 풀이 시간 17.1% 감소했다. 후속 검증 우선 후보이며 장기 기본값은 미채택이다. 공통 코드·본 실행 미변경, 다른 상태·재시작 검증이 남았다. [조건·결과·한계](../R1_teacher_velocity_reset/timestep_search/evidence/inexact4_margin_20260912/README.md).

- **최신 검증(2026-09-12):** 본 실행 v2는 첫 2.5초·150프레임 검산 통과 후 계획된 정지다. 사용자 승인으로 어려운 127~130번 연속 프레임의 strict/EW 비교를 완료했다. 양쪽 256단계 통과, EW 풀이 시간 28.8%·HVP 36.9% 감소. 최대 힘 잔차가 허용치의 99.24%여서 다음은 수렴 여유·비용 균형 보완이다. 장기 기본값 미채택, 본 실행 미변경. [조건·결과·한계](../R1_teacher_velocity_reset/timestep_search/evidence/inexact4_hard_20260912/README.md). 아래 준비·실행 대기 표기는 이전 상태다.

- **최신 검증(2026-09-11):** 사용자 승인으로 4배의 동일 1프레임(64단계)에 내부 선형 허용오차 조절을 시험했다. 네 조건 모두 기존 최종 힘 기준과 독립 검산 통과. EW2형은 HVP 39.5% 감소, 공유 GPU 관측 계산 시간 약 33% 감소. 관련 8개 검사 통과. [조건·결과·한계](../R1_teacher_velocity_reset/timestep_search/evidence/inexact4_20260911/README.md). 장기 기본값은 미채택이며 진행 중 본 실행은 변경하지 않았다. 다음은 어려운 상태·연속 구간 검증이다. 아래 준비/대기 표기는 이전 시점 기록이다.

- **최신 정정(2026-09-11):** 사용자 확인으로4시간은 새10초 본 실행 전체의 한도이며 이전 실행·개발 시간을 차감하지 않는다. 초기 상태·사용0초의4배 전환v2를 준비만 했다.2.5초마다 정지하고 같은 본 실행의 시간은 누적한다. [새 실행·검증](../R1_teacher_velocity_reset/timestep_search/evidence/adaptive4_four_hour_20260911/README.md). 아래 잔여 예산 표기는 이전 해석이며 이번v2에는 적용하지 않는다.

- **최신(2026-09-11):** 초기rest·어려운 구간current 전환을 구현하고 개발 검증했다. 같은 전환1배 대비 초기0.1초4배의 가속과1% 수치 보간 비교 통과, GPU 재개 차이0·16개 검사 통과. [정확한 범위·비용·새 실행](../R1_teacher_velocity_reset/timestep_search/evidence/adaptive4_20260911/README.md). 새본 실행은 잔여7368.317275초로 준비만 했으며2.5초/10초/공간 수렴은 미완료다.

- **최신 판정(2026-09-11):** 4배 실행 연결·21개 검사·실제GPU 재시작 검증 완료. 본 실행은 초기0.1초 비용이 과거1배보다 커서 기존 사용자 비용 조건에 따라 일시 중단했다. 확정7frame 보존,2.5초/전체 정확도 미완료. 수치 실패·예산 소진이 아니다. [비용·잔여 예산·다음 분기](../R1_teacher_velocity_reset/timestep_search/evidence/segments4_20260911/README.md). 초기rest 보조 풀이 활용 검토 여부를 질문한다.

- **최신(2026-09-11):** 사용자 승인으로4배 실행 연결·재시작·2.5초 계산·구간 판정까지 진행한다. 현재 재사용의 frame 경계 초기화, 각 구간 정지와 부분 구간 비교를 구현했다. 관련21개 검사 통과. [동결 설정·결과](../R1_teacher_velocity_reset/timestep_search/evidence/segments4_20260911/README.md). 이전 선택 대기는 해소됐으며 본 실행 잔여7998초를 유지한다.

- **최신 결과(2026-09-11):** 4배+현재 행렬 재사용의 짧은 전체 수치 보간 비교가1% 이내이며 같은 최적화1배보다 빨랐다.64배는1단계만 통과,32배는 재사용/매번 재구축 모두 비선형 line_search 실패. 준뉴턴·장기 검증은 미완료이며4배 긴 구간 우선 여부의 사용자 선택 대기. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/acceleration4_20260911/README.md).

- **최신(2026-09-11):** 사용자 선택으로4배 무보정 → 행렬 재사용 → 필요 시 준뉴턴 →32배·64배 확장 순서로 변경했다. 같은 최적화의1배보다 느리면 장기 채택하지 않는다. [현재 시험·기준](../R1_teacher_velocity_reset/timestep_search/evidence/acceleration4_20260911/README.md). 기존256배 전용 방침은 이전 결정이다. 물리·허용오차·본 실행 잔여 예산은 유지한다.

- **최신(2026-09-11):** 사용자 승인으로 물리·허용오차·256배를 유지한 빠른 탄성 진동 분리 시험을 수행했다. 시작/중간 접선 지수 후보는 시간 정확도 미달로 보류하고, Gauss6 경로+지수 보정 후보와2/4분할 참조의 국소 끝 상태 차이 감소를 확인했다. [현재 판정·근거](../R1_teacher_velocity_reset/timestep_search/evidence/exponential256_20260911/README.md). 결합 후보의 끝 상태1% 비교는 통과했으나 전체 시간 곡선·n=32 재개·엄격한 형식 간 동등성은 미완료다. 다음은 지수 작용 정밀도·비용 및 전체 곡선 검산 보완이다. 본 실행 잔여7998초 유지, 기존 wrapper는 Newmark용이며 새 장기 실행은 미연결이다.2.5초/10초·해상도 수렴·R1 채택은 미완료이며 작은 Δt 자동 전환은 하지 않는다. 아래 이전 선택 대기는 과거 기록이다.

- **최신(2026-09-11):** 사용자는32배 축소 대신64배 풀이 개선 후256배 진행을 선택했다. 탐색 방향 보존 수240·3주기(최대720회)로 기존 실패 단계와 후속4단계의 독립 검산을 모두 통과했다.64배·2.5초 구간·잔여7998초의 새 v4를 rest부터 실행하도록 준비했다.10초·시간 정확도·해상도 수렴·256배는 미완료이며 장기 계산은 사용자 실행 대기다. [결과·명령](../R1_teacher_velocity_reset/timestep_search/evidence/gmres_restart_20260911/README.md). 아래 v1–v3 준비/선택 대기는 과거 기록이다.

- **최신 채택:** 사용자 선택으로64배 Δt를 유지하고 선형 반복 한도12를 새 v3에 반영했다. 다른 정확도 기준·바람은 유지, v1/v2 보존·rest부터 재검증한다. 관련15개 검사와 동결 CUDA smoke 통과. 남은 본 실행 예산12072초,2.5초씩 이어가기 설정으로 준비 완료·사용자 실행 대기다. [근거·명령](../R1_teacher_velocity_reset/timestep_search/evidence/linear_cycles_20260911/README.md#채택과-새-실행-준비).

- **최신:** v2는2.5초 구간 통과 후2.695833초에서 선형 반복 한도로 실패했다(38분30초, 시간 초과 아님). 동일 실패를 재현하고 한도8→12만 바꾼 시험에서5개 interval과 독립 CPU 원식·기하·에너지 검산을 통과했다.64배+한도12 장기 반영 또는32배 짧은 비교의 다음 선택 대기이며 기본 코드/동결 plan은 미변경이다. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/linear_cycles_20260911/README.md).

- **최신:** 사용자 v1 실행은 초기 frame1에서 반올림 검사 오탐으로 종료했다. 상쇄된 Newton 중간 수정량을 오차 예산에 반영해 수정했고, 실제 조건의 초기24 interval 독립 검산과9개 회귀 검사를 통과했다. 실패 원본 보존, v2 동결 준비 완료·사용자 실행 대기다. 기존 사용18초를 차감한14382초 예산으로2.5초씩 이어간다. [원인·검증·명령](../R1_teacher_velocity_reset/timestep_search/evidence/position_guard_20260911/README.md).

- **후속 완료:** 고정밀 stepper·hi/lo checkpoint·별도 탐색 schema를 연결했다. 단기8+6개 interval, 별도 프로세스 재시작·공력·기하·에너지 검산 및25개 검사를 통과했다. sub001 선형 풀이 실패는 별도 분모로 유지한다. 사용자 선택으로4분할부터10초 검증을 준비했고 동결 CUDA smoke를 통과했다. 사용자가 합계4시간·2.5초 구간별 통과 후 이어가기를 선택했다. 150/300/450/600 frame의 새 동결 계획과 실행 스크립트를 준비했고 관련14개 검사를 통과했다. 장시간 계산은 사용자 실행 대기이며 시간 정확도·해상도 검증은 미완료다. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/gpu_precision_api_20260911/README.md).

- 사용자 확인 범위: ① 고정밀 GPU·저장/재시작 보완 → ② 짧은 실패 구간 검증 → ③ 새10초 시간 간격 탐색 → ④ 해상도 수렴 검증까지. 주요 기준·비용 분기에서는 질문한다. 사용자는 수치적 재현성 기준을 채택했다. 저장·복원은 정확 일치, 이어 계산은 위치 차이≤1e-16m·속도 차이≤1e-12m/s와 기존 물리식 검산 통과를 요구한다. 장기 재시작은 별도 검증하며 물리 허용오차는 유지한다.

- 2026-09-11 GPU 고정밀 기하 시험은 8/8 step·독립 CPU 잔차 기준을 통과했다. 당시 재시작 정확 일치 실패를 확인했다. 현재 후속 상태는 위의 명시적 API 검증을 따른다. [조건·비용·근거](../R1_teacher_velocity_reset/timestep_search/evidence/gpu_precision_20260911/README.md).

확인 기준: 2026-09-11 KST. 실패 재현에 이어 Newton 수정 누적의 짧은 CUDA 전진을 검산했다.
**부분 개선이며 10초 추천 없음·4배 바람 필수19/20 통과를 유지한다.** 장시간 새 실행과 허용오차 변경은 하지 않았다.

- [Newton 정밀도 보완 결과](../R1_teacher_velocity_reset/timestep_search/evidence/incremental_newton_20260911/README.md): 기존 실패 세 step 통과, 후속 sub016 정체. 완료 구간은 CPU 원식·기하 검산을 통과했다. 비교 분모·새 실패와 source는 보고서가 소유한다.
- 사용자는 남은 문제에 허용오차를 유지하는 고정밀 상태 표현의 별도 검토를 선택했다. 저장 schema의 즉시 변경이나 장시간 실행으로 확대하지 않는다.
- [고정밀 검토 완료](../R1_teacher_velocity_reset/timestep_search/evidence/highprecision_state_20260911/README.md): 새 실패 지점의 8 step과 hi/lo 저장 후 재시작 일치를 확인했다. 같은 상태의 float64 내보내기는 잔차 기준에 미달했다. CPU 고정밀 힘 평가 비용이 커 정식 반영은 보류하며 다음은 저장·검산 계약과 GPU 경로 설계다.

- [Δt 실패 진단](../R1_teacher_velocity_reset/timestep_search/evidence/diagnosis_20260911/README.md): 세 실패의 마지막 시도가 동일하게 재현됐다. CPU/GPU 공통의 극소 수정 정밀도 문제가 유력하다. 다음은 실제 Newton 방향의 표현 오차·요소별 힘 상쇄 분해다.
- [4배 바람 속도 진단](../R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/evidence/diagnosis_20260911/README.md): 선택 원본 비교가 저장값과 일치하고 수직 방향 진동 차이가 지배적이다. 더 긴 구간의 진폭·위상 분해가 남았다.
- 동결 manifest 두 묶음과 선택 NPZ/hash를 확인했다. 전체 궤적 물리 재검산·R1 채택·학습 발행은 미완료다.
- Experiments의 진단 근거·연결 문서를 갱신했다. 구현 변경은 [code 기록](../../code/sessions/2026-09-10_02_teacher_timestep_search.md)이 소유한다. 원본 실행을 보존했으며 commit/push/fetch는 하지 않았다.

## 인계 당시 확인 범위

- [Δt 종료 결과와 확인 범위](../R1_teacher_velocity_reset/timestep_search/README.md#2026-09-11-인수인계-시-저장-결과): 네 후보 풀이 실패, 기존 간격은 후보 시간 한도. 정확도 비교 미도달.
- [다른 사용자 실행의 종료 결과](../R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/README.md#2026-09-11-인수인계-시-저장-결과): 4배 바람 보완 작업116개 종료, 필수 비교 하나의 공간 속도 기준 미달.
- 다음: 두 결과의 원본 연결과 실패 원인을 검토한다. 장시간 재실행·한도 변경·허용오차 완화는 하지 않았다. R1 채택·학습 발행은 보류다.
- 구현 결정·최종30fps 목표·새 채팅 작업 순서는 [code 인수인계](../../code/sessions/2026-09-10_02_teacher_timestep_search.md)를 따른다.
- 이번에는 실험 README, compact metadata evidence와 session/index만 갱신했다. 전체 물리 재검산, commit/push/fetch는 하지 않았다.

## 이전 구현 검증과 운영 결정

- 모든 후보는 같은 rest와 실제 wind 배열에서 독립적으로 시작한다. 중간 실패를 작은 Δt로 이어 성공 처리하지 않는다.
- 후속 사용자 요청에 따라 GPU 사용 중에도 즉시 시작한다. 기존4배 바람 실행과 원본은 유지한다.
  물리 계산 전 중단된 기본 묶음의 controller만 이력을 보존해 갱신했다. [제어 변경 근거](../R1_teacher_velocity_reset/timestep_search/evidence/no_gpu_wait/).
- 작은 CPU 흐름에서는 큰 Δt의 수치/기하 통과와 시간 정확도 미달을 구분해 추천을 보류했다.
  이 관찰은0.1초 smoke 조건이며10초 물리 안정성/정확도 근거가 아니다.
- 코드10개 검사와 CLI 중단·재개 근거는 [evidence](../R1_teacher_velocity_reset/timestep_search/evidence/)에 연결한다.
- 실제 CUDA 결과의 전체 원본/물리 재검증은 별도로 남아 있다. 작은 CPU 검증을10초 통과 근거로 승계하지 않는다.
