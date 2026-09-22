# 기존 세 씬에 셀프 컬리전 추가: 실행 준비

## 현재 상태

이 문서는 초기 CPU 실행기와 당시 검증 기록이다. 최종 요청의 **GPU 전 단계 구현·세 씬 실행 스크립트**는
후속 [GPU 실행 안내](gpu.md)를 따른다. 아래 GPU 미완료 설명은 CPU 기준 준비 당시의 범위다.

2026-09-22. 직사각형·손수건·삼각 깃발의 기존 **굽힘1/500 입력**을 그대로 동결했다.
세 씬 초기 검사와 중력/최대풍의 짧은 CPU 연결 검사는 통과했다. 본 시뮬레이션은 미실행이며,
실행 backend는 사용자가 명시해야 한다. **GPU 전체 셀프 컬리전은 미구현**이다.
GPU를 요청하면 CPU로 대체하거나 접촉을 끄지 않고 종료 코드2로 중단한다.

실행기: [run_three_scenes.sh](run_three_scenes.sh).
구현 계약: [code 문서](../../../code/docs/p3_self_contact.md#기존-세-씬-실행기).
국소 접촉 샘플·barrier 강도 비교는 [기존 보고서](README.md)를 따른다.

## 동일하게 유지하는 입력과 달라지는 실행

원본: `experiments/artifacts/runs/teacher_timestep_search/newmark_dt_gauss_retry_bend500_v1`.
준비된 새 run: `experiments/artifacts/runs/p3_self_contact/three_scenes_bend500_v1`.
원본의 config·phase plan·메시·forcing·wind는 모두 기존 승인 SHA-256과 대조하고 byte 그대로 복사한다.
Source package의 Python 파일도 새 run의 `runtime/`에 동결한다. 이전 실행의 상태·속도는 가져오지 않는다.

| 항목 | 이번 스크립트 |
| --- | --- |
| 씬 | `reference_rectangle`, `handkerchief`, `triangular_flag` 순차 실행 |
| 형상·고정점·재료·바람·중력 | 기존 입력 유지. 굽힘1/500을 재료에 중복 적용하지 않음 |
| 프리로드 | 접촉 ON, 평면 rest/속도0에서 중력2초: 120프레임 |
| 이후 분기 | 새 preload 최종 u/v/time에서 무풍4초·바람4초를 각각 시작. 속도 reset 없음 |
| 시간 간격 | 60fps, 프레임당64단계, dt=1/3840초 유지 |
| 접촉 시험값 | proxy subdivision3, 최소 간격1mm, 활성 범위10mm, barrier1,000, LBVH |
| 정밀도·풀이 | CPU FP64 단일 상태, Newmark+rest preconditioner. 기존 GPU hi/lo/current와 다름 |
| 실패 처리 | 자동 Gauss/절반dt 복구 없음. 원래 허용오차 유지, 거절 시 중단 |
| 저장 | 모든 substep 검산 JSON, 프레임 끝 u/v/time·held force NPZ, phase 최종 checkpoint |

접촉 간격은 재료 두께로부터 자동 결정하지 않는다. 계수1,000도 작은 접촉 샘플의 시험값이지,
실장면 최종 calibration이 아니다. Proxy 공간 오차는 매 단계 기록하지만 기본 설정에서 고정 예산을
강제하지 않으므로 정확한 P3 곡면의 전역 비접촉 인증이라고 해석할 수 없다.

기존 plan은 원본 근거로 보존하므로 GPU/backend/current 등 옛 메타데이터도 남아 있다.
**실제 실행의 차이는 `suite.json`과 각 report의 `effective_solver_policy`가 소유한다.**
CPU rest 보조 풀이의 큰 접힘 성능·장기 안정성은 미측정이며 기존 GPU 속도를 기대하면 안 된다.
전체 실행은 씬당38,400단계다. 이 문서를 만들면서 긴 실행을 자동으로 시작하지 않았다.

## 사용법

Workspace root에서 실행한다. 현재 기본 run은 준비·preflight·smoke까지 완료되어 있다.

```bash
# 준비된 실행/검사 상태 확인: 계산하지 않음
bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh --action status

# GPU 단계별 구현 위치 확인: GPU 계산/벤치마크가 아님
bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh --action gpu-readiness

# CPU 기준 본 실행을 선택할 경우에만 실행. 세 씬을 순차 계산한다.
bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh \
  --action run --backend cpu_reference

# GPU 전체 경로 요구: 현재는 명시적으로 중단하며 아무 본 결과도 만들지 않는다.
bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh \
  --action run --backend gpu_resident
```

한 씬만 계산하려면 `--shape handkerchief` 등을 추가한다. 중단·실패한 출력은 자동 재개하지 않는다.
이미 실행/검사한 같은 작업을 다시 호출하면 덮어쓰기를 거절한다. 새 이름으로 준비한 다음 재실행한다.
접촉 설정 변경도 `prepare`에서만 허용하며, `run`에 전달한 변경값을 조용히 무시하지 않는다.

아래는 **새 run에 대한 재현 명령**이다. 기본 action은 `prepare`이며 본 계산을 시작하지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh \
  --action prepare --out experiments/artifacts/runs/p3_self_contact/three_scenes_bend500_reproduction \
  --subdivisions 3 --minimum-distance-m 0.001 --activation-distance-m 0.01 --barrier-stiffness 1000
timeout 180 bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh \
  --action preflight --backend cpu_reference \
  --out experiments/artifacts/runs/p3_self_contact/three_scenes_bend500_reproduction
timeout 180 bash experiments/R1_teacher_velocity_reset/self_contact/run_three_scenes.sh \
  --action smoke --backend cpu_reference --smoke-substeps 1 \
  --out experiments/artifacts/runs/p3_self_contact/three_scenes_bend500_reproduction
```

Wrapper는 TBB/OpenBLAS/OMP thread1과 CPU 프로세스 address-space4GiB 상한을 설정한다.
이 제한은 비용/메모리 문제를 숨겨 완료 처리하지 않는다. `timeout` 중단이나 native crash 뒤 남은
`running` report는 통과가 아니며, 자동 재개 대상도 아니다. 동결 Python/numpy/scipy/ipctk 버전이
현재 환경과 다르면 실행을 거절한다. 패키지 설치 방법은 [API 문서](../../../code/docs/p3_self_contact.md)를 따른다.

## 이번에 실제 수행한 검증

기본 run에 위 prepare/preflight/smoke 명령을 실행했다. 검사는 순차 실행했고 GPU 계산은 하지 않았다.
Preflight는 원본/동결 hash·외력 schema·두 wind 파일의 일치·초기 proxy 간격/퇴화를 검사한다.
세 씬 모두 초기 접촉 에너지·접촉력이0이었다.

Smoke는 각 씬의 **평면 rest에서 별도로** 중력 첫 입력(frame0), 최대 풍속 입력(frame168)을
각각1단계 계산한다. 프리로드 완료 상태에서의 frame168 재생이 아니다. 강한 바람이 실제로 전달되는지
검사하기 위한 독립 진단이며, 실제 본 궤적·접촉 발생·시간 수렴을 검증하지 않는다.

| 씬 | P3 노드 | Proxy 삼각형 | 초기 LBVH 후보 | 중력/최대풍 검산 | 최대 힘 잔차/한도 |
| --- | ---: | ---: | ---: | --- | ---: |
| 직사각형 | 1,813 | 3,456 | 15,217 | 2/2 통과 | 0.008206 |
| 손수건 | 925 | 1,728 | 7,537 | 2/2 통과 | 0.005477 |
| 삼각 깃발 | 703 | 1,296 | 9,940 | 2/2 통과 | 0.004782 |

힘 잔차 비율≤1, 위치 업데이트 오차≤2e-14m, 독립 에너지 ledger 차이≤3e-16+1e-8|balance|J,
국소 metric 비퇴화, 고정점 유지, quadratic 시간 경로 인증을 요구했다. 6단계 모두 flags0이었다.
에너지 ledger 일치는 시간 이산화 에너지 보존/정확도를 뜻하지 않는다.
이 짧은 구간에서 접촉 에너지는0이며, gap11mm는 **하한**이지 정확한 최소 곡면 간격이 아니다.

추적 근거는 [checks/](three_scene_checks/)의 동결 suite·manifest·입력 hash 및 씬별 preflight/smoke report다.
실제 source 파일과 상태 NPZ는 위 ignored run에 보존한다. 실패한 초기 연결 진단은
`three_scenes_bend500_preflight_v1`에 보존하며 본 결과로 사용하지 않는다.
GPU 거절 경로는 종료 코드2와 `outputs/` 미생성을 확인했다.

추가/관련 단위·회귀45개 통과. 새 실행기 검사는11개이며 입력 변조/덮어쓰기/설정 무시 방지,
CPU 자동 대체 금지, 접촉 포함 독립 검산, 시간 경로 거절, 프리로드 실패 시 분기 금지,
두 분기의 초기 u/v/time 일치를 포함한다. 분기 제어 테스트는 모의 step을 쓰며 full 물리 완주가 아니다.

```bash
cd code
TBB_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 timeout 120 ../.venv/bin/python -m pytest \
  tests/test_teacher_self_contact_scene_suite.py tests/test_p3_collision_proxy.py \
  tests/test_p3_shell_contact.py tests/test_teacher_p3_shell_dynamics.py \
  tests/test_gravity_wrinkles.py tests/test_local_geometry_certificate.py -q
```

## CPU 기준 준비 당시의 GPU 목표와 남은 범위

이 CPU 실행기의8단계 정적 점검에서 proxy 보간, LBVH/후보 탐색, VF/EE 거리, barrier 힘/HVP, adjoint,
solver CCD, 시간/공간 검산, 접촉 포함 Newton/Krylov가 모두 CPU다.
기존 GPU shell 솔버·GPU 검산기에 CPU IPC 호출만 붙이는 것으로 완료 처리하지 않는다.

GPU 이식은 후보 버퍼와 overflow 거절, BVH 갱신, VF/EE·힘/HVP, 보폭/시간 CCD,
잔차/상태 승인까지 장치에 유지해야 한다. 매 Newton/HVP의 CPU 배열 왕복과 scalar readback도
검사 대상이다. 고정 위상 준비와 기록 경계는 기존 [GPU 구현 기준](../../../code/docs/gpu_solver_design.md)을 따른다.
GPU FP32/혼합 정밀도의 누락률·최소 간격·힘/HVP·최종 잔차를 CPU 기준과 대조해야 하며,
FP32 입력 저장 시험만으로 GPU FP32 연산을 승인하지 않는다.

후속 GPU 전 단계 구현·실행·graph 전송 검사와 실제 시간은 [GPU 보고](gpu.md)에 확정했다.
실제 세 씬의 큰 접힘/풍하중 완주, barrier/두께 calibration, proxy 공간 수렴,
R1 acceptance와 학습 적격성은 아직 미완료다.
