# 256배 고정 시간 간격의 Gauss 적분 비교

2026-09-11 사용자 승인: 물리식·허용오차·Δt=1/60초를 유지하고 시간 적분법을 별도 시험한다.
기존 Newmark 실행기/동결 원본은 유지하며 이 시험을 R1 채택으로 승계하지 않는다.

## 현재 판정

후속: 사용자 승인으로 [빠른 진동 분리·지수 결합 시험](../exponential256_20260911/README.md)을 진행했다. 아래는 당시 Gauss 단독 판정이다.

256배를 유지한6단계12차 후보는 독립 물리 검산과 후속 구간의 국소1% 상대 비교를 통과했다.
그러나 **참조 수렴이 확인되지 않아 정확도 확보·장기 채택을 확정하지 않는다**.
[현재 집계](summary.json), [최종 고차 참조 비교](gauss_reference4_comparison.json).
참조 차이 방향의 빠른 탄성 진동 지표를 확인했다. 다음은 이를 별도로 처리하는256배 적분 시험의 방향 확인이다. 물리적 불가능 판정이 아니다.

## 시험 계약

2단계 Gauss–Legendre collocation(4차)을 첫 후보로 사용한다.
근거: [Hairer 강의자료](https://www.unige.ch/~hairer/poly_geoint/week2.pdf),
[Hairer·Zbinden의 Gauss 방법 정리](https://www.unige.ch/~hairer/preprints/conjsympl-hz.pdf).
공식 웹 자료를 조회했으며 원본 시뮬레이션 입력은 로컬 동결 자료만 사용했다.

- A=[[1/4,1/4−√3/6],[1/4+√3/6,1/4]], b=[1/2,1/2], c=A·1.
- 각 단계: Uᵢ=u₀+h ΣⱼAᵢⱼ Vⱼ, Vᵢ=v₀+h ΣⱼAᵢⱼ aⱼ, M aᵢ=f(Uᵢ)+F.
- 끝 상태: u₁=u₀+h ΣᵢbᵢVᵢ, v₁=v₀+h Σᵢbᵢaᵢ.
- F는 frame 시작 공력으로 고정한다. 단계마다 공력을 새로 평가하지 않는다.
- 2단계 후보는 내부2개, 후속 고차 후보는3/4/6개 단계를 동시에 푼다. 외부 시간 단계는1/60초이며256배가 계산 속도256배를 뜻하지 않는다.
- Newton의 변위 수정과 a 수정=(A²)⁻¹δU/h²을 함께 누적한다. 현재 단계별 보조 행렬과 원래 HVP의 참 잔차를 사용한다.
- force_atol=1e-10 N, force_rtol=1e-9, displacement_atol=1e-12 m,
  displacement_rtol=1e-9, linear_rtol=1e-10, max_newton=15, GMRES240×3을 유지한다.

단계 힘은 별도 CPU longdouble 원식으로 다시 계산한다. 위치·속도 갱신은 위 원래 RK 식으로 검사한다.
기하는 Gauss의 단계 수와 같은 차수의 위치 collocation 곡선을 Bernstein control로 검사한다.
곡선의 시작 미분은 물리 초기 속도와 다를 수 있으므로 Newmark 전용 초기속도를 그대로 넣지 않는다.
끝 상태 에너지 변화−고정 힘의 일은 독립 에너지 장부로 비교하며 비선형 에너지의 정확 보존을 주장하지 않는다.
현재 endpoint 비교는 이전과 같은 질량/면적 가중 L2이며 전체 시간 보간 정확도 판정은 별도다.

## 재현

[probe_gauss.py](probe_gauss.py)는 이전64배 궤적3.25초의 동일 입력과 frame195 고정 공력을 사용한다.
비교 참조는 앞서 검산한32분할의 공통 끝 시각 상태다. `[1/60초,2 stages]`와 `[32개 작은 step]`을 분리 기록한다.

```bash
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/gauss256_20260911/probe_gauss.py 새_출력_경로
```

원본은 `experiments/artifacts/runs/teacher_timestep_search/20260911_gauss256_v1`에 source.zip,
입력 hash, 단계 hi/lo 배열, endpoint checkpoint와 report로 보존한다.
구현 단위 검사는 일정 힘의 정확 갱신, 해석적 진동자에서4차 오차 감소·선형 에너지, 계수 관계를 확인한다.

## 2단계 결과

[원본 집계](stage2_report.json): Newton4회·36.823초·HVP2490회. 독립 단계 힘 잔차/한도 최대0.011566 미만,
위치/속도 갱신 결함 최대5.5e-20 미만, 에너지 장부 차이6.94e-18 J, 전체 곡선 기하 상한0.174898 미만으로 통과했다.
위치 갱신 결함은 기존 진단의 더 엄격한2e-14 m 기준도 만족한다.
공통32분할 참조 대비 끝 상태 상대 차이는 변위0.011714%, 속도1.895402%다.
Newmark의 변위0.037609%, 속도1.612754%와 비교하여 변위는 개선됐지만 속도는 개선되지 않았다.
두 결과 모두 주어진 한 구간의 비교이며 보편적 물리 한계 판정이나 전체10초 판정은 아니다.
3단계6차 Gauss 후보는 같은 외부 dt·허용오차·힘 갱신으로 추가 비교한다.
고차 위치 곡선은 Bernstein control의 projected gradient 상한으로 기하를 검사하고,
독립 계수에서 얻은 단계 위치와 그 곡선의 일치를 별도로 확인한다.

## 3/4단계와 결합 보조 풀이 결과

| 같은 입력·1/60초 후보 | 계산(초) | 끝 시각 변위 차이 | 끝 시각 속도 차이 | 독립 단계/기하 검산 |
| --- | ---: | ---: | ---: | --- |
| Gauss2·4차 | 36.823 | 0.011714% | 1.895402% | 통과 |
| Gauss3·6차 | 66.380 | 0.003319% | 1.714750% | 통과 |
| Gauss4·8차·개별 보조 풀이 | 108.082 | 0.003017% | 0.631183% | 통과 |
| Gauss4·8차·결합 보조 풀이 | 49.061 | 0.003017% | 0.631183% | 통과 |

[3단계](stage3_report.json), [4단계](stage4_report.json), [결합 보조 풀이](stage4_coupled_report.json).
결합 보조 풀이는 현재 단계들의 공통 접선을 구성하고 `(A²)⁻¹`의 복소 고유변환으로 단계 연결을 반영한다.
켤레 복소 LU 두 개를 재사용하되 실제 선형 검산은 원래 단계별 HVP를 사용한다.
4단계의 Newton 선형 반복은120–162회 수준에서15–17회로 줄었다. 세부 횟수는 원본 report를 따른다.
[해 차이 검산](coupled_endpoint_check.json): 변위 최대5.64e-17 m·속도2.59e-14 m/s로 채택한 수치적 재현성 기준 이내다.
시간은 단기 개발 측정이며 warm/컴파일·외부 부하와 일부 CPU 회귀 검사 동시 실행의 영향을 포함한다. 정식 가속률은 아니다.

[오차 방향 진단](error_frequency.json)은 초기 현재 접선의 Rayleigh 지표 약99–123Hz를 보여준다.
이는 혼합 모드의 가중 지표이고 단일 실제 진동수나 모드 분포의 증명은 아니다. 물리 감쇠/필터는 추가하지 않았다.

[전체 국소 곡선 비교](curve_comparison.json):4단계의 변위/속도 상대 상한은0.003832%/0.797713%로1% 이하다.
동일 구간의16→32분할 참조 속도 차이 상한은0.200095%다.
Gauss의 U/V collocation 다항식은 단계 외에서 `dU/dt=V`가 정확히 같지는 않다.
4단계의 해당 속도 결함 상한은 참조 peak 대비0.395328%로 별도 기록하며, Newmark의 반올림 결함과 혼동하지 않는다.
상한은 차이 Bernstein control의 L2 convex hull과 부동소수 여유를 사용한 개발 검산이다.
엄밀한 interval arithmetic, 독립 ODE 정답 또는 전체10초 판정으로 승계하지 않는다.

## 저장 후 후속 구간

Gauss4 첫 endpoint를 다른 프로세스에서 읽고 frame196 공력을 갱신해1/60초를 더 계산했다.
[후속](stage4_followup_report.json):47.683초, 독립 단계 힘/갱신/에너지/기하 모두 통과.
32분할 참조 대비 끝 변위0.004489%, 속도0.690476%다.
[후속 참조 분모](followup_reference_report.json):16분할은 첫 단계만 통과 후 선형 풀이 실패,
32분할32개 interval은 모두 통과했다. 참조16 실패를 숨기거나 물리적 불가능으로 해석하지 않는다.
64분할64개 interval도 검산을 통과했다([참조](followup_refine64_report.json)).
[전체 곡선 비교](followup_curve_64_comparison.json)에서8차 후보의 속도 차이는1.009884%로1%를 초과했다.
동일 입력의6단계12차 후보는53.483초에 독립 검산을 통과했고 속도 차이는0.584830%였다
([6단계 검산](stage6_followup_report.json)). 참조32→64 차이가0.640007%라128분할 참조로 재확인했다.
[128분할 검산](followup_refine128_report.json)은128개 interval 모두 통과했다.
[128분할 곡선 비교](followup_curve_128_comparison.json):8차1.012250%,12차0.626347%의 속도 차이다.
그러나 참조64→128 차이는0.706285%로 줄지 않아 Newmark 참조 수렴이 확인되지 않았다.
따라서12차의1% 이내 상대 비교만으로 정확도를 확정하지 않고, 같은 힘으로 Gauss6의2/4분할 참조를 추가한다.
각 구간의 참조는 그 구간의 Gauss 시작 상태에서 출발한다. 따라서 국소 시간 오차 비교이며,
두 구간을 최초 입력에서 독립 전진한 전역 오차 비교나2.5초/10초 통과로 합산하지 않는다.

## 구현 검증과 적용 범위

[검증 집계](validation.json): Gauss 단위 검사9개, colored 보조 풀이2개, 고정밀 상태8개,
기존 동역학5개로24개 통과. 해석적 진동자의4/6/8/12차 오차 감소, 실제 P3 n=4의
Gauss4/6 coupled hi/lo 저장·재개를 확인했다. 해당 재개 기준은 변위1e-16 m·속도1e-12 m/s다.
실제 n=32 후보는2/3/4/6단계다.5단계는 계수 검사만 있으며 GPU 실험 증거는 없다.

기존 `run_precision_segments.sh`는 여전히 Newmark256배용이다. 새 Gauss API를 호출하지 않는다.
장기 적용에는 단계 trace·독립 검산·적분기 식별을 포함한 별도 실행 연결과 n=32 재개 비교가 필요하다.
본 실행의 잔여 예산7998초는 그대로다. 진단 비용을 새 장기 실행으로 집계하거나 예산을 늘리지 않았다.
6단계의 한 구간53.483초를 단순 외삽하면2.5초150구간은 약8022.5초이며 검산·준비 비용도 추가된다.
서로 다른 변형 상태의 비용이 달라질 수 있어 완료 시간 예측이나 정식 속도 비교로 사용하지 않는다.
2.5초·10초 누적 정확도와 공간 해상도 수렴은 모두 미완료다.

### 추가 재현 명령

GPU probe는 공통으로 `PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`에서
`.venv/bin/python <probe> <존재하지_않는_출력_경로>`로 실행한다.
3/4단계는 `probe_gauss3.py`, `probe_gauss4.py`, 결합 보조 풀이는 `probe_gauss4_coupled.py`,
저장 후4/6단계는 `probe_gauss4_followup_coupled.py`, `probe_gauss6_followup.py`다.
참조 계산은 `probe_followup_reference.py`(16/32), `probe_followup_refine.py`(64),
`probe_followup_refine128.py`(128)를 사용하고 `PYTHONPATH`를
`experiments/artifacts/runs/teacher_timestep_search/20260911_target256_segments_v2/runtime/code`로 지정한다.
참조는 당시 동결한 Newmark 코드를 사용하며 새 Gauss 코드로 대체하지 않는다.
CPU 곡선 비교는 `PYTHONPATH=code`에서 `compare_curves.py`, `compare_followup_curves64.py`,
`compare_followup_curves128.py`에 결과 JSON 경로를 인자로 준다. 모든 경로는 workspace root 기준이다.
probe의 원본 `report.json`과 `source.zip`/동결 runtime hash는 [식별 정보](identity.json)에 연결한다.

고차 참조는 `probe_gauss6_reference.py <새_출력_경로> <2또는4>`를 `PYTHONPATH=code`에서 실행한다.
공력은 최초 입력에서 한 번 구해 원래1/60초 동안 고정한다. 각 작은 구간도 독립 단계·기하·에너지 검산을 한다.
`compare_gauss_reference.py <결과_JSON> <2또는4>`는 같은 물리 시간에서 전체 곡선을 비교한다.
참조 분할은 검산 전용이며 목표 후보의256배 설정을 변경하지 않는다.

## 고차 참조 교차 확인 결과

Gauss6 검산용2분할·4분할의6개 작은 구간은 모두 독립 검산을 통과했다
([2분할](gauss_reference2_report.json), [4분할](gauss_reference4_report.json)).
공통 시작 상태·원래1/60초 동안의 고정 공력은 유지했다.

| 후속 한 구간 전체 곡선 비교 | 변위 상대 상한 | 속도 상대 상한 |
| --- | ---: | ---: |
| Gauss6 목표256배 → Gauss6 참조4분할 | 0.001492% | 0.686840% |
| Gauss6 참조2분할 → 참조4분할 | 0.000220% | 0.716642% |
| Newmark 참조128분할 → Gauss6 참조4분할 | 0.000200% | 0.607199% |

[직접 비교](gauss_reference2_comparison.json)와[Gram 질량 내적 재사용 비교](gauss_reference2_gram_comparison.json)는
2분할 참조의 모든 JSON 수치가 같았다.4분할 비교에는 같은 Gram 계산을 사용했다.
후보 차이는1% 미만이지만 참조 자체 차이가 비슷한 규모라, 참조의 잔여 오차가 충분히 작다는 근거가 아니다.
고차의 명목 차수나 힘 방정식 잔차 통과만으로 시간 정확도를 판정하지 않는다.
추가 참조에도 수렴 미확인인 분모를 남기며, 필터·인위적 감쇠·허용오차 완화는 적용하지 않았다.

## 참조 차이 방향 진단과 다음 분기

[현재 접선 Rayleigh 진단](reference_frequency.json)은 공통 끝 상태의 속도 차이 방향을 초기 접선에 적용했다.
Gauss6 목표 대4분할 참조는1688.47Hz,2분할 대4분할 참조는2246.99Hz,
Newmark128 대Gauss6 참조4분할은2918.91Hz의 가중 진동 지표다.
이는 혼합 모드의 지표이며 단일 고유 진동수·모드 분포·발생 원인을 확정하지 않는다.
끝 속도로 정규화한 해당 report와 참조 peak로 정규화한 전체 곡선 표의 백분율은 분모가 다르다.
바람 갱신60Hz와 구분하며,256배의 물리적 불가능 근거로 쓰지 않는다.

현재 시험은 고차 후보의 개선 효과와 참조 미수렴을 확인한 상태다.
다음 후보 제안은 빠른 탄성 진동을 별도로 계산하는 시간 적분이다.
물리식·바람 갱신·256배·기존 허용오차를 유지하고, 새 방식의 수치 오차/비용을 별도 검산해야 한다.
이 새 방식은 아직 구현하지 않았다. 사용자에게 다음 시험 방향을 확인하며 장기 실행은 시작하지 않는다.
