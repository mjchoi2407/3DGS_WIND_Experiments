# Shell 한 주기 전체 시간 refinement

- 날짜: 2026-09-08
- 범위: Wind3DGS experiments-side, R1 개발 진단
- 상태: 관련 184개 검사·실제 원본/독립 재실행·전체 검산 완료, full 응답 기준 통과

사용자 “진행해줘”로 [code 설계](../../code/sessions/2026-09-08_04_teacher_shell_full_refinement_design.md)의
full N=20480/40960/81920·독립 재실행·검산 범위를 승인받았다.
신규 [실험 README](../R1_teacher_shell_full_refinement/README.md)에 실행·보존 방식을 기록했다.
기존 네 원본, 물리 모델과 solver source를 유지하고 새 폴더에만 결과를 기록한다.

두 CPU 계산은 별도 프로세스에서 동시에 실행한다. 검산은 성공 checkpoint의 chunk부터 순서대로 읽고,
각 run의 모든 상태·반복을 각각 재계산하며 배열·runtime 제외 trace도 직접 대조한다.
검산 대기 방식을 case 완료에서 chunk 완료로 바꾸면서 최초 읽기 전용 검산 프로세스만 중단·재시작했다.
두 수치 계산과 raw output, 고정 runtime source 25개는 중단·변경하지 않았다.
원격 fetch·설치·stage·commit·push는 수행하지 않았다. 기존 dirty 변경은 그대로 보존한다.

## 완료 결과

두 raw run은 `artifacts/runs/teacher_shell_full_refinement/20260908_reference_v1`와
`20260908_reference_v1_replay`다. 각 143,360 step을 완료했고 source/reference/short 회귀/prefix/solver/full 응답은 모두 통과했다.
정규화 속도 차이는 N=20480/40960/81920에서 **6.05975811% → 2.97472254% → 0.868280813%**다.
정규화 위치 차이는 1.74305602e-4 → 6.79436464e-5 → 1.87127486e-5로 감소했다.
Finest native energy drift는 3.67369912e-10이다. 기존 1%/1e-3 판정 기준을 바꾸지 않았다.

각 run에서 560개 chunk·143,363 frame·1,576,960개 반복 벡터를 확인했다.
힘·반력·에너지·EOM·Newmark 갱신·state chain, 143,360개 trial·286,720개 선형 correction을 각각 재계산했다.
배열·runtime 제외 trace와 chunk hash chain, 공통 grid 선택본·보고서·CSV·판정이 정확히 일치한다.
전체 검산 결과는 [verification.json](../R1_teacher_shell_full_refinement/evidence/verification.json)에 있다.

공통 semantic report SHA-256은 `14700c5346b3f9502f724abd32febcc7a7a6266771ab08fbb750dae531e985f5`다.
원본 audit 2742.384초, 재실행 2750.674초로 모두 7,200초 상한 안에서 완료했다.
각 run inventory 2,262개 파일, 원본 2,183,688,760byte·재실행 2,183,688,237byte를 보존한다.
최상위 manifest 자체는 이 byte 합에서 제외한다. 검산 시간 2395.712초에는 live chunk 대기가 포함된다.

[Provenance](../R1_teacher_shell_full_refinement/provenance.json)에 source 25개와 네 입력,
원본·재실행 byte/hash·선택 evidence 9개·검산 명령을 기록했다.
원본 회수 시 각 manifest와 chunk descriptor의 상대 경로·byte/hash·상태/trace/vector identity 및 연결을 확인한다.
Raw run·네 선행 원본은 삭제하거나 덮어쓰지 않는다. 새 실행은 새 폴더를 사용한다.

이번 결과는 고정 n=4 shell 한 조건의 시간 refinement 통과다.
`teacher_eligible=false`, `convergence_status=not_assessed`이며 공간·공통 probe/스펙트럼·work·감쇠·공력,
다른 물성/하중과 학습 dataset 발행은 포함하지 않았다. 기존 정적/공간 실패도 그대로 보존했다.
실험 README/index·본 note와 신규 evidence/provenance만 이번 experiments 변경 범위다.
Code와 experiments 모두 현재 변경은 미stage·미commit·미push다. Root·ideas는 변경하지 않았다.

최종 QA는 기존 비ignored 파일 613개 중 허용된 문서 5개 변경과 신규 파일 15개를 확인했다.
로컬 문서 링크 96개, 고정 runtime source 25개, evidence 9개 byte/hash,
공백·개인 경로/credential 패턴과 code/experiments의 `git diff --check`를 통과했다.
선행 8개 run의 inventory 1,746개 파일도 기존 byte/hash로 보존됨을 확인했다.
