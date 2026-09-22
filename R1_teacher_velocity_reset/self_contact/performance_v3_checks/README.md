# 성능 후보v3의 기능 검증 snapshot

확인일2026-09-22. 최종 실행 코드의 동결 manifest는 `scenes_manifest.json`, 설정은
`scenes_suite.json`이다. 원시 runtime/native와 큰 씬 NPZ는
`artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v3`에 보존했다.
본 세 씬 `outputs/`는 미생성이다.

- [검산 집계](summary.json):6프레임384단계 모두 통과. 장기 궤적 미실행.
- [국소6사례](strength_report.json):56단계 GPU/CPU 대조 전부 통과, NPZ의 hash 검증 후 복사.
- [이전 상태·메모리 대조](comparison.json):같은 v2 저장 상태와의 차이 및 공유 GPU의 부분 측정 판정.
- `shared_gpu_prototype_report.json`은 최종 코드보다 앞선 중간 후보의 **비채택 성능 기록**이다.

관련113개 테스트(skip0/fail0)는 `refined_gpu_checks/README.md`의 같은18개 모듈 선택으로
최종 코드에서 실행했다. native 경로만 `three_scenes_gpu_bend500_v2/native`로 지정했다.
새 regression은 기존 테스트 모듈에 추가됐으며, 새113개와 과거106개를 합산하지 않는다.

생성 명령(workspace 루트):

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action prepare
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action smoke
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_validation.sh \
  --out experiments/artifacts/runs/p3_self_contact/gpu_strength_v3
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/wind3dgs-contact-mpl .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_gpu_checks.py \
  --scenes experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v3 \
  --samples experiments/artifacts/runs/p3_self_contact/gpu_strength_v3 \
  --out experiments/R1_teacher_velocity_reset/self_contact/performance_v3_checks
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  experiments/R1_teacher_velocity_reset/self_contact/summarize_performance_validation.py \
  --old experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v2 \
  --new experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v3 \
  --shared experiments/artifacts/runs/p3_self_contact/performance_frames_v3 \
  --out experiments/R1_teacher_velocity_reset/self_contact/performance_v3_checks/comparison.json
```

이미 생성된 출력이므로 재실행 시 새 경로를 지정한다. 승인 조건·성능 해석은
[성능 점검](../performance.md)을 따른다. 이 검증의 시간은 공유 GPU 부하에서 측정되어
가속 배수의 근거가 아니며 GPU 단독 재측정은 사용자 실행 대기다.
