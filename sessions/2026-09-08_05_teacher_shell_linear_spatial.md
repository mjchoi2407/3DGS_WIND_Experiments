# Shell 선형 공간 응답 진단

2026-09-08 Wind3DGS experiments-side. 사용자의 샘플 생성·검증까지 연속 진행 지시에 따라
[code 설계·구현](../../code/sessions/2026-09-08_05_teacher_shell_linear_spatial_design.md)의 두 run을 실행했다.

기존 full 시간 검증 원본을 무결성·시간 척도로 연결하고, 같은 x² 초기 변형의 n=4/8/16×세 삼각분할을 비교했다.
Run당 9개 사례·92,169 frame·720 chunk, integration step은 0개다.
[결과·명령](../R1_teacher_shell_linear_spatial/README.md)과 provenance/evidence를 보존했다.

공간 속도 차이는 n=8→16에서 22.6855–23.2100%, finest 방향 최대 51.5462%로 두 물리 gate가 실패했다.
대수·mapping·linear response는 통과했다. 최대 상대 에너지 drift 6.00209e-12, EOM 1.45258e-12다.
원본·재실행 전체 frame 재계산과 report/1,508개 파일 byte가 일치하며 runtime.json만 다르다.
Source 30개, inventory 1,509개/run, 약 266.25MB/run이다.
Audit 시간은 113.373/40.772초, 검산은 30.874/29.878초다. 1,800초 상한 안에서 완료했다.

Raw 폴더는 `artifacts/runs/teacher_shell_linear_spatial/20260908_reference_v1`와 `_replay`다.
Report SHA-256은 `3a0d8e7ee5be505b190008d387c67a113a027ce0651595cb43b0812c8c33ba1a`다.
기존 source25개·원본을 보존했고 물리 기준을 바꾸지 않았다. 관련 228개 검사 통과와 cache 권한 재시도는 code note에 기록했다.

본 학습용 Teacher로 채택하지 않았다. [개발용 샘플](2026-09-08_06_teacher_sample_dataset.md)은
기존 Newton native 경로를 사용하는 별도 loader 검증 자료다. 본 공간 실패를 통과 결과로 승계하지 않는다.
Code/experiments만 갱신했고 root/ideas 기존 변경을 유지했다. Stage·commit·push·fetch는 하지 않았다.
