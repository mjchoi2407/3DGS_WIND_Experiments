# GPU 세 씬 v12 완주 분석·v11 결과

## 현재 상태

- 2026-09-30 후속: [별도 XPBD 구현·작은 실행·속도/실패/미완료](2026-09-30_01_xpbd_pilot.md#현재-상태)를 확인했다. 아래 P3 근거·동결 실행은 보존하며 새 후보로 승계하지 않는다.
- 2026-09-29 사용자 요청으로 막5ms 유지·굽힘1ms/5ms 마지막2초 테스트를 구현·동결했다. GPU 적분은 실행하지 않았다.
- [현재 조건·검증 범위](../R1_teacher_velocity_reset/self_contact/bending_damping.md#현재-상태): 기존 막5ms의8초 raw 상태에서8→10초, 전역 감쇠0, 같은 메인 GTX1080Ti.
- [실행과 재생](../R1_teacher_velocity_reset/self_contact/bending_damping.md#실행과-재생): GPU 연산 대조·두 첫 프레임 이후 새1ms→5ms 순차 실행. 굽힘0은 기존 결과 재사용.
- [추가 모델·접선·독립 장부](../R1_teacher_velocity_reset/self_contact/bending_damping.md#모델과-검산): 곡률과 요소 접힘각 변화 감쇠, 기존 탄성·접촉·물성·외력·검산·복구 계약 유지.
- [동결 식별과 준비 검증](../R1_teacher_velocity_reset/self_contact/bending_damping.md#입력과-검증): 초기 네 raw 배열·원본 외력 마지막120프레임·native 동일. 새 runtime은 현재 소스와 일치.
- CPU 물리9개·실행기9개·기존 회귀27개, 실제8초 NumPy/Warp CPU 힘/접선/소산 대조 통과.
- 기존 굽힘0의121상태 뷰어 캐시 확인. 새 후보 GPU 대조·graph/첫 프레임·2초 완주·실제 GUI·실패 주입 rollback 검증은 미완료.
- [이전 막1/5ms 완료 분석](../R1_teacher_velocity_reset/self_contact/internal_damping.md#완료-결과-분석): 두 후보 잔진동과5ms 빠른 성분 감소가 이번 굽힘 후보의 근거다.
- 다음은 사용자 run 후 세 조건 시각 비교.8초 감쇠 전환 진단을 원래wind 전체·수렴 통과로 해석하지 않는다.
- 학습/R1 채택·새 모델 시간/공간 민감도는 미완료. canonical/R/TeX/PDF 변경 없음.
- 기존 dirty·원본 결과·서브8/16 작업 보존, commit/push·fetch·외부 다운로드 없음. 아래 당시 준비/분석 상태를 이번 준비로 갱신한다.

## 직전 작업 상태 — 당시 기록

- 2026-09-29 메인 막 감쇠1ms/5ms 사용자가 완료한 결과를 분석했다. 두300프레임·저장 검산 flag0, GPU 연산 대조/첫 프레임도 통과했다.
- [완주·식별·미완료 범위](../R1_teacher_velocity_reset/self_contact/internal_damping.md#현재-상태):5ms는9.1초의 code2 한 번을dt/2로 복구, 버린 시도 보존.
- 사용자 관찰대로 두 후보의 빠른 떨림이 남는다. [수치·측정 방식·원본](../R1_teacher_velocity_reset/self_contact/internal_damping.md#완료-결과-분석)에서5ms의 빠른 성분 감소약25%와 큰 움직임 유지 확인.
- 막 감쇠는 실제로 작동한다. 굽힘 감쇠0인 현재 후보의 한계와 수치 진동 가능성을 구분하며 원인은 확정하지 않았다.
- 새600+기준24의300 raw 프레임 hash·시간·핀·검산·checkpoint·외력 확인과 공통512점 CPU 분석 완료. 새 시뮬레이션/구현 변경 없음.
- 기존24는 다른 GPU의 관찰 참고다. 새 모델의시간/공간 수렴·시각 채택·학습/R1 완료는 미승인이다.
- [실행/뷰어·결과 보존 규칙](../R1_teacher_velocity_reset/self_contact/internal_damping.md#실행과-재생): 기존 완료 묶음은 재실행/덮어쓰지 않는다.
- 다음은 약한 굽힘 감쇠 등 후속 방향을 검토하는 것이며 이번 요청을 추가 구현/계산 승인으로 해석하지 않는다.
- 기존 원본·dirty/서브8·16 작업을 보존했다. R1 경계 확인, canonical/TeX/PDF 변경 없음. commit/push·fetch·외부 다운로드 없음.

## 이전 작업 상태 — 당시 기록

- 2026-09-29 사용자 wind 관찰: 감쇠24의 움직임이 둔해 최종 시각 채택 보류.
  [공통5초 상태에서wind8/16 준비·기존24 재사용·대안](../R1_teacher_velocity_reset/self_contact/wind_damping.md#현재-상태).
  CPU9개·실제 동결 입력 동일성·기존24 캐시/한 프레임 렌더 통과. 새 GPU 실행·대안 감쇠/적분법 구현은 하지 않았다.

- 2026-09-29 감쇠24 완료 결과 전용 뷰어 스크립트 연결. 기본64·전체5초에서 시작,128 선택 가능.
  [명령·캐시 검증·실제 렌더 확인·시각 대기](../R1_teacher_velocity_reset/self_contact/damping24_time.md#완료-결과-뷰어).
  두600프레임 캐시와64 한 프레임 렌더 통과. 원본 보존, 새 시뮬레이션/코드 구현 변경 없음.

- 2026-09-29 서브 감쇠24 사각형64/128의 독립10초 완료 결과를 CPU 비교했고 수치 통과·시각 대기다.
  [정확한 run·기준 대비 수치·검산·한계](../R1_teacher_velocity_reset/self_contact/damping24_time.md#서브-완료-결과-분석).
  기본64 유지 근거 확보,256 추가 불필요. 다음은 wind 시각 검토. 원본 보존, 새 GPU 실행 없음; R1 기준/TeX/PDF 변경 없음.

- 2026-09-29 후속 요청으로 감쇠24의64→128을 한 PC/cuda:0에서 순차 실행하는 통합 스크립트를 준비했다.
  [단일 명령·동결 복사·실패 중단·비교·검증 한계](../R1_teacher_velocity_reset/self_contact/damping24_time.md#단일-pc-통합-실행).
  CPU6개·실제 입력 쌍·셸 검사 통과, GPU 미실행. 이전 교차 GPU 실행 계획을 대체하며 기존 입력/결과/dirty는 보존한다.

- 2026-09-29 감쇠24 사각형 연속10초 메인64/서브128 독립 실행 준비 완료.
  [명령·동결 입력·교차 GPU 해석·검증 한계](../R1_teacher_velocity_reset/self_contact/damping24_time.md#현재-상태).
  CPU61개 회귀+수정 후5개 준비 검사 통과. 기존 결과/dirty 보존, GPU 미실행. 동일 GPU 비교 기준·R1 채택 경계 유지.

- 2026-09-29 사용자 시각 판단으로 감쇠24 s^-1을 후속 실험의 잠정 기준으로 선택했다.
  [적용 범위·이전 후보 대체·wind 후 재조정 조건](../R1_teacher_velocity_reset/self_contact/damping_sample.md#감쇠율-잠정-선택).
  고감쇠 실결과 재분석·wind 검증·최종 학습 채택은 이번 작업에 포함하지 않았다. 기존 입력/결과/solver 기본값 유지.

- 2026-09-28 사용자 지정8/16/24 s^-1 입력·실행/뷰어 준비 완료.
  [동일 초기 상태·실행 명령·상한 변경·검증 한계](../R1_teacher_velocity_reset/self_contact/damping_sample.md#고감쇠-비교-준비).
  CPU28개 검사와 실제 manifest/상태/외력 확인 통과. 감쇠 상한만24로 확장, 기존 커널·검산·복구 유지.
  GPU 실행/시각 판정/학습 채택 미완료. 기존 dirty·실결과 보존, R1 기준·TeX/PDF 변경 없음.

- 2026-09-28 강화 감쇠3/5/8 s^-1 비교 입력·실행/뷰어 래퍼 준비 완료.
  [같은 초기 상태·순차 실행 명령·검증 한계](../R1_teacher_velocity_reset/self_contact/damping_sample.md#강화-감쇠-비교-준비).
  CPU24개 검사·실제 동결 입력 확인 통과. 기존0/1/3과 호환, 기존 결과/dirty 보존. GPU 실행·최종 채택은 미완료다.

- 2026-09-28 감쇠 세 조건의 GTX1080Ti 완료 결과를 CPU 분석했다.
  [완료 검산·운동 감소·시각 후보와 한계](../R1_teacher_velocity_reset/self_contact/damping_sample.md#완료-결과-분석).
  뷰어 캐시 준비 완료. 약한 감쇠 우선 시각 비교 후보이며 최종 채택/학습 판정은 보류다.
  새 GPU 실행·코드 수정 없이 원본 보존. 아래 감쇠 실행 대기는 당시 기록이다.

- 2026-09-28 사용자 요청으로 서브 v13 사각형 기본128/복구256 묶음과 완료 후 비교 래퍼를 준비했다.
  [동결 입력·실행/비교 명령·검증 한계](../R1_teacher_velocity_reset/self_contact/v13_time128.md#현재-상태).
  원본 runtime/native·초기 상태·외력 동일, CPU25개 검사와 실제 묶음 읽기 통과. 최근 감쇠 코드는 포함하지 않았다.
  GPU 실행/완주/실제 시간 비교/시각·학습 승인은 미완료다. 다음은 사용자 RTX5070 실행 후 CPU compare다.
  기존 dirty/원본/준비 묶음을 보존했다. R1 경계를 확인했고 기준·TeX/PDF는 변경하지 않았다.

- 2026-09-28 사용자 명령으로 완료된 서브 v13을 CPU 재분석했다.
  [새 보고서·수치·복구 분모·채택 한계](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v13.md#완료-v13-재분석).
  세 씬600프레임/저장 검산·raw 구간 연결·산출물 hash 확인. 사각형/삼각형의 처짐과 무풍 후반 운동이 남는다.
  시각 채택·민감도·학습은 보류다. 감쇠 샘플 결과로 해석하지 않으며 새 GPU 계산/코드 수정은 없다.
  원본과 이전 분석을 보존했다. R1 경계 유지로 TeX/PDF 수정·빌드 없음; 다음은 감쇠 샘플 사용자 실행/비교다.

- 2026-09-28 사용자 요청으로 삼각 깃발1초×감쇠0/1/3 비교 묶음을 준비했다.
  [동일 시작 상태·실행/뷰어 명령·분할 감쇠 한계](../R1_teacher_velocity_reset/self_contact/damping_sample.md#현재-상태).
  CPU34개 검사·동결 입력·셸 구문 통과. GPU 계산/graph 실행/실제 시각 판정은 미실행이다.
  기존 v13/dirty/실결과는 보존하며 프레임 감쇠는 최종 재료 모델 채택이 아니다.
  다음은 사용자 run과 세 결과 시각 비교다. R1 경계 확인, canonical 변경 없어 TeX/PDF 수정·빌드 없음.

- 2026-09-28 서브 컴 RTX5070 v13 세 씬600프레임 완료 결과에 뷰어·분석·비교 래퍼를 연결했다.
  [정확한 run·바로 실행 명령·실제 검증](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v13.md#서브-컴-완료-결과와-연결).
  캐시/화면/분석과 사각형 자기 비교를 확인했다. 사각형 복구466개와 폐기 증거를 보존했다.
  실제 두 정밀도 비교·사용자 시각 판정·학습 적격성은 별도다. 핵심 Python·원본·동결 runtime은 수정하지 않았다.
  이번 작업은 experiments 래퍼/기록만 변경했다. R1 조건을 확인했고 운영 연결이므로 TeX/PDF 수정·빌드는 없다.

- 2026-09-28 사용자 요청1번 공통512점 비교기 준비 완료. CPU29개 검사와 v12 자기 비교 출력 확인.
  [직접 run 비교 CLI·조건·한계](../R1_teacher_velocity_reset/self_contact/cg_comparator.md#현재-상태). 수치 통과는 시각 대기이며 최종/학습 pass를 발행하지 않는다.
  실제 새 dt/메시 결과 비교와 HTML 브라우저 재생은 미검증이다. T/S 준비·실행·24 지원은 별도다.
  기존 원본/동결 runtime/실행 중 작업을 수정하지 않았고 새 GPU 계산·학습·commit/push·외부 다운로드는 없다.

- 2026-09-28 서브 컴 v13 계산과 독립적으로 CPU 처짐 분석·공통512점 map 구현/검증 완료.
  [명령·실제 v12 분석·지원 해상도와 한계](../R1_teacher_velocity_reset/self_contact/motion_analysis.md#현재-상태). 검사13개, v12 세 씬 각600프레임·복구113개 보존.
  사각형16/32 정적 map 검증 통과. 계획24는 기존 생성기 미지원이며 실행 코드 확장은 아직 하지 않았다.
  사용자 보고상 v13은 서브에서 실행 중이다. solver/동결 runtime/원본을 수정·중단하지 않았고 새 GPU 계산·학습은 없다.
  다음은 v13 완료 후 분석·시각 확인. T/S 비교·GS/작은 응답·학습 진입은 미완료다.

- 2026-09-28 후속 사용자 선택: 초기5도 원통형 굽힘·preload1/calm4/wind5초의 v13 묶음 준비 완료.
  [새 설정·명령·검증 한계](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v13.md#현재-상태). 테스트29개 및 실제 입력/초기 국소 기하 정적 검사 통과.
  GPU preflight/smoke/run·자연스러운 처짐은 미검증이다. v12 결과는 보존하고 새 결과로 승계하지 않는다.
  다음은 사용자 v13 실행·시각 확인이며, R1/CG 민감도·학습 판정은 그대로 미완료다.

- 2026-09-28 v12 뷰어 연결 완료: 세 씬 연속10초 캐시·15개 검사·실제8.5초 표시 확인.
  [명령·조작·원본/캐시 검증 범위](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v12.md#연속10초-뷰어).
  전체 궤적의 사용자 시각 판정과 CG 민감도 통과는 아직 별도다.

- 2026-09-28 사용자 결정: CG 목적의 두 해상도 민감도·시각 확인과 제한 학습 진입을 채택했다.
  [T/S 설정·예산·스크립트별 구현/실행 순서](../R1_teacher_velocity_reset/self_contact/cg_development_checks.md#현재-상태).
  당시에는 문서만 갱신했다. 후속 뷰어 구현은 위 항목이며 새 시뮬레이션·학습은 수행하지 않았다.

- 확인일2026-09-28. 동일 v12 manifest의 GTX1080Ti 저장 결과에서 세 씬 연속10초·각600프레임
  완료를 확인했다. [완료 분모·원본 식별과 비용](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v12.md#v12-사용자-실행-결과).
- 사각형 wind113개는 code2 111개/code1 2개의 기본 dt 실패 뒤 GPU dt/2로 승인됐다.
  마지막74프레임 모두 복구하므로 기본 dt 무복구 안정성으로 해석하지 않는다.
  [복구 frame·폐기 증거·재검토 조건](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v12.md#사각형의-복구와-남은-부담).
- 이번 사후 분석은 manifest296개·프레임1,800개·폐기 증거113개·여섯 raw hi/lo 경계를 확인했다.
  채택122,432단계의 저장 flags는0이며, 물리 잔차/CCD를 다시 계산한 검산은 아니다.
  [검사 범위와 수치](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v12.md#완주와-사후-검산).
- 미완료: CG 개발용 민감도·사용자 시각 판정·GS/기준 모델·제한 학습 진입, 정식 수렴과 R1 Gate.
  RTX5070 v12는 미검증이지만 첫 CG 개발 진입의 선행 검사에는 포함하지 않는다.
  [보장 범위·다음 작업](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v12.md#완료-범위와-다음-작업).
- 2026-09-27 준비/대기 상태는 이번 GTX1080Ti 결과로 대체한다. 기존 v11 및 실패 원본은 보존한다.
  이전 실행기8개/관련33개 회귀는 당시 결과이며 이번에는 재실행하지 않았다.
- 저장 결과 CPU 분석과 후속 뷰어 렌더링을 수행했다. 시뮬레이션 재시작·학습·commit/push 없음.

## 이전 v11 근거

- 확인일 2026-09-24. 원본 v11 사각형 wind 메인169·서브193 실패 직전 상태를
  메인 GTX1080Ti에서 각각 1프레임 재생해 기본 code1을 재현했고, 진단 opt-in GPU
  dt/2는 두 상태 모두 독립 검산을 통과했다. RTX5070 직접 복구·wind 잔여 구간과
  직렬10초 궤적은 미검증이다. [원본·입력·명령·결과](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#사각형-wind-code1-dt2-격리-진단).
- 확인일 2026-09-24. 동일 manifest의 메인·서브 v11에서 손수건·삼각 깃발은 preload/calm/wind 120/240/240 전부 승인됐다. 사각형은 메인 wind169·서브 wind193 표시 프레임에서 Newton15회 한도(code1)로 실패했다. 양쪽 실패 지점에서 이전 후보 초과(code10)는 아니다. [원본 report와 실패 진단](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#v11-사용자-실행-결과).
- 완료 두 씬의 preload→wind 저장 경계를 기존 메시 뷰어에 연결했다. 메인·서브 각각 별도 캐시를 만들고 7개 단위/회귀·양쪽 headless 표시를 통과했다. 물리 계산·원본 변경은 없다. [명령·캐시 hash·표시 범위](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#완료-두-씬-뷰어).
- v11 동결 설정은 원래 물성·바람·dt·허용오차를 유지하고 swept 용량2M·cuDSS 결정성을 적용한다. [당시 설정·제한 검증](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#v11-변경과-검증-범위).
- 미완료: RTX5070 직접 복구·wind 잔여 구간, 양 GPU 궤적·성능 비교 및 R1 Gate 판정.
  완료 두 씬의 표시 화면은 새 수치 검산이나 3DGS 결과가 아니다. [검증 범위](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#사각형-wind-code1-dt2-격리-진단).
- 당시 대기였던 직렬10초 선택과 code1 신규 bundle 반영은 위 v12 준비로 대체됐다.
