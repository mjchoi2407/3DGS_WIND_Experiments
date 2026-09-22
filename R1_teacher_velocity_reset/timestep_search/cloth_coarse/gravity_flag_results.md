# 깃발 중력·바람 완료 분석

2026-09-13 로컬 원본 `artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_hilo_v1` 확인. GTX1080Ti, FP64 hi/lo,384삼각형/1813노드,왼쪽 고정,굽힘1/100,dt1/3840초. 상세 수치는 [JSON](gravity_flag_results.json), 설정은 [실행 문서](gravity_wrinkles.md)를 따른다.

| 단계 | 프레임/substep | worker 시간 | 마지막 RMS 속도(m/s) |
| --- | ---: | ---: | ---: |
| 중력2초 | 120/7680 | 377.122초 | 0.00005190 |
| 무풍4초 | 240/15360 | 783.432초 | 0.00003568 |
| 바람4초 | 240/15360 | 938.607초 | 0.485767 |

합계2099.162초(약35분), 계산·검산 합계2065.293초. 각 worker 타이머는 setup을 포함한다. 과거 비동기 최적화 기록이나 아직 미실행인 최초 하이브리드 비교의 성능 증거로 사용하지 않는다.

중력2초 끝 최대 하강0.131767mm, 무풍4초 추가 후0.131931mm. 면외 변위는0이다. 왼쪽 고정으로 변경했지만 가시적인 중력 처짐 준비 상태를 만들지 못했다. 평평한 수직 XZ 초기 상태와 면내 중력이 유지되며 면외 굴곡을 유도하는 조건이 없다. 단순 대기 시간 부족이나 솔버 실패로 확정하지 않는다. 깃발이면 충분히 처질 것이라는 이전 설명은 이 결과로 지지되지 않는다.

바람의 원래 평면 대비 최대 면외 변위는60Hz 표시 기준0.624448m(분기1.6333초), 최대 RMS 속도0.857580m/s. 마지막 최대 하강0.633178m, 마지막 면외 변위 성분 범위−0.188996~0.188608m. 마지막 대표 렌더는 큰 접힘과 화면상 겹침을 보인다. 잔주름 수·높이 또는 실제 자기 교차를 측정한 것은 아니다. 무중력 바람 대조군이 없어 중력의 추가 효과를 분리하지 않는다.

전체38400substep 저장 audit flag0. 동결 입력 manifest·재생용 모든 원본 chunk/audit hash 확인, 두 분기 동일 preload checkpoint 확인. 최대 힘 잔차 비율0.299358, 위치 업데이트 오차1.544e-20m, 에너지 장부 오차2.429e-17J. 바람 국소 변형률 성분 상한0.160340으로 보수적 면적비 하한0.518979; 실제 최대 신장률과 다르다. 이전 투영 상한은 최대2.18268이며10405단계에서1이상이지만 현재 국소 기하 검사는 통과했다. 이는 큰 회전 허용과 국소 비퇴화 확인이며 전체 자기 교차 방지 인증이 아니다.

세 단계 표시 캐시 생성, 바람4초 GPU 대표 화면 확인. CUDA/OpenGL 공유 대신 복사 경로로 정상 표시. 시뮬레이션 재계산·외부 fetch 없음. 자기 충돌 검사/응답·학습 적격성 미완료.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh wind
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh preload
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh calm
```

Space 재생/정지. 바람1.63초 큰 면외 변위,3~4초 접힘을 확인할 수 있다.
