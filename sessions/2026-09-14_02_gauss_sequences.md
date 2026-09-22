# Gauss6차8분할·1/500 세 씬 준비

## 현재 상태

- 후속 완료 결과 재생 연결: 세 씬의 preload120/calm240/wind240 완료 report를 확인하고 세 바람 재생 캐시를 준비했다. 서브컴의 실제 날짜별 run을 선택하는 완료 전용 wrapper를 추가했다. [실제 경로·명령](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gauss6_bend500_three_scenes.md#완료된-세-씬-재생-연결--2026-09-14). 추가 시간 수렴/teacher 정확도 판정은 하지 않았다.

- 확인일2026-09-14. 직사각형·삼각 깃발·손수건의 개별 실행/재생 스크립트를 준비했다. dt1/30720초·프레임당512단계, 중력2초 후 동일 상태에서 무풍4초/바람4초 분기다.
- 준비 당시 main과sub_pc 각 출력에서 세 씬 모두 ready로 동결했고 본 계산은 시작하지 않았다. 두 컴퓨터는 서로 다른 씬을 맡아 실행한다. 같은 GPU에서는 순차 실행한다.
- 메인 GTX1080Ti에서 세 메시×세 단계의1프레임 smoke, 총4608적분 단계 검산과9개 재생 캐시 준비 통과. 서브컴 GPU 계산을 실행한 것은 아니다.
- 원본·정확한 설정/실행·검증 hash·기록 밀도는 [실행 보고서](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gauss6_bend500_three_scenes.md)가 소유한다.
- 원시 hi/lo 상태는60Hz, 검산은 모든512단계, 확정 저장은2초마다다. 기존 모든substep 상태 기록과 혼합하지 않는다. 학습 적격/Gate 미완료.
- 검증 중 초기 graph 준비 실패는 보존하고 수정된 별도v2 run을 확인했다. 원본 변경·외부 fetch·stage·commit·push 없음.
