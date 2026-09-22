# 직사각형112번째 프레임 실패 재현·GPU 절반 간격 복구

## 판정과 범위

2026-09-22, GTX1080Ti. `manual_v8`의 wind111프레임까지 승인된 raw hi/lo에서112번째 프레임
(index111, 바람1.85~1.8666667초)를 독립 재현했다. 최초 실패는60번째 substep의 Newton 첫 선형
풀이 code2였다. 기존 출력·동결 runtime은 수정하지 않았다. 원본·config·모든 코드 hash·상세 검산은
`artifacts/runs/p3_self_contact/frame112_diagnosis_v1/{baseline,cycles6,half,gpu_recovery}/`가 소유한다.

**반복 한도 증가는 실패했고, dt절반은 모든 검산을 통과했다. 이 방식의 실제 GPU 자동 복구도 통과했다.**
기본 구간은 기존64단계, 복구 가능 실패만 같은 프레임을128단계로 한 번 다시 계산한다.
세 씬 장기 완주, RTX5070의 해당 실패 복구, 시간 이산화 수렴·R1/학습 적격성까지 확인한 결과는 아니다.

## 같은 입력 비교

사용자가 기존 GPU 시뮬레이션을 종료한 뒤 순차 실행했다. GPU graph 제출~동기화 wall이며
초기 준비·최종 파일 저장은 제외한다. 한 번씩의 기능 진단이므로 반복 통계 기반 성능 벤치마크가 아니다.

| 경로 | 채택 단계 | 최초 실패/판정 | 계산+검산 wall |
|---|---:|---|---:|
| 원본 dt1/3840·cycles3 | 59/64 | code2, 선형720회 | 95.726초 |
| 같은 dt·cycles6 | 59/64 | 같은 단계 code2, 실제1420회/6cycle | 104.303초 |
| dt1/7680·cycles3 | 128/128 | 전체 통과 | 11.843초 |
| 기본→GPU 조건부 dt/2 복구 | 재시도128/128 | 원래 code2 보존 후 전체 통과 | 106.948초 |

원본 최초 실패의 참 선형 잔차는0.064044799N, 목표는0.034185129N이었다. cycles6에서는
0.035455923N으로 줄었지만 같은 목표에 미달했다. 앞59단계 flag0, 통계 유한·행렬 상태0,
접촉/path 상태0이었다. 원본의 후속 flag14는 미완료 상태의 힘·위치 갱신·에너지 검산 불일치이며
audit99가 원래 solver code2를 덮었다. 이번 결과로 실제 기하 붕괴나 충돌 침범을 주장하지 않는다.

dt절반의 GMRES 누적은2,875회였고 원본 실패까지는29,765회였다. 더 작은 dt는
`M+(dt²/4)H`에서 접선 항의 상대 비중을 줄이며 관측과 일치한다. 조건수·고유값을 측정한
원인 증명이나 모든 장면에서 더 빠르다는 주장은 아니다. 실패와 성공의 완료 분모가 달라
95.726/11.843을 동등 작업 가속률로 사용하지 않는다.

자동 복구의106.948초에는 버린 첫 시도 약94.870초와 재시도 약12.078초가 모두 포함된다.
두 구간은 raw GPU marker 비율로 전체 host wall에 배분한 보정 시간이다. 초기 두 solver 준비는
별도7.005초다. 정상 프레임에서도 두 solver의 메모리를 준비하지만 half 계산은 실패 시에만 실행한다.
실패 비용을 없앤 최적화가 아니며, 프레임마다 실패하면 이 비용이 반복될 수 있다.

## 복구 승인과 검증

- 최초 오류·단계·원래/선형 잔차·유한성을 GPU에 보존한다. audit 오류 코드는 CAS로 기록해 원래
  solver code를 덮지 않으며 최초 audit 인덱스는 별도로 최소값 집계한다.
- **code2·유한 통계·contact/path0·정상 시간축·실패 전 prefix flag0**만 GPU에서 복구를 선택한다.
  다른 solver 오류와 실제 기하/CCD/힘/시간축 검산 실패를 우회하지 않는다.
- GPU의 frame-start hi/lo를 복원하고 같은 held force를 byte 단위로 재사용한다. 물성·barrier·
  정밀도·허용오차를 바꾸지 않는다. 재시도에도 별도 GPU 힘/기하/CCD 검산을 수행한다.
- 재시도128단계 flag0, 최대 힘 잔차 비율0.278997(<1), 최소 면적 비 하한0.467803(>0),
  contact/path/mass 상태0, 시간축 정상이다. Graph의 host copy/callback은0이다.
- 독립 dt절반 실행과 자동 복구 끝 상태의 hi 최대 차이는 위치1.11e-16m·속도5.03e-13m/s 이하다.
  두 계산의 held force는 정확히 같았다. 이는 같은 dt 구현 연결 검증이지 시간 수렴 비교가 아니다.
- 자동 복구의 폐기 시도 진단·검산은 최종 승인128단계 결과와 분리한다. 실패 재시도는 프레임
  시작 상태를 보존하고 중단하며 재귀 세분화·CPU/Gauss/contact-OFF fallback은 없다.

관련 고유 회귀54개 통과: 접촉 프레임·재시도·접촉 stepper·독립 audit·무압축 기록·GPU/CPU 실행기.
첫 묶음48개 통과/명시 CUDA 조건6개 skip 후 `WIND3DGS_TEST_DEVICE=cuda:0`으로 audit 파일을
실행해8개(중복2개 포함) 모두 통과했다. CUDA/native 환경은 위 동결v8과 같았다.
오류 자격 거절, 비유한 최초 통계 보존, 병렬 최초 audit 인덱스, 재실패 rollback, 실제 접촉의
half 직접 실행 대조와 다음 프레임 외력/기본 dt 복귀, 폐기 시도 파일/hash를 검사했다.

## 재현

workspace root에서 다음 공통 환경으로 `code/scripts/diagnose_gpu_contact_frame.py`를 실행했다.
`--out`은 반드시 존재하지 않는 새 경로여야 한다. 원본 실패는 의도한 진단 결과이며 프로세스 종료0과
물리 `status=passed`를 구분한다.

```bash
env PYTHONPATH=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v8/runtime \
 CUDSS_LIBRARY_PATH=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v8/native/libcudss.so.0 \
 LD_PRELOAD=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v8/native/libcudss_workspace.so \
 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
 .venv/bin/python -u code/scripts/diagnose_gpu_contact_frame.py \
 --root experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v8 \
 --out experiments/artifacts/runs/p3_self_contact/my_frame112_probe --frame 111 --cycles 3 --split 1
```

cycles6는 `--cycles 6`, dt절반은 `--split 2`, 현행 자동 복구는 `--runtime code --recovery`로
바꾸고 각각 별도 출력에 실행했다. 자동 복구는 원래 dt·cycles3에서 시작한다.
원본 manifest SHA-256은 `6eea4a53db03041fe584ace97ffc9ba81da853ce75503b753915d97e7c2a4f95`,
시작 NPZ는 `9d14ba0b43dd6580b12ba169e04d78b8b6b07a4a4be7b6e1da7068c795666257`다.
config의 전체 runtime hash와 result의 diagnostics hash로 각 실제 실행 코드를 구분한다.

메인 v8의108프레임 외부 종료라는 과거 추정은 잘못됐으며 최종 원본은112번째 시도 수치 실패다.
서브컴 원본은 `artifacts/runs/sub_pc/20260922T112548Z-c95910efe3344086bb24d33c3857f7f4/simulation/`
직사각형 wind115번째 시도에서 같은 code99/flag14 형태를 보였다. 이번 GPU 재현은 메인컴 저장 상태에
한정하며 서브컴 실패의 최초 잔차까지 확인했다고 주장하지 않는다.

사용자 전체 실행은 [세 씬 스크립트](gpu.md#세-시뮬레이션-실행)를 따른다. 새 출력은
`three_scenes_gpu_bend500_manual_v10`이며 기존 v8/v9 출력은 덮어쓰거나 자동 재개하지 않는다.
v10 manifest290개 검증, 세 씬9개 phase 입력이 v8과 byte 일치하며 실제 자동 복구에 사용한
runtime 전체 hash가 v10 동결 runtime과 일치한다. 본 outputs는 생성하지 않았다.
suite SHA-256은 `1419da7a8413c4ab2603c51501bfecc27e802769da401e8c2498c2a63180fd4e`,
manifest는 `f94f52dcdd823e45fff039e1255b56694eaea5270ac61a9cda2ed9d1ea56a562`다.
code/experiments의 base HEAD는 각각 `6b4faddb85845508385ca44a89f81f2e3de17983`,
`b918500a12dc80f979834c9a689e74b227da299f`이고 dirty snapshot의 실제 코드는 위 hash가 식별한다.
원격 fetch·commit·push는 하지 않았다.

회귀 재현은 `code/`에서 동결 native 환경을 지정한 다음 아래 파일들을 실행한다.

```bash
env WIND3DGS_TEST_DEVICE=cuda:0 \
 CUDSS_LIBRARY_PATH=../experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v8/native/libcudss.so.0 \
 LD_PRELOAD=../experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v8/native/libcudss_workspace.so \
 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ../.venv/bin/python -m pytest -q \
 tests/test_resident_contact_retry.py tests/test_resident_contact_frame.py \
 tests/test_resident_contact_stepper.py tests/test_resident_audit.py \
 tests/test_resident_uncompressed_recording.py tests/test_teacher_gpu_contact_scene_suite.py \
 tests/test_teacher_self_contact_scene_suite.py
```

실제 검증은 위 설명대로 환경 조건으로 skip된6개를 별도 보완한 두 실행이며, 이 명령은
처음부터 그 CUDA 조건을 명시한 재현용이다. R1 source/PDF38쪽과 master bundle20항목도
갱신·무결성 검증했으며 Gate 체크는 변경하지 않았다.
