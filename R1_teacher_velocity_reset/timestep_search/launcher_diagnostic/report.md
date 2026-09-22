# GTX1080Ti 공통 실행 경로 진단

확인 기준:2026-09-17. 과거 약2.5배 저하는 현재 재현되지 않았고 **원인은 미확정**이다.
M1 정밀도 문제나 자동 선택 코드의 성능 결함으로 확정하지 않는다. 생산 solver 수정은 없다.

## 결론

- 동일 무풍3프레임 C/D의 교대3쌍에서 기존 R64 시간과 반복량·검산이 회복된 상태를 관측했다.
  C/D 차이 방향은 쌍마다 바뀌었고 과거2.5배 차이를 설명하지 않는다.
- C는 부모에서 Warp/CUDA를 로딩하지 않았다. D는 기존 GPU 탐지 초기화를 수행했다.
  별도1회/2회 초기화 조회에서 현재 context와 primary context 모두 비활성이었다.
  GPU 프로세스 목록 두 항목을 활성 CUDA context 두 개의 증거로 간주하지 않는다.
- 회복 확인 뒤 동일 바람 checkpoint3프레임 R64/M1을3쌍 비교했다.
  계산+독립 검산 median **30.641→25.038초**, **1.224배 /18.29% 단축**.
  각 쌍 단축률17.85–18.70%. 전체 process wall median39.143→34.077초(약12.94% 단축).
  이는 W1의3프레임 개발 측정이며 전체 바람·HL01·teacher 생성 가속률이 아니다.
- 두 방법 모두 기존 독립 검산 통과. 이 바람 비교에서는 M1 fallback0, Gauss retry0.
  M1 GMRES 총반복11356–11369, R64는10630회/3프레임. 반복은 늘었지만 시간은 줄었다.
- Nsight Systems는 GPU UUID 변환 오류로 유효한 report를 만들지 못했다. 도구를 교체/설치하지 않았다.
  observer의 실제 Graph/배열/host 호출 관측은 보존하되 profiler 실행 시간은 일반 통계에서 제외했다.
- 생산/학습 적격성은 승격하지 않는다. 5070 Graph 문제와 회귀 예산 미정도 그대로다.

## 안전한 종료와 보존

요청 확인 시 현재 suite/worker 프로세스는 이미 없었고 바람 report는 interrupted였다.
따라서 추가 종료 신호를 보내지 않았다. 프리로드120·무풍240의 완료 checkpoint와
바람120프레임의 확정 chunk를 hash 및 독립 검산 flag0/finite로 확인했다.
바람의 미저장 prefix를 복구·재생하지 않았다. `preserved_results.json`, `preserved_audit_check.json` 참조.

## 조건과 실행 순서

원본은 기존 `newmark_dt_gauss_retry_bend500_v1/reference_rectangle`이다.
무풍은 검증된 preload checkpoint(절대2초), forcing index0..2.
바람은 검증된 wind chunk의 저장 index60(절대3초), 원본 forcing index60..62.
forcing을 한 번만 잘랐고 worker는 잘린 배열0..2를 사용한다.
각 실행에서 상태·모델·보조 행렬을 새로 초기화한다. JIT cache만 동일 경로를 재사용한다.

C/D는 현재 controller 함수의 PHASES를 단일 phase로 제한하고, 완료 뒤 분기 간 비교 대신 반환한다.
worker 본문/인자/물리/기록/Graph 정책은 동일하다. 모두 같은 `work/active_case` 경로를 사용한 뒤
결과를 run별로 옮겼다. GPU 초기화는 D에서만 수행하고 C는 검증된 출력 경로로 탐지를 우회한다.
부모의 실제 indirect import/라이브러리 로딩 상태는 각 `parent.json`에 있다.

screening: C 3프레임5.355초(평균1.785), D 5.686초(평균1.895).
확인 순서: C1→D1→D2→C2→C3→D3.

| 구간/조건 |3프레임 계산+검산 median|MAD|min–max|process wall median|
|---|---:|---:|---:|---:|
| 무풍 C |5.473초|0.124초|5.349–5.792초|14.025초|
| 무풍 D |5.582초|0.131초|5.385–5.712초|14.774초|
| 바람 R64 |30.641초|0.074초|30.561–30.716초|39.143초|
| 바람 M1 |25.038초|0.067초|24.912–25.105초|34.077초|

C/D의 D 시간 변화는 C 대비+1.99%, -7.03%, +6.80%로 일관되지 않다.
C/D가 모두 기존1.8초대에 가까웠으므로 추가 B/A는 조건 불충족으로 생략했다.
A의 보존된 코드·native library는 source 대조에만 사용했으며 A를 실행했다고 보고하지 않는다.
바람 순서는 R64_1→M1_1→M1_2→R64_2→R64_3→M1_3이다.

## 공통 경로 대조

- `source_comparison.json`, `common_path.diff`: Newmark retry, Gauss retry, GMRES,
  cuDSS, audit, 조건 제어 kernel과 기존4개 최적화 코드 hash가 이전과 동일하다.
  stepper 차이는 기존 MixedLinear 선택 hook이며 R64에서는 None으로 기존 FP64 호출을 그대로 capture한다.
- 별도 실행의 실제 imported 파일과 SHA는 `inspection/current/worker_audit.json`.
  R64에서 `wind3dgs_low`/`resident_precision_v3`는 import되지 않았고 mixed_strategy=NoneType이다.
- mesh1813 nodes/384 triangles, free DOF5292, mass nnz86058, P nnz601506.
  volume 구적 shape384×36. ids/G/H/weights의 dtype/shape/hash와 NPZ를 보존했다.
  master u/ul/v/vl/RHS/delta는 FP64. 실제 force Graph block256, grid54/9/1을 조회했다.
  conditional body 목록은 생성 중 포착한 집합이며 body별 solver 소유권을 중복 없이 구분한 kernel count는 아니다.
- Newmark·GMRES·cuDSS·audit는 기존 Graph 경로를 유지한다. no-graph로 바뀌었다는 증거는 없다.
  별도 observer에서 준비 중 ScopedCapture15회, 이후 매 프레임 capture0회였다.
  프레임마다 Graph 제출130회(기존64 Newmark+64 audit+2 frame/aero),
  명시 synchronize_device5회, `.numpy()` readback10회가 원래 계산+검산 함수 안에서 관측됐다.
  GPU 상태 저장용 readback은 그 밖에도 있어 전체 observer 합계와 구분한다.
- Graph 내부 실제 force/HVP/cuDSS/line-search kernel 실행 횟수는 Nsight report 실패로 unavailable이다.
  host 함수 호출 수를 GPU 내부 반복 횟수로 치환하지 않았다. GMRES/rebuild/retry는 원래 device counter다.
- 기록은 동일한 scene 프레임 요약 JSONL과 필수 NPZ/audit chunk이다. v3 frozen-linear
  full/summary trace harness를 실행한 것이 아니며 누적 대량 linear trace 복사는 없다.
  부모는 subprocess.Popen으로 새 Python worker를 실행하며 stdout pipe를 읽어 파일에 저장한다.
  fork로 CUDA 상태를 worker에 상속하는 Python multiprocessing 경로가 아니다.
- 실제 worker 인자/PID는 telemetry, parent PID/명령은 run.json에 있다.
  PYTHONPATH/CUDSS_LIBRARY_PATH/LD_PRELOAD/WARP_CACHE_PATH는 원래 controller 코드로 설정한다.
  이번 진단의 CUDA_LAUNCH_BLOCKING 등 CUDA debug 동기화 변수는 부모 환경에서 설정되지 않았다.
  과거 느린 실행은 이미 종료돼 당시 사용자 shell/worker 환경변수 전체를 조회하지 못했다.
  따라서 이번 환경변수 관측으로 과거 debug 설정 차이를 배제하지 않는다.
  native cuDSS/shim hash는 이전 runtime과 동일하며 실제 버전은 cuDSS0.7.1이다.
- CUDA runtime12090/driver API13000, Warp1.17.0, GTX1080Ti sm61/28SM,
  Ryzen5800X, WSL2 환경이었다. `worker_audit.json`의 environment와 실제 library 경로를 따른다.

## 타이머와 계측 한계

주지표는 원래 `NewmarkRetrySequence.run_frame`의 동일 완료 경계 `compute_audit_s`이다.
초기 GPU 동기화 뒤 시작하여, 기본 시도·실패 시도·Gauss 복구·독립 검산 및 기존 결과 readback까지 포함한다.
종료 후 별도로 추가 동기화를 넣지 않았고, 모든 커널 뒤 동기화를 추가하지 않았다.
원래 함수 원문은 `timer_and_control_source.json`에 보존한다.

setup_s는 모델 전처리 뒤 시작하는 기존 worker의 GPU 준비 타이머로 JIT/capture 등을 포함한다.
CPU 모델 준비/프로세스 import는 외부 process wall에 포함된다. JIT 개별 시간은 실행 로그에 있다.
instantiate 단독 시간과 전체 전송/IPC를 완전히 분해한 값은 unavailable이다.
observer의 raw 키 `capture_exit_includes_instantiate`는 실제로 ScopedCapture.__exit__ wrapper 시간이며
실제 instantiate 시간을 포괄/분리 측정한 값으로 해석하면 안 된다(`profiler_status.json`).

save_s는 기존 chunk 저장 경계 타이머다. 종료 checkpoint/close/report까지 외부 process wall에 포함한다.
성능용 run에는 observer/profiler를 넣지 않았다. observer의 readback·동기화 시간은 측정된 원래
호출의 경과값이지만 계산+검산과 중첩하므로 단순 합산/차감하지 않는다. GPU event는 사용하지 않았다.
GPU telemetry는1초 간격의 clock/사용률/온도/전력/VRAM/제한 사유와 부모·worker CPU 사용률이다.
초기 CPU 표본은 이전값이 없어 null이며, 준비/저장까지 포함한 범위 요약을 계산 전용 통계로 해석하지 않는다.

## 원인 확정 수준과 종료

| 가설 | 관측/판정 |
|---|---|
| M1 정밀도가 무풍을 느리게 함 | 해당 구간은 R64이고 mixed 모듈도 미로딩. 지지하지 않음 |
| 부모 CUDA 초기화만으로2.5배 저하 | C/D 교대 결과 지지하지 않음. 별도 probe에서 primary context도 비활성 |
| 공통 경로가 no-graph로 변경 | source/실제 Graph 재사용 관측으로 지지하지 않음 |
| 반복/재시도 증가 | 무풍192 GMRES·2 rebuild·0 retry로 동일 |
| 과거 환경·동시 부하·scheduling 차이 | 가능성만 남음. 당시 연속 telemetry가 없어 특정 원인 확정 불가 |

원인을 확인하지 못했으므로 생산 경로를 추측으로 수정하지 않았다. 새 변경은 bounded 진단/집계 도구뿐이다.
5070 대응 변경으로 공통 no-graph default가 생겼다고 보고하지 않는다.
이번 바람 가속률은 실제 쌍의 비율이며 과거 무풍 저하율로 나눈 가상 가속률이 아니다.
후속은 지연이 다시 나타날 때 당시 환경과 같은 짧은 checkpoint의 동시 관측이 필요하다.
이 결과로 장시간 바람/HL01 또는 전체 FP32 개발을 재개하지 않는다.

## 파일

- `runs.csv`, `frames.csv`, `pairs.csv`, `summary.json`: 일반 실행 원시 시간·반복과 집계.
- `runs/<label>/`: 실제 로그,telemetry,frame JSONL,checkpoint/NPZ,audit,입력/소스 manifest.
- `inspection/`: 별도 profiler 오류·observer 결과·실제 전처리 배열. 일반 시간 통계 제외.
- `runtime_hashes.json`, `source_comparison.json`, `common_path.diff`: 소스/native 대조.
- `parent_*probe.json`: 별도 부모 context 조회. `preserved_*`: 기존 결과 보존 검증.
- `changes.diff`, `tools/`, `reproduce.md`: 이번 최소 도구 변경과 재현.
- 첫 `C_screen`은 controller adapter의 문자열 대상 개수 assertion에서 계산 전에 실패했다.
  해당 결과를 보존하고 `C_screen_fixed`만 실제 screening에 사용했다. 수치 실패가 아니다.
