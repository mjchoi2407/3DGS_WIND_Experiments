# 4배 랜덤 바람: 자연 응답·속도 초기화·원식과 세분 검증

사용자는 제시한 다음 작업의 1–3단계를 승인했다. 기존 파형을 정확히 4배로 만들어
목표 knot 풍속 1–2m/s에서 1.5초 동안 rest natural과 0.3/0.7/1.1초의 독립 velocity-reset을 검증한다.
Seed 20260909, 방향·시각·고정 폭·재료·물리 law 및 solver 허용오차는 유지한다.
벡터 보간 중의 풍속은 knot 하한보다 작을 수 있다. 마지막 0.3초에는 ambient wind를 0으로 만들며 상대속도 항력은 남는다.

이번 완료 범위는 원식과 공간·시간·메시 방향의 기존 1% 기준 확인이다.
후속 풍속 확대·재료/학습 적격성의 채택과 학습데이터 생성은 포함하지 않는다.

## 현재 이어하기 인계

기존 결과를 보존하고 개선 경로로 남은 계산을 잇는 [사용자 실행 묶음](fast_handoff/README.md)을 준비했다.
CPU/CUDA 작은 흐름 검증을 마쳤으며 장시간 실행은 사용자 실행 대기다. 아래 수치 표의 미완료 항목은
이번 준비만으로 통과 처리하지 않는다.

## 실행과 검산 연결

`teacher_p3_shell_random --wind-scale 4`가 명시적 배율을 config에 저장한다.
Chunk schema v2는 배율과 전체 파형 identity의 일치를 요구한다. 검산기·checkpoint 분기·
비교기·그림도 원본의 배율을 사용한다. 별도 배율의 원본을 같은 바람의 수렴 비교로 섞지 않는다.
물리/단기 GPU source 22개는 선행 결과와 동일하다. 새 producer 26개와 runtime 47개는
`../evidence/p3_shell_random_runtime_v5.zip` 및 `runtime_manifest_v5.json`에 동결했다.
실험 wrapper의 대응 snapshot은 `p3_shell_random_experiment_wrappers_v2.zip`이다.

```bash
bash code/scripts/check_teacher_p3_shell_random.sh --wind-scale 4 --resolution 8 --substeps 128 --output experiments/artifacts/runs/teacher_p3_shell_random/scale4_natural_m8_s128
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/p3_shell_random/verify_development_evidence.py experiments/artifacts/runs/teacher_p3_shell_random/scale4_natural_m8_s128 --output experiments/artifacts/runs/teacher_p3_shell_random/verification/scale4_natural_m8_s128
```

원식 검산은 전 interval CUDA 재계산과 frame별 3개 NumPy 상태 및 공력 대조를 구분해 명시한다.
큰 원본 NPZ는 ignored `artifacts/runs/teacher_p3_shell_random/`에 새 이름으로 보존한다.
기존 약한 바람과 모든 snapshot을 덮어쓰지 않는다. 선행 schema v1의 재현에는 runtime v4와
wrapper v1의 격리된 source를 사용한다.

## 진행 상태

배율 연결과 기존 경로를 포함한 관련 검사 10개가 6.258초에 통과했다.
실제 CUDA n4/sub8의 3 frame을 실행했고 CPU 전체 상태 및 CUDA/CPU 두 경로의 검산도 통과했다.
긴 계산은 n8/sub128, n16/sub128, n16/sub256 forward/backward의 네 조건으로 시작했다.
시간·공간 오차를 구분해 필요한 해상도만 추가한다.
완료 결과와 실패·보완 과정은 아래에 누적하며, 아직 이 4배 조건의 수렴 통과를 선언하지 않는다.

[결정·검증 요약](../../../sessions/2026-09-09_02_teacher_velocity_reset.md)

## 완료된 중간 검증

- Runtime v5를 별도 폴더에 풀어 CPU 전체24 interval 검산도 통과했다.
- N8/sub128 natural90 frame(1.5초)의11,520 interval 원식 검산과 checkpoint42 재시작이 통과했다.
  재시작9개 배열과 step diagnostics가 원본과 정확히 같다.
- 이 거친 natural의 최대 nodal 변위는0.109058054936m, 최대 원식 force 잔차/허용치 비는0.573284376이다.
  Bernstein 면적비 하한0.960348160, mid-surface strain 성분 상한0.000358222486,
  선형 표면 strain 성분 상한0.003892241366이다. 재료 허용치의 최종 채택은 별도다.
- 마지막0.3초의 zero-ambient 공력 일 합은−0.000767278468J이며 최대 frame 에너지 결산 차이는
  3.02508161e−11J다. 이 값은 아직 n8의 개발 관찰이며 공간 수렴 판정이 아니다.
- [선택 시각의 형상](figures_shapes_m8_s128_v2/natural_shapes.png)은 P3 surface evaluation을 사용했다.
  모든 축에 같은 물리 축척을 적용했고 변위를 확대하지 않았다. 그림의 최대 시각은 nodal 변위 기준이다.
  V1 초안의 label 간격을 v2에서 보완했으며 그림별 source/원본/검산 SHA를 보존한다.

선행 약한 바람 205개, 단기 GPU 100개, 초기 유한 회전 147개 compact evidence의 기존 inventory를
다시 대조했다. 총 452개 모두 변경이 없으며 `evidence/legacy_compact_integrity_v1.json`에 확인을 기록했다.

## 첫 공간 기준 실패와 보완

N8→16/sub128 natural의 속도 전체 보간 상대 상한은1.087961809%로 기존 1% 기준을 넘었다.
변위/증분은0.0632761324%다. 최대 속도 차이는 frame88의0.003749052115m/s RMS이며
reference peak는0.344594091809m/s다. 후반 zero-ambient 구간에서 차이가 커졌고,
이 비교는 속도에 별도 padding을 더하지 않으므로 평가 상한의 임의 완화로 처리하지 않는다.

동일 수식/배율/허용오차로 n32/sub256 natural과 세 reset을 추가했다.
N16→32/sub256 비교를 연결했으며 n16의 시간·방향 비교도 계속한다.
N8→16 실패 원본과 보고서는 보존한다. 더 촘촘한 조건이 통과하더라도 이 거친 조건이
통과한 것으로 기록하지 않는다. 최종 시간·방향 비교 범위는 실제 완료한 조건을 명시한다.

최대 차이의 실제 시각1.4578125초(frame87/index60, zero-based)에서 공간 적분 오차를 성분별로 분해했다.
초기 법선 y 성분 RMS는0.003724265910m/s이고 오차 제곱합의98.682105806%를 차지한다.
x/z RMS는0.000418892899/0.000098812607m/s다. 합성 RMS는 원래 비교와1e−12 상대 허용 내에 일치했다.
이는 오차 방향의 진단이며 원인 확정은 아니다. `evidence/diagnostics/`에 실제 evaluator와 report를 보존한다.

32격자의 시간(sub128→256)·방향(forward/backward/sub256) 비교도 배치했다.
두 새 자연 응답은 각각 n8/sub128과 n16/sub128 검증 묶음이 모두 끝난 뒤 시작해 동시 GPU 작업 수를 유지한다.
보완 판정 조건은 결과를 보기 전에 `evidence/plan_v1.json`으로 선언했다. 기존 coarse 실패를 제외한
n16 시간/방향 및 n16→32 공간, n32 시간/방향의 모든 natural/reset 분기가 기존 1% 기준을 통과해야 한다.

N16 natural의 sub128→256 시간 비교는 속도0.144731648980%, 변위/증분0.000870589596%로 통과했다.
이는 n16의 시간 차이이며 n8 시간 오차까지 직접 측정한 값은 아니다. N16→32 공간 보완과
finest n32의 시간/방향 대조를 계속한다. N8의 reset42 suffix48 frame/6,144 interval도 원식 검산을
통과했고 제거 kinetic은0.001473182516J다. 아직 세분 비교 묶음 전체의 통과를 선언하지 않는다.

N8/sub128은 natural/세 reset의29,952 interval과 별도 checkpoint128 interval 검산을 모두 완료했다.
N16/sub256 natural23,040 interval의 원식·기하와 checkpoint42 정확한 재시작도 통과했다.
이 natural의 최대 nodal 변위는0.109084863908m다. 실제5상태의 CPU 구적6/4 대10/8 최대 상대 차이는
energy7.64569753e−10%, force mass-dual0.000931460492%, moving aero0.000646301517%,
동일 위치/velocity0 aero3.21550101e−12%다. 선택 상태의 진단이며 전 상태 구적 인증은 아니다.

N16/sub256 natural의 forward/backward 방향 비교도 기존 1%를 통과했다. 속도 상대 상한은0.0595894390801216%다. 초기화 분기의 결과는 완료 후 따로 판정한다.

N8→16/sub128 reset18의 속도 상대 상한도1.2110153574758873%로1% 기준에 미달했다. 자연 응답과 분기 실패를 모두 보존하고 같은 n16→32 세분 계획으로 확인한다.

N8→16/sub128 reset42도 속도1.1938830132097489%로 기존 1%에 미달했다. 세 번째 coarse 실패도 보존하며 보완 계획은 유지한다.

N8→16/sub128 reset66도 속도3.4952609601647144%로 미달했다. Coarse 공간 비교는 네 분기 모두 1% 기준에 미달한다. 마지막분기의 속도 절대 RMS 차이 상한은 0.001871508541185961m/s, reference peak는0.053544172023646724m/s다. 절대오차와 분기 응답 크기를 함께 해석하며 기준은 유지한다.

N16 reset18의 sub128→256 시간 비교는 속도0.15886229109515948%로 통과했다. 다른 분기와 n32 조건은 각각 완료된 결과로 판정한다.


[4배 파형의 변위·속도·운동에너지 시계열](figures_timeseries_m8_s128_v1/random_reset.png)을
원식 검산을 마친 n8/sub128의 네 분기에서 생성하고 실제 그림을 확인했다. 속도/운동에너지의
점선은 초기화 개입이며 위치는 연속이다. 1.1초 초기화는 운동에너지의 큰 부분을 제거하고 작은 응답을 남긴다.
자유 영역 0.75m²의 RMS와 µJ 단위를 사용했고 그림별원본/검산/renderer SHA를보존했다.
이 그림으로 coarse 공간 기준 미달을 대체하지 않는다. 최종 수치 판정은 별도 비교 결과를 따른다.

## 분기별 수치 비교표 — 중간 결과

아래는 속도 상대 상한(%)이다. 통과 판정에는 변위와 변위 증분도 함께 포함한다.
`대기`는 실행 또는 검산이 아직 끝나지 않았다는 뜻이다. 기존 기준은 1%다.

| 비교 | Natural | Reset 0.3s | Reset 0.7s | Reset 1.1s | 현재 판정 |
|---|---:|---:|---:|---:|---|
| 공간 n8→16 / sub128 | 1.087962 | 1.211015 | 1.193883 | 3.495261 | 네 분기 실패, 원본 보존 |
| 시간 n16 / sub128→256 | 0.144732 | 0.158862 | 0.143669 | 0.731830 | 네 분기 통과 |
| 방향 n16 / sub256 | 0.059589 | 0.068246 | 0.062644 | 0.274527 | 네 분기 통과 |
| 공간 n16→32 / sub256 | 0.444132 | 대기 | 대기 | 대기 | 자연 응답 통과 |
| 시간 n32 / sub128→256 | 0.140173 | 대기 | 대기 | 대기 | 자연 응답 통과 |
| 방향 n32 / sub256 | 대기 | 대기 | 대기 | 대기 | 미확정 |

표의 갱신과 별개로, 과거 보고 원문과 실패·보완 과정은 위 session 링크에서 시간순으로 보존한다.

선행 소변형 샘플 99개 출력(376,077bytes)과 producer 54개 출력(167,594,035bytes)의 manifest 및 각 파일 SHA도 재확인했다. 모두 보존되었으며 `evidence/legacy_raw_preservation_v1.json`에 기록했다. 이 샘플을 유한 회전 shell의 학습데이터로 재분류하지 않는다.

N16 reset42의 시간 sub128→256 비교도 통과했다. 속도 상대 상한은 0.14366917432414084%다. 이 분기의 원식 검산과 방향 비교는 각각의 완료 보고서로 별도 연결한다.

N16 reset42의 대각선 방향 비교도 통과했다. 속도 상대 상한은 0.0626438794914952%다.

N32/sub128 natural의 90 frame / 11,520 interval이 원식·기하 검산을 통과했다. 최대 nodal 변위는 0.10909146016523852m, 최대 force 잔차/허용치 비는 0.9988100673728209다. Bernstein 면적비 하한은 0.9603987560631257, mid-surface strain 성분 상한은 0.00029429985776974047, 선형 fibre strain 성분 상한은 0.003947362933549428이다. 최대 frame 에너지 결산 차이는 3.1877922669456114e−11J, zero-ambient tail 일 합은 −0.0007659045008296678J다. 이는 이 조건의 원식 검산이며, n32 시간·방향 및 n16→32 공간 판정은 아직 기다린다.

N16 reset66의 시간 sub128→256 비교도 통과했다. 속도 상대 상한은 0.73183011529917%다. N16 시간 비교 네 분기가 모두 완료·통과했다. 각 원본 검산과 최종 n32 공간·시간·방향은 별도로 확인한다.

N16 reset66의 방향 비교도 통과했다. 속도 상대 상한은 0.27452723457168476%다. N16 시간·방향 비교 여덟 건이 모두 통과했으며, n16/sub256 정방향의 네 원본 59,904 interval 및 checkpoint 256 interval 검산도 모두 끝났다.

N16/sub256 역방향의 네 원본과 checkpoint 검산도 모두 완료했다. 처음 네 조건(n8/n16 sub128 및 n16/sub256 정·역방향)은 주원본 179,712 interval과 별도 checkpoint 768 interval을 모두 검산했다. 보완을 위한 n32 세 조건은 계속 진행 중이다.

N32 natural의 sub128→256 시간 비교가 통과했다. 속도 상대 상한은 0.14017320185221682%다. 공간 비교, 원식 검산 및 초기화 분기의 결과에 자동 승계하지 않는다.

N16→32/sub256 natural의 공간 비교가 통과했다. 속도 상대 상한은 0.4441317011175531%다. Coarse n8→16/sub128 natural의 1.087961809% 실패는 보존한다. N32 natural 시간 비교는 별도로 0.140173202%를 통과했다. 세 초기화 분기와 n32 방향 및 원식 검산 전체의 완료가 더 필요하다.

공간 비교의 조건은 coarse n8→16/sub128과 보완 n16→32/sub256으로 다르다. 두 수치만으로 공간 수렴 차수를 추정하지 않는다. N16과 n32의 sub128→256 시간 비교를 별도로 제시하며, 보완 공간 판정 자체는 동일 sub256에서 수행했다.

N32/sub256 natural의 23,040 interval 원식·기하 검산이 통과했다. 최대 nodal 변위 0.10909161545556276m, 최대 force 잔차/허용치 비 0.9999504637067977, Bernstein 면적비 하한 0.9603993022634437, mid-surface strain 성분 상한 0.00029430928983860063, 선형 fibre strain 성분 상한 0.003948190025140212다. 최대 frame 에너지 결산 차이는 7.517887918993388e−12J, zero-ambient tail의 일 합은 −0.0007659055302491345J다. 재시작과 세 reset은 이어서 확인한다.

N32/sub256 checkpoint42의 256 interval 원식 검산과 정확한 재시작도 완료했다. 9개 배열의 10,941,686개 scalar와 step diagnostics가 원본과 정확히 일치했다. 이어서 세 velocity-reset 분기를 검증한다.
