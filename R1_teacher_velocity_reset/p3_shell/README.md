# P3 유한 회전 shell의 수식 구현과 검증

사용자는 2026-09-09에 제시한 선택지 중 **① 유한 회전 shell**을 선택했다.
추가 학습데이터는 물리 수식 구현·검증 뒤 생성하며, 이 작업에서는 발행하지 않는다.
기존 P3 형상 함수와 E=1e6Pa, nu=.3, h=.01m, 면밀도 .1kg/m²를 재사용한다.
왼쪽 .25m 고정, 구조 감쇠 0, 양면 normal 상대풍·frame-start force hold를 유지한다.
큰 회전의 기하를 허용하는 Koiter/StVK thin-shell 모델이며 임의의 큰 재료 신장, 소성,
두께 변화, 접촉 또는 self-contact 모델을 새로 포함하지 않는다.

구현은 `teacher/p3_shell_kernels.py`, `p3_shell.py`, `p3_shell_dynamics.py`다.
기존 native/P3 pressure/small-wind 원본과 producer는 변경하지 않는다.

[실제 P3 중앙 단면과 reset 에너지 장부](figures_v5/rest_reset_diagnostic.png) /
[벡터 PDF](figures_v5/rest_reset_diagnostic.pdf)에서 위치 보존과 속도 개입의 효과를 볼 수 있다.
그림은 n16/sub128의5m/s peak 진단 원본이며 재생 wrapper와 원본·검산 hash를 함께 보존한다.
마지막 frame은 zero ambient이며 reset 직후 속도도0이라 이 frame의 held force는0이다.
따라서 해당 구간은 저장 탄성에너지로 다시 움직이는 응답이고, finite 상태에서 바람 방향이 바뀌는
공력 응답은 첫째→둘째 frame에서 확인한다. 3 frame 결과를 장기 랜덤 바람의 검증으로 소개하지 않는다.

## 동결할 수식과 검사 순서

- Flat-rest Green strain과 현재 unit normal이 투영하는 곡률에 기존 StVK/KL 구성 행렬을 적용한다.
  `E_volume = 1/2 int(e^T D_m e + b^T D_b b) dA_rest`.
- 내부 edge는 plus의 rest 외향 conormal mu를 양쪽에서 동일하게 사용한다.
  `R=n_plus-n_minus`, `q=<F_a m_ab mu_b>`로 두고
  `E_edge=int(R·q + alpha/(2 h_avg)|R|²) ds_rest`.
- 경계는 `R=n-n_fixed`, `q=F_a m_ab mu_b`인 full flux다.
  P3 penalty alpha=`2.25 E h³`를 유지하고 결과에 따라 조정하지 않는다.
- 복원력은 전체 에너지의 음의 gradient이며 Hessian-vector product도 정확한 방향 미분으로 계산한다.
  요소 내부뿐 아니라 edge의 normal, moment, current tangent도 미분한다.
- 허용 free DOF의 선형 극한을 기존 clamped P3 K와 대조한다. Fixed row에는 full normal 경계의
  추가 접선 방향 미분이 있으므로 old normal-slope-only 식의 반력 행과 구분한다.
- Consistent M의 위치별 성분 결합과 정확한 HVP를 acceleration-form Newmark에 연결한다.
  내부 상태는 rest 기준 변위로 저장해 작은 dt에서 rest 좌표를 반복 차분하지 않는다.
  GMRES는 실제 residual을 검사하며 line search/실패 prefix와 입력 상태 보존을 요구한다.
- 학습자료의 확대 대신 큰 회전의 해석적 에너지·기하, 독립 시간 적분, 고정 하중 clock의
  방향 변화 바람을 차례로 대조한다. 정적 수식 검사는 동적 공간 수렴을 대신하지 않는다.

Edge 구성은 [Noels (2009), nonlinear DG Kirchhoff–Love shells](https://orbi.uliege.be/handle/2268/2093)의
normal-jump/consistent moment-flux 원리와 대조했다. 이 구현은 고정 두께의 Koiter/StVK 에너지에서
직접 유도한 보존적 식이다. 논문의 두께 적분 hyperelastic law 또는 nonlinear acceptance를 복제하거나
승계한 것으로 주장하지 않는다. Canonical 식과 상세 결과는 R1 본문에 통합한다.

검사별 수치·원본 경로·한계와 실패를 해결한 과정은 아래에 함께 기록한다.

## 검사별 범위와 확인된 결과

모든 아래 실행은 CPU 수식 진단이다. `status=completed`는 계산의 정상 종료이고, 물리 수렴 통과는
각 비교의 1% 조건을 별도로 확인한다. `training_eligible=false`, `r1_complete=false`,
`generated_training_samples=0`을 유지한다. 후속 GPU 이식은 [별도 실행·검산 기록](../p3_shell_gpu/README.md)을 따른다.

| 검사 | 실제 조건과 결과 | 해석 |
|---|---|---|
| 수식·solver 회귀 | 최초 신규15개+기존P3 21개=36개,44.284s 통과; 최종 신규23개13.329s 통과 | 고유 테스트 합계44개, 전체 repository suite와 구분 |
| Raw validator | 최종5개 통과 | 원본 변조, 잘못된 material/초기 계열·support torque, 실패 prefix의 오채택 거부 |
| Bernstein 상한 | 3개 통과 | 강체 영 strain, 시간 중간 overshoot, 해석적 cubic field의 공간/시간 대조 |
| 정적 원통 | n4/8/16,2대각선,곡률1.2/2 m^-1,축0/±45도:36조합 | 주어진 finite-rotation 형상의 에너지 수렴 |
| 원통 에너지 최대 차이 | n4 .628545%, n8 .0642517%, n16 .00747187% | 정확한 isometry의 E*=.5 D κ²×.75m² 기준 |
| Short 독립 시간 | n4,0.0005s,rest/bent-preloaded,Newmark32/64/128 vs DOP853 | finest 속도 상대 차이4.07803e-7/2.99502e-6, 두 계열 통과 |
| Actual wind 시간 | n4/n8의sub64→128 속도 차이.275331%/.471643% | 저장 공통 시각에서1% 아래; finest mesh의 시간 검사는 별도 |
| Actual wind 공간 | n4→8 at sub64:5.501521%; n8→16 at sub128:1.357196%; n16→32 at sub128:.385696% | 거친 격자의 실패와 마지막 sampled 1% 통과를 함께 보존 |
| Actual wind 방향 | n16/sub128 forward→backward:속도.153774% | 동일 공간 해상도·시간 간격의 대각선 방향 비교 |
| Bent release 시간 | n4 sub128→256:13.313118%; sub256→1024:7.737815%; sub1024→2048:.762185% | 세분 후 n4의 시간 비교 통과, 원통 release의 공간 수렴은 별도 |
| Bent 구적 자체 대조 | 동일4개 상태에서 volume/edge6/4 vs10/8 | 최대 force mass-dual 차이.00682105%, 구적 오차는 작은 범위 |
| Reset | n8 sub128,frame1에서위치유지·속도0,384step 원본 검산 통과 | 제거 kinetic1.86857643438e-5J, exact state/clock와 새 공력 |

Short temporal의 bent는 최대 회전0.9rad인 analytic cylinder를 **초기 형상 지지 하중**으로 유지한 뒤
추가 바람을 가한다. 지지 없는 bent release와 다르다. DOP853 두 기준의 최악 자체 상대 차이는
6.92588e-10이며 Newmark의 dt/2마다 약1/4로 오차가 감소했다. 큰 초기 변위로 분모를 부풀리지 않고
`u(t)-u(0)`과 속도를 각각 비교했다. 같은 ODE의 독립 적분이며 독립 공간 reference는 아니다.

Actual wind는60Hz에서 `[0,.5,0]`, `[.25,.35,-.25]`, `[0,0,0]` m/s의3 frame=.05s다.
현재 표면/속도로 frame 시작 힘을 계산하고 전체 구조 substep에 고정한다. 마지막 ambient0에서도
공기저항은 유지한다. 이 짧은 강제 응답의 통과를1.5s 랜덤 바람이나 장기 수렴으로 확장하지 않는다.

Bent release는 같은 바람과 material을 쓰되 analytic cylinder κ=1.2m^-1, 초기 속도0에서
지지 하중 없이 출발한다. n4 초기 nodal 변위 최대.329974m, 회전 최대.9rad다.
확인한 n4 실행의 최대 engineering strain 성분은.006916 미만이다. 이 형상은 바람으로 도달한
상태가 아니라 별도의 수식 진단이며, 사용자가 정한 rest-start/reset 데이터 생성 순서를 바꾸지 않는다.

비교 norm은 양의 common material-area quadrature에서 `sqrt(int |a-b|² dA0 /1m²)`의 최대값을,
기준 응답의 같은 RMS 최대값으로 나눈다. 고정 영역의 변위/속도 차이는0이다. 두 대각선을 함께
분할한 overlay의 degree-six 적분으로 signed P3 field를 대조한다. **공통 저장 시각의 sampled error**이며
기존 선형 P3의 모든 시간에 대한 modal/Lipschitz 상한으로 소개하지 않는다.

## 막힌 부분과 수정·진단 과정

1. 기존 normal-only P3는 finite rotation과 막 응답을 표현하지 못한다. Shape와 material은 재사용하면서
   3D Green strain/normal curvature의 에너지를 조립하고 edge의 current F/m/n까지 모두 미분했다.
2. 첫 rest-K/HVP 검사의33개 fixed-row 성분이 불일치했다. Old scalar normal-slope boundary에서
   full-normal 경계의 두 접선 미분으로 보완했다. 수정 후 전체 K-HVP와 free block의 old-P3 K가 일치한다.
3. 작은 dt에서 절대 rest 좌표를 반복 차분하는 정밀도 손실은 rest-relative u와 rest tangent 분리로 줄였다.
   Force/변위 tolerance, 재료, penalty와 공력은 실패 결과에 맞춰 완화하지 않았다.
4. Fixed nodal reaction만 저장하면 normal frame의 support couple이 빠진다.
   `g_n0=-(q+alpha R/h_avg)`와 `tau_frame_to_shell=int n0×g_n0 ds0`를 추가했다.
   전체 nodal internal torque와 이 항의 일치를 검산했다. Trace의 support torque는 모델링한.75m² 영역의
   nodal+normal-frame 지지 모멘트다. 고정 외부.25m²의 wind reaction ledger를 포함한 전체 객체 registry는 후속이다.
5. 거친 시간 간격의 wind pilot에서 속도 차이가 약2% 남았다. 60Hz force clock을 유지하고 구조 dt만
   세분화하여 n4/n8의 sub64→128 비교를1% 아래로 줄였다.
6. 큰 굽힘 release의 속도13.3%는 실패로 남긴다. 같은 상태의 구적 차이는.0068% 이하이고
   저장 상태의 Newmark/residual/work 검산을 통과했다. 시간 refinement와 초기 접선 진단으로
   높은 주파수의 위상 오차를 확인했고, sub1024→2048에서.762185%까지 줄였다.
   이 진단은 material strain/공력 감쇠를 바꿔 통과시키는 조치가 아니다.
7. Raw validator는 reset 직전/직후 속도를 구분해 마지막 pre-reset interval의 운동과 일을 검산한다.
   Reset 제거 에너지를 따로 더해 전체 장부를 확인한다. Python 예외에서 마지막 완료 prefix를 보존하며,
   hard kill/OOM에서도 복구되는 checkpoint 시스템을 구현한 것은 아니다.

## 실행과 원본 보존

Workspace root에서 기존 환경을 사용한다. 출력 경로는 항상 새 이름을 사용해야 하며 재실행으로 기존 run을
덮어쓰면 안 된다. 아래는 같은 조건을 다시 만드는 예시다. 큰 메시·작은 dt의 CPU 진단은 오래 걸린다.

```bash
export PYTHONPATH=code
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
.venv/bin/python -m wind3dgs.evaluation.teacher_p3_shell --phase static --output experiments/artifacts/runs/teacher_p3_shell/new_static
.venv/bin/python -m wind3dgs.evaluation.teacher_p3_shell --phase temporal --output experiments/artifacts/runs/teacher_p3_shell/new_temporal
.venv/bin/python -m wind3dgs.evaluation.teacher_p3_shell --phase wind --resolution 8 --substeps 128 --reset-frame 1 --output experiments/artifacts/runs/teacher_p3_shell/new_reset
.venv/bin/python -m wind3dgs.evaluation.teacher_p3_shell --phase wind --resolution 4 --substeps 2048 --initial-curvature 1.2 --output experiments/artifacts/runs/teacher_p3_shell/new_bent
.venv/bin/python -m wind3dgs.evaluation.teacher_p3_shell_validation experiments/artifacts/runs/teacher_p3_shell/new_reset --output experiments/artifacts/runs/teacher_p3_shell/verification/new_reset.json
```

`--compare`는 완료 run 두 개를 검산한 뒤 같은 law/material/policy/reset/초기 형상과 mechanical source인지 확인한다.
CLI/진행 로그만 다른 producer version은 source 차이를 보고하며 실제 wind/clock/shape/force를 재계산한다.
여러 해상도 축이 동시에 바뀌면 isolated convergence로 표시하지 않는다. Snapshot/hash와 dependency version은
Git HEAD와 구분한다. Source14개 hash는 각 config에 있으며 새 dependency 설치나 external checkout 변경은 없다.

Raw 위치는 `experiments/artifacts/runs/teacher_p3_shell/`이다. 이 ignored NPZ는 Git clone만으로 복구되지 않는다.
Compact evidence의 source snapshot/manifest/config/report를 기준으로 로컬 원본을 전달받거나 같은 source/environment에서
새 경로에 재실행한다. 원본 manifest와 다른 출력은 별도 run으로 보존해야 한다.

Compact evidence와 후속 refinement의 최종 결과는 아래에 함께 기록한다.

## 큰 굽힘의 시간 오차와 초기 경계 조건 진단

추가 n4 release 시간 비교에서 sub256→1024의 속도 차이는7.737815%였다.
sub1024→2048에서는 **.7621845%**로1% 아래로 줄었다. 변위 증분 차이는.00455078%다.
동일 material/force clock/solver tolerance를 유지한 결과이며, n4 시간 진단을 통과한 범위다.
Fine의 에너지 적분 잔차 합은7.7829164e-9J, 저장 u/v의 운동방정식과 reset 없는 전체 장부도 통과했다.

원통 release의 n4→8 at sub256은 속도85.250331%, 변위 증분14.352218%의 차이가 남았다.
이 비교에는 아직 충분히 분리하지 않은 시간 오차가 포함되며, converged spatial reference로 사용하지 않는다.
큰 초기 변위를 분모로 사용하면 변위 차이가1.658896%로 작아 보이므로 증분 지표를 함께 유지한다.
이 실패를 삭제하거나 강한 바람의 rest-start 결과로 덮어쓰지 않는다.

원인 진단은 두 가지로 분리했다.

- n4 초기 비선형 접선 H의 generalized eigenbasis에 sub256/1024 속도 차이를 투영했다.
  최대 차이 시각은.049609375s이며 제곱 mass-norm 차이의85.856763%가500–1000Hz,
  3.451033%가1000–5000Hz에 있었다. 초기 H 대칭 오차1.522e-16, 음의 고유값0개다.
  대표876.46Hz 성분의 **고정 선형계라면** Newmark 위상 지연은 sub256에서2.894rad,
  sub1024에서.184rad로 예측된다. 이는 설명용 초기 접선 진단이며 nonlinear 고정 모드 해 또는
  canonical `TeacherSpectrumStatus=converged`를 발행한 결과가 아니다.
- Analytic cylinder는 자유 tip/side의 moment=0 조건과 호환되지 않는다. 곡률1.2m^-1의
  tip/side moment resultant는 각각.1098901N/.0329670N이다(단위 길이당 모멘트).
  이를 지지 하중 없이 놓을 때 초기 가속도 RMS는 n4/8/16에서368.481/1005.274/2793.453m/s²로
  증가했다. 같은 mesh의 rest+0.5m/s wind는1.28553/1.29226/1.29564m/s²였다.
  이 값은 고정 영역을 포함한 전체1m² RMS이며 자유0.75m²만 평균하면 각각1.154700538배다.
  초기 원통의 자유단에서 갑자기 moment를 제거하는 강한 과도응답과, 바람으로 도달한 상태를 구분한다.
  주어진 형상이 에너지 공간에서 의미 없다는 결론이나 P3 구성식의 수렴 완료 주장으로 확대하지 않는다.

사용자가 정한 **rest→wind 변형→v=0→계속 전진**의 순서는 그대로 유지한다.
그 경로에서 유한 변형을 확인하기 위해 별도 `--wind-scale 10` 수식 진단을 추가했다.
이는 [0,5,0]→[2.5,3.5,-2.5]→[0,0,0]m/s의3 frame에서 frame2에 속도를 초기화하는 조건이다.
학습데이터 풍속 범위를5m/s로 동결하거나 원통 release 실패를 대체한 것이 아니다.

n4/sub128의 실제 도달 변위 최대.0727356m, 현재 법선 회전 최대.254037rad,
engineering strain 성분 최대.00622455, 최소 area ratio.995873을 확인했다.
Shape/time 보존·공력 재평가·384step의 Newmark 식·work/energy/reset 원본 검산을 통과했다.
Reset이 제거한 consistent kinetic은.1775534J다. 후속 시간·공간 비교는 아래에 별도로 기록한다.
Frame force hold는 기존 Registry/R1 계약을 유지하며, structural dt refinement를 공력 sample clock의
연속 시간 수렴으로 해석하지 않는다. Trace의 순간 공력 수동성과 frame-held work의 부호도 구분한다.

CPU 비용 점검용으로12step의 inexact-Newton 선형 forcing 진단을 따로 했다.
최종 force/correction tolerance를 유지하면서 보조 GMRES tolerance만 조절했을 때 HVP 수가
rest n8에서96→84, bent n4/sub128에서537→417로 줄었다. 이 보조 실험은 본 producer에 채택하지 않았고,
원래 solver와 모든 실제 수렴 run의 identity를 유지했다. 본 결과의 허용오차를 완화한 조치가 아니다.


더 큰 rest-start/reset의 n4 sub128→256 속도 차이는.1035714%로 시간 진단을 통과했다.
n8 sub128→256도.3046200%로 시간 비교를 통과했다.
반면 n4→8 at sub128은 속도7.3120094%, 변위2.4415643%였고,
n8→16은 속도1.8495292%, 변위.2744271%여서 n32 공간 refinement로 이어갔다.
n16의 sub128→256 속도 차이는.2367784%, n16/sub128의 대각선 방향 차이는.1601556%로 통과했다.
후속 GPU의 n16→32 비교는 수치 보간 전체 시간을 포함한 속도 차이 상한.3917943%,
n32의 sub128→256 시간 차이 상한.2437471%로 통과했다.
CPU 원식의 전체 상태 검산과 GPU/CPU 궤적 일치는 [GPU 보고서](../p3_shell_gpu/README.md)에 연결한다.
동일 물성·5m/s peak·60Hz force sampling·frame2 reset을 유지한다.

추가한 회전 반영 preconditioner의12step 보조 진단에서는 원래 최종 잔차 기준을 유지하면서
n4 원통의 HVP537→268, n8 wind-reached 상태의337→220으로 감소했다. 최종 상태와 원래 방법의
최대 속도 차이는1.18e-12m/s 미만이었다. 이 프로토타입도 본 producer에 아직 채택하지 않았다.
현재 수렴 실험의 source identity와 정확한 Newton/HVP 방식은 유지한다.

## 요소 내부·시간 간격 사이의 기하와 strain 검산

구적점의 `J>0` 검사만으로 요소 내부의 fold를 배제할 수 없으므로,
`p3_shell_bounds.py`에서 **P3 공간 × quadratic Newmark 수치 보간**의 Bernstein 상한을 계산한다.
각 구간의 시간 control은 `u0`, `u0 + dt*v0/2`, `u1`이다. Newmark의 평균 가속도를 따르는
수치 보간이며 정확한 연속 ODE 궤적이나 실제 연속 풍장의 오차 상한은 아니다.

- 공간2차/시간2차인 displacement gradient의 Bernstein 계수에서 reference 평면 투영의
  Frobenius norm 상한 `r`를 계산한다. Convex 사각형과 영 변위 고정 영역의 연속 연장에 대해
  `r<1`이면 projected map이 전역 injective이고 `J >= (1-r)^2 > 0`이다.
  이 충분조건이 실패했다고 곧 self-intersection이라고 판정하지 않는다.
- 양의 Bernstein product로 Green strain의 공간4차/시간4차 계수를 구해 성분별 상한을 계산한다.
  Rest 곡률0 조건에서 Hessian의 vector norm으로 engineering curvature 성분의 상한을 얻고,
  `mid-surface strain bound + (h/2)*curvature bound`로 선형 두께 보간의 표면 strain을 한정한다.
  두께 방향 고차항·3D hyperelastic 재료의 검증과 구분한다.
- Float64 누적 여유를 따로 보고한다. 엄밀한 interval arithmetic 인증이라고 주장하지 않는다.
  허용 strain 범위를 실험값에 맞춰 새로 정한 것은 아니다.

5m/s reset의 n16/sub128에서 `r<=.034625438`, `J>=.931948045`,
mid-surface engineering strain 성분 상한 .001136284,
곡률 성분 상한3.201317m^-1, 선형 표면 strain 성분 상한 .017044350이었다.
모든 요소와384구간의 수치 보간에서 injectivity 충분조건을 만족했다.
약한 바람 n32/sub128은 `r<=1.030722e-5`, `J>=.999979385`,
mid-surface strain 상한7.049721e-7, 선형 표면 strain 상한 .000215506이었다.

최종 신규 테스트23개는13.329s에 통과했다. 선행36개 검사에 포함된 기존P3 21개까지
중복 없이 합하면44개이며 repository 전체 suite를 실행했다는 뜻은 아니다.
Rigid rotation의 영 strain, 끝점만 보면 놓치는 quadratic 시간 중간의 fold 위험,
해석적3차 field의 조밀한 공간/시간 표본과 strain/곡률 상한을 검사했다.
최초 rigid test는 명시한 roundoff 여유까지 영으로 가정해 실패했으므로 여유를 분리해 실제 strain 잔차를 검사하도록
수정했다. 상한의 여유나 물리 통과 기준을 낮추지 않았다.

```bash
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s code/tests -p 'test_teacher_p3_shell*.py' -v
```

최종 validator는 저장 지지 모멘트도 `Ma-f_int-f_hold`의 fixed reaction과 normal-frame couple에서
재계산한다. Hash를 다시 봉인한 잘못된 support torque가 거부되는 검사를 포함한다.
V1 원본에는 support torque가 없으므로 `support_torque_saved=false`로 명시한다.
각 검산은 실제 사용한16개 source의 SHA-256과 producer와의 차이를 별도로 기록한다.
Producer v1/v2/v3/v4 및 최신 검산 v5는 서로 덮어쓰지 않고 보존한다.

## 평면 내 변위가 필요한 이유의 실제 상태 대조

N16/sub128의 reset 도달 상태에서 평면 내 변위 최대값은7.23639mm였다.
이 상태의 평면 내 성분만0으로 만들고 같은 finite-rotation 에너지를 다시 평가하면 다음과 같다.

| 상태 | 막 에너지 (J) | 전체 탄성 에너지 (J) | 구적점 engineering strain 성분 최대 |
|---|---:|---:|---:|
| 실제 바람 도달 형상 | .0000706081 | .0359804 | .00105913 |
| 평면 내 변위만 제거한 설명용 형상 | .902094 | .936965 | .0337355 |

휘는 동안 평면 내 좌표가 함께 움직여 불필요한 신장을 줄이는 것을 확인했다.
이는 같은 유한 회전 law에 두 좌표장을 대입한 설명용 대조이며 선형 P3의 재시뮬레이션,
별도 대안 모델의 실패 판정 또는 수렴 기준으로 사용하지 않는다.
원본 시각·manifest/source 해시는 `verification/inplane_compensation_m16.json`에 있다.

## 수치 보간의 전체 시간 응답 차이

`evaluation/teacher_p3_shell_comparison.py`는 coarse 저장 시각에 더해 fine 시각과 reset 직전의
속도를 포함한다. 두 run의 quadratic Newmark 변위와 linear 속도를 공통 fine clock에서 비교한다.
속도 차이 norm의 구간 최대는 끝점에 있으며, 변위에는
`dt_fine/2 * (max_velocity_error + kinematic_defect_A + kinematic_defect_B)`를 더한다.
Defect는 저장 u/v의 `2*(u1-u0)/dt-v0-v1`에 대한 consistent-mass 면적 norm이다.
기준 응답의 끝점 최대를 분모 하한으로 쓰며, 변위 증분도 같은 방식으로 평가한다.
Reset 우극한은 두 run 모두0이고 좌극한은 별도 event의 pre-reset 속도다.
정확한 연속 ODE 해나 interval arithmetic 인증이 아닌 **수치 보간 응답 차이 상한**이다.

| 약한 바람의 비교 | 속도 상한 (%) | 변위/증분 상한 (%) |
|---|---:|---:|
| n32, sub128→256 | .2312997 | .00223245 |
| n16→32, sub256 | .3811609 | .0117041 |

기존 sampled 결과를 삭제하지 않고 두 지표를 함께 보존한다. 같은 원본의 별도 raw validator에서
운동방정식·공력·일·reset·Bernstein bounds를 확인하고 manifest hash로 연결했다.
추가 interpolation 테스트3개는.051s에 통과했다. 첫 테스트의 기대 배열 shape를 명시했고,
시간 차분 roundoff1.33e-16에 대해8 machine-epsilon 여유를 사용하도록 테스트를 보완했다.
물리1% 조건이나 보고서의 오차 값을 줄인 조치가 아니다.

## 마지막 CPU 검산의 완료

`20260909_strong_reset_m32_s128_v4`도7255.413s에 완료했다. 원래16개 source를 유지한
`verification_final_v5`는 wind24개를 모두 검산하고20개 시간·공간·방향 비교를 마쳤다.
Static/temporal을 더한 전체26개 완료 원본의 config/report/manifest를 compact evidence에 보존했다.
Strong n16→32/sub128의 공통 저장 시각 속도 차이는.3917943%로1%를 통과했다.
Finest GPU 공간/시간/방향 수치 보간 상한과 동일 grid의 CPU/GPU 사후 대조는
[GPU 보고서](../p3_shell_gpu/README.md)에 연결한다. 실패한 coarse·원통 release 결과도 그대로 남는다.

## RMS 정규화 영역의 명시

선행 보고서는 위에서 정의한 전체1m² RMS를 사용했다. 고정된0.25m²의 응답을0으로 연장하므로
`sqrt(integral_free |field|² dA0 / 1m²)`가 그 RMS다. 초기 단위 오류 해석은 이 정의를 확인한 뒤 철회했다.
새 장시간 비교 law v2는 `sqrt(integral_free |field|² dA0 / 0.75m²)`인 자유 영역 RMS를 명시한다.
둘 모두 SI RMS이며 자유 영역 값은 전체 영역 값의 `1/sqrt(.75)=1.154700538`배다.
초기 가속도의 본문은 전체 영역 기준을 유지하며 두 기준의6개 값과 해석 정정 근거는
[metric_units_v6.json](evidence/metric_units_v6.json)에 보존했다.
상대 오차·kinematic padding의 상대 상한에는 같은 인자가 소거되므로 위1% 판정은 유지된다.
원본 u/v·힘·에너지, 기하 상한, 실제 solver 잔차와 허용오차에는 변경이 없다.
Raw/source snapshot을 소급 수정하지 않으며 RMS 이름과 함께 정규화 면적도 인용한다.
