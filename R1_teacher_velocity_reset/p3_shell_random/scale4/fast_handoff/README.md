# 개선 경로를 사용한 남은4배 바람 검증 준비

## 현재 상태

2026-09-10 사용자가 **기존 계산을 보존하고 개선 경로로 이어가기**를 선택했다.
**2026-09-11 사용자 실행의116/116 task 종료와 기준 미달 결과를 확인했다.**
준비 당시 분모는 기존1,325 frame 보존과 신규313 frame/74,240 interval 전진이다.
연결 진단·checkpoint 재시작·검산·비교 비용은 이 전진 분모와 별개다.

## 2026-09-11 인수인계 시 저장 결과

후속 [원본 속도 비교·진동 성분 진단](evidence/diagnosis_20260911/README.md): 선택 frame의
원본 비교가 저장값과 일치했다. 차이는 주로 수직 방향 진동에 있으며 정확한 모드 원인은 미확정이다.
필수19/20 통과와 학습 발행 보류를 유지한다. 아래 내용은 인계 당시 확인 범위다.

기본 `scale4_fast_continuation_v2`의 `status.json`은 완료116/116, `summary.json`은 `기준 미달`이다.
Summary 파일의 로컬 수정 시각은2026-09-11 02:26:02 KST이며 별도의 실행 종료 시각 필드로 해석하지 않는다.

- 최종 판정에 쓰는 필수20개 비교 중19개 통과,1개 미달이다.
- 미달은 `compare_space16_32_s256_reset66`: 1.1초에서 속도를0으로 만든 분기의 n16→32 공간 비교다.
  변위 상대 상한0.022088%, reset 후 변위 변화0.023411%는 통과하나 **속도1.855258%가1% 기준을 넘는다**.
  속도 절대 RMS 상한은0.000993330m/s, 기준 peak 하한은0.053541309m/s다.
- Coarse n8→16 비교 네 실패는 기존 계획대로 별도 보존한다. 전체24개 중19개 통과이며 "필수19/20"과 분모를 혼동하지 않는다.
- 선택 상태 구적 진단은 저장 결과상 통과했다. 전체 상태 구적 인증을 의미하지 않는다.

[인계 evidence](evidence/handoff_20260911/)에 summary/status와 확인 범위·원본 metadata hash를 보존했다.
이번 인계에서는24개 비교 결과와 summary의 값/판정 일치, 구적 결과의 summary 일치를 확인했다.
전체 원본 NPZ/source chain 재검증·독립 물리 재계산은 수행하지 않았다. 실패 원인 분석·보완 선택과 최종 검토가 다음 작업이다.
116개 작업의 종료를 물리 수렴 통과, R1 전체 채택 또는 학습 적격성으로 올리지 않는다.

## 직접 실행

Workspace root에서:

```bash
bash experiments/R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/run_remaining.sh
```

기본 결과 폴더는 `experiments/artifacts/runs/teacher_p3_shell_random/scale4_fast_continuation_v2`다.
이미 준비된 동결 runtime과 plan으로 실행하므로 이후 workspace 코드 편집이 이번 계산에 섞이지 않는다.
처음에는 저장 원본의 hash를 확인한다. 원본 확인·계산·검산 진행 수와 활성 task를 터미널에 표시하며,
변화가 없어도30초마다 상태를 출력한다. Task 수의 비율은 남은 시간 비율이 아니다.

상태만 보거나 계산을 중단할 때:

```bash
bash experiments/R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/run_remaining.sh --status-only
bash experiments/R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/run_remaining.sh --stop
```

**Ctrl+C는 진행도 표시만 닫는다. 계산까지 멈추려면 `--stop`을 사용한다.**
같은 실행 명령으로 다시 연결하거나 마지막 확정 frame부터 이어간다.
미저장 frame만 다시 계산하며, 기존 파일을 삭제하거나 덮어쓰지 않는다.
검산·비교 도중 중단된 경우 그 task는 다시 실행한다.

- `status.json`: 완료 task 수, 활성 task, 오류/완료 판정.
- `scheduler.log`, `logs/`: supervisor 및 task별 상세 로그. 오류 로그에 원본 경로를 연결한다.
- `views/`: 구간별 producer와 원본 hash를 잇는 index, 새 frame, 연결 대조·재시작·검산 결과.
- `results/`, `summary.json`: 수렴 비교·선택 상태 구적 및 최종 보완 판정.
- `plan.json`, `runtime/manifest.json`: 실행 계획과 동결 source identity.

완료 후 `summary.json`의 결과를 알려주면 원본 근거와 함께 검토한다.
종료 코드0은 이번 보완 검증 통과,2는 계산을 마쳤으나 기준 미달,1은 실행/검산 오류다.
기준 미달 결과도 보존하며 허용오차를 자동 완화하거나 무한 재시도하지 않는다.

## 실행 범위·병렬 처리·보존 방식

기존7조건 × natural/세 reset의28 view와6비교 ×4분기, n32 선택 상태 구적을 연결했다.
116개 task 중 이미 완료된 계산은 원본 확인 후 건너뛰고, 완료된 원식 검산도 원본/source/검산 hash가
일치할 때 재사용한다. 수렴 비교는 새 view에 연결해 다시 수행한다.
Coarse n8→16의 네 실패는 별도 보존하며, 선언된 나머지20개 비교와 구적의1% 기준을 최종 보완 판정에 사용한다.

독립 원본 확인·CPU 비교 작업은 기본2개, 같은 GPU를 쓰는 작업은 기본1개까지 실행한다.
의존성이 없는 CPU 작업과 GPU 작업은 겹칠 수 있다. 필요하면 `--cpu-jobs 1`로 CPU 동시 작업 수를 줄이거나,
`--gpu-jobs 2`로 GPU 작업 두 개를 허용할 수 있지만 더 빠르다는 보장은 없다. 이번 묶음은 속도 벤치마크가 아니다.

원래 chunk schema와 strict source 검사에 예외를 넣지 않고 별도
`wind3dgs.p3_shell_segmented_continuation.v1` view를 사용한다.
기존 config/report/source ZIP과 frame identity는 원본에 연결하고, 새 frame의 producer는 동결 runtime과
`hvp_graph` 실행 환경으로 명시한다. 물리 core 및 `wind_program`/`advance_frame`/`verify_frame`의 식이
일치하는지 확인하며, 각 연결 상태에서 기존/개선 풀이의 실제 외력 한 substep을 대조한다.
이 짧은 진단을 전체 궤적 동등성 증명으로 해석하지 않는다. 새/혼합 구간은 원식과 frame 경계 연속성을 검산한다.
재시작 정확 일치 검사는 재생 대상 frame을 만든 계산 경로·device를 사용한다.

동일 단일 producer를 요구하는 기존 원본 검산·비교 명령을 변경하지 않았다.
새 묶음은 이력이 명시된 개발 검증이며 R1 전체/학습 적격성 채택이나 추가 학습데이터 발행이 아니다.
원래 자료의 위치가 바뀌거나 파일이 변경되면 hash 확인에서 중단하므로 기존 ignored 원본도 유지해야 한다.

## 보존형 이어하기 검증

- CPU와 실제 CUDA 각각 n4/sub8의4 frame natural 및2 frame reset 묶음에서10개 task 전체가 통과했다.
- 기존2 frame 보존 → 새1 frame 계산 → 저장 후 재개 → 마지막 frame 계산을 시험했다.
  원본 파일은 그대로이며, 두 연결 지점의 모양·속도·시간은 정확히 일치했다.
  연속 기준 실행과의 모양·속도 차이도 기존 CPU/GPU 대조 허용오차 안이었다.
- Reset의 위치 보존/v0/제거 kinetic, 무개입 재시작의 배열·진단 정확 일치, 원식·기하 검산,
  비교/선택 구적/최종 요약, 원본 변조 거부를 확인했다.
- 종료 요청과 새 child 생성이 겹치는 경합을 막도록 종료 신호를 공유했고, 실제 child 종료 시험을 통과했다.
  이 제어 보완 뒤 CPU 전체 흐름을 재검증했다. CUDA 전체 흐름의 물리 모듈은 최종본과 동일하다.
- 실제 기존22개 원본의 설정·물리 core·frame 식을 대조했다. 준비된 plan/source/metadata hash와 DAG도 확인했다.
  큰 NPZ 전체 hash 확인은 사용자 실행의 adopt task에서 수행한다.
- 미실행 준비본v1은 보존하고 최종 제어기를 동결한v2를 기본 대상으로 삼았다.

[준비·검증 근거와 source archive](evidence/segmented_v2/)에 계획, preflight, CPU/CUDA 결과와 runtime을 보존했다.
전체 흐름 재현 검사는 `check_remaining.py`에 있으며 먼저 동일 n4/sub8/4 frame reference를 만든 뒤 실행한다.

## 공통 구현과 검증

- CPU 반복 풀이를 유지하는 실행 factory를 추가했다. CUDA에서는 HVP 전용 연산과 graph를 사용한다.
- 계산 경로·실제 graph 사용 여부·CPU 선형 풀이를 환경에 기록하고 factory/fast kernel도 source snapshot에 넣는다.
- Parent 분기와 일반 수렴 비교의 경로 불일치는 거부한다. 검산기는 원래 물리식을 유지한다.
  기존 동결 원본을 현재 소스로 생성한 것처럼 취급하지 않는다.
- CPU 신규2개 검사: 정·역 대각선에서 자연 응답과 속도 초기화 후 응답을 기준 풀이와 대조하고 원식을 검산했다.
  기존 랜덤 바람/비교 회귀10개도 통과했다.
- 실제 CUDA n4/sub8/4배 바람/역 대각선2 frame smoke에서 graph 경로와 HVP 실행을 확인했다.
  별도 CPU 검산으로16 interval 전부 통과했다. Source 동결과 환경 기록 불일치 거부도 확인했다.
- V1은 초기 연결 확인이며 V2는 환경 일치 검사를 추가한 최종 실행기 결과다. 이 작은 검증을 n32 전체 검증으로 확대하지 않는다.

Raw: `experiments/artifacts/runs/teacher_p3_shell_random/20260910_fast_cli_smoke_v2`.
검산: 같은 상위의 `verification/20260910_fast_cli_smoke_v2_cpu.json`.
설정·보고서·source ZIP과 검산은 [evidence](evidence/)에 보존했다.

```bash
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 WARP_CACHE_PATH=code/outputs/warp-cache .venv/bin/python -m unittest discover -s code/tests -p 'test_teacher_p3_shell_execution.py'
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m unittest discover -s code/tests -p 'test_teacher_p3_shell_random*.py'
bash code/scripts/check_teacher_p3_shell_random.sh --compute-backend hvp_graph --resolution 4 --substeps 8 --end-frame 2 --wind-scale 4 --diagonal backward --device cuda:0 --output experiments/artifacts/runs/teacher_p3_shell_random/새로운_smoke_폴더
```

## 인계 전 기존 중단 상태

기존 n32 역방향 natural88 frame, sub256 reset18의23 frame,
sub128 reset42의26 frame을 포함해 이미 보고된 prefix를 유지한다.
기존 결과 보존이라는 사용자 선택을 구현했으며, 나머지 조건·분모는 동결 plan과 preflight를 따른다.
