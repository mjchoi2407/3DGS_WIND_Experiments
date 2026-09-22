# 마지막 reset의 공간 속도 차이 진단

## 현재 상태

2026-09-11. 필수 비교 19/20 통과 판정을 유지한다. `reset66` n16→32의 속도
1.855258% 미달은 저장 원본에서 재현되며 비교기의 보수적 padding 때문이 아니다.
변위 0.022088%, reset 후 변위 변화 0.023411%는 기존 기준을 통과한다.

## 확인 결과

- 동결 runtime 188항목의 size/hash와 비교 결과가 참조하는 두 view index hash를 확인했다.
  Frame 66/71/89의 NPZ/metadata hash를 확인하고 속도 RMS 비교를 다시 계산해 저장값과 정확히 일치했다.
  Frame 66 시작의 두 속도 배열은 모두 정확히 0이다.
- 속도 차이의 peak는 frame 89(1.48333–1.5초)에서 0.000993330 m/s다.
  기준 peak 0.053541309 m/s는 frame 71에서 나온다. 매 순간 0에 가까운 속도로 나눈 결과가 아니다.
- 같은 공간 비교의 natural/reset18/reset42 상대 속도 차이는 각각 0.4441/0.4679/0.5199%다.
  Reset66은 절대 오차가 더 작지만 기준 움직임도 작아 상대 기준을 넘는다.
- Reset66의 시간 세분 비교는 n16 0.7318%, n32 0.6787%, 대각선 방향 비교는
  각각 0.2745%, 0.1061%다. 시간 오차가 0이라는 뜻은 아니지만 공간 비교에서만 필수 기준을 넘었다.

추가로 frame 66/89의 전체 257개 저장 시점에서 두 P3 속도장 차이를 공간 적분했다.
Frame 89의 성분별 시간 RMS는 x/y/z 각각 5.122e-5/7.195e-4/1.193e-5 m/s다.
Rest 표면은 x-z 평면이므로 y가 초기 표면의 수직 방향이다.
시간 평균 차이장의 제곱 norm은 전체 시간 평균 제곱 norm의 0.449%에 불과하다.
속도 차이는 주로 평균 이동의 편차보다 수직 방향 진동 차이에 있다.

256개 시점(마지막 경계 제외)의 FFT에서 frame 89의 120 Hz bin이 차이 신호 제곱 norm의
69.37%를 차지한다. Frame 66의 최대 bin은 360 Hz(37.07%)다.
**한 frame FFT의 주파수 간격은 60 Hz이며 창 경계 누설이 있다.** 이 값은 진단용이고
고유 진동수, 정확한 모드, 위상 오차 또는 reset이 원인임을 확정하는 근거가 아니다.
600 Hz 이상 성분은 각각 frame 66 1.804%, frame 89 0.736%로,
substep마다 번갈아 부호가 바뀌는 최고 주파수 진동이 지배하는 양상은 아니다.

## 재현과 한계

후속으로 주변 풍속이 0인 frame72–89(0.3초)의 고정 물리 위치 9개에서 수직 속도를 분석했다.
원본 frame36개(n16/n32 각18개)의 hash를 로더로 확인했다. 3차 추세 제거와 Hann 창을 사용한
FFT 간격은 3.3333 Hz다. 두 격자 모두 60 Hz 이상 대역에서 113.3333 Hz bin이 가장 컸고,
차이 신호도 같은 bin에서 최대였다. 그 bin의 n16/n32 진폭 norm 비는 0.89293,
복소 공간 상관은 0.999635, 위상 차이는 39.5809도였다.
이는 선택 위치에서 유사한 진동 패턴의 진폭·위상 차이를 시사한다. 공간 전체의 1% 판정을
대체하거나 정확한 고유 진동수·분산 원인을 확정하지 않는다. 위상을 맞춰 기존 오차를 낮추지도 않는다.
[후속 수치](phase_result.json), [재현 스크립트](analyze_phase.py)는 아래와 같은 동결 `PYTHONPATH`로 실행한다.

동결 CPU 비교 경로로 원본을 읽었으며 새 궤적은 계산하지 않았다.
전체 source chain/물리 재검산, 더 높은 공간 해상도, 전체 시간 구간의 모드 분석은 미실행이다.
기존 1% 기준과 원본 결과를 유지한다.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=experiments/artifacts/runs/teacher_p3_shell_random/scale4_fast_continuation_v2/runtime/code \
.venv/bin/python experiments/R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/evidence/diagnosis_20260911/analyze_velocity.py
```

[수치 결과](velocity_results.json), [source/view identity](source_identity.json).
스크립트는 동결 구현을 사용하며 raw frame 로더에서 NPZ/metadata hash를 확인한다.
실제 계산 경로의 source는 위 manifest hash로 식별한다.

다음은 저장된 더 긴 구간에서 격자별 진동의 진폭·위상 차이를 분해하는 것이다.
새 해상도 실행이나 감쇠 추가를 자동 채택하지 않는다. R1 전체 채택·학습 발행은 보류다.
