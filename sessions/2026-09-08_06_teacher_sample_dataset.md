# Teacher 개발용 샘플 생성·검증

2026-09-08 Wind3DGS experiments-side. 사용자의 연속 진행 요청에 따라
[code 추출기](../../code/sessions/2026-09-08_06_teacher_sample_dataset.md)를 실행했다.
물리 기준 미달 상황에서 개발용 샘플/본 학습용 데이터 중 용도를 질문했고, 응답 전 개발용 소량 샘플로 진행한다는
가정을 알렸다. 본 학습용 적격성은 false이며 독립 GS·R1/R2 완료를 주장하지 않는다.

[실험 README](../R1_teacher_sample_dataset/README.md)에 실행·읽기·검산 명령과 그래프를 보존했다.
CPU n=8, 60fps, substeps16, iterations10, 기존 native 물성·M_ref0.1kg와 25 probe를 사용했다.
바람 pulse, step-on/off, aero-off displaced free decay 각 1초다. 모든 파생물은 한 source group의 development split이다.

- 원본 180 interval/183 state → 12 interval/13 state window **15개**.
- 데이터 20개 파일·125,293byte; raw inventory 93개·1,150,138byte.
- 세 CPU replay의 위치·속도·공력 force/work 최대 차이 모두 0.
- 원본 대조·시간/단위/measure/pin/guard·완료성·NumPy batch [4,4,4,3] 검사 통과.
- 추가 독립 프로세스의 전체 inventory·producer source24개·모든 sample 값 대조 통과.
- 생성/세 replay/dataset 검증 48.370초. 신규 검사 11개, 관련 공간/회귀 포함 서로 다른 239개 검사 통과.

Dataset 경로는 `artifacts/datasets/teacher_samples/20260908_sample_v1/`,
raw 경로는 `artifacts/runs/teacher_sample_dataset/20260908_sample_v1/`다.
Manifest SHA-256은 `1ab229207fa8ec60c282aa433c49d7a5f8a288deb1575688794b72b2afdae8f5`다.
환경·설정·split·report·run/dataset manifest·검산 JSON과 재현용 그래프 스크립트를 compact evidence로 보존했다.
기존 로컬 Matplotlib/Noto Sans CJK로 끝점 변위·속도 그래프를 만들었다. 설치나 외부 조회는 하지 않았다.

`training_eligible=false`는 데이터에 함께 저장하며 loader에서 `allow_development=True`를 요구한다.
공간/시간·공력·spectrum의 accepted Teacher와 independent GS/common-valid map/oracle이 남아 있다.
이번 작업의 개발용 샘플 생성·구조/수치 검증은 완료했고 본 학습용 물리 채택은 보류다.
Code/experiments만 갱신했다. Root/ideas 기존 변경 유지, stage·commit·push·fetch 미실행이다.

최종 QA에서 root/ideas 상태 보존, source snapshot 일치, raw/dataset ignore와 문서 링크 117개를 확인했다.
새 그래프를 직접 열어 한국어 글꼴·세 사례의 입력/끝점 응답 표시를 확인했다.
Code/experiments 모두 미stage·미commit·미push 상태이며 기존 사용자 변경도 그대로 남아 있다.
