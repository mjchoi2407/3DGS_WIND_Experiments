# 막5ms 유지·굽힘1ms/5ms 마지막2초 진단

## 현재 상태

- 2026-09-29 사용자 요청으로 메인 GTX1080Ti용 구현·동결 입력·실행/뷰어 스크립트를 준비했다. GPU 계산은 실행하지 않았다.
- [직전 막 감쇠 결과](internal_damping.md#완료-결과-분석)는1ms/5ms 모두 빠른 떨림이 남았다. 막5ms를 유지하고 굽힘 변화에만 추가 저항을 주는 두 후보를 비교한다.
- 기존 막5ms 궤적의 전체8초 raw hi/lo 위치·속도에서 출발해8→10초120프레임씩 계산한다. 속도 초기화나 바람 ramp 재시작은 없다.
- 굽힘0은 기존 완료 결과를 재사용한다. 새1ms→5ms만 같은 GPU에서 순차 실행하며 전역 속도 감쇠는0이다.
- [실행 순서와 재생](#실행과-재생): 두 GPU 독립 연산 대조·두 첫 프레임이 모두 통과한 뒤 본120프레임씩 계산한다. 첫 실패에서 중단하고 실패 증거를 보존한다.
- [법칙·정확한 접선·소산 장부](#모델과-검산): 면 내부 곡률 변화와 요소 사이 접힘각 변화를 함께 감쇠한다. 기존 탄성·접촉·외력·dt/검산/복구 조건은 유지한다.
- 새 물리 검사9개·실행기9개·기존 경로 회귀27개, 총45개 CPU 검사 통과. 실제8초 상태에서도 NumPy/Warp CPU 힘·접선·소산 대조 통과.
- [동결 hash와 검증](#입력과-검증): 초기 네 raw 배열·원본 마지막120프레임 외력 동일, native 동일, 동결 runtime은 현재 구현과 일치한다.
- 기존 굽힘0의121상태 뷰어 캐시는 확인했다. 새 후보의 실제 결과·GUI 표시·GPU graph/첫 프레임·2초 완주는 아직 검증하지 않았다.
- 새 모델의 시간/공간 민감도·시각 채택·학습/R1 완료는 미완료다. 기존 감쇠24의 수렴 근거를 승계하지 않는다.
- 다음은 사용자 run 후 굽힘0/1/5ms를 눈으로 비교하는 것이다. 원본 결과·서브8/16 묶음·기존 dirty는 보존하며 canonical/TeX/PDF 변경은 없다.

## 실행과 재생

프로젝트 루트에서 실행한다. 이미 입력 준비가 끝났으므로 prepare를 다시 호출할 필요가 없다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_bending_damping.sh --action run
```

실행은 한 GPU에서 순차 진행된다.

1. 굽힘1ms·5ms 각각 실제8초 상태와 변형 속도의 힘·접선·소산을 GPU와 독립 NumPy 기준으로 대조한다.
2. 두 후보 각각 원본8초 다음 첫 프레임을 계산해 기존 접촉·기하·힘/에너지·시간 검산을 확인한다.
3. 모두 통과하면 다시 같은8초 raw 상태에서1ms→5ms 각각120프레임을 계산한다. 선행 첫 프레임 결과는 본 궤적의 초기 상태로 사용하지 않는다.

총 본 계산은240프레임이며 첫 프레임 검사2개가 별도다. 같은 결과 경로의 재실행·덮어쓰기는 거절한다.
실패하면 해당 로그와 raw 증거를 보존하고 원인 확인 후 다음 조치를 정한다. 입력 묶음·GPU 모델·환경의 동일성도 확인한다.
기본 동작은 상태 조회이며 다음 명령은 적분하지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_bending_damping.sh --action status
```

완료 후 세 조건을 함께 본다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_bending_damping.sh
```

왼쪽부터 **굽힘0·1ms·5ms**, 모두 막5ms이다. 표시0–2초는 전체 궤적8–10초다.
`--case bend0|bend1ms|bend5ms`로 단독 재생하고 `--prepare-only`로 프레임·시간·핀·hash·소산과 캐시를 확인한다.
굽힘0은 기존 완료 결과의 마지막120프레임을 읽으며 새로 적분하지 않는다. 새 후보가 미완료면 전체 비교를 거절한다.

## 입력과 검증

- 새 묶음: [rectangle_bending1_5ms_tail2_main_01](../../artifacts/runs/p3_self_contact/rectangle_bending1_5ms_tail2_main_01/suite.json). `cases`, `phase_start_s`, `phase_time_offset_s`, `reference0`이 식별 근거다.
- manifest SHA256: `8dba93d41b0341574c154d1a1cd2f5ba03ec5107966bceaad78622ce0585eff6`.
- 원본: [rectangle_wind_internal1_5ms_main_01의 입력 식별](internal_damping.md#입력과-동결), 그 안의 `tau5ms/reference_rectangle/outputs/wind/frame_0179.npz`.
- 원본 manifest SHA256: `3c5ef6764035b84cf5953e4228f563577f7355b31022e036168361d6bccbe8a1`.
- 원본8초 NPZ SHA256: `00d845e64efba0ae4dc337c07f219b0e3b32b556fbc9064b7a109b63d8eb1972`.
- 새 `initial_state.npz`는 원본 메타데이터를 제외한 네 raw 배열만 저장한다. 파일 hash는 달라도 네 배열은 비트 단위로 같다. 새 파일 hash는 [검증 JSON](bending_damping_checks.json)의 `reference0.initial_state_sha256`에 기록했다.
- `forcing.npz`의 중력·바람 및 `wind.npz`는 원본300프레임 중 `[180:300]` 배열이다. 두 후보는 동일한 외력을 받는다.
- 본 프레임은 `frame_0000.npz`부터 시작하되 `phase_time_s`는 원래wind의3+1/60→5초, `trajectory_time_s`는8+1/60→10초다.
- 기존 물성·적분기·허용오차·접촉 설정·swept 후보 용량2,000,000·cuDSS 결정성1을 유지한다.60Hz, 기본64/조건부128이다.
- 동결 Python 소스는 굽힘 구현이 추가됐으며 원본 막5ms runtime과 같다고 주장하지 않는다. native 파일은 원본과 동일하다.
- 각 후보의 `preflight/oracle.json`, `preflight/contact_frame/report.json`, `reference_rectangle/outputs/wind/report.json`과 `oracle.log`, `smoke.log`, `wind.log`가 실행 근거다.

[준비 검증 JSON](bending_damping_checks.json)은 물리9개·실행기9개·회귀27개와 실제8초 CPU 대조 수치, 동결/배열 동일성을 담는다.
물리 검사는 자유 패치 강체 운동 불변성·힘/토크 평형·양의 소산·접선 유한차분·Warp CPU 대조·접힘만 있는 패치를 포함한다.
실행기 검사는 raw 연결·외력 절단·실패 중단·기존 로그 보존·시간 기록·결과 hash/소산 거절을 포함한다.
실제8초 CPU 힘 오차는 최대약5.9e-13N, 접선 방향 작용 오차는약1.1e-9N 이하였다.
이는 GPU 검증이나 실제 실패 주입 rollback 검증을 대신하지 않는다. GPU 검사는 사용자 run의 선행 단계다.

## 모델과 검산

법칙 식별자는 `p3_curvature_hinge_rate_damping_v1`이다. 천 전체의 이동 속도에 저항을 주는 대신,
휘어지는 정도와 요소 사이 접힘각이 변하는 속도에 저항을 준다.1ms/5ms는 이 저항의 시간 계수이며 적분 시간 간격이 아니다.

진단 소산 함수는 `R_b = (τ_b/2)∫κdotᵀ Db κdot dA + (τ_b/2)Σ∫penalty·θdot² ds`이다.
기존 양의 굽힘 재료 행렬 `Db`와 경계 penalty를 가중치로 사용한다. 기존 탄성 edge flux나 전체 Hessian을
그대로 점성에 복사하지 않는다. 요소 내부 곡률 항만으로 빠질 수 있는 요소 사이 접힘의 변화까지 같은τ_b로 감쇠한다.
경계 penalty를 쓰는 이 진단 법칙의 메시 의존성·최종 재료 모델 채택은 별도 검토 대상이다.

현재 기하의 법선과 접선으로 접힘각 속도를 계산하므로 자유 패치의 강체 병진/회전 속도에서는 소산하지 않는다.
고정 가장자리의 rest 법선은 고정 제약으로 취급한다. 위치·속도 미분을 모두 포함한 정확한 접선 방향 작용을 쓰며,
위치 미분 생략·대칭화·PSD 투영을 하지 않는다. CUDA 반복 중 힘·접선·소산·판정은 GPU 버퍼에 남는다.

막+곡률+접힘의 총 소산률을 기존 endpoint 사다리꼴 소산 장부에 연결한다. solver와 독립 audit은 별도 객체로
raw 상태에서 각각 계산한다. 보고서의 `internal_damping.dissipation_j`는 채택 substep별 총 소산량이며
`dissipation_scope=membrane_plus_curvature_plus_hinge`로 구분한다. 물리 검산과 조건부 code1/2 한 번dt/2 복구 규칙은 유지한다.
굽힘0 기본값은 기존 막 감쇠 객체를 그대로 사용한다. 기존 동결 결과는 변경하지 않는다.

구현은 [NumPy 기준의 evaluate](../../../code/wind3dgs/teacher/bending_damping.py),
[GPU/CPU 커널과 ShellInternalDamping](../../../code/wind3dgs/teacher/resident_bending_damping.py),
[prepare·worker·run·cache_case 실행기](../../../code/wind3dgs/evaluation/teacher_gpu_bending_damping.py)에 있다.

## 해석과 다음 판단

우선 기존 굽힘0보다 잔진동이 줄고 큰 펄럭임이 살아 있는지 눈으로 판단한다. 이후 같은8–10초 구간의
빠른 위치 성분·프레임2차 차분·속도 RMS를 보조 비교한다. 후보간 모델 차이에 시간 수렴1%/10% 기준을 적용하지 않는다.

8초에서 감쇠를 바로 전환한 짧은 진단이므로 초반 전환 반응과 이후 상태를 구분한다. 이 결과는 시작부터
같은 감쇠를 사용한 wind 전체 궤적이 아니다. 새 후보가 좋을 때만 더 긴 궤적과 필요한 시간 민감도 확인을 후속 검토한다.
2초 결과만으로 진동의 물리/수치 원인, 공간 수렴이나 학습 적격성을 확정하지 않는다.

관련 R1의 canonical 구조 감쇠0과 제한 CG 진단 경계는 유지한다. 이번 후보 준비가 연구 모델 채택을 뜻하지 않으므로
R 문서·canonical 수식·완료 기준·TeX/PDF는 수정하지 않았다. commit/push·fetch·외부 다운로드도 하지 않았다.
