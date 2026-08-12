# M01--M04 재사용 후보 감사

작성일: 2026-08-13

이 감사는 기존 자산의 삭제 여부가 아니라 새 TD 완료 상태로 승격할 수 있는지를 판정한다. 현재 결론은 모두 “재사용 가능성은 있으나 TD contract 재검증 전 완료 승격 금지”다.

| 기존 자산 | 재사용 가능한 부분 | 금지되는 해석 | 새 검증 위치 |
| --- | --- | --- | --- |
| M01 static 3DGS I/O | PLY/camera parsing, synthetic leaf, static render fixture | `CanonicalGaussianAsset`와 affine transport가 이미 완료됨 | TD01 schema/round-trip, TD13 renderer |
| M02 mesh proxy/binding | cloth fixture, 수치 transport test seed, triangle-reference baseline | target runtime mesh 또는 XY proxy가 mainline임 | TD01 E0 fixture, TD12 topology gap, E1 mesh baseline |
| M03 procedural wind | prescribed spatial/temporal query와 qualitative preview seed | 물리 force/상태 적분 또는 teacher임 | TD04 wind-query fixture, qualitative baseline |
| M04 mesh extraction | independent static GS 생성, offline mesh preprocessing/viewer support | runtime mesh가 허용되거나 새 solver가 구현됨 | TD02 reconstruction, mesh-privileged baseline |

추가 판정:

- PLY의 `f_dc`/`f_rest`는 appearance SH다. 공력 RSH 잔재로 간주해 삭제하지 않는다.
- RSH는 mainline runtime dependency가 아니며 향후 TD06/E2 representation ablation에서만 opt-in한다.
- M02/M03의 procedural displacement는 물리 정확도 evidence로 사용하지 않는다.
- 기존 M## `[x]`/완료 기록은 TD00--TD14 상태에 승계하지 않는다.
- 현 TD semantic packages가 legacy `wind3dgs.m0*` 또는 RSH module을 import하지 않는지는 TD00 smoke가 AST import scan으로 검사한다.

