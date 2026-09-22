# 깃발 굽힘1/300 비교 준비

2026-09-13. 사용자 요청에 따라1/100 다음 조건으로1/300을 준비했다. 기존 하이브리드 비교와 결과는 보존한다. 2026-09-14 본 출력 `artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_bend300_v1`의 세 단계 완료. [결과](gravity_bend300_results.md). CPU 테스트9개, 동결 manifest·원본 외력 배열 일치·메시384삼각형/1813노드 확인 통과. 준비 당시 GPU 검증은 미실행이었으며 이후 사용자가 본 실행을 완료했다.

```bash
# 기존 GPU 실행 종료 후 짧은 검증
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_bend300.sh --smoke --out experiments/artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_bend300_smoke_v1
# 본 실행: 중력2초 → 같은 자체 checkpoint에서 무풍4초/바람4초
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_bend300.sh
# 상태
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_bend300.sh --status-only
# 완료 후 재생
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_bend300.sh wind
```

굽힘은 baseline 대비1/300, 기존1/100 대비1/3이다. 기존 scaling 규칙대로 E를sqrt(3)배, h를1/sqrt(3)배 하여 Eh·면밀도를 유지하고 Eh³ 및 경계 굽힘 penalty를1/3로 줄인다. E=17320508.07568877Pa, h=0.0005773502691896258m, nu=.3, 면밀도=.1kg/m². 여기서 h 조정은 굽힘 제어용이며 향후 접촉 두께를 이 값으로 자동 확정하지 않는다.

FP64 hi/lo·왼쪽 고정·384삼각형·중력/바람/ramp·dt1/3840·60Hz/64substep·국소 기하 검산·무압축2초 저장은 유지한다. 물리/솔버 검사 실패 시 종료한다. 위치/속도 reset 없음. 양쪽은 동일 rest에서 시작하되 각 preload 차이가 바람 분기에 계승된다.

완료 후 기존 [1/100 결과](gravity_flag_results.md)와 처짐·큰 접힘/잔주름·속도·검산·계산 비용을 비교한다. 아직 더 자연스러운 결과나 안정성을 검증한 것은 아니다. 그 결과를 확인한 뒤 셀프컬리전을 별도 조건으로 도입하며 정밀도·굽힘·접촉 변경을 섞지 않는다. 현행 연구 계약의 contact-off 범위를 자동 해제하지 않는다.
