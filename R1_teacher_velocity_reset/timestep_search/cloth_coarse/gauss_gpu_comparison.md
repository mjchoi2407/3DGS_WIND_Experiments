# 1/500 GPU Gauss·기존 솔버·세분 Newmark 비교

2026-09-14. [선행 정확도 진단](bend500_accuracy.md)의 후속이다. **3단계6차 Gauss의 적분·반복 풀이·보조 행렬 갱신/분해와 독립 검산을 GPU에 연결했다.** 기본 Newmark/FP64 hi/lo·물성·외력·원본은 유지한다. 최종 teacher 채택은 아니다.

원본: `artifacts/runs/teacher_timestep_search/gauss_gpu_comparison_v1/`. [선별 JSON](gauss_gpu_comparison.json), [구현 계약](../../../../code/docs/gpu_gauss_solver.md).

[비용·정확도 그림](../../../artifacts/runs/teacher_timestep_search/gauss_gpu_comparison_v1/cost_accuracy.png): 두 국소 구간의 끝 속도 차이와 풀이+검산 비용을 비교한다. 원본 manifest224개 파일의 해시와 기존 실패 trace 계승을 확인했다.

후속 [타임스텝 탐색](gauss_timestep_sweep.md)은 두 상태의1–32분할 비용을 새로 측정했다. 아래 선행 시간과 혼합하지 않으며, Gauss의 인접16↔32분할 차이도 후속에서 확인한다.

## 조건과 측정 범위

- 메시: 1/500 굽힘의 왼쪽 고정 `reference_rectangle`, 384삼각형·1813 P3 계산점. 원본 `gravity_wrinkles_flag_bend500_v1`의 입력/manifest 및 저장 chunk hash를 검증했다.
- 첫 시작 상태는 원본 바람2.0초 checkpoint, 두 번째는 실패 시도 직전의 확정 상태2.0145833333초다. 각 비교 구간은 **1/3840초(약0.0002604초)**이며 한 프레임/4초/10초 전체가 아니다.
- 첫 GPU frame-start 공력+중력 배열을 한 번 보존해 모든 lane에 같은 배열로 전달한다. 실패 직전 상태에서도 원래 frame의 이 외력을 유지한다. 물성·공력 갱신·감쇠를 바꾸지 않았다.
- `split=128`은 Newmark128차가 아니라 원래1substep 폭의128분할이다. Gauss는 모든 lane에서3단계6차이며, 과거 파일명 Gauss6의6단계12차 후보와 구분한다.
- GPU: 이번 main 환경의 **NVIDIA GeForce GTX 1080 Ti**, Warp1.17.0·CUDA Toolkit12.9/Driver13.0·동결 cuDSS0.7.1. CPU Gauss는 longdouble 상태+GPU hi/lo 힘, GPU 경로는 FP64 hi/lo 상태다.
- 공식 최종 허용오차는 같다. 기존 Newmark의 내부 힘 여유0.3배와 EW 선형 목표는 보존했고, Gauss는 기존 CPU 구현의 단계별 힘 기준과 고정 선형 목표를 유지했다. 내부 반복 정책까지 동일하게 강제한 비교는 아니며, 최종 독립 검산과 참조 상태 차이로 결과를 대조한다.
- 같은 GPU에서 lane을 순차 실행했다. 성능은 동일 구간 warmup 후3회 중앙값이다. 참조용 Newmark512와 실패 직전의256/512는1회 측정으로 구분한다. 독점 장치/클록·그래픽 부하는 통제하지 않았으므로 정식 통계적 benchmark나 구간 사이의 인과적 속도비로 일반화하지 않는다.
- GPU 풀이 시간은 구간 제출부터 완료 동기화까지다. 매substep CPU 조회·기록은 별도 replay에만 있다. 기존 프레임별 로그 실행 및 과거 동기화 진단의8.05/16.89초와 직접 섞지 않는다.
- GPU 검산 시간은 이미 GPU에 준비된 기록에서 D2D 제출·검산·완료까지이며 별도 준비/warmup 후3회 중앙값이다. 표의 합은 **별도 측정한 풀이+GPU 검산의 합**이다. 초기 모델/행렬 준비·입출력·기록 replay·통합 장기 실행 비용은 포함하지 않는다.

## 2.0초 시작 상태의 결과

속도 차이는 **Newmark512분할 끝 상태 대비 consistent-mass 상대 L2**다. 위치는 성분 최대 차이다. 기준은 exact solution이 아니며 Newmark256↔512 속도 차이도0.02648% 남는다. 따라서 Gauss16의0.00591%를 참해 오차 인증으로 해석하지 않는다.

| 후보 | 풀이(s) | GPU 검산(s) | 합산(s) | 끝 속도 차이 | 위치 최대 차이(µm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 기존 GPU Newmark·원래dt | 2.078 | 0.017 | 2.095 | 32.3229% | 41.1870 |
| GPU Newmark32분할 | 1.105 | 0.250 | 1.355 | 2.0977% | 0.9517 |
| GPU Newmark64분할 | 1.894 | 0.495 | 2.388 | 0.5488% | 0.2364 |
| GPU Newmark128분할 | 3.837 | 0.932 | 4.769 | 0.1321% | 0.0578 |
| GPU Newmark256분할 | 7.601 | 1.796 | 9.397 | 0.0265% | 0.0117 |
| CPU 중심 Gauss8분할 + GPU 검산 | 13.623 | 0.224 | 13.847 | 0.1724% | 0.0807 |
| GPU Gauss8분할·매번 행렬 갱신 | 3.748 | 0.221 | 3.969 | 0.1724% | 0.0807 |
| GPU Gauss8분할·행렬 재사용 | 0.910 | 0.246 | 1.156 | 0.1724% | 0.0807 |
| **GPU Gauss16분할·행렬 재사용** | **1.518** | **0.442** | **1.960** | **0.00591%** | **0.00284** |

Newmark512는 참조용 풀이13.327초(1회)이며 표의 정확도 순위에서0% 정답으로 취급하지 않는다.
CPU Gauss도 위 표에서는 동일한 GPU 검산기를 붙였다. 선행 CPU 독립 검산 시간은 raw report에 별도로 보존한다.

같은 Gauss8 계산에서 CPU→GPU 경로의 풀이 개선은 매번 행렬 갱신 조건에서약3.64배다.
행렬 재사용까지 합치면약14.98배다. 서로 다른 최적화를 모두 순수 GPU 이식 효과로 부르지 않는다.
재사용 간격64는 **Newton 선형 풀이 횟수** 기준이다. 이번 짧은 구간의 구축16→1회, GMRES48→63회로 바뀌었고 총시간은 감소했다. Gauss16은 구축1회·GMRES110회다. 기본 Newmark의 해당 수치는 구축1회·GMRES650회다.

GPU Gauss8 재사용 대 CPU Gauss8의 위치 최대 차이는1.37e-18m, 속도 최대 차이는1.56e-13m/s 이하다. GPU 이식/재사용 때문에 앞서 확인한 시간 적분 정확도가 눈에 띄게 달라진 근거는 없다.

## 실제 실패 시도 직전 상태의 대조

이 seed는 앞선 실패 trace의 마지막 확정 상태다. 끝 두 raw 상태가 같은 실패 후 기록을 확인하고, 실패 시도 전 상태를 사용했다. 비교를 위해 **모든 lane의 보조 행렬을 새로 준비**한다. 이전 연속 실행의 낡은 행렬/cache까지 재현하는 시험은 아니다.

| 후보 | 풀이(s) | GPU 검산(s) | 합산(s) | 끝 속도 차이(Newmark512 대비) |
| --- | ---: | ---: | ---: | ---: |
| 기존 GPU Newmark·원래dt | 4.800 | 0.011 | 4.811 | 34.2964% |
| GPU Newmark128분할 | 7.079 | 0.956 | 8.036 | 0.1375% |
| GPU Gauss8분할·재사용 | 1.918 | 0.234 | 2.151 | 0.1759% |
| **GPU Gauss16분할·재사용** | **3.207** | **0.469** | **3.677** | **0.00623%** |

이 구간에서도 Gauss16이 Newmark128보다 참조에 가깝고 합산 비용은약2.19배 짧았다(첫 seed에서는약2.43배).
참조256↔512 차이는0.02758%다. 원래dt의 단일 재시작은 이번에는 통과했으나 GMRES누적740회로 비쌌다. 이는 Newton 여러 회의 합이며 단일 선형 풀이 한도720을 초과 허용했다는 뜻이 아니다. 원래 연속 실행의 실패를 해결했거나 전체4초를 통과한 것으로 해석하지 않는다.

## 검산과 재현성

- 완료된16개 lane 모두 원래 후처리 검산을 통과했다. Newmark는1890개 고유 substep, Gauss는64개 고유 substep/192개 내부 stage다. 반복 시간 측정과 같은 구간의 replay를 서로 독립된 물리 궤적으로 합산하지 않는다.
- Gauss의64개 substep 모두 CPU longdouble 식과 GPU 독립 검산을 대조했다. GPU의 별도 buffer에서 단계별 힘/위치/속도 연결·끝 갱신·고정점·유한성·에너지 장부·P3×cubic 국소 기하를 다시 계산했다. GPU 검산은4회 실행(첫 회 제외 후3회 측정) 모두 flag0이다.
- 공식 힘 허용오차와 위치2e-14m/속도1e-12m/s의 연결 결함, 에너지 장부 차이3e-16J+1e-8×장부 절댓값을 유지한다. 비선형 Gauss의 실제 수치 에너지 변화는 별도 기록하며0으로 강제하지 않는다.
- 단순 residual 통과를 시간 수렴으로 간주하지 않는다. 위치가 수십µm만 달라도 순간 속도는 수십% 다를 수 있다.
- 실제 적분 graph에서 host copy/callback0과 조건부 body까지 확인했다. GPU 검사 graph도 host node0이며 제출 중 `.numpy()`를 금지한 검사를 통과했다. 손상 가속도·에너지·NaN 입력은 거부했다.
- 관련4개 회귀 검사 통과: 실수/복소 보조 풀이 대조, CPU/GPU 상태 대조·재개·zero RHS, 선형 실패의 확정 상태 보존, GPU 독립 검산/손상 입력 검출.
- 같은 입력 반복에서 raw bitwise 차이가 있을 수 있다. 합성 위치1e-16m/속도1e-12m/s 이내의 기존 수치 재현성 기준을 검사했고 허용오차를 새로 완화하지 않았다.
- 초기3개 개발 시도는 source ZIP 경로 처리, 큰 행렬에 필요한 기존 workspace shim 누락, 진단기의 과도한 bitwise 요구로 완료 판정하지 않았다. 해당 결과를 보존하고 비교표에서 제외했다. 최종 측정은 별도 경로와 source ZIP으로 식별한다. 원본 시뮬레이션의 물리 실패 분모와 혼합하지 않는다.

## 초기화·입출력과 남은 범위

첫 seed의 solver 초기 준비는 Newmark128약3.09초/Gauss16약3.33초, 검산기 준비는약0.319/0.250초였다. 모델 준비·기록 replay·원본 읽기/업로드·디스크 저장은 각 raw report의 별도 구간이다. 풀이+검산 합산을 완성된 데이터 생성기의 전체시간으로 부르지 않는다.

**현재 추천은 GPU Gauss6차16분할을 다음 검증 후보로 사용하는 것**이다. 두 국소 시작 상태에서의 근거이며 전체 궤적/공간 수렴이나 최종 학습 적격성은 아니다. 이미 coarse dt로 계산한 seed의 이전 누적 오차는 수정하지 않았다. 전체 rest 시작 궤적, 시간 보간 속도·GS 매핑, 접촉, 장기 checkpoint/실행기 연결은 남아 있다. 재사용64가 모든 구간에 적합하다고 고정하지 않는다.

서브컴 `artifacts/runs/sub_pc/`의 manifest/config/report도 검색했으나 이번1/500 Gauss 비교의 추가 실행은 없었다. 이번 표는 main GPU의 동일 장치 비교다. 외부 fetch/다운로드, 원본 실행 중단/재개, 기본 솔버 전환, stage/commit/push는 하지 않았다.

## 실행 경로

- 공통 입력 준비/개별 lane: `code/scripts/compare_gauss_gpu.py --prepare --out <새입력폴더>` 및 `--input <입력폴더> --out <새lane> --method newmark|gauss_cpu|gauss_gpu --split N --rebuild N`.
- 명시적 CUDA 환경: `PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`, workspace `.venv/bin/python`.
- `CUDSS_LIBRARY_PATH`는 원본에 동결된 `wind/runtime/native/libcudss.so.0`, `LD_PRELOAD`는 비교 원본의 `native/libcudss_workspace.so`다. 기존 C source를 별도 비교 폴더에 복사해 `cc -shared -fPIC -O2 -Wall -Wextra -Werror ... -ldl -pthread`로 빌드했다. source/binary hash는 manifest에 남긴다.
- GPU 검산: `code/scripts/audit_gauss_gpu_comparison.py <비교root> --lanes <lane들> --tag <새태그>`. 최종 측정은 `gpu_audit_v2`다.
- 집계: `code/scripts/analyze_gauss_gpu_comparison.py <비교root> --reference newmark512`.
- 원본의 각 config/report/source ZIP, CPU/GPU audit 파일, raw hi/lo endpoint/trace/stage와 manifest를 함께 사용한다. 같은 실행의 실패 파일을 덮어쓰거나 자동 재개하지 않는다.
