# P3 굽힘 강성 절반 비교·뷰어 시간 호환 수정

## 현재 상태

- 2026-09-30 사용자 실행의 새1/1000 첫 검사1/1·본120/120 완료를 확인했다. 이번 작업에서 물리 시뮬레이션은 재실행하지 않았다.
- [조건·현재 상태](../R1_teacher_velocity_reset/self_contact/bending_stiffness.md#현재-상태): 기존1/500 재사용, 막5ms·굽힘 감쇠0, 같은8초 raw에서 마지막2초 비교다.
- [오류 원인·수정](../R1_teacher_velocity_reset/self_contact/bending_stiffness.md#시간-기록-호환-수정): 과거 동결 기록기는phase0–2초를 저장하지만 뷰어가wind3–5초를 요구해 거절했다. 전체 시간8–10초는 정상이다.
- 뷰어가 manifest로 검증된 동결 저장식을 식별해 형식별 기대 시간·전체 시간·유한성을 검사한다. 원본 NPZ를 바꾸거나 임의offset으로 오류를 통과시키지 않는다.
- [검증 근거](../R1_teacher_velocity_reset/self_contact/bending_stiffness_viewer_fix_checks.json)의 `tests`·`actual`·`preservation`: CPU/모의 실행20개 검사, 실제 두 궤적의121상태 캐시, 한 프레임 렌더 통과.
- 표시 CUDA/OpenGL interop 미지원은 기존copy fallback으로 처리됐다. 물리 계산 fallback이나 새 시뮬레이션 실행이 아니다.
- 원본 NPZ·보고서·동결 runtime·manifest를 보존했다. 현재 뷰어와 동결 실행기의 소스 차이는 표시 호환 수정이다.
- [실행·재생](../R1_teacher_velocity_reset/self_contact/bending_stiffness.md#실행과-재생): 기존 뷰어 명령으로 비교한다. 완료된run 재실행 불필요.
- 원본 phase 메타데이터의 의미 차이는 후속 분석에서도offset과 함께 해석해야 한다. 진동 개선·민감도·학습 채택은 미판정이다.
- [사용자 시각 평가](../R1_teacher_velocity_reset/self_contact/bending_stiffness.md#사용자-시각-평가): 기본 비교의 하늘색 기존1/500 움직임을 주황색1/1000보다 선호했다. 이번 갱신은 선호 기록이며 위 검증은 재실행하지 않았다.
- [화면 가림 수정](../R1_teacher_velocity_reset/self_contact/bending_stiffness.md#화면-가림-수정): 두 결과 로드를 확인했고, 좁은 창/큰 UI에서 왼쪽 천이 완전히 가려지는 별도 재현을 수정했다. 사용자 미표시 쪽은 미확인이다.
- 사이드바 밖 전체 궤적 맞춤·창 크기 자동 대응·Fit all recordings 버튼 적용. 공용 뷰어 포함38개 검사와1280/960폭 UI 렌더에서 두 천 표시 확인.
- 후속 권고는 기존1/500을 움직임 비교 기준으로 유지하면서 잔진동 억제를 검토하는 것이다. 강성 추가 감소의 우선순위는 낮추며, 새 방법 채택·구현·계산은 승인되지 않았다.
- R1 제한 CG 경계는 유지한다. 사용자 선호 기록으로 canonical/완료 기준/TeX/PDF 변경 없음. 이번에는 experiments 문서만 갱신했고 code·experiments 기존 미커밋 변경과 원본 결과를 보존했다. commit/push/fetch·외부 다운로드 없음.
