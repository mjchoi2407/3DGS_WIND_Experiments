# Gauss 전용 FP64 / 혼합 FP32 우선 프레임 비교

2026-09-20. Newmark 실패 뒤 Gauss를 반복 호출한 전체 프레임 시험과 분리하여,
같은 고부하 시작 상태에서 처음부터 Gauss6차만 사용하는 별도 비교를 준비했다.
기존 실행과 생산 설정은 변경하지 않는다.

비교 대상은 표시 frame 190, 194, 200이다. 각 프레임은 저장된 원시 FP64 hi/lo 상태와
해당 `held` 외력을 복원하고, `dt=1/30720`초의 Gauss 512단계로 정확히 1/60초를 진행한다.

- `GAUSS_R64`: 기존 FP64 Gauss를 512단계 연속 실행한다.
- `GAUSS_MIXED32_FALLBACK64`: 상태·힘·stage·비선형 판정·원래 FP64 참 잔차는 FP64로
  유지하고, HVP/GMRES/평형화 보조 행렬은 FP32로 실행한다. 연속 8단계 묶음이 solver 또는
  독립 검산을 통과하지 못하면 묶음 시작 상태에서 기존 FP64 Gauss 8단계를 다시 계산한다.

8단계 묶음은 기존 Newmark 한 substep을 Gauss로 대체할 때 사용한 동일 물리 시간 폭이다.
실패한 혼합 계산과 FP64 재계산 비용을 모두 전체 시간과 항목별 누적 시간에 포함한다.
공식 허용오차, line search, Newton/GMRES 정책, 독립 검산 기준은 바꾸지 않는다.

GTX 1080 Ti 실행:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss_precision_frame_probe.sh
```

RTX 5070에서 같은 스크립트를 복사하지 않고 block만 명시하려면:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss_precision_frame_probe.sh \
  --blocks 32 32 256
```

기본 출력은 `experiments/artifacts/runs/teacher_precision_v3/gauss_precision_frame_<시각>`이다.
`report.md`는 전체 프레임 시간과 역할별 누적 시간을, `raw.csv`와 `role_times.csv`는 원시값을,
`differences.csv`는 FP64 기준 끝 상태·힘·에너지 차이를 기록한다. 각 worker의 CUDA 초기화 정보는
원본 `.log`에 보존하고 터미널에서만 숨긴다. `graphs.json`, 환경·전처리 hash, 실제 명령도 함께 남긴다.
동결 `selection.json`의 선행 Newmark+Gauss 복구 프레임 시간도 `pairs.csv`와 보고서에 참고값으로
연결한다. 다만 새 진단은64개 묶음 경계 동기화와 GPU 역할 계측을 추가하므로 이를 엄격한 동일 harness
가속률로 해석하지 않는다.

이 시험은 세 개의 독립 한 프레임 진단이다. 장기 궤적, production 적용, training 적격성을
자동 승인하지 않는다.

## 프리로드 저부하 한 프레임

고부하와 같은 두 Gauss lane을 평면 rest 상태의 중력 ramp 첫 프레임에도 실행한다. 입력은
선행 Gauss 정밀도 시험이 보존한 `inputs/preload/input.npz`이며 raw FP64 hi/lo0 상태와 실제
첫 프레임 `held`를 사용한다. 물성·정책·`dt=1/30720`초·512단계는 고부하 비교와 같다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss_precision_preload_probe.sh
```

출력은 `gauss_precision_preload_<시각>`이다. 같은 시작 조건의 선행 GTX1080Ti Newmark64
프레임 시간도 provenance와 함께 참고값으로 연결한다. 기존 측정은 역할 계측과64개 묶음 동기화가
없는 다른 실행 구조이므로 새 Gauss lane과 엄격한 paired speedup으로 간주하지 않는다.

## 2026-09-20 첫 실행 오류와 재실행

첫 고부하/저부하 실행의 `GAUSS_R64` lane은 정상 완료했으나 혼합 lane은 계산 전에 Warp Graph
컴파일에서 중단됐다. 동결한 high-load v3의 `wind3dgs_low` 안에 FP64 Gauss 커널이 남아 있어,
FP32 `pair_scale(vec2f, float32)`에 `vec2d, float64`를 전달한 런타임 조합 오류였다. 이는 FP32
수렴 실패나 정확도 실패 결과가 아니다.

실행기는 새 결과 폴더를 만들 때 기존 Gauss 혼합 시험에서 검산을 통과한 `mixed_v3/wind3dgs_low`
패키지를 manifest hash로 검증해 복제한다. 완료된 R64 결과는 입력·설정·출력 hash와 `passed`를
확인한 뒤 새 폴더로 복사할 수 있다. 실패 원본은 보존한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss_precision_preload_probe.sh \
  --reuse-completed experiments/artifacts/runs/teacher_precision_v3/gauss_precision_preload_20260920T032001

bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss_precision_frame_probe.sh \
  --reuse-completed experiments/artifacts/runs/teacher_precision_v3/gauss_precision_frame_20260920T031505
```

각 명령은 새 timestamp 폴더를 만들며, 재사용한 R64 lane은 건너뛰고 누락된 혼합 lane부터 진행한다.
GPU가 노출된 환경에서는 worker의 `--graph-smoke`로 Graph 생성과 두 정밀도 경로의 8단계 워밍업만
검사할 수 있다. 이 개발 컨테이너에서는 CUDA driver가 노출되지 않아 실제 smoke 결과는 미측정이다.

## GTX 1080 Ti 실행 결과

Canonical 결과는 다음 두 폴더다.

- 저부하: `artifacts/runs/teacher_precision_v3/gauss_precision_preload_20260920T032834`
- 고부하: `artifacts/runs/teacher_precision_v3/gauss_precision_frame_20260920T032934`

네 조건 모두 512/512단계와 매 묶음 독립 검산을 통과했고, FP64 복구 묶음은 0개였다.

| 구간 | Gauss R64 계산+검산(s) | 혼합 FP32 우선(s) | 혼합 시간 변화 | R64 / 혼합 GMRES |
|---|---:|---:|---:|---:|
| 저부하 frame1 | 33.153 | 34.344 | +3.59% | 1,946 / 2,048 |
| 고부하 frame200 | 46.262 | 44.410 | -4.00% | 5,109 / 5,557 |
| 고부하 frame194 | 48.933 | 51.118 | +4.47% | 5,036 / 5,511 |
| 고부하 frame190 | 54.897 | 50.574 | -7.87% | 5,133 / 5,580 |

고부하 3프레임 합계는 R64 150.091초, 혼합 146.103초로 혼합이 2.66% 짧았다. 그러나
프레임별 방향이 다르고 각 1회 측정이다. 혼합의 GMRES 반복은 고부하 합계에서 8.97% 늘어
FP32 단위 연산 이득을 상당 부분 상쇄했다. 현 결과만으로 혼합을 R64 대신 기본 경로로 채택할
성능 근거는 부족하다.

끝 상태 차이의 최댓값은 위치 1.40e-16m, 속도 1.64e-12m/s, 힘 8.83e-13N이었다.
모든 flag는 0이고 비유한 값은 없었다. 따라서 이 동결 1프레임 범위의 정확도는 유망하지만,
연속 궤적과 장기 teacher 적격성은 미검증이다.

저부하에서는 선행 Newmark 경로 1.825초에 비해 Gauss가 33~34초로 현저히 느렸다. 반면
고부하에서는 선행 Newmark+반복 Gauss 복구 266~290초 대비 직접 Gauss가 44~55초였다.
선행 경로와 현 harness의 묶음 경계 동기화·계측 구조가 달라 엄격한 paired speedup은 아니지만,
저부하는 Newmark를 유지하고 반복 복구가 예상되는 고부하에서 직접 Gauss로 전환하는 방향을 지지한다.

항목별 계측은 Graph 자식 커널이 `other_device`로 합쳐져 주요 연산 항목이 0으로 남았고,
event 합계와 wall이 일치하지 않았다. 이 실행으로 항목별 비중이나 개별 가속을 판정하지 않는다.

## RTX 5070 교차 장치 비교

서브컴 canonical 결과는
`artifacts/runs/sub_pc/20260919T183759Z-edbc21b5b5424c12a878dc4785122099/frame`이다.
입력 NPZ와 plan hash, Gauss low runtime hash가 GTX1080Ti 결과와 일치한다. 물리·수치 코드는
같고 GPU별 선택 block만 GTX1080Ti `256/256/256`, RTX5070 `32/32/256`으로 다르다.

| 표시 frame | GTX1080Ti R64(s) | RTX5070 R64(s) | 장치 배속 | GTX1080Ti 혼합(s) | RTX5070 혼합(s) | 장치 배속 |
|---|---:|---:|---:|---:|---:|---:|
| 200 | 46.262 | 33.063 | 1.399x | 44.410 | 25.509 | 1.741x |
| 194 | 48.933 | 32.930 | 1.486x | 51.118 | 25.307 | 2.020x |
| 190 | 54.897 | 32.683 | 1.680x | 50.574 | 25.329 | 1.997x |
| 합계 | 150.091 | 98.676 | 1.521x | 146.103 | 76.145 | 1.919x |

RTX5070의 혼합 경로는 세 프레임 모두 R64보다 빨랐고 합계 시간 감소는 22.83%였다. GTX1080Ti의
2.66%·프레임별 혼재와 달리 방향과 크기가 일관됐다. 모든 RTX5070 실행은 512/512단계, 독립 검산,
flag0, FP64 복구0을 만족했다. R64 GMRES와 rebuild는 두 장치에서 완전히 같았고, 혼합 GMRES는
장치 사이 최대4회만 달랐다.

동일 lane의 장치 간 끝 상태 최대 차이는 위치 1.12e-15m, 속도 2.21e-12m/s, 힘 1.13e-12N이다.
교차 장치 정확도 budget은 정의되지 않았으므로 정량값만 보존한다. 이 세 동결 프레임에서는
RTX5070은 혼합 FP32 우선, GTX1080Ti는 R64 Gauss를 쓰는 장치별 후보가 성능상 타당하다.
장기 연속 적분과 학습 적격성은 아직 승인하지 않는다.

서브컴 프리로드 canonical 결과는
`artifacts/runs/sub_pc/20260919T184651Z-17b048be114842d4a3f5cdbd47ecd19f/preload`이다.
초기 상태·plan·runtime hash가 GTX1080Ti 프리로드와 일치했고 두 lane 모두 512/512단계,
독립 검산, flag0, FP64 복구0을 만족했다.

| 프리로드 lane | GTX1080Ti(s) | RTX5070(s) | 장치 배속 | 장치 내부 혼합 변화 |
|---|---:|---:|---:|---:|
| Gauss R64 | 33.153 | 24.389 | 1.359x | 기준 |
| Gauss 혼합 FP32 우선 | 34.344 | 20.994 | 1.636x | GTX1080Ti +3.59%, RTX5070 -13.92% |

프리로드에서도 RTX5070은 혼합 경로가 R64보다 빨랐고 GTX1080Ti는 반대였다. R64 GMRES는
두 장치 모두 1,946회, 혼합은 2,048회였으며 rebuild도 각각 16회로 같았다. 동일 lane의 장치 간
끝 상태 최대 차이는 R64에서 위치 1.82e-17m·속도 8.23e-13m/s·힘 7.69e-13N, 혼합에서
위치 2.25e-17m·속도 1.40e-12m/s·힘 8.23e-13N이었다. 교차 장치 정확도 budget은 정의되지
않았으므로 통과 판정으로 확대하지 않는다.

RTX5070 혼합 Gauss 20.994초도 선행 GTX1080Ti Newmark 참고값 1.825초보다 11.50배 길다.
이 비교는 장치와 harness가 달라 paired speedup이 아니며 RTX5070 Newmark 자체는 이번에 재측정하지
않았다. 그럼에도 저부하에 처음부터 Gauss를 쓰는 선택을 지지하지 않으며, Newmark를 유지하다 반복
복구가 예상되는 고부하에서 직접 Gauss로 전환한다는 결론은 유지된다. 첫 worker의 process wall에는
CUDA JIT/Graph 준비가 크게 포함됐으므로 모든 교차 장치 표는 완료 경계의 계산+검산 시간만 사용한다.
