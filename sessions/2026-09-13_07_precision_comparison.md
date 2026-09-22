# 네 정밀도 비교와 선택적·적응 정밀도

## 현재 상태

- 최종 사용자 결정: **FP64 hi/lo로 솔버를 고정하고 정밀도 최적화를 보류한다.** 아래 hi/lo+선형 보정 결합 제안도 진행하지 않는다. 다음은 [10초 기하 경고 진단](2026-09-13_08_geometry_diagnosis.md). 기존 정밀도 비교 원본은 보존한다.

- 2026-09-13 후속: 4초 새 두 경로×세 메시 완료 후 직사각형 Newton 정체를 진단했다. 동일 저장 상태 3개×3경로의 단일 substep GPU 대조에서 hi/lo는 모두2회 수렴, Pure/보정은5·15·15회이며 마지막 상태는 한도 경고다. [정체 보고서·원본](../R1_teacher_velocity_reset/timestep_search/precision_compare/rectangle_stagnation.md).
- 주된 증거는 hi/lo 제거에 따른 상태·기하 산술의 정밀도 한계를 가리킨다. 선형 보정은 이 한계를 해결하지 않는다. 재사용 행렬 이력을 복원하지 않은 대표 상태 대조이며 상태/기하의 단독 기여는 미분리다. `solver_warning_counts`의 키2는 bitmask로 Newton 경고이고 선형 오류 코드가 아니다.
- 다음 후보는 hi/lo 상태·기하를 유지한 FP64 선형 보정 결합이다. 제안만 했으며 솔버·물리·허용오차·Gate는 변경하지 않았다. 새 계산은 진단9 substep뿐이며 기존 원본 보존·commit/push 없음. 아래 준비 상태는 이전 기록이다.

- 후속 요청: Pure FP64 기존 풀이를 추가해 hi/lo 원본·Pure FP64·FP64 보정의 세 경로로 확장했다. 새 두 경로×세 메시를 같은 진단/저장 조건에서 순차 실행한다. 두 풀이×세 메시 각각2프레임 GPU·독립 검산·자동 비교 통과, CPU/중단8개 검사 통과. 이전 동결본 보존, 본 실행 미시작.

- 확인일: 2026-09-13. [굽힘1/100·4초 FP64 보정 실행과 자동 비교](../R1_teacher_velocity_reset/timestep_search/precision_compare/refine64_4s.md)를 준비했다. 세 메시 ready, 본 실행 미시작.
- 기준은 메인컴4초 목표 run이며1/100은 모두 기하 검사로 조기 중단됐다. 자동 시간비는 공통 정상 저장 구간만 사용한다. 서브컴10초 RTX5070 시간과 섞지 않는다.
- 기존 정밀도 diagnostic 승인에 따라 유한 초과를 기록·계속하며 원래 독립 hi/lo 검산을 유지한다. 완료는 학습 적격 판정이 아니다.
- 세 메시 각각2프레임 및 최종 연결 손수건2프레임의 GPU·저장·자동 비교 통과.
  [작은 검증 근거](../R1_teacher_velocity_reset/timestep_search/precision_compare/refine64_4s_validation.json). 본4초 속도/장기 안정성은 미측정.
- [구현 기록](../../code/sessions/2026-09-13_11_precision_comparison.md). 원본 보존, 외부 fetch/다운로드·commit·push 없음.

## 앞선 적응 정밀도 검증

- 확인일: 2026-09-13. 적응 FP32/FP64와 동일 알고리즘 FP64 대조군의 순·역방향10프레임 비교 및 별도 계측 완료.
- [적응 비교 보고서](../R1_teacher_velocity_reset/timestep_search/precision_compare/adaptive_report.md)와
  [선별 근거](../R1_teacher_velocity_reset/timestep_search/precision_compare/adaptive_evidence.json)가 조건·명령·hash·분모를 소유한다.
- 혼합 정밀도는 대부분 FP64로 전환해 가속 이득 미확인. FP64 보정 대조군은 짧은 구간에서 더 빨랐다. 기본 채택과 장기 일반화는 보류한다.
- 순방향3경로의 각640단계 독립 GPU 물리·기하 검산과 기준 궤적 대조 통과. 역방향/계측은 프레임 끝 CPU 독립 표본 분석이다.
- [구현 기록](../../code/sessions/2026-09-13_11_precision_comparison.md). 실행 중 사용자 계산 변경·원본 수정·Git fetch·commit·push 없음.
- 다음은 FP64 보정 후보의 긴 구간 검증이며, 아래는 이전 FP32 변형률 보정의 보존 상태다.

- 확인일: 2026-09-13. 기존 네 정밀도 비교에 이어 식 재작성·선택적 FP32 보정 후보를 별도 검증했다.
- [개선 보고서](../R1_teacher_velocity_reset/timestep_search/precision_compare/stable_strain_report.md)와 [선별 근거](../R1_teacher_velocity_reset/timestep_search/precision_compare/stable_strain_evidence.json)가 설정·수치·hash를 소유한다.
- 굽힘1/100 손수건·같은 초기 상태/바람/물성/dt에서 식 재작성과 최종 보정의 네 경로 모두10프레임/640단계 완료, 독립 분석 오류0이다.
- 중간 법선·기하 계수 후보는 같은 저장 상태의 GPU 대조만 수행했다. 각 단계의 효과를 구분하고 기존 실행을 보존했다.
- 힘 계산·표본 잔차 개선은 확인했으나 최대 위치 차이와 에너지 장부 오차는 크게 줄지 않았다. 엄격 기준과 가속 채택은 미완료다.
- 실행 간 기준 시간도 달라 시간비를 일반 가속률로 해석하지 않는다. 모든 수치는0.167초 범위이며10초 장기 검증은 하지 않았다.
- [구현 기록](../../code/sessions/2026-09-13_11_precision_comparison.md). 원본 변경·외부 fetch/다운로드·commit·push 없음.
