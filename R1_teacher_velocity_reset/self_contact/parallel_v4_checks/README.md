# 병렬 실행 v4의 기능 검증 snapshot

2026-09-22. [집계](summary.json)의6프레임384단계와 [국소6사례](strength_report.json)의56단계는
모두 통과했다. 본 전체 궤적은 미실행이다. [v3 상태·추가 메모리](comparison.json),
[측정 도구 기능 검사](measurement_tool_check.json)는 속도 채택 근거와 구분한다.

`scenes_manifest.json`과 `scenes_suite.json`에 source244개·입력/native를 동결했다.
원시 씬 상태와 runtime은 `artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4`,
국소 raw/source는 `artifacts/runs/p3_self_contact/gpu_strength_v4`에 보존한다.
국소 NPZ는 hash 대조 후 이 snapshot에도 복사했다. 기존v3 근거를 덮어쓰지 않았다.

관련121개 검사(skip0/fail0)는 [v2 근거](../refined_gpu_checks/README.md#관련-회귀-검사)의
같은18개 모듈 선택으로 실행했다. 이번 native 경로는 `three_scenes_gpu_bend500_manual_v3/native`이며
v4와 byte/hash가 같다. 새8개 검사는 `test_gpu_shell_contact.py`에 추가됐고 과거 검사를 합산하지 않는다.

생성 명령(workspace 루트, 이미 생성된 결과이므로 다시 실행하려면 새 출력 지정):

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action prepare
timeout 240 bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_validation.sh \
  --out experiments/artifacts/runs/p3_self_contact/gpu_strength_v4
timeout 240 bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action smoke
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/wind3dgs-contact-mpl .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_gpu_checks.py \
  --scenes experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4 \
  --samples experiments/artifacts/runs/p3_self_contact/gpu_strength_v4 \
  --out experiments/R1_teacher_velocity_reset/self_contact/parallel_v4_checks
PYTHONPATH=code OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_parallel_validation.py \
  --old experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v3 \
  --new experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4 \
  --out experiments/R1_teacher_velocity_reset/self_contact/parallel_v4_checks/comparison.json
```

측정 도구의 제한 기능 검사:

```bash
contact_run=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4
PYTHONPATH="$contact_run/runtime" CUDSS_LIBRARY_PATH="$contact_run/native/libcudss.so.0" \
LD_PRELOAD="$contact_run/native/libcudss_workspace.so" \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1 \
timeout 90 .venv/bin/python experiments/R1_teacher_velocity_reset/self_contact/check_parallel_measurement.py \
  --out experiments/R1_teacher_velocity_reset/self_contact/parallel_v4_checks/measurement_tool_check.json
```

해석과 남은 한계는 [v4 보고](../parallel_v4.md)를 따른다.
