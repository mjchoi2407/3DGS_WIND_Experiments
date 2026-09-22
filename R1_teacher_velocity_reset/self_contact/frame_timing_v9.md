# GPU 프레임 자동 시간 보정·선형 실패 복구 v9

## 현재 판정

후속 [실패 프레임 재현·v10](frame112_recovery.md)에서 cycles3→6으로는 실제 실패가 해결되지
않음을 확인했다. 현재 실행기는 GPU dt/2 제한 복구로 교체했다. 아래 v9 구현·검증은 당시 기록이다.

`three_scenes_gpu_bend500_manual_v9`은 BVH v5의 접촉 수식·입력·물성·허용오차를 유지하면서
두 운영 문제를 보완한 사용자 실행 묶음이다. 세 씬 모두 준비 완료·미실행이며, 기존 v5/v8과
서브컴 결과는 수정하지 않았다.

첫째, v8의 내부 구간은 PTX `%globaltimer` 차이를 그대로 (10^{-9})배 해 초로 표시했다.
GTX1080Ti의 직사각형 calm 전체에서 `(solver+audit)/frame wall` 중앙값은 약1.0608이었고,
wind101프레임도1.0601이었다. RTX5070 저장 결과에서는 약1.111이었다. 이는 solver가 frame보다
실제로 오래 실행된 것이 아니라 장치별 timer 환산 차이다.

v9은 CUDA graph 전체를 감싸는 별도 GPU marker를 추가한다. 매 프레임 다음 배율로 내부
solver/audit/collision 구간을 자동 정규화한다.

```text
scale = host frame wall / max(raw outer-frame marker, raw solver + raw audit)
```

보정 전 raw 값·배율·host wall은 각 프레임 `stage_timings.calibration`에 보존한다. 터미널은
`프레임 wall`, 보정된 solver/collision/audit, `계측보정 ×...`을 표시한다. Collision은 여전히
solver/audit의 부분집합이므로 합산하지 않는다.

둘째, 과거 실패에서 solver의 원래 오류가 audit의 일반 code99로 덮였다. 이제 solver failure가
이미 있으면 audit flag는 진단용으로 남기되 code99와 `first_bad`로 덮지 않는다. 원래 code2
(GMRES 한도)이고 contact/path status가0일 때만 GPU rollback 상태에서 같은 프레임을
`linear_cycles=6`으로 한 번 다시 계산한다. 기본값은3이므로 최대 반복 한도만720→1440으로
늘어난다. 선형/비선형 허용오차, dt, barrier, FP64 hi/lo, 기하·CCD 승인 조건은 바꾸지 않는다.
재시도의 접촉·Newton/GMRES·독립 검산·rollback도 전부 GPU이며 CPU/Gauss/contact-OFF fallback은 없다.
code1/3, 접촉/CCD/기하/audit 오류 또는 재시도 실패는 계속 프레임 전체를 거절한다.

재시도가 발생하면 폐기한 첫 graph와 승인 재시도의 wall·stage 시간을 합산하고, 새 solver graph
준비 시간은 `recovery.setup_s`로 따로 기록한다. 이후 프레임은 cycles6 solver를 유지하므로 같은
한도의 무의미한 재시도를 반복하지 않는다.

## 오류 해석과 남은 검증

- 메인 v5 직사각형은 wind104프레임 뒤 다음 시도에서 `code99/flags14`, GMRES 최대720으로
  종료됐다. 서브컴 v5도 wind114프레임 뒤 같은 형태로 종료됐다. Contact/path와 기하 인증은
  통과했으므로 원래 code2가 audit99에 가려졌다는 해석과 일치한다.
- 메인 v8의 최종 원본은 wind111프레임 승인 뒤112번째 시도에서 code99/flags14로 실패했다.
  앞서108프레임 외부 종료로 판단한 것은 프로세스 가시성에 근거한 잘못된 추정이었다.
  후속 저장 상태 재현에서 최초 code2를 확인했으며 상세 원본은 v10 보고서가 소유한다.
- v9의 code2 복구는 안전한 제한 후보이지 과거 실패 frame이나 세 씬 장기 완주가 아직 확인된
  것은 아니다. 사용자가 실행한 결과에서 실제 recovery 통과/실패와 추가 비용을 판정한다.

동결 cuDSS 환경의 관련 GPU 회귀113개가 통과했다. 여기에는 바깥 marker 보정 관계,
solver code2 보존, 기존 BVH/힘/HVP/CCD/정밀 기하/rollback과 복구 정책 검사가 포함된다.
세 씬 본 실행과 smoke는 사용자 직접 실행 방침에 따라 시작하지 않았다.

동결 suite/manifest SHA-256은 각각
`9590a55b0049521f7a0db29c0b33a495f690d20ed72e1497848ddeb4c0ea7fba`,
`b75af888dd1ca79a96485e8bc66f7f2940b519ad0f40d2b92e24f8ba1ad2481d`다.

## 사용자 실행

개별 스크립트는 별도 옵션 없이 해당 씬 전체 실행을 시작한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_rectangle.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_handkerchief.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_triangular_flag.sh
```

세 씬 순차 실행은 다음 명령이다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
```
