# v10 메인·서브 복구 빈도 읽기 전용 점검

## 현재 상태

- 확인일: 2026-09-23. 양쪽 v10 manifest 실제290개 파일씩 검증했고 설정/원본/native/source 불일치0이다.
- 같은 wind 표시1–143 복구20 대22. 다른 진행 구간의 단순 횟수비를 실패율로 채택하지 않는다.
- 사용자 양쪽3회1프레임 결과는6/6 통과했지만 CPU 배열 차이와 같은 GPU의 비트 불일치를 확인했다. CPU weights로 각 원래 held force를 정확히 재현했다. [후속 근거](../R1_teacher_velocity_reset/self_contact/cross_device_v10.md#사용자-반복-실행으로-확인한-결과).
- 원본/hash·상세 차이와 한계는 [원본과 확인 분모](../R1_teacher_velocity_reset/self_contact/cross_device_v10.md#원본과-확인-분모), 코드 경로는 [경로별 조사](../R1_teacher_velocity_reset/self_contact/cross_device_v10.md#경로별-조사와-남은-구분)에 기록했다.
- 고유 출력의 CPU 입력/동일 상태1프레임/비계측/sanitizer wrapper를 준비했다. [사용자 명령](../R1_teacher_velocity_reset/self_contact/cross_device_v10.md#사용자-실행-먼저-cpu-입력-그다음-동일-상태-한-프레임)을 따른다.
- CPU 동결77배열 공통 NPZ·pinned wrapper 준비, 이전 메인 host35개/업로드3개와 bitwise 일치. CPU 검사16개·실제 host 로드 통과. [동결 원본·명령·한계](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#현재-상태).
- 사용자 동결 GPU 첫 프레임은 양쪽 각3회, 총6회 승인. 시작 NPZ·CPU 계수·정적 업로드196개와 초기 힘이 모두 같지만 동일 GPU의 첫 substep 상태 차이가 남았다. [결과 원본·판정 범위](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#동결-gpu-재생-결과와-다음-시험).
- 사용자 원시 경계 GPU 6/6 승인: RHS·정적 업로드 동일, 첫 불일치는 무접촉 첫 substep의 질량 풀이 출력 `a0`. 여섯 독립 CPU 잔차는 상대 `2.61e-16`–`2.98e-16`. [원본·수치·원인 한계](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#원시-질량-경계-결과). sanitizer는 미실행이다.
- R1의 장기 검증·채택 미완료 경계를 유지하고 TeX/Gate는 바꾸지 않았다. 기존 run을 수정하거나 중단하지 않았다.
- 사용자 독립 질량 풀이: 양쪽 각3 fresh process·각 process 8회, 총48회 정상 완료. 같은 GPU의 같은 분해 객체·같은 RHS를 직접 solve해도 4/4 해 hash가 달랐고 내부 x와 최종 a0는 매번 같다. 상대 질량 잔차 2.235e-16–2.980e-16. [원본·독립 재검산·한계](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#독립-질량-풀이-결과).
- 사용자 공통 메인 wind115 상태 GPU 재생: 양쪽 각3회 모두 기본64단계 승인·dt/2 없음. 시작 상태/CPU·GPU 업로드196개 동일, 최초 수치 차이는 substep0 질량 풀이 출력, 한 프레임 종료 모든 쌍 최대 u_hi 1.11e-16 m·v_hi 6.86e-13 m/s. 원래 표시115 직전 서브 상태는 메인과 최대4.06 mm·2.39 m/s 다르다. [원본·분모·계측 한계](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#공통-메인-wind115-상태-1프레임-결과).
- 서브 원래 wind115 상태의 양쪽 교차 재생은 [기존 옵션·명령](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#공통-메인-wind115-상태-1프레임-결과)에 남아 있다. 완료 결과로 승계하지 않는다.
- cuDSS 결정성 설정의 **별도 질량 풀이**를 메인·서브 각2 fresh process × graph/direct 각4회 완료했다. 동일 입력·설정/source/native에서 각 장치 내부 해시는 모두 같고 잔차2.98e-16이지만, 장치 간 126/5,292성분·최대3 ULP 차이가 남는다. 원본 v10 본 run 설정은 그대로다. [양쪽 원본·독립 검산·한계](../R1_teacher_velocity_reset/self_contact/cpu_frozen_v10.md#cudss-결정성-설정-격리-시험).
- 판정: 같은 GPU 재실행 비결정성은 이 격리 질량 풀이에서 설정만으로 해소됐다. 서로 다른 GPU의 bitwise 완전 일치는 해소되지 않았다. 장기 wind dt/2 빈도 해결·전체 프레임 결정성·race 부재는 미확정이며, 추가 본 시뮬레이션을 자동 실행하지 않는다.
