# Teacher 가속 개발 제한 종료 보고서

- 선택 동결: RTX5070 일반 바람/HL00 M2 32/32/256; GTX1080Ti 일반 바람/HL00 M1 256/256/256; GTX1080Ti C0/알려진 HL01 R64.
- 전체 FP32/새 solver 개발 종료. production_enabled=false, training_eligible=false. 회귀·교차 정확도 예산 미정.
- RTX5070 성공 환경 driver API13000, 현재 읽기 전용 조회 API13040/driver616.92. Graph 충돌 미해결, 인프라 복구 미실행.
- 첨부 중간 결산 보고서와 codex_bounded_closeout 파일은 작업 폴더에서 미발견. 이번 사용자 메시지의 명시 지시를 기준으로 구현·측정했다. 첨부 대조는 미완료.

## 기록 모드 비교

1080Ti M1 W30의 동일 checkpoint/forcing index60–89, 절대시각3.0–3.5초. full 다음 summary 각1회이며 추가 반복은 없다.

| 모드 | process wall(s) | 계산+검산(s) | validated generation(s) | trace 전송+decode(s) | trace 저장(s) |
|---|---:|---:|---:|---:|---:|
| W30_full | 519.564 | 435.106 | 435.160 | 0.402 | 32.202 |
| W30_summary | 429.644 | 419.623 | 419.674 | 0.032 | 0.315 |

실제 process wall 감소율 17.31%. 단일쌍 관측이며 순서·부하/clock·setup 차이를 기록 모드 효과로 단정하지 않는다.
필수31 snapshot/30 audit 보존 및 기존 검산 통과. audit 배열 exact=False; 최종 선형 trace exact=False. 정확 일치는 관측값이며 새 채택 기준이 아니다.

| 수치량 | 전체 저장 시각의 최대 절대 차이 | 단위 |
|---|---:|---|
| elastic_j | 1.28870723e-08 | J |
| force | 8.71821345e-05 | N |
| kinetic_j | 1.0548424e-08 | J |
| ledger_check_max_j | 6.92534138e-18 | J |
| u | 6.13886555e-07 | m |
| v | 0.000625302518 | m/s |

trace 전송/저장 자체는 32.604→0.347s, 98.93% 감소했다. 전체 wall 감소를 이 효과 하나로 설명하지 않는다. setup은 18.226→6.394s이며 첫 실행의 cold import/파일 cache 영향도 분리되지 않았다.
Newton 선형 호출 10385→10389, GMRES 반복 182765→183755. 수치 차이의 원인은 이 단일쌍으로 확정하지 않는다. 저장된 trace/보정 길이와 device 카운터의 일치·연속 solve_id·overflow 여부는 trace_completeness.json에 있다. 회귀 예산 없이 수치 동등성 승인으로 해석하지 않는다.

process wall은 새 worker 시작부터 종료까지이며 종료 bulk dump·close·메타데이터 저장을 포함한다. validated_generation_s는 기존 정의(계산+검산+필수 상태 전송/저장)로 trace 및 진단 snapshot 비용을 제외한다. trace CSV는 bulk D2H+host decode와 직렬화/저장을 분리한다. 작은 집계 메타데이터 저장은 process wall에 포함하되 trace 소계에는 포함하지 않는다. 기존 batch delta read는 계산+검산에 이미 포함된다. 타이머 중첩을 더하지 않는다.

## 저장된 HL01 선형계

판정: `promising_frozen_candidate`. 원본 frame225(상대frame10/substep29), 최고비용 frame236 미측정.
warm-up 후 각3회 원래 A64 잔차 기준 통과. 중앙값 R64 factor+solve 2.826987s → fresh assembly+factor+solve 0.242087s, 감소 91.44%.
old factor가 이미 상주하면 R64 solve 2.816755s이며, 이 분모 대비 fresh 전체 감소는 91.41%다.
20%는 개발 자원 배분 기준이다. 원래 Newton/EW 목표를 완화하지 않았다. 잔차 재검산 비용은 CSV에 별도 기록하며 process wall에 포함된다. 전역 P 갱신·추가 checkpoint·전체 HL01 재생은 하지 않았다.

## 과거 완료 쌍만 집계

| GPU | 구간 | 완료쌍 | validated generation R64→mixed(s) | 감소율 | process wall R64→mixed(s) |
|---|---|---:|---:|---:|---:|
| gtx1080ti | C0 | 6 | 1.739 → 1.855 | -6.67% | 10.928 → 11.169 |
| gtx1080ti | W1 | 6 | 28.849 → 23.315 | 19.18% | 38.222 → 32.847 |
| gtx1080ti | W30 | 3 | 450.980 → 358.577 | 20.49% | 492.683 → 401.329 |
| gtx1080ti | HL00 | 1 | 383.583 → 329.068 | 14.21% | 447.132 → 389.918 |
| rtx5070 | C0 | 6 | 1.228 → 1.070 | 12.89% | 11.607 → 12.210 |
| rtx5070 | W1 | 6 | 18.709 → 12.893 | 31.08% | 29.273 → 23.976 |
| rtx5070 | W30 | 2 | 295.290 → 206.236 | 30.16% | 343.791 → 256.473 |
| rtx5070 | HL00 | 1 | 260.888 → 181.069 | 30.59% | 334.724 → 253.647 |

5070 W30은2쌍이며 추가 M2와 미완료 prefix는 빠진 R64를 대신하지 않는다. W1/W30/HL00은 겹치므로 전체 가속률로 합산하지 않는다. 구간/입력·반복 원시값은 historical_complete_pairs.csv에 있다.

## 원본·재현과 종료 범위

Canonical 결과: `experiments/artifacts/runs/teacher_precision_v3/bounded_closeout_20260916/`. `logs/commands.jsonl`은 실제 명령과 외부 wall, `runtime/`은 동결 solver에 host worker만 추가한 코드, `inputs/`는 원본 checkpoint metadata/hash 및 HL01 snapshot이다. 원래 W1/HL01 입력 경로와 전체 원본 hash는 inputs/*/input_source_hashes.json에 있다.
선택 manifest, 환경 차이, source/input hash, changes.diff, 원시 CSV/NPZ/로그와 telemetry를 함께 보존한다. numerical budget은 추가하지 않고 생산 승격하지 않는다. 고하중 최대점 전체/장기 teacher 적격성/R1 Gate는 미완료다.
