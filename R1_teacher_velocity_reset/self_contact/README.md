# P3 셀프 컬리전 기준 비교

## 현재 상태

후속 [정밀 GPU 기하 인증](refined_geometry.md)으로 기존 scalar 검사가 거절한12구간을
재인증했고6개 GPU 접촉 사례가 전체 검산을 통과했다. 아래 CPU 초기 결과와 구분한다.
사용자 요청으로 본 GPU 계산을 종료하고 직접 실행할 세 스크립트를 별도 출력에 준비했다.
[v2 비용 정리](cost.md)는 기존 저장 결과 비교다. 후속 [v3 성능 점검](performance.md)에서는
중복 계산을 줄이고 스크립트를 갱신했으며, 공유 GPU 부하가 확인되어 최종 가속 배수는 보류했다.
이전 실행기 [병렬 개선 v4](parallel_v4.md)는 후보 공통 항·GPU 작업 큐·실행 폭 개선 후
회귀와 제한 GPU 검증을 완료했으며 v3 근거와 구분한다.
이후 [유휴 조건 속도 재측정](idle_performance.md)으로 초기v1 대비 개선과 통제된 접촉 추가 비용을
확인했다. 마지막v4 병렬화만의 일관된 추가 가속은 미확인이다.
현재는 [BVH 개선 v5](broadphase_v5.md)다. 탐색과 후보별 거리 계산을 분리해 제한 프레임의
추가 단축을 확인했고139개 회귀·국소/세 씬 GPU 검증을 통과했다. 본 시뮬레이션은 미실행이다.
사용자 결정으로 v5를 세 씬 실행 기준으로 고정했다. 소폭 개선을 위한 추가 최적화는 중단하며,
실제 장기 실행에서 중요한 병목·정확성 문제가 확인될 때 재검토한다.
후속 [v10 실행 묶음](frame112_recovery.md)은 시간 보정·원래 오류 보존과 GPU dt/2 제한 복구를
사용한다. 직사각형112번째 실패 프레임의 재현과 실제 자동 복구를 확인했으며 장기 완주는 별도다.

CPU FP64 기준 비교 기록이다. 후속 [GPU 전 단계 구현·세 씬 스크립트와 실제 실행](gpu.md)이 완료됐다.
기본 contact-OFF GPU/Gauss 실행이나 연구 Gate·학습 적격성을 변경하지 않는다.
접촉 OFF / LBVH ON / 전수 AABB 탐색 ON을 같은 시작 상태·재료·시간 간격에서 비교한다.
**계수1,000·10,000은 당시 힘·시간 CCD의 제한 검증을 통과했다.** `local_metric` 기하 승인까지
포함한 결과는 아니며, 후속 GPU/CPU 기하 대조의 거절 사례는 위 GPU 보고서에 보존한다. 약한 계수100의 고속 실패도 보존한다.
시험한 세 값 중 모든 샘플을 통과한 가장 작은 값은1,000이다. 실제 장면의 최종 기본값은 아니다.
원래 곡면의 전역 비접촉 인증과 접촉 응답의 공간 수렴은 미완료다.

구현·API와 보장 범위는 [code 문서](../../../code/docs/p3_self_contact.md)를 따른다.
상세 수치·source hash는 아래 결과 JSON이 소유한다.

기존 직사각형·손수건·삼각 깃발의 굽힘1/500 입력에 추가하는 스크립트는
[CPU 세 씬 실행 준비](three_scenes.md)와 [GPU 실행](gpu.md)을 따른다. 장기 본 실행은 미완료다.

## 목표와 반증 조건

- 공간 가속이 충돌 후보를 누락하거나 전수 탐색과 다른 접촉 응답을 만드는가?
- 접촉이 없으면 기존 shell 결과가 보존되는가? 접촉력이 수치 미분·총힘·총토크 검사를 통과하는가?
- 빠른 접근과 시간 중간의 충돌을 거절하는가? 실패한 step의 입력 상태가 보존되는가?
- P3 곡면을 선형 삼각형으로 세분할 때 공간 오차와 접촉 에너지가 수렴하는가?
- FP32 좌표 저장이 작은 간격과 접촉력에 어떤 영향을 주는가?

입력은 합성 P3 shell의 mesh/material/position/velocity다. Training-only privileged fixture이며
실제 GS dataset/object package/model은 사용하지 않아 해당 version은 `not_applicable`다.
Teacher 및 target runtime의 최종 채택 근거로 자동 승계하지 않는다.

## 시험 설정과 재현

국소 fixture는 두 0.2m 삼각형이다. 동일 P3 시스템에 있지만 분리된 두 component이므로
연결된 천의 큰 접힘을 모두 대표하지 않는다. 별도로 연결된 원통형 말림의 geometry/refinement와
한 접촉 step을 검사한다. 재료 E=100Pa, ν=0.3, h=1mm, 면밀도 0.1kg/m², 고정점 없음,
외력·마찰·추가 감쇠 없음. 접촉 최소 간격은 **시험값 1mm**이며 재료 h와 자동 연결하지 않는다.
활성 범위 10mm, barrier 계수100/1,000/10,000, proxy subdivision3, 원래 FP64 solver 허용오차를 유지한다.
초기 간격8mm부터 barrier가 활성화되어 있으므로 계수를 키우면 초기 접촉 에너지도 커진다.
더 큰 반발이 자동으로 더 정확한 재료 모델을 뜻하지 않는다.

| 사례 | 접근 속도 | 시간 간격 | 전체 시간 | 비교 |
| --- | ---: | ---: | ---: | --- |
| 면 접근 | 0.2m/s | 1ms | 60ms | OFF / LBVH / BruteForce |
| 엣지 교차 접근 | 0.2m/s | 1ms | 60ms | OFF / LBVH / BruteForce |
| 빠른 면 접근 | 1m/s | 1ms | 12ms | OFF / LBVH / BruteForce |

실패 시 최대 6단계 dt 이분을 시도한다. 실패한 재귀 분기의 중간 prefix는 최종 채택하지 않으며,
JSON의 재시도 수는 완전히 완료된 상위 step만 센다. 실패 자체·한도·마지막 완료 시각은 별도 기록한다.

`code/`에서 실행한다. 출력 경로는 새 이름이어야 하며 기존 artifact를 덮어쓰지 않는다.

```bash
../.venv/bin/python -m pip install -e '.[teacher-contact-samples,dev]'
ulimit -v 2097152
TBB_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/wind3dgs-contact-mpl \
  timeout 180 ../.venv/bin/python -u -m wind3dgs.evaluation.p3_contact_samples \
  --barrier-stiffness 100 \
  --output ../experiments/artifacts/runs/p3_self_contact/20260922_weak_barrier_isolated
```

CPU 단일 TBB/OpenBLAS thread, 2GiB address-space 상한·180초 상한으로 실행한다. 이 명령의
`passed=false`/종료 코드1은 고속 시험 실패를 의미하며 실패를 숨기는 성공 marker를 발행하지 않는다.
GPU를 사용하지 않는다. 연산 시간과 별도 저장 상태 검산 시간을 분리하고, 속도 측정 중 다른
시험은 동시 실행하지 않는다. 세분화 곡면 측정은 곡면 생성·proxy 초기화 비용을 제외한다.

사용자 승인 후 같은 명령에서 `--barrier-stiffness 1000` / `10000`, 출력 suffix
`20260922_barrier_1000` / `20260922_barrier_10000`으로 순차 실행했다. 두 실행은 종료 코드0이다.
강도 비교와 계수1,000의 추가 시간 세분화는 다음 명령으로 수행했다.

```bash
ulimit -v 2097152
TBB_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/wind3dgs-contact-mpl \
  timeout 120 ../.venv/bin/python -u -m wind3dgs.evaluation.p3_contact_strength \
  --runs ../experiments/artifacts/runs/p3_self_contact/20260922_weak_barrier_isolated \
         ../experiments/artifacts/runs/p3_self_contact/20260922_barrier_1000 \
         ../experiments/artifacts/runs/p3_self_contact/20260922_barrier_10000 \
  --output ../experiments/artifacts/runs/p3_self_contact/20260922_strength_comparison_final
```

## 검사 기준

- LBVH와 BruteForce 후보 집합 일치. 작은 fixture는 AABB를 쓰지 않는 모든 비incident VF/EE
  실제 거리 oracle의 가까운 쌍을 LBVH가 포함해야 한다. 거리 함수 자체는 같은 toolkit이므로
  toolkit narrow-phase의 독립 구현 대조라고 주장하지 않는다.
- 접촉 ON은 완료된 모든 substep의 힘 잔차·시간 보간 경로를 독립 재계산한다.
  재구성 가속도의 반올림 차이를 허용하는 잔차 비율 한도는 1.05이며 solver 자체의 한도는 1이다.
- LBVH/BruteForce 최종 위치 차이 <1e-10m, 속도 차이 <1e-8m/s. 미완료 prefix 일치는 완주를 뜻하지 않는다.
- OFF는 최소 간격 침범 또는 시간 경로 미인증이 관측되어야 비교 대조군이 성립한다.
- 뉴턴/시간 경로·예산 검사 실패는 안전한 거절이지 해당 동역학 사례의 통과가 아니다.
- Bernstein 곡면 오차는 세분화에 따라 감소해야 한다. 정확한 곡면 자기 접촉 및 접촉 응답의
  공간 수렴은 별도 판정이며, 이번 unweighted IPC 에너지는 세분화에 불변하지 않는다.

## 확정된 제한 결과

| Barrier 계수 | 면 접근 | 엣지 교차 | 고속 접근 | 고속 저장 시점 최소 간격 | 고속 LBVH 풀이 시간 |
| ---: | --- | --- | --- | ---: | ---: |
| 100 | 통과 | 통과 | 미완료·안전 거절 | 완료 prefix 1.171mm | 실패 비용 포함1.75s |
| 1,000 | 통과 | 통과 | 통과 | 2.421mm | 0.406s |
| 10,000 | 통과 | 통과 | 통과 | 6.629mm | 0.428s |

실패 행과 성공 행은 완료 시간 분모가 다르므로 위 시간으로 단순 가속 배수를 계산하지 않는다.
계수1,000과10,000은 각각 LBVH/BruteForce 합계264개 접촉 substep 모두 독립 검산을 통과했고,
재시도0이다. 끝점만이 아니라 모든 채택 quadratic 시간 경로가 최소 간격1mm 기준으로 검사됐다.
탐색 방식별 최대 위치 차이는1.12e-16m 미만이다.

계수1,000 고속 사례의1/0.5/0.25/0.125ms 시간 세분화에서 마지막 두 끝점의 상대 차이는
위치0.0163%, 속도0.0303%다. 노드 Euclidean norm으로, 위치 분모는 초기 대비 변위,
속도 분모는 finer endpoint 속도다. 사전1% 진단 한도와 fine 경로 검산을 통과했지만
전체 궤적/독립 기준에 대한 canonical 시간 수렴은 아니다. 고속 최대 step 에너지 잔차는
계수1,000의1ms에서1.19e-6J,0.125ms에서2.56e-9J로 감소했다.
계수10,000의1ms 값은6.42e-5J로 더 커서 강도 증가를 무조건적인 정확도 향상으로 해석하지 않는다.

- 면 접근·엣지 교차는 ON 두 탐색 경로 모두60/60단계의 독립 잔차·시간 경로 검산을 통과했다.
  OFF는 각각11/60구간에서 접촉 기준을 위반해 대조군이 성립했다. 위치 차이는 최대7e-18m 수준이다.
- 계수100의 고속 ON 두 경로는7ms까지 완료 후 실패했다. 이후12ms 전체 완료로 세지 않는다.
- 격자4/8/16의 LBVH 후보 탐색은 전수 AABB 탐색 대비 각각약3.30/10.27/48.97배 빠르다.
  격자16의 unfiltered VF+EE 조합20,139,006개를 후보15,217개로 줄였다. Candidate set은 모두 일치했다.
  가장 작은 두-triangle 동역학에서는 전체 실행 시간이 줄지 않았다. 이 수치를 전체 solver 가속으로 쓰지 않는다.
- 말린 천의 공간 오차 상한은 subdivision3/6/12/24에서 약11.405/3.027/0.780/0.198mm다.
  같은 상태의 barrier 에너지는 약0.149/0.300/0.601/1.197mJ로 증가해 응답 수렴은 미달이다.
- 1m 좌표 이동·최소 간격 위10nm 조건에서 FP32 저장 후 접촉력 상대 오차는 약78.6%다.
  원점에서는 같은 clearance의 오차가 약0.575%다. 큰 좌표에서의 불리한 조건과 구분해 보고한다.
- 단위·회귀47개 통과, CUDA graph 전용1개 미실행. 기본 CPU/Newmark/Gauss 및 Warp CPU 경로를 포함한다.

재현 테스트 명령(`code/`):

```bash
TBB_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 WP_CACHE_DIR=/tmp/wind3dgs-contact-warp \
  timeout 120 ../.venv/bin/python -m pytest \
  tests/test_p3_collision_proxy.py tests/test_p3_shell_contact.py \
  tests/test_teacher_p3_shell_dynamics.py tests/test_teacher_p3_shell_gauss.py \
  tests/test_teacher_p3_shell_precision_state.py tests/test_teacher_p3_shell_colored_preconditioner.py \
  tests/test_teacher_p3_shell_warp.py tests/test_teacher_p3_shell_warp_fast.py \
  tests/test_teacher_p3_shell_warp_precision.py -q
```

## 실패·해석·남은 작업

1. 약한 barrier의 고속 사례는 최소 간격에 약50nm까지 접근한 뒤, dt/64에서도 quadratic 시간
   보간의 중간 침범이 검출되어 거절됐다. 사용자 승인 후1,000/10,000 비교로 세 사례의 제한 검증을 통과했다.
2. 접촉 OFF의 이미 침범한 상태를 CCD에 넘긴 초기 검산에서 메모리 오류가 재현됐다.
   시작/끝의 원래·확장 간격을 먼저 검사하는 fail-closed 분기를 추가했다. VS Code 종료와의
   인과관계는 미확정이며 초기 v1/v2/v3는 개발 진단으로 보존한다.
3. 말린 곡면의 proxy subdivision3은 공간 오차 상한이 접촉 간격보다 크다. 세분화로 오차는
   줄지만, 고정 계수의 unweighted IPC 에너지는 표본 수에 따라 증가한다. 이 결과는 proxy/접촉
   응답의 최종 공간 수렴이 미완료임을 뜻한다. 이를 단순히 coarse proxy에서도 안전하다고 해석하지 않는다.
4. FP32 시험은 좌표 저장→FP64 복원이다. 전체 FP32 solver의 성능·정확도 시험이 아니다.
5. GPU resident 접촉, 마찰, 실제 장면 calibration, 시간/공간 수렴, 긴 풍하중 구간 및 R1 채택은 미완료다.

## 근거 파일

- 최종 약한 barrier 단독 비교: `artifacts/runs/p3_self_contact/20260922_weak_barrier_isolated/`의
  `report.json`, lane별 JSON/NPZ, `comparison.svg`. 아래 compact report와 원본 hash를 대조한다.
- 약한 barrier의 [비교 보고서](weak_barrier_report.json), [비교 그림](comparison.svg).
- 강도1,000 [보고서](barrier_1000_report.json), 강도10,000 [보고서](barrier_10000_report.json).
- [강도·시간 세분화 집계](strength_report.json), [강도 비교 그림](strength_comparison.svg).
  원본은 `artifacts/runs/p3_self_contact/20260922_strength_comparison_final/`에 보존한다.
  그림의 세로축은 두 층의 평균 signed gap이다. 위 표의 최소 primitive 간격과 같은 metric이 아니다.
- 단위·회귀 검사 및 인계: [code 기록](../../../code/sessions/2026-09-22_01_self_contact.md).

공식 문헌은 code 문서의 IPC / C-IPC / High-Order IPC / IPC Toolkit 링크를 따른다.
온라인 문서와 PyPI는 실제 조회·다운로드했고, 프로젝트 저장소는 fetch 없이 로컬 snapshot만 사용했다.
