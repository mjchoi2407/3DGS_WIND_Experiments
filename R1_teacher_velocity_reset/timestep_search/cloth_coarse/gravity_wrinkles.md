# 중력 처짐 후 바람·무풍 주름 비교

## 실행

사용자 수정에 따라 기본 대상을 왼쪽 가장자리 고정 직사각형 깃발(`reference_rectangle`)로 변경했다. 정착을 기다리지 않는다. 굽힘1/100 깃발에 중력을1초 동안 부드럽게
증가시키고 **총2초** 계산한 뒤, 그 위치·속도를 그대로 두 분기의 초기 상태로 사용한다.
속도를0으로 만들거나 추가 감쇠·초기 주름·랜덤 바람을 넣지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_wrinkles.sh
```

기본 출력은 `artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_hilo_v1`이다.
깃발 본 실행 완료. [깃발 결과](gravity_flag_results.md)를 참고한다. 이전 손수건 실행과 [결과 분석](gravity_wrinkles_results.md)은 보존한다. 실행 순서는 다음과 같다.

| 단계 | 계산 구간 | 중력 | 바람 |
| --- | ---: | --- | --- |
| preload | 2초/120프레임 | 처음1초 smoothstep으로0→9.81m/s², 이후 유지 | 0 |
| calm | 4초/240프레임 | 9.81m/s² 유지 | 0 |
| wind | 4초/240프레임 | 9.81m/s² 유지 | 기존 동결 바람의 처음4초, 첫1초 smoothstep 증가 |

두 분기는 같은 preload checkpoint의 원시 hi/lo 위치·속도로 시작한다. 각 분기는 preload 이후
시간을0으로 기록한다. 계산 구간의 합계는10초지만 각 비교 궤적은 공통 준비2초+응답4초다.
위쪽은+Z이므로 중력은−Z다. 메시·물성·고정 조건은 기존 `bend_001` 직사각형 깃발의 물성·해상도·왼쪽 가장자리 고정을 유지한다.
정밀도 FP64 hi/lo, dt=1/3840초,60Hz·64substep, 기하 정책은 `local_metric`이다.

```bash
# 읽기 전용 상태 조회
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_wrinkles.sh --status-only
# 다른 출력 위치에 준비만 수행(서브컴도 --out 지정)
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_wrinkles.sh --out <새경로> --prepare-only
# 준비된 다른 출력 실행
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_wrinkles.sh --out <새경로>
```

Ctrl+C는 전체 비교와 소유 worker를 종료한다. 확정 저장 구간을 보존하고 미저장 구간은 폐기하며
interrupted/실패 실행은 자동 재개하지 않는다. 완료된 단계는 재실행하지 않는다.
매 프레임 GPU 완료 후 시간·질량 가중 RMS속도를 표시한다. 기본2초마다 모든 substep의
상태·외력·에너지 장부·검산을 무압축 저장하므로 원시 산출물은 수GB가 될 수 있다.

## 재생

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh preload
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh calm
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh wind
```

다른 출력은 단계 뒤에 `--out <경로>`를 붙인다. `--prepare-only`는 표시 캐시만 만들며
`--time 1` 같은 기존 뷰어 옵션을 뒤에 전달할 수 있다. 초기 프레임도 처진 checkpoint를 표시한다.

## 무엇을 확인할 것인가

각 단계의 `handkerchief/frame_timings.jsonl`에 속도 RMS·운동에너지·중력 위치에너지와 시간을 남긴다.
이는 진단값이며 정착 조건이 아니다. `comparison.json`은 두 분기의 동일 초기 checkpoint와
최종 위치·속도 차이를 기록한다. 전체 시간 곡선·주름 개수의 자동 평가는 아직 수행하지 않는다.

중력은 consistent FE 질량을 적분한 외력이며, 공력과 합친 힘으로 적분하고 독립 물리 검산을 수행한다.
에너지 검산은 기존 탄성+운동 에너지 변화와 **중력·공력이 한 일**을 비교한다. 중력 위치에너지를
여기에 다시 더해 일을 이중 계산하지 않는다. Ramp 중에는 중력 크기가 바뀌므로 위치에너지 포함
총량이 보존되어야 한다고 판정하지 않는다.

현재 깃발은 XZ 수직 평면이며 왼쪽 가장자리를 고정한다. 자유단이 중력으로 처질 수 있지만 중력만으로 면외 잔주름이
반드시 생기지는 않는다. 이번 실험은 실제 움직임을 확인하는 첫 비교이며, 고정점 여유·미세
초기 굴곡·바람 공간 변화·해상도 변경은 별도 조건으로 남긴다.
셀프컬리전·접촉 두께·마찰은 없다. 국소 기하/물리 검산 통과를 전체 비접촉 또는 학습 적격성으로 해석하지 않는다.

## 짧은 검증과 한계

검증 원본·수치는 [선별 근거](gravity_wrinkles_validation.json)를 따른다. 본 비교는 완료했으며 결과는 위 분석에 기록했다.
smoke는 단계별2프레임으로 입력·중력·분기·저장·재생을 확인하는 별도 run이다. 실제 처짐 양이나
주름 발생·장기 안정성을 검증한 것은 아니다. 이전 준비/검증 출력은 보존했다.
원본이나 기존 솔버의 기본 외력을 바꾸지 않았고 commit/push는 하지 않았다.

이전 손수건 재생은 단계 뒤에 `--out experiments/artifacts/runs/teacher_timestep_search/gravity_wrinkles_hilo_v3`을 붙인다. 뷰어는 해당 config의 메시를 자동 선택한다.

깃발 변경 검증: 단위 테스트5개, 별도 `gravity_wrinkles_flag_smoke_v1`의 각 단계2프레임/128substep 총384단계 GPU 검산과 동일 checkpoint 분기 통과. 본 실행은 미시작이며 smoke만으로 처짐·주름 발생을 판정하지 않는다.

최초 하이브리드와 현행 풀이를 같은 깃발 조건으로 새로 비교하는 명령은 [속도 비교](gravity_speed_compare.md)를 따른다.

후속 굽힘 비교: [1/300 준비](gravity_bend300.md).

추가 굽힘 비교: [1/500 준비](gravity_bend500.md).
