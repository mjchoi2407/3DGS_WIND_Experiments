# 정밀 기하 v2의 완료 검증 근거

확인일2026-09-22. 본 폴더는 전체 시뮬레이션 시작 **전** 완료한 개발 검증 snapshot이다.
`summary.json`의 미시작 표시는 이 집계 시점에만 해당한다. 이후 전체 실행 상태는
`artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v2/<shape>/outputs/report.json`을 따른다.

- [국소6사례 보고](strength_report.json):56단계 전부 최종 승인, 원래12개 기하 미인증 flags 보존.
- [세 씬 집계](summary.json):초기3검사와6프레임384단계 통과. 활성 접촉 없는 연결 시험이다.
- [source·입력 manifest](scenes_manifest.json), [실행 설정](scenes_suite.json), [원본 입력](scenes_reference_inputs.json).
- 각 NPZ는 report의 SHA-256과 대조해 복사했다. 대형 씬 상태·실행 당시 Python source·native는 위 ignored run에 보존한다.
- [강도 비교](strength_comparison.png):×는 새 검사의 실패가 아니라 기존 scalar 기하 충분조건의 미인증 지점이다.

## 관련 회귀 검사

같은 source에서 실제 CUDA 검사를 포함해 **106 passed in43.16s, skip0/fail0**를 확인했다.
새 정상 상태 인증, 공간/시간 붕괴·거의 퇴화·비유한 값·용량/깊이 한도 거절,
GPU 프레임 복원,2^40 공통 이동의 hi/lo, 기존 접촉 OFF 및 CPU 경로 회귀를 포함한다.
이 숫자는 아래 선택 모듈 범위이며 저장소 전체 test suite의 실행 주장과 구분한다.

workspace의 `code/`에서 실행한 명령:

```bash
CUDSS_LIBRARY_PATH=../experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v1/native/libcudss.so.0 \
LD_PRELOAD=../experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v1/native/libcudss_workspace.so \
WIND3DGS_TEST_DEVICE=cuda:0 WARP_CACHE_PATH=/tmp/wind3dgs-gpu-contact-cache \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1 \
timeout 300 ../.venv/bin/python -m pytest \
  tests/test_metric_geometry_certificate.py tests/test_resident_metric_certificate.py \
  tests/test_resident_contact_frame.py tests/test_gpu_shell_contact.py \
  tests/test_resident_contact_stepper.py tests/test_resident_stepper_gpu.py tests/test_resident_audit.py \
  tests/test_resident_current_first.py tests/test_resident_parallel_reductions.py \
  tests/test_resident_preconditioner_reuse.py tests/test_resident_accepted_evaluation.py \
  tests/test_teacher_gpu_contact_scene_suite.py tests/test_teacher_self_contact_scene_suite.py \
  tests/test_p3_collision_proxy.py tests/test_p3_shell_contact.py tests/test_teacher_p3_shell_dynamics.py \
  tests/test_gravity_wrinkles.py tests/test_local_geometry_certificate.py -x -q
```

당시 v1 native를 사용했으며 v2 native는 byte/hash가 동일하다. Python 수치 source는
`strength_report.json#source_sha256` 및 `scenes_manifest.json`에 동결했다.
live source가 바뀐 후 과거 source의 검사 완료를 새 코드에 자동 승계하지 않는다.

## 보존 명령

workspace 루트에서 다음 집계를 실행했다. 기존 출력이 있으면 덮어쓰지 않는다.

```bash
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/wind3dgs-contact-mpl .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_gpu_checks.py \
  --scenes experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v2 \
  --samples experiments/artifacts/runs/p3_self_contact/gpu_strength_v2 \
  --out experiments/R1_teacher_velocity_reset/self_contact/refined_gpu_checks
```

수치 해석·한계와 본 실행 스크립트는 [정밀 기하 보고](../refined_geometry.md)를 따른다.
