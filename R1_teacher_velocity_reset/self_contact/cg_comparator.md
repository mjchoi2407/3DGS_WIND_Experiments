# 공통512점 CG 비교기

## 현재 상태

2026-09-28 [v13 사각형 기본128/복구256 실행·비교 연결](v13_time128.md#현재-상태)을 준비했다.
원본 동결 코드/입력 보존·CPU25개 검사 확인. 실제128 GPU 실행·시간 민감도 판정은 미실행이다.
이 좁은 v13 시간 비교 준비는 아래 당시 v12 통합 T/S·예산 runner 계획과 구분한다.

2026-09-28 [완료된 서브 컴 v13 전용 뷰어·분석·비교 연결](three_scenes_gpu_v13.md#서브-컴-완료-결과와-연결)을 추가했다.
세 씬 실결과 재생/분석과 사각형 자기 비교를 확인했으며 실제 두 정밀도 비교는 아직 별도다.

- 2026-09-28 사용자 요청의1번 비교 스크립트를 구현했다. T/S 입력 생성·실행·24 해상도 지원은 추가하지 않았다.
- CPU 검사29개(비교16+기존 분석13) 통과. 합성 time/space 결과와 실제 v12 자기 비교의 읽기·곡선·HTML 생성 확인.
- 새 두 정밀도의 실제 시뮬레이션 결과 비교는 아직 없다. 수치 통과는 `numerical_pass_visual_pending`이며 최종/학습 pass는 발행하지 않는다.
- [실제 자기 비교 보고서](../../artifacts/runs/p3_self_contact/cg_comparison/identity_v12_20260928_01/index.html)는600프레임/512점·복구113개와0오차를 확인한 도구 점검이다.
- 브라우저/JS 실행 도구가 없어 HTML 재생 자체는 직접 검증하지 못했다. JS 데이터와 정적 산출물은 확인했다.
- 원본·실행 중 작업·동결 runtime은 수정하지 않았다. 계산은 CPU1스레드이고 새 GPU 계산·학습은 없다.
- [compact 검증 근거](cg_comparator_checks.json)의 `tests_passed`, `identity_status`, `implementation_sha256`을 따른다.

## 사용 명령

`candidate`는 덜 정밀한 완료run, `reference`는 더 정밀한 완료run이다. 원본 raw 기록을 재검증하고
공통점에서 다시 보간하므로 기존 분석 캐시를 먼저 만들 필요가 없다. 기본 씬은 사각형이다.
`--out`은 두 원본 밖의 **새 경로**여야 하며 기존 출력은 덮어쓰지 않는다.

```bash
# 같은 메시: reference의 기본 substeps가 candidate의 정확히2배
bash experiments/R1_teacher_velocity_reset/self_contact/compare_gpu_cg_checks.sh \
  --candidate <기본64단계_완료_run> --reference <128단계_완료_run> \
  --axis time --out <새_시간비교_폴더>

# 같은 substeps: reference가 더 높은 사각형 메시 해상도
bash experiments/R1_teacher_velocity_reset/self_contact/compare_gpu_cg_checks.sh \
  --candidate <낮은해상도_완료_run> --reference <높은해상도_완료_run> \
  --axis space --out <새_공간비교_폴더>
```

`--shape handkerchief` 또는 `triangular_flag`의 시간 비교도 가능하다. 공간 비교는 현재 사각형만 지원한다.
도구 자기 점검은 양쪽에 같은 run을 넣고 `--axis identity-check`를 사용한다.
이 모드는 반드시 같은 manifest여야 하며 `identity_check_only`로 표시한다. 민감도 검사 통과가 아니다.
스크립트는 직접 run 경로를 받는다. 과거 계획의 `--suite` 옵션은 구현 인터페이스가 아니다.

## 비교 조건과 판정

- 양쪽 manifest 전체, 완료 상태, 모든 raw frame/체크포인트/폐기 증거 hash, 저장 검산 flag,
  시각·외력 기록 및 raw hi/lo 구간 연결을 확인한다. 실패·미완료·진행 중 결과는 거절하고 사유를 보존한다.
- 물성·solver 허용오차·접촉/기하/복구 정책·동결 teacher 코드·native·환경·GPU 모델이 같아야 한다.
  기존 물리 검산을 재실행하는 도구는 아니다. 같은 GPU 모델 문자열은 같은 물리 장치의 증명까지 뜻하지 않는다.
- 중력/바람 배열·phase 시간 구성·기준 표면·고정 영역·초기 조건을 확인한다.
  시간 비교는 초기 네 raw hi/lo 배열까지 같아야 한다. 공간 비교는 같은 초기 프로그램과 공통점 상태를 확인한다.
  공간 초기 상태 대조의 FP64/P3 매핑 여유는1e−8L이며 위치/속도에 각각 m/m·s⁻¹ 단위로 적용한다.
- v12/v13처럼 외력·초기 상태·시간 구성이 달라진 두 run을 민감도 비교로 통과시키지 않는다.
- 실제 저장 dt/substeps가 기본 또는 한 번의2배 단계 복구인지 확인하고 양쪽 복구/폐기 횟수를 각각 기록한다.
- 동일 ordered512점·양의 rest 면적 가중치를 사용한다. `L`은 reference의 rest bbox 대각선이다.
- 위치: 면적·시간 RMS 변위 차이/L≤1%. 속도: RMS 속도 차이/max(reference RMS 속력,0.01L/s)≤10%.
  임계값과 수치가 거의 같은 경우에만 상대1e−12의 FP64 반올림 여유를 둔다. 물리 허용량은 바꾸지 않는다.
- 바람 전체와 마지막2초를 **각각** 판정한다. v12는6–10/8–10초, v13은5–10/8–10초다.
  구간 시작 경계를 제외하고 끝 경계를 포함해 v12 wind240/후반120, v13 wind300/후반120프레임이다.
- preload/calm/전체 시간 지표도 기록하지만 조용한 구간으로 wind 실패를 희석하지 않는다.
  곡선의 프레임별 속도 비율은 구간 RMS 분모를 쓰는 최종 수치와 구분한다.

상태는 `numerical_pass_visual_pending`, `numerical_fail`, `rejected`, `identity_check_only`다.
종료코드는 수치 대기/자기 점검0, 수치 미달1, 입력·검증 거절2다. 종료0이 최종 pass를 뜻하지 않는다.
항상 `final_pass=false`, `training_eligible=false`이며 R1 Gate·학습 진입을 자동 변경하지 않는다.

## 산출물과 시각 검토

- `report.json`: 구간 오차/분모/수치 판정, 입력 계약·원본 hash·복구/폐기 횟수·구현/산출물 hash.
- `frame_errors.csv`, `errors.png`: 기록 프레임별 위치/속도 오차와 복구 여부.
- `comparison_samples.npz`: 원본 FP64 보간 결과, 같은 시각·rest·면적 가중치.
- `index.html` + `overlay_data.js`: 로컬에서 여는512점 겹쳐보기. 파랑 candidate·주황 reference,
  정면/측면/사선 고정 카메라·축척, 시간 슬라이더·재생/정지·1/0.5/0.25배속.
  카메라 중심은 rest bbox 중심, 표시 폭은2L로 고정하며 결과 오차를 보고 자동 재조정하지 않는다.
  표시만 FP32이고 수치 판정은 FP64다. 두 파일을 같은 폴더에 유지한다. 외부 라이브러리/서버는 필요 없다.
- `visual_review_template.json`: 원본 두 hash가 들어간 pending 양식.
  검토할 때 원본 양식은 보존하고 별도 `visual_review.json`으로 복사해 관찰/검토자를 기록한다.
  이 스크립트는 수동 양식을 읽어 최종 pass로 승격하는 기능을 포함하지 않는다.

512점 겹쳐보기는 전체 메시가 아니다. 관통·고정점 이탈·갑작스러운 튐·폭주·비정상 떨림은
[원본 메시 뷰어](three_scenes_gpu_v12.md#연속10초-뷰어)와 함께 정상/느린 재생으로 확인해야 한다.
시각 검토 완료와 이후 T/S 두 비교·GS/작은 응답 근거를 묶는 최종 진입 보고서는 후속 작업이다.

## 검증과 남은 한계

[비교기 구현](../../../code/wind3dgs/evaluation/compare_gpu_cg_checks.py)의 `input_contract`,
`compare_arrays`, `run`과 [검사](../../../code/tests/test_compare_gpu_cg_checks.py)가 소유한다.

- CPU29개 통과: 알려진 벡터 RMS·정지 분모 하한·reference 분모·wind 후반 미달·v13 시간 창,
  수치 통과 후 시각 대기, time/space 합성 연결과 다른 노드 수, 외력/물성/초기 조건/시간/GPU/dt 오류,
  미완료·동일 run·뒤집힌 기준 실행 거절, 기존 출력 보존을 확인했다.
- 최초 검사에서 정확히1%/10%인 입력이 누적 FP64 반올림으로 임계값을 미세하게 초과했다.
  상대1e−12 경계 여유를 추가했고 실제 기준 초과는 계속 거절하는 회귀까지 통과했다.
- 실제 v12 사각형600프레임을 양쪽에서 읽어 복구/폐기113개, wind240/후반120프레임과0오차를 확인했다.
  실제 서로 다른 dt/메시의 통과 근거는 아니다. 자기 비교는 `identity_check_only`다.
- 사각형24 생성기 제한은 그대로다. 기존 입력·solver를 변경하지 않았고2번/3번 작업은 수행하지 않았다.
- HTML/JS와 곡선 생성 및 데이터 크기/유한 값은 확인했다. 브라우저 엔진이 없어 재생 조작은 미검증이다.
