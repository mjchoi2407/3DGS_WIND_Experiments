# 깃발 굽힘1/500 준비

2026-09-14. 사용자가1/300의 시각적 움직임을 긍정적으로 평가하여1/500을 추가 요청했다. 별도 출력 `artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_bend500_v1`은 준비 후 사용자가 실행했다. 2026-09-14 확인 시 중력·무풍 단계 완료, 바람 단계는2초 직후 선형 풀이 실패로 종료됐다. 확정2초 prefix를 보존한다. [실패 재현/개선 진단](bend500_failure_diagnosis.md).

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_bend500.sh
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_bend500.sh --status-only
# 완료 후 재생; preload/calm도 선택 가능
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_bend500.sh wind
```

왼쪽 고정 직사각형 깃발384삼각형/1813노드, FP64 hi/lo, dt1/3840초. 중력ramp1초 포함2초 준비 후 자체 위치·속도를 무풍4초/바람4초에 계승한다. 추가 감쇠·속도reset·셀프컬리전 없음. 무압축2초 저장 및 물리/국소 기하 검산은 유지한다.

굽힘은 baseline의1/500이며1/300의0.6배다. E=22360679.774997897Pa,h=0.00044721359549995795m,nu=.3,면밀도=.1kg/m². 기존 scaling 규칙으로 Eh·면밀도를 유지하고 Eh³/경계 굽힘을 낮춘다. 향후 접촉 두께를 h로 자동 확정하지 않는다.

Shell 구문·동결 manifest 확인, 세 단계별1/300 대비 굽힘비0.6·면내 강성/면밀도 유지·외력 배열 완전 일치 검증 통과. 전체 GPU 실행·안정성 검증은 아직 완료하지 않았으며 결과를 예측해 채택하지 않는다. [1/300 결과](gravity_bend300_results.md)와 완료 후 비교한다.

사용자는 하이브리드 비교를 직접 종료했으며 추가 비교/재개를 요청하지 않았다. 원본과 중단 결과는 보존한다. 셀프컬리전 구현 후에도 접촉 검산·안정성 및 연구 Gate 완료 여부를 별도로 판단한다. Commit/push 없음.
