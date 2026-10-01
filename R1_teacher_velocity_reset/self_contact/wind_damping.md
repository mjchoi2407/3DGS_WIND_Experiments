# 공통5초 상태의 wind 감쇠8/16 비교

## 현재 상태

- 2026-09-29 후속: 서브8/16 실행 중은 사용자 보고. 메인용 [막 감쇠1/5ms 구현·스크립트·CPU 검증](internal_damping.md#현재-상태)을 별도 준비했다. 아래 대안 미구현 상태는 당시 기록이며, 기존8/16 동결 runtime은 변경하지 않았다.
- 2026-09-29 사용자 관찰: 감쇠24는 잔진동을 억제하지만 wind 움직임이 둔하다.24의 시간 민감도 수치 통과는 유지하되 최종 시각 채택은 보류한다.
- 승인된 후속은 원본24의5초 raw hi/lo 위치·속도를 공통 시작으로 wind8/16을 각각5초 계산하는 진단 준비다. 시뮬레이션은 실행하지 않았다.
- 사각형·60Hz·기본64/조건부128 복구·기존 물성/외력/contact/geometry/시간/독립 검산·rollback을 유지한다. 바람 ramp는 원본 전체5초부터 그대로다.
- 기존24 wind의 초기 raw 상태가5초 checkpoint와 byte 동일함을 확인했다.24는 재계산하지 않고 완료 결과를 참조한다.
- 새 계산은 원본과 같은 RTX5070으로 제한한다. 서로 다른 GPU의 감쇠 효과를 혼동하지 않는다. 뷰어는 메인에서도 가능하다.
- [동결 입력·hash·검증](wind_damping_checks.json): CPU9개 검사, 셸 구문, 원본 runtime/native·외력·초기 상태 동일성 통과.8/16 plan은 감쇠값만 다르다.
- 기존24의300프레임 캐시와 한 프레임 실제 렌더를 확인했다. 새8/16의 GPU 완주/물리 검산/실결과 재생은 미완료다.
- 전 구간8/16 궤적이나 새 시간 수렴 통과 근거가 아니다. 기존24의 통과 판정을8/16에 승계하지 않는다.
- 다음은 사용자 run 후8/16/24의 잔진동과 큰 바람 반응을 함께 비교하는 것이다. 기존 실행/결과/dirty 변경은 보존했다.

## 실행과 재생

서브컴에서 한 명령으로8→16을 순차 실행한다. 한 조건이 실패하면 뒤 조건을 시작하지 않는다.

```bash
bash /mnt/wind3dgs/experiments/R1_teacher_velocity_reset/self_contact/run_gpu_wind_damping.sh --action run
```

원본 preload/calm은 재계산하지 않는다. 새 계산은 각300프레임, 합계600프레임이다.
읽기 전용 공유의 입력을 `/mnt/wind3dgs-sub-results/wind_damping8_16_from24_01`로 복사하고
서브의 `WIND3DGS_PYTHON` 또는 worker 로컬 venv로 실행한다.
기본 action은 status이며 `--action status`로 진행 상태만 확인한다. 기존 출력/로그나 실패 복사 경로는 덮어쓰거나 자동 재개하지 않는다.

완료 후 메인 프로젝트 루트:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_wind_damping.sh
```

왼쪽부터8(파랑)·16(주황)·기존24(초록), 동일 축척·카메라·동기 시간으로 표시한다.
표시0–5초는 전체 궤적5–10초다. Space 재생, Playback speed로 느리게 확인한다.
메인 래퍼는 위 서브 결과 경로의 로컬 공유 대응 경로가 있으면 자동 선택한다.
서브에서 뷰어를 열 때는 명령 경로 앞에 `/mnt/wind3dgs/`를 붙이며 표시 캐시는 worker 로컬에 저장한다.
`--case rate8|rate16|rate24`는 개별 재생 선택에만 사용한다. `--prepare-only`는 캐시만 검증한다.

입력 묶음은 `experiments/artifacts/runs/p3_self_contact/rectangle_wind_damping8_16_from24_01`이다.
이미 준비됐으므로 prepare를 반복하지 않는다. 새 준비는 `--action prepare --out <새 경로>`이며
다른 결과 경로를 쓰면 run/status/view에 모두 같은 `--out`을 전달한다.
원본 기준은 `sub_pc/20260929T002107Z-65221d3a61d34d0f93b4d01006eb5602/simulation/steps64`.
`reference24`의 manifest/report/initial hash로 실제 기준을 고정하고 사용자별 절대 경로를 config에 저장하지 않는다.

## 비교 해석과 대안

이 실험은0–5초에는24로 정돈된 상태를 사용하고, wind 시작부터8 또는16으로 전환한다.
속도를 초기화하지 않으며 기존24의 완만한 준비 상태를 세 조건이 공유한다. 채택된 최종 물성의 자연감쇠 모델로 바로 간주하지 않는다.
강한 감쇠의 둔함을 바람 세기 증가로 동시에 보상하지 않아 감쇠 효과를 구분한다.

8/16도 잔진동과 둔함 사이 타협이 안 되면 다음 순서로 검토한다. 이번 작업은 대안 구현 승인이 아니다.

1. **변형에 따른 내부 감쇠:** 모든 속도를 일률적으로 줄이는 대신 늘어남·전단·굽힘의 변화에 각각 감쇠를 건다.
   강체 이동/회전을 불필요하게 제동하는 문제를 줄이는 방향이지만 큰 굽힘 운동도 영향을 받을 수 있어 계수와 구현 검산이 필요하다.
   [Baraff–Witkin, SIGGRAPH1998 §4.5](https://www.cs.cmu.edu/~baraff/papers/sig98.pdf)의 변형 조건 변화율 기반 감쇠가 참고 근거다.
2. **빠른 수치 진동을 줄이는 적분법:** 진단상 빠른 성분의 시간 적분 오차가 주원인이라면 generalized-alpha 같은 방법을 검토한다.
   [공식 방법 설명](https://opensees.github.io/OpenSeesDocumentation/user/manual/analysis/integrator/GeneralizedAlpha.html)은 고주파 에너지 소산을 지원하지만,
   현행 비선형 접촉의 안정성과 정확성을 자동 보장하지 않는다. 접촉 시간 경로·힘/에너지 검산을 함께 맞춰야 하는 별도 구현 작업이다.
3. **물성·고정 경계 점검:** 진동을 줄여도 판처럼 느껴지면 굽힘/면내 강성·고정 경계가 원하는 천과 맞는지 분리 확인한다.
   현재 굽힘 강성이 과하다는 원인은 확정되지 않았다. 여러 물성과 바람을 한꺼번에 바꾸지 않는다.

R1의 시각·학습 채택 경계를 유지한다. 이번 변경은 실행/재생 진단 준비이고 새 재료 모델이나 적분법을 채택하지 않았다.
따라서 canonical R1/TeX/PDF 수정·빌드는 없다. 대안 설명에는 원문 논문과 공식 문서를 웹 조회했으며 외부 패키지 설치는 하지 않았다.
