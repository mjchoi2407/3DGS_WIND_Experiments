# FP64 hi/lo 병목 분리 진단 — 준비와 장치 확인

2026-09-15. 기존 실행 스크립트에 별도 `--profile` 진입점을 추가했다.
일반 실행과 프로파일러 실행 시간을 섞지 않으며 수식/전처리/dt/검산 기준은 유지한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_teacher_precision_profile.sh
```

기본은 완료된 `newmark_dt_fixed_bend500_v1/reference_rectangle`의 preload checkpoint에서
wind 첫1프레임(1/60초, 기본64substep)을 동일하게3회 독립 실행한 뒤 별도 Nsight Systems → 상위 최대3개 커널 Nsight Compute 실행이다.
현행 실패 시 Gauss6차8분할 정책을 보존하고 실제 적분기/재시도를 기록한다.
`--frames N`, `--source-run <씬root>`, `--out <새폴더>`, `--prepare-only`, `--spec <문서>`를 지원한다.
`--profile`은 wrapper 첫 인수로 둔다. 기존 본3씬 시뮬레이션은 시작/변경하지 않는다.

## 확인한 결과와 미완료

원본 입력/라이브러리 hash 확인, checkpoint 복사, 코드 동결, 커널 대응 목록 생성 및
장치/도구 확인을 실행했다. 현재 환경은 **GTX 1080 Ti**, 요청 장치는 **RTX 5070**이어서
`blocked_device`로 종료했다. 일반 반복0회, GPU 커널 측정0회이며 빈 CSV에 추정치를 넣지 않았다.
Nsight Systems2024.5.1, Nsight Compute2024.3.2 설치 확인만 완료했다.
Systems environment 검사에서 CPU process-tree 가능/system-wide 실패가 출력됐으며 원문을 보존했다.
이 결과만으로 RTX 5070 또는 GPU CUDA tracing 지원/실패를 판정하지 않는다.

Nsight Systems 뒤 누적 시간이 큰 상위 최대3개 커널을 자동 선정해 Nsight Compute도 실행한다.
각 커널은 동일 checkpoint의 별도 프로세스에서 첫 호출1개만 표본 측정하며 일반 실행 시간과 분리한다.
`selected_kernels.json`, `ncu_topN.ncu-rep`, `ncu_topN.csv`, `ncu_status.json`에 선정/측정/오류를 저장한다.
도구 미설치·권한·지원·이름 대응 오류는 원문으로 남기고 기존 결과를 보존한다. 자동 설치는 하지 않는다.
현재 GPU capture는 미실행이며 CPU parser/선정/오류 보존 테스트3개 통과다.

FP64/FP32 고정 작업량 비교는 **미구현·미측정**이다. 현행 명령은 두 프로파일러 수집 시도 뒤
`awaiting_fixed_work_comparison`으로 끝나며 NCU 자체의 성공 여부는 `ncu_status.json`에서 확인한다.
첨부 `teacher_precision_profiling_spec`는 확인하지 못했고 채팅에 붙인 조건을 반영했다.

실제 환경 확인 원본:
`artifacts/runs/teacher_timestep_search/precision_profile_20260915_v1`.
이 폴더의 `commands.jsonl`, `gpu.log`, `nsys_environment.log`, `status.json`이 환경 확인 근거다.
`ordinary.csv`/`fixed_work.csv`는 미측정 상태에서는 header만 있고 값은 없다.
`runtime`, `input`, `input_source_hashes.json`, `kernel_source_map.csv`에 코드·입력을 보존한다.
후속 harness는 새 결과의 `reproduce.json`에 재현 명령/worker 환경도 저장한다.
사용자가 RTX 5070 서브컴에서 직접 실행하기로 했으며 추가 실행은 하지 않았다.
현재 원본은 준비/도구 조회이며 solver 시간 비교가 아니다.

서브컴 `artifacts/runs/sub_pc/`의 기존 결과가 존재함은 확인했으나 새 프로파일 결과나
원격 RTX 5070 장치를 조회/실행한 것은 아니다. 기존 시뮬레이션 성능을 이번 측정으로 대체하지 않는다.
[타이머·정밀도·미구현 경계](../../../../code/docs/teacher_precision_profiling.md).
