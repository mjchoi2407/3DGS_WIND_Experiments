# CPU shell 동역학 기준 solver 진단

- 날짜: 2026-09-07
- 범위: Wind3DGS experiments-side, R1 동역학 개발 검증
- 상태: 두 CPU run·재현/상태 검산·evidence 보존 완료. 수치 계약 통과, 비선형 속도 응답 진단 실패.
- 승인: 사용자 “응 시작해”로 [code session 12](../../code/sessions/2026-09-07_12_teacher_shell_dynamics_design.md)의 구현 범위를 승인했다.

## 실행과 결과

실행 전에 [실험 README](../R1_teacher_shell_dynamics/README.md)에 입력·기준·실패 보존 계획을 작성했다.
E=1e6Pa, ν=0.3, h=0.01m, M_ref=0.1kg, 1m×1m의 synthetic mesh를 사용했다.
Python 3.12.3 / NumPy 2.4.4 / SciPy 1.18.1 CPU이며 dataset/object/checkpoint/split은 해당하지 않는다.
질량·normal mode·dense 검사는 n=4/8·세 분할, 실제 응답은 n=4에서 수행했다.

Workspace root의 명령은 다음과 같다. Replay에는 output 이름 끝에 `_replay`를 붙였다.

```bash
bash code/scripts/audit_teacher_shell_dynamics.sh \
  --young-modulus-pa 1000000 --poisson-ratio 0.3 --thickness-m 0.01 \
  --reference-mass-kg 0.1 --width-m 1 --height-m 1 \
  --output ../experiments/artifacts/runs/teacher_shell_dynamics/20260907_reference_v1
```

각 run은 19개 rollout·2,105 step을 완료했다. 별도로 기준 1+회전/이동 12개 step과 작은 선형계를 검사했다.
선형 이산 해·해석 운동·반력·수치 잔차·객관성은 통과했다. 선형 시간 오차의 관측 차수는 약 2다.
비선형 160/320-step의 정규화 위치 차이는 0.058855%, 속도 차이는 11.393922%다.
속도 차이가 40→80→160에서 감소하지 않아 `response_check=failed`를 보존했다.
상대 energy defect와 진폭 감소에 따른 선형 극한 대조는 통과했다.

저장된 속도 차이를 분해하면 Z 오차는 0.519167→0.125152→0.033202%로 감소하지만
XY는 10.175745→10.459624→11.393922%다. Rest 최고 각속도는 첫 굽힘 모드의 약 651.71배,
320-step에서도 `dt*omega_max≈12.7964`다. 빠른 면내 진동의 시간 해상도 부족 가능성을
후속 검증 대상으로 기록했다. 원인 확정·시간 수렴 판정이나 물성/감쇠 변경은 하지 않았다.

## 재현과 보존

- 원본 두 폴더: `artifacts/runs/teacher_shell_dynamics/20260907_reference_v1{,_replay}/`.
  각각 NPZ 상태 배열과 JSONL 반복 기록을 포함한 63개 파일이며 manifest는 자신 외의 62개를 검증한다.
- 두 report의 전체 수치 payload/hash와 상태 배열 114개가 일치한다. 상태·step trace hash도 같다.
  UUID와 계산 시간은 비교에서 제외한다.
- Source 16개, JSON/CSV, 원본 inventory·array identity·state chain을 재검산했다.
  총 4,210 step에서 운동방정식·pin/반력·Newmark 갱신을 재검증했고 모두 통과했다.
- 관련 106개 자동 검사는 code에서 21.205초에 통과했다. 새 24개에는 실패 prefix·중단·부분 파일·재사용 거부도 포함한다.
- [Compact evidence](../R1_teacher_shell_dynamics/provenance.json)는 9개 파일·299,967byte다.
  Reference의 report/config/CSV/environment/manifest/log, replay manifest, 검산 JSON과 이 두 run 전용 검산 script를 선택했다.
  원본 삭제·교체는 하지 않았고, 기존 GPU·native·판·구조 원본/evidence도 보존했다.

## 판단과 다음 단계

`status=completed`, `solver_check=passed`, `response_check=failed`,
`teacher_eligible=false`, `convergence_status=not_assessed`를 구분한다.
구현 완료는 움직임 계산과 수치 계약·기록 경로에 대한 판단이다. 물리 Teacher 채택과 학습 데이터 준비 완료를 뜻하지 않는다.
다음 기능은 같은 mesh의 XY/Z·모드별 속도와 더 촘촘한 시간 기준해 대조를 먼저 설계한다.
이 시간 해상도 문제를 확인한 뒤 공간 응답·공력/감쇠·저장 계약·학습 데이터 발행으로 진행한다.

## Git

`experiments/`에는 새 실험 README·provenance·evidence·본 note/index가 worktree에 있고 미commit·미push다.
`code/` 구현과 해당 README/session도 미commit·미push다. Root·ideas 및 기존 dirty 변경은 보존했다.
실행 시 code HEAD `7010682`, experiments HEAD `61d972e`는 로컬 snapshot이다.
실제 미commit source는 environment의 SHA-256으로 식별하며 이번 구현에서 network fetch·설치·다운로드는 하지 않았다.
