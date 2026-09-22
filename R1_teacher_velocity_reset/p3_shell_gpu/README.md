# P3 유한 회전 shell의 GPU 연산자 이식

사용자는 CPU 최적화/현행 CPU 유지/GPU 이식의 장단점을 검토하고 **GPU 이식부터 진행**을 선택했다.
[선행 CPU 수식과 진단](../p3_shell/README.md)의 Koiter/StVK 에너지·경계·질량·상대풍,
Newton/Newmark 허용오차를 유지한다. 추가 학습데이터는0개이며 R1 채택은 아직 미완료다.

## 실제 이식 범위

Warp1.17.0의 float64로 요소 및 edge의 현재 기하, 막·굽힘 에너지, 해석적 gradient의 정확한
방향 HVP, 요소 적분, 고정 순서 nodal gather와 current-area 공력을 구현했다.
Element/quadrature의 합산 순서를 고정하고 force atomic 합산을 사용하지 않는다.
Fast math와 FMA fusion을 끄며 생산 HVP를 유한 차분으로 바꾸지 않았다.

Newton 제어, consistent-mass 희소 풀이·rest-K preconditioner, GMRES와 마지막 총에너지 합산은
CPU에 남는다. CPU↔GPU 입력/출력 복사를 포함한 첫 연산자 이식이며, 전체 solver가 GPU에
상주하거나 모든 반복 계산을 CUDA로 옮긴 것으로 소개하지 않는다.
원래 CPU source16개를 수정하지 않아 진행 중인 CPU run과 검산 v5의 identity를 보존했다.

새 파일은 `teacher/p3_shell_warp_kernels.py`, `p3_shell_warp.py`,
`evaluation/teacher_p3_shell_gpu.py`와 사용자 실행 script다.
`pyproject.toml`에 `teacher-gpu` optional dependency를 명시했으며 이미 설치된 Warp를 재사용했다.
새 dependency 설치, external checkout 변경 또는 물리 계수 조정은 없다.

Kernel/API 대조는 설치된 Warp1.17.0의 source/tests와
[공식 Warp 코드 생성 문서](https://nvidia.github.io/warp/latest/user_guide/programming_model/code_generation.html)를
참고했다. 실제 버전과 source SHA는 각 run에서 동결하며 최신 문서의 기능을 자동 승계하지 않는다.

## 검사와 실제 하드웨어

- GTX1080Ti,11GiB,sm61; Warp1.17.0/CUDA Toolkit12.9/Driver13.0.
  NVML의 드라이버 표기는582.28이었다.
- 기본 실행 환경은 GPU 접근을 차단했다. 권한 있는 읽기 전용 조회와 이후 실제 CUDA 실행은 성공했다.
  GPU가 없는 경우 CPU로 몰래 대체하지 않고 실패로 기록한다.
- 신규 테스트5개는 Warp CPU에서2.427s, 실제 CUDA에서8.021s에 통과했다.
  CUDA 첫 검사 시간에는 커널 컴파일4.406s가 포함된다.
- 정식 연산자 대조는 n4/8/16/32 각각 rest/원통/부드러운 전역 변형의12개 상태다.
  NumPy의 energy/force/HVP/normal/strain/지지 couple와 current-area 공력을 대조했고,
  같은 GPU 호출의 반환값 반복은 정확히 일치했다.
- Warm 이후 energy/force/HVP/조립/host 복사를 포함해5회씩 측정한 비율은
  n4 3.27배, n8 17.38배, n16 27.59배, n32 58.78배였다.
  이는 이 환경·이 입력의 연산자 측정이며 전체 rollout의 가속 비율과 구분한다.

N16/sub128의5m/s peak·frame2-reset을 실제3 frame 전진했다.
CPU와 GPU의 면적 norm 속도 상대 차이는7.17524e-13, 변위 차이는7.33627e-16이었다.
HVP 호출9501회는 같았고 reset 제거 kinetic .179405468665J도 같았다.
CUDA 연결의 전진·trace 저장은77.648s였고, 선행 CPU report의 전체 시간은1348.494s였다.
후자는 source/초기 조립 등 실행 범위와 동시 CPU 작업 부하가 달라 통제된 전체 solver benchmark로
해석하지 않는다. 원본 Newmark/힘/일/reset/Bernstein 검산은 별도로 수행한다.

## 실행과 로그

Workspace root에서 아래 script를 실행한다. 기본 출력은 날짜·microsecond별 새 run이며,
`--output`을 지정해도 기존 경로는 거부한다. Supervisor는 optional import/CUDA 초기화의 실패와
native process 종료를 로그에 남기고 개인 경로를 치환한다.
`console.log`, config/report, 정확한 source snapshot과 manifest가 같은 폴더에 생긴다.

```bash
bash code/scripts/check_teacher_p3_shell_gpu.sh --phase operators
bash code/scripts/check_teacher_p3_shell_gpu.sh --phase rollout --reference experiments/artifacts/runs/teacher_p3_shell/20260909_strong_reset_m16_s128_v4
```

두 번째 명령은 CPU 원본의 초기 조건·실제 wind·고정 조건·시간 간격을 읽지만 이후 CPU 궤적이나
힘을 GPU 전진에 주입하지 않는다. GPU가 현재 상태에서 공력을 다시 평가하고 같은 Newmark 식을 푼다.
CPU/GPU 동일 구현 대조의 tolerance는 상대1e-6에 변위 절대1e-9m/속도 절대1e-7m/s를 더한 값이며,
물리적인 mesh/time 수렴의1% 기준과 구분한다. GPU run의 `status=completed`와 각 검증의 `passed`는 다르다.

정식 raw는 `experiments/artifacts/runs/teacher_p3_shell_gpu/`에 있으며 NPZ는 Git clone에 포함되지 않는다.
최종 compact evidence/source snapshot/재실행 경로와 이후 대조는 아래에 누적한다.

## 전체 궤적 대조·재실행과 세분 비교

- N32/sub128의 약한 바람도 CPU/GPU 속도 상대 차이6.62087e-12, 변위3.54437e-15로 일치했다.
  HVP4898회는 같았다. GPU 전진·trace 저장126.409s, 전체 report150.288s였고,
  선행 CPU report3382.799s와는 초기 조립·동시 작업 부하가 다른 관측값이다.
- Source v3의 n16/sub128 강한 바람 재실행은17개 배열/4,228,422 scalar와 step diagnostics가
  정확히 일치했다. 독립 새 process에서 초기화부터 다시 전진했으며 NPZ archive byte의
  일치와 배열 값의 일치를 구분한다.
- GPU의 n32/sub256 strong-reset은768 interval을 완료했다. CPU 원식으로 모든 상태의
  Newmark·공력·일·reset·지지 모멘트를 다시 검산했다. Reset 제거 kinetic.179406992697J,
  누적 에너지 적분 잔차−2.5314274e-8J, support torque 재계산 차이 최대2.929e-15N·m였다.
- 같은 n32의 전체 P3/Newmark 수치 보간에서 projected gradient 상한.034156968,
  area ratio 하한.932852763, mid-surface strain 상한.001006379,
  선형 두께 보간의 표면 strain 상한.017308061이었다. 전역 단사성 충분조건을 만족했다.
  새 material 허용 strain 기준을 관측값에 맞춰 정하지 않았다.
- 이 finest 원본의4개 실제 상태에서 volume/edge6/4 대10/8의 CPU 구적 대조도 통과했다.
  최대 force mass-dual 상대 차이는.000959886%다. 독립 공간 discretization의 기준값은 아니다.

수렴은 같은 v3 producer끼리 비교한다. 변위 quadratic/속도 linear 수치 보간의 fine 시각,
reset 좌극한과 구간 사이의 변위 상한을 포함한다. 별도 CPU raw 검산·manifest와 연결한다.

| 5m/s peak·rest/frame2-reset 비교 | 속도 상한 (%) | 변위/증분 상한 (%) |
|---|---:|---:|
| n16→32, sub128 | .3917943 | .0182097 |
| n32, sub128→256 | .2437471 | .00335713 |
| n16→32, sub256 | .4000651 | .0176079 |
| n32, sub256, forward→backward | .0406189 | .00361927 |

약한0.5m/s 진단의 n32/sub256 방향 비교도 속도 상한.0397466%, 변위 상한.00376005%로 통과했다.
따라서 이 짧은 wind-reached/reset 조건에서는 시간·공간·방향을 분리한1% 검사를 통과했다.

이는.05s의 진단이며 장시간 랜덤 바람·독립 공간 기준·canonical probe/oracle/GS 검증을 완료한 것은 아니다.
처음 n4→8/n8→16의 실패와 analytic cylinder release의 실패도 선행 CPU 보고서에 남긴다.

V3의 `--resolution`, `--substeps`, `--diagonal`은 CPU 원본의 입력 조건을 보존하며 grid만 바꾼다.
변경 grid의 실행은 `reference_cpu_role=condition_template`, `cpu_gpu_parity_assessed=false`,
`passed=null`로 기록한다. `completed`만으로 같은 grid의 CPU 대조나 물리 수렴을 통과시켜서는 안 된다.
새 grid의 CPU 원본이 완료되면 `compare_cpu_gpu.py`로 별도 사후 대조할 수 있다.

```bash
bash code/scripts/check_teacher_p3_shell_gpu.sh --phase rollout --reference experiments/artifacts/runs/teacher_p3_shell/20260909_strong_reset_m16_s128_v4 --resolution 32 --substeps 256
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/p3_shell_gpu/verify_development_evidence.py --output experiments/artifacts/runs/teacher_p3_shell_gpu/new_verification
```

`verify_development_evidence.py`와 `verify_finest_evidence.py`는 해당 고정 진단 묶음의 완료를 기다려
순서대로 검산하는 실험 wrapper다. 같은 source/조건을 다른 이름에 재실행했다면 재사용 가능한
`teacher_p3_shell_validation`/`teacher_p3_shell_comparison` CLI에 새 run 경로를 명시한다.
원본 source16개와 GPU producer22개, 별도 검산 source21개의 역할을 구분한다.

CPU device를 실제 GPU 검사에 지정한 의도적 거부 실행도 남겼다.
`20260909_reject_cpu_v3`은 exit1, `status=failed`와 한국어 사유·console/manifest를 저장했다.
이 초기 device 거부는 수치 producer 시작 전이므로 config/source snapshot은 생성되지 않는다.
신규 테스트5개와 보간3개를 선행44개에 더한 고유 검사 범위는52개다. Repository 전체 suite는 아니다.

## 격리 재실행과 다음 긴 구간

처음 보존한 수식/검산 ZIP만으로는 package initializer가 불러오는 주변 project 파일이 부족했다.
실제 import37개와 producer22개의 합집합40개를 `p3_shell_runtime_bootstrap_v1.zip`으로 추가 보존했다.
별도 임시 경로에서37개 project import가 모두 격리본을 사용하고 producer22개 hash가 같음을 확인했다.
그 복사본으로 n16/sub128 strong-reset을 전진하고 CPU 원식으로 다시 검산했다.
원래 v3와17개 배열/4,228,422 scalar·step diagnostics가 정확히 일치했다.
이는 제3자 dependency를 포함한 환경 이미지가 아니며 run의 NumPy/SciPy/Warp 버전도 함께 필요하다.

GPU raw 묶음은 연산자1개, 의도적 CPU-device 거부1개, 실제 wind11개다.
Wind11개는 모두 저장 상태의 Newmark/공력/work/reset/지지 모멘트와 Bernstein 기하를 CPU로 검산했다.
별도 CPU n32 strong run도7255.413s에 완료했다. Reset 좌극한을 포함한 사후 CPU/GPU 대조는
속도 상대2.89993e-12, 변위9.52711e-16로 통과했다. HVP 호출은 CPU14329/GPU14330회로
한 번 달랐으며, 각 원본의 실제 solver 잔차를 통과한 뒤 위 궤적 차이를 확인했다.
동일한 정수 반복 횟수를 GPU 채택 조건으로 삼거나 모든 실행이 bitwise 같다고 주장하지 않는다.
대응 GPU의 전진289.237s/전체305.241s는 실행 범위·동시 부하를 명시한 관측값이다.

사용자는 다음1.5초 wind 범위로 **기존0.25–0.5m/s를 먼저 확인하고 결과에 따라 확대**를 선택했다.
90 frame natural 및18·42·66 frame의 독립 velocity-reset 분기 실행과 검산은
[긴 랜덤 바람 보고서](../p3_shell_random/README.md)로 연결한다. 이 단기 보고서의5m/s는 진단 조건으로 보존한다.

선행 absolute RMS는 [CPU 보고서의 전체1m² 기준](../p3_shell/README.md#rms-정규화-영역의-명시)을 따른다.
위 표의 상대 오차는 동일 면적 인자가 소거되어 유지된다. 원본·snapshot과 지지/에너지/solver 식은 변경하지 않는다.
