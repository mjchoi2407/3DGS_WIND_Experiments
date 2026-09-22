# GPU 유휴 조건 재측정

2026-09-22 사용자 확인: 다른 GPU 작업을 종료한 상태에서 새로 측정한다.
과거v1/v2/v3/v4 공유 부하의 시간은 이 비교의 속도 기준으로 재사용하지 않는다.
기존 실행·실패 원본은 보존한다. 본 시뮬레이션 대신 같은 초기 상태의 제한 프레임만 반복한다.

실행 중 GPU 사용률·클럭·전력·온도는 `gpu_telemetry.csv`에2초 간격으로 기록한다.
시작 전 표시는 사용률22~26%, SM607MHz/메모리405MHz/약21W였다.
사용자 유휴 확인과 드라이버의 비영 사용률을 구분하며, 완전한 외부 부하0의 계측 증명은 아니다.
측정과 상태 검산을 완료했고 telemetry 프로세스도 종료했다. 최종 해석은
[유휴 조건 보고](../idle_performance.md), 상세 중앙값·변동·분모는 [집계](summary.json)를 따른다.

- [통제 ON/OFF/재사용/병렬 비교](controlled_report.json):같은 실행기·예열1회·측정3회·순서 회전.
- [실제 동결v1/v4](frozen_report.json):소스 수정 없이 별도 프로세스·6조건에서 순서 교대.
- `frozen/`의12개 report는 각 원본 source hash·graph inventory·예열/측정·상태 hash를 보존한다.
- 대형 원시 상태·로그·동결 측정 소스는 아래 ignored run 경로에 보존한다.
- 통제 측정99프레임4,860단계·동결36프레임2,304단계 모두 승인됐다. 예열/전체 궤적과 구분한다.

workspace 루트에서 실제 실행한 명령:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_performance.sh --gpu-idle-confirmed
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1 \
timeout 600 .venv/bin/python -u -m wind3dgs.evaluation.p3_gpu_contact_frozen_benchmark \
  --v1 experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v1 \
  --v4 experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4 \
  --out experiments/artifacts/runs/p3_self_contact/performance_frozen_v1_v4_idle \
  --gpu-idle-confirmed
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_idle_performance.py \
  --controlled experiments/artifacts/runs/p3_self_contact/performance_idle_v4 \
  --frozen experiments/artifacts/runs/p3_self_contact/performance_frozen_v1_v4_idle \
  --out experiments/R1_teacher_velocity_reset/self_contact/idle_v4_checks
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q \
  code/tests/test_gpu_contact_frozen_benchmark.py
```

마지막 검사는4 passed in0.10s다. 기존v4의121개 수치 검사는 직전 결과이고 이번에 합산하지 않는다.
같은 출력은 덮어쓸 수 없으므로 재측정은 새 `--out`을 지정한다.
동결 측정기의 실행 당시 source는 `performance_frozen_v1_v4_idle/benchmark_source.py`에 hash로 보존했다.

Telemetry는 `nvidia-smi --query-gpu=timestamp,name,driver_version,utilization.gpu,utilization.memory,memory.used,clocks.sm,clocks.mem,power.draw,temperature.gpu --format=csv -l 2 -f <새 CSV>`로
이번 측정 동안만 수집했다. 자체 기록 프로세스만 정상 종료했고 다른 GPU 작업을 중단하지 않았다.
