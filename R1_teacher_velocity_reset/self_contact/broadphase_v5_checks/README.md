# BVH v5 재현 근거

2026-09-22 사용자 유휴 확인을 이어받아 같은 GTX1080Ti에서 제한 측정했다.
판정·한계는 [BVH 개선 보고](../broadphase_v5.md), 정확한 수치·hash는 [summary.json](summary.json)이 소유한다.
`comparison.json`은 같은 실행기에서 v4 대조와 분리 경로를 순서 교대 측정한 원본이다.
`strength.json`은 동결v5의6사례 GPU/CPU 대조, `smoke/`는 동결v5의 세 씬 초기 프레임 검증이다.
`suite.json`과 `manifest.json`은 본 시뮬레이션용 입력/native/소스247개를 동결한다.

대형 원본은 다음 ignored run에 보존한다. 삭제하거나 재사용해 덮어쓰지 않는다.

- `experiments/artifacts/runs/p3_self_contact/broadphase_v4_profile`: 변경 전 세부 단계 진단·소스 snapshot.
- `experiments/artifacts/runs/p3_self_contact/broadphase_split_prototype`: 초기 분리 시제품 진단·소스 snapshot.
- `experiments/artifacts/runs/p3_self_contact/broadphase_v5_comparison`: 통제 비교의 소스·원시 상태·139회귀 XML.
- `experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5`: 동결 실행 코드·입력·native·smoke 상태/로그.
- `experiments/artifacts/runs/p3_self_contact/gpu_strength_v5`:6개 접촉 사례의 원시 상태·GPU/CPU 대조.

workspace 루트에서 수행한 진단/측정 명령의 재현형이다. 같은 출력이 이미 있으면 새 `--out`이 필요하다.
첫 진단은 해당 run의 runtime snapshot, 최종 비교는 `manual_v5/runtime`의 동일 소스 hash를 사용한다.

```bash
export PYTHONPATH=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5/runtime
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
contact_native="$PWD/experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5/native"
export CUDSS_LIBRARY_PATH="$contact_native/libcudss.so.0"
export LD_PRELOAD="$contact_native/libcudss_workspace.so"
timeout 600 .venv/bin/python -u -m wind3dgs.evaluation.p3_gpu_contact_broadphase_benchmark \
  --scenes experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4 \
  --out experiments/artifacts/runs/p3_self_contact/broadphase_v5_comparison \
  --gpu-idle-confirmed --compare --repeats 3
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_validation.sh \
  --out experiments/artifacts/runs/p3_self_contact/gpu_strength_v5
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action smoke
```

실제 최종 비교 당시 `PYTHONPATH=code`, native는 보존v4를 사용했다. 집계 때 현재 code·
측정 runtime·동결v5 소스247개의 hash 일치와 v4/v5의 native·접촉 정책·세 씬 입력 byte 일치를
확인했다. v4 공통 teacher source는 `gpu_shell_contact.py`의 orchestration 이외에 동일하다.
새 benchmark wrapper는 v5 동결 코드와 새 출력 경로를 사용한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_broadphase_performance.sh --gpu-idle-confirmed
```

검증한 회귀 모듈 목록과 명령은 다음과 같다. GPU 실행 후 **139 passed, skip0, fail0,25.47초**였다.

```bash
PYTHONPATH=code WIND3DGS_TEST_DEVICE=cuda:0 timeout 300 .venv/bin/python -m pytest -x -q \
  --junitxml=experiments/artifacts/runs/p3_self_contact/broadphase_v5_comparison/regression.xml \
  code/tests/test_gpu_contact_broadphase.py code/tests/test_gpu_contact_frozen_benchmark.py \
  code/tests/test_metric_geometry_certificate.py code/tests/test_resident_metric_certificate.py \
  code/tests/test_resident_contact_frame.py code/tests/test_gpu_shell_contact.py \
  code/tests/test_resident_contact_stepper.py code/tests/test_resident_stepper_gpu.py \
  code/tests/test_resident_audit.py code/tests/test_resident_current_first.py \
  code/tests/test_resident_parallel_reductions.py code/tests/test_resident_preconditioner_reuse.py \
  code/tests/test_resident_accepted_evaluation.py code/tests/test_teacher_gpu_contact_scene_suite.py \
  code/tests/test_teacher_self_contact_scene_suite.py code/tests/test_p3_collision_proxy.py \
  code/tests/test_p3_shell_contact.py code/tests/test_teacher_p3_shell_dynamics.py \
  code/tests/test_gravity_wrinkles.py code/tests/test_local_geometry_certificate.py
PYTHONPATH=code .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_broadphase_validation.py \
  --old experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v4 \
  --new experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5 \
  --benchmark experiments/artifacts/runs/p3_self_contact/broadphase_v5_comparison \
  --samples experiments/artifacts/runs/p3_self_contact/gpu_strength_v5 \
  --out experiments/R1_teacher_velocity_reset/self_contact/broadphase_v5_checks
```

측정54프레임2,472단계는 예열 제외이며, 별도smoke384단계와 접촉 강도56단계를 혼합하지 않는다.
전체 본 궤적, 접촉 OFF 추가 비용 재측정과 연속 GPU telemetry는 이번 범위에 포함하지 않았다.
실행 중 단일 조회는SM1911MHz/메모리5005MHz/온도62°C였다. 외부 부하0을 증명하지 않는다.
서브컴에서 해당 접촉 run은 발견되지 않았다. 외부 fetch·다운로드·commit·push는 하지 않았다.
