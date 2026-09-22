# 중력 후 바람 비교 결과

2026-09-13 확인. 원본 `artifacts/runs/teacher_timestep_search/gravity_wrinkles_hilo_v3`. GTX1080Ti, FP64 hi/lo, dt1/3840초, 굽힘1/100 손수건. [설정](gravity_wrinkles.md), [수치](gravity_wrinkles_results.json).

| 단계 | 프레임/substep | worker 시간 | 마지막 RMS 속도(m/s) |
| --- | ---: | ---: | ---: |
| 중력2초 | 120/7680 | 160.325초 | 0.00001259 |
| 무풍4초 | 240/15360 | 340.245초 | 0.00000611 |
| 바람4초 | 240/15360 | 520.885초 | 0.155474 |

두 분기는 동일 preload checkpoint의 위치·속도를 보존했다. Worker 합계1021.456초, compute_audit 합계1003.749초. 매 프레임 동기화/진단 읽기를 포함하므로 과거 비동기 성능과 직접 비교하지 않는다.

중력2초 끝 최대 하강0.060239mm, 무풍4초 추가 후0.060226mm. 면외(Y) 변위는 저장60Hz 전 구간0이다. 수직 XZ 평면에 중력이 면내로 작용해 눈에 띄는 처짐이나 면외 주름을 만들지 못했다. 단순한 대기 시간 부족으로 해석하기 어렵다.

바람 최대 면외 변위37.669cm(분기3.4333초,206프레임), 최대 RMS 속도0.825534m/s. 마지막 면외 최대 변위5.114cm. 이는 원래 평면에서 벗어난 양이며 주름 높이가 아니다. 2초 대표 화면은 넓은 굽힘 위주이며 촘촘한 잔주름 발생은 입증하지 않는다. 무중력 바람 대조군이 없어 중력의 주름 증가 효과도 판정하지 않는다. 다음 비교에는 지지 간격의 여유나 초기 기울기 등 처짐을 만드는 별도 조건이 필요하다. 이번에는 설정을 변경하지 않았다.

동결 manifest와 뷰어 원본 chunk/audit hash 검증 통과. 총38400단계 flag0. 최대 힘 잔차 비율0.299946, 위치 업데이트 오차2.631e-21m, 에너지 장부 오차6.942e-18J. 국소 변형률 성분 상한0.00724021, 보수적 면적비 하한0.978279. 실제 신장률이나 자기 교차 측정과는 다르다. 셀프컬리전 검사/응답 없음, 학습 적격성 미판정.

세 단계 재생 캐시를 준비하고 wind2초 GPU 렌더링을 확인했다. CUDA/OpenGL 직접 공유 대신 복사 경로로 정상 표시된다. 시뮬레이션 재계산 없음. 로컬 원본만 조회했고 외부 fetch 없음.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh wind
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh preload
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh calm
```

Space 재생/일시정지. wind3.43초가 최대 면외 변위 부근이다.
