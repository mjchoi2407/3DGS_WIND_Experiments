# GPU 상주 검산 검증

확인일:2026-09-13. 실제 직사각형7081점·10프레임·640구간을 재시뮬레이션 없이 검사했다.
GPU 검산과 기존 검산의 전체 단계별 대조 통과. 이번 채택 범위는 개발용 검산 실행 경로이며
학습 발행·R1 Gate·장기 안정성 판정은 변경하지 않는다.

## 입력과 재현

- 입력:`experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_reuse_uncompressed_v1/candidate`.
  원본 프레임166 끝 이후167–176, 물리 시간 약0.167초. dt1/3840초, 외력은64구간마다 고정한다.
  10초 시뮬레이션 검증이 아니다.
- 최종 동결 실행:`experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_audit_frozen_validation_v1`.
  `audit_run.json`은 새 모듈과 원본 연결을, `results/`는 GPU 결과와 단계별 검사값을 보존한다.
- 기존 검산 대조:`experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_audit_reference_check_v1`.
  `reference_per_step.npz`는 동일 후보의 기존 검산값이다. 하이브리드 시뮬레이션·하이브리드 검산을 다시 실행하지 않았다.
- 원본·동결 파일·검증 스크립트 해시는 [sources.json](sources.json), 상세 GPU 결과는
  [gpu_audit.json](gpu_audit.json), 단계별 대조는 [reference_comparison.json](reference_comparison.json)을 따른다.

실행 환경은 기존 GTX1080Ti·Warp1.17·cuDSS0.7.1과 workspace shim이다. Wrapper가 환경을 설정한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gpu_audit.sh --out experiments/artifacts/runs/teacher_timestep_search/새_GPU_검산
```

전체 단계별 대조 명령은 같은 GPU 환경에서 다음과 같다. 출력은 새 경로를 사용한다.

```bash
PYTHONPATH=code .venv/bin/python code/scripts/check_teacher_gpu_audit_actual.py \
  --source experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_reuse_uncompressed_v1/candidate \
  --candidate experiments/artifacts/runs/teacher_timestep_search/새_GPU_검산/results \
  --out experiments/artifacts/runs/teacher_timestep_search/새_검산_대조
```

## 검사 내용과 결과

- CPU는 정적 메시·Bernstein 계수·희소 구조를 처음 준비하고 NPZ 읽기·해시·청크 전송·JSON 기록을 담당한다.
  검산에 쓰이지 않는 강성 행렬은 생성하지 않는다.
- GPU는 저장 상태의 힘·탄성에너지 재계산, 질량 풀이, 위치·운동에너지·일·잔차 검사,
  구간 전체의 기하 상한과 기준 궤적 대조를 계산한다. 적분기의 성공 상태나 저장 잔차를 그대로 신뢰하지 않는다.
- 변형률·곡률 상한도 유지했다. 입력 hi/lo를 CPU longdouble로 합치지 않고 GPU의 보정 연산으로 처리한다.
- 공식 힘 한도, 위치 갱신2e-14m, 에너지 장부3e-16+1e-8×|balance|J, 기하 상한<1,
  기준 궤적 위치atol1e-10m·속도atol1e-8m/s·rtol1e-6을 유지했다.
- 640구간의 실패 판정 모두 일치했다. 최대 힘 잔차 비율은 GPU0.055243이며 허용 한도1보다 작다.
  기존 검산과 GPU 검산의 최대 단계별 차이는 힘 비율1.85e-4, 위치 갱신2.71e-20m,
  에너지 장부1.39e-17J, 기하 상한2.22e-16이다.
  대조용 수치 허용 범위는 검산기 간 회귀 기준이며 물리 통과 한도를 완화한 것이 아니다.
  CPU longdouble, GPU hi/lo와 서로 다른 LU/합산 순서 때문에 bitwise 일치를 주장하지 않는다.
- 실행 graph는 자식 cuDSS graph를 포함해 kernel248개·GPU 내부 복사8개·memset8개,
  host 전송0개·CPU callback0개다. 각 검산 구간 내부에서 CPU 수치 조회를 하지 않는다.
- 회귀7개 통과:압축·무압축/다른 파일 경계 읽기, 잘못된 파일 경계 거부, 청크 크기별 결과 일치,
  고정점·힘·위치·에너지 실패, 시간축·기준 궤적·NaN 실패, hi/lo 하위 비트 보존,
  다항식 상한 및 양 끝이 정상이어도 중간이 실패하는 구간 검출.

## 시간의 범위

최종 동결 실행의 GPU 계산은5.643초, 검산 본체(`audit_s`)는7.343초,
검산 worker의 입력 준비·해시·파일 읽기까지 포함한 시간은12.673초다.
외부 launcher의 원본 확인·runtime 복사·shim 빌드 및 최종 결과 파일 쓰기는 마지막 값에 포함하지 않는다.
첫 실행의 컴파일과 캐시 상태에 따라 초기 시간이 달라진다.

동일 후보를 기존 검사기로 대조한 루프는32.336초, 그 초기화는8.852초였다.
이 루프에는 마지막 기준 궤적 대조가 없고 새 GPU 계산에는 포함되므로 단순 동일 범위 배율로 보고하지 않는다.
과거48.440초도 파일 읽기와 마지막 궤적 대조가 빠진 기록이다.
이번 값은 한 메시·짧은 저장 구간의 개발 측정이며 다른 메시·긴 궤적의 속도나 물리 적격성을 증명하지 않는다.
