# P3 수식 구현 우선: 요소 내부의 3D 기하·질량·가상 일

2026-09-09 사용자는 **물리 수식을 제대로 구현한 뒤 학습데이터를 생성**하도록 순서를 명확히 했다.
이 작업에서는 학습데이터를 추가 생성하지 않았다. 기존 76개 작은 굽힘 sample과 원본은 역사적
개발 검증 자료로 보존하며, 전체 비선형 Teacher나 학습 적격성으로 승격하지 않는다.

## 요소 구현 당시의 범위와 후속 결정

기존 P3의 10개 signed shape와 미분을 재사용한 `P3SurfaceElement`를 추가했다.
삼각형 rest material 좌표 `[3,2]`로 만들고 10개 DOF의 현재 3D 위치·속도를 입력한다.
기하량, 방향 미분, consistent mass, 공력과 응력 가상 일의 음의 adjoint를 반환한다.
새 dependency, GPU, GUI, 시간 rollout 또는 학습 producer는 추가하지 않았다.

요소 구현 당시에는 아래 선택지를 제시했다. 이후 사용자가 **① 유한 회전 shell**을 선택했다.
후속 구현·검증의 현재 판정은 [P3 shell 보고서](../p3_shell/README.md)를 따른다.

| 선택 | 장점 | 한계 |
| --- | --- | --- |
| 유한 회전 shell (권장) | 변형 중 새 방향의 바람에 대응하는 최종 목표에 맞음 | 비선형 요소 연결과 solver 검증량이 큼 |
| von Kármán 판 | 신장·굽힘 결합을 비교적 간단히 구현 | 큰 회전에는 적용 불가 |
| 선형 P3 완성 | 작은 굽힘 조건의 검증을 빨리 정리 가능 | 최종 큰 회전 범위를 충족하지 않음 |

답변을 받기 전 공통의 기하/질량/가상 일 연산을 검증했으며, 이 요소를 곧바로
전역 nonlinear shell로 채택하지 않았다. 현재 `stress_force`는 주어진 응력 resultant의
가상 일만 계산한다. 재료 응력의 생성, 저장 에너지와 완전한 구조 접선을 구현한 API가 아니다.

## 수식과 단위

Flat rest material 좌표를 `(s,t)` [m], 현재 P3 표면을 `r=sum_i N_i x_i`라 한다.
`F_a=r_,a`, `H_ab=r_,ab`, `c=F_s×F_t`, `J=|c|`, `n=c/J`를 사용한다.
`F`와 `J`는 무차원, `H`와 곡률은 1/m다.

- Green strain: `epsilon_ab=(F_a·F_b-delta_ab)/2`.
- 곡률: `b_ab=n·H_ab`; flat rest의 기준 곡률은 0이다.
- Engineering 순서: `e=(epsilon_ss,epsilon_tt,2epsilon_st)`,
  `b=(b_ss,b_tt,2b_st)`. 공액 resultant의 shear에는 2를 다시 곱하지 않는다.
- `delta c=delta F_s×F_t+F_s×delta F_t`,
  `delta n=(I-n n^T)delta c/J`.
- `delta b_ab=delta n·H_ab+n·delta H_ab`.
- 2차 변화는 `c=nJ`를 두 번 미분한다. `delta_1 delta_2 c`와
  `delta_1 n delta_2 J`, `delta_2 n delta_1 J`, `n delta_1 delta_2 J`를 모두 포함한다.
- 내부 가상 일: `delta E=int(S·delta e+B·delta b)dA_rest`.
  `S`는 N/m, `B`는 N이며 `stress_force`는 이 선형 functional의 음의 adjoint다.
- 질량: `M=rho_A N^T diag(a_rest) N`.
  `a_rest>0`, `1^T M 1=rho_A A_rest`; signed shape를 양의 DOF mass로 바꾸지 않는다.
- 상대풍: `v_rel=v_air-N v`, `tau=kappa |v_rel·n|(v_rel·n)n`.
  `f=N^T diag(a_rest J) tau`. 현재 면적은 한 번만 곱한다.
  `f·v=sum_q a_rest J tau·(Nv)`, 합력과 원점에 대한 모멘트도 보존한다.
- 정지 공기의 일률: `P=-kappa sum_q a_rest J |(Nv)·n|^3<=0`.
  `aero_active=False`만 공력 0이며, ambient 0과 구분한다.

기하식은 [Verhelst 등, Kirchhoff–Love shell analysis §2.1–2.3](https://link.springer.com/article/10.1007/s00366-024-01958-4)와
대조했다. 논문의 두께 방향 strain에서 사용하는 곡률 부호와 여기의 `b=n·H` 정의를 구분한다.
이 단계의 `B`는 **여기서 정의한 b**의 공액 입력이다. 해당 논문의 spline discretization,
적응 mesh나 nonlinear acceptance를 P3로 승계하지 않았다. 1차 자료를 웹에서 조회했으며
외부 코드 다운로드·Git fetch·외부 dependency 변경은 하지 않았다.

## 막힘과 보완

1. 기존 판은 `r=(s,w,0.5-t)`인 normal-only DOF여서 면내 신장과 회전된 형상 전체를 표현하지 못한다.
   기존 결과를 유지한 채, 같은 shape로 모든 DOF의 3D 표면 기하를 계산하는 별도 모듈을 추가했다.
2. 곡률의 미분에서 현재 법선을 상수로 두면 에너지와 복원력의 가상 일이 어긋난다.
   법선의 1·2차 변화를 포함하고 finite difference 및 강체 회전으로 검사했다.
3. 좌표 중심화 후 anchor 자유도의 미분을 보정하지 않으면 translation invariance가 깨질 수 있다.
   shape의 partition/derivative sum과 centered position에 같은 anchor 보정을 적용했다.
4. 큰 회전의 요소 연결법을 선형 C0IP의 이름만 바꿔 사용하면 전역 일관성을 보장할 수 없다.
   전역 구조식 선택은 질문으로 남겨 두었다. 이 report는 정적 수식 대조이며 수렴 보고서가 아니다.

## 검증

신규 10개 unit test는 다음을 확인한다: 6차 다항식의 독립 해석 적분과 질량 SPD,
비직각 삼각형의 3차 field/미분 재현, 큰 기울기의 해석적 strain/curvature,
1.7 rad 강체 회전, 기하 1·2차 미분과 대칭, 응력 virtual work/합력/모멘트,
공력의 현재 면적/부호/회전/일률, zero-ambient 수동성, guard-before-area와 invalid input 거부.
신규 10개는 0.014s, 기존 P3를 포함한 21개 회귀 검사는 44.290s에 통과했다.
각 log는 `evidence/element_tests.log`, `evidence/p3_regression.log`에 보존한다.

별도 정적 실행은 기존 P3 n4/n8 × 두 대각선의 4개 모델, 총 240개 요소를 대조했다.
모든 대조에 사전 상대 허용치 `1e-10`을 사용했다.

| 항목 | 네 경우의 최대 상대 차이 |
| --- | ---: |
| Consistent mass | 1.39875e-15 |
| Normal generalized force | 1.40513e-15 |
| 고정 영역 반력 포함 합력 | 1.76425e-15 |
| 공력 일률 | 3.48598e-16 |
| 3D force/velocity의 가상 일 | 3.48598e-16 |

자유 영역 질량은 0.075kg, 모든 local mass의 최소 고유값은 양수다.
원본은 `artifacts/runs/teacher_p3_surface/20260909_geometry_v1/report.json`,
compact 결과와 source hash는 [evidence/report.json](evidence/report.json)에 있다.
이후 source 변경은 해당 파일의 hash와 구분해야 한다.

```bash
# Workspace root. --output은 새 파일이어야 한다.
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  -m wind3dgs.evaluation.teacher_p3_surface \
  --output experiments/artifacts/runs/teacher_p3_surface/recheck/report.json
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  -m unittest discover -s code/tests -p 'test_teacher_p3_*.py' -v
```

## 주장 경계

현재 geometry guard는 **구적점에서의** 비퇴화를 검사한다. 모든 요소 내부의 injectivity,
self-intersection 방지, strain/material 유효 범위 또는 장기 안정성 증명이 아니다.
단일 요소 내부 식이 통과해도 요소 사이 회전 연결·고정 경계·반력·에너지 tangent·solver,
동일 backend의 시간/공간/방향/독립 기준 수렴은 아직 완료되지 않았다.
새 데이터 0개, `training_eligible=false`, `r1_complete=false`다.
