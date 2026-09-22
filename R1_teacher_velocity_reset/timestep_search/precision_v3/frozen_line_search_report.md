# Frame225 저장 보정의 FP64 line search 진단

fresh의 λ=1 최대 성분 변위 보정40.517mm는 거부됐다. 기존 line search는 λ=1/8에서5.065mm 보정을 승인했지만 비선형 잔차 감소는 작았다. 이 값은 승인된 프레임 오차나 완성된 timestep 결과가 아니다.

초기 RHS는 동일 uh/lo/a/held를 기존 FP64 evaluate로 재계산했으며 저장본과 성분별 정확 일치(L2/L∞ 차이0)했다. 초기 잔차 L2는533.726987781N이다. 기존 A64 참 잔차 기준도 두 저장 보정 모두 다시 통과했다.

| 방법 | 승인 λ | backtrack | 최대 성분 보정(mm) | 승인 후 비선형 잔차 L2(N) | GPU 탐색(ms) | readback 포함 탐색 wall(ms) |
|---|---:|---:|---:|---:|---:|---:|
| R64 | 1.0 | 0 | 1.258327 | 31.648124940 | 8.003 | 14.080 |
| F64_fresh | 0.125 | 3 | 5.064576 | 527.620687991 | 19.273 | 23.442 |

R64는 비선형 잔차를 약94.07%, fresh는 약1.14% 줄였다. R64의 선형 잔차보다 fresh의 선형 잔차가 훨씬 작아도, 큰 보정에서 선형 근사가 실제 비선형 응답을 충분히 설명하지 못한다. 어느 쪽도 이 한 번의 보정만으로 공식 Newton 종료 잔차를 충족하지 않는다. 다음 Newton 반복량·전체 substep 비용은 측정하지 않았으므로 fresh의 전체 가속을 주장하지 않는다.

## λ별 실제 결과

| 방법 | λ | 비선형 잔차 L2(N) | Armijo 상한(N) | status | 승인 |
|---|---:|---:|---:|---:|---|
| R64 | 1.0 | 31.648124940 | 533.673615082 | 0 | True |
| F64_fresh | 1.0 | 99591.317120499 | 533.673615082 | 0 | False |
| F64_fresh | 0.5 | 12751.449107787 | 533.700301432 | 0 | False |
| F64_fresh | 0.25 | 1765.046623441 | 533.713644607 | 0 | False |
| F64_fresh | 0.125 | 527.620687991 | 533.720316194 | 0 | True |

기존 trial/evaluate/line_decide와 병렬 FP64 합산을 그대로 capture했다. λ 시작1, 실패 시1/2, 최대12회, Armijo 계수1e-4와 기존 geometry/status 판정을 변경하지 않았다. 모든 trial의 status는0이며 fresh의 앞선 세 거부는 Armijo 미충족이다. 기존 after_linear에 필요한 선형 잔차·반복 필드는 저장 출력과 A64 재검산에서 공급했다. 완전한 timestep control을 복원한 것은 아니다.

## 상태·검증과 비용 범위

- HVP status/failure, 초기 evaluate status와 cuDSS factor info는 모두0. 저장된 조립 행렬/보정/RHS는 유한하다.
- P는 closeout의 P64_used를 재사용했고 재조립하지 않았다. 기존 cuDSS factor info도0이며 이번에는 저장 행렬의 factor 상태만 별도로 확인했다. 원본 assembly의 독립 status 값은 별도 저장돼 있지 않아 미확인으로 둔다. result.json의 stored_assembly_factor_info 필드는 원본 cuDSS factor info만 담는다. 원래 row/col/ids/mass와 dt 계수의 정확 일치를 확인했다.
- 원래 A64 기준0.053372698778N에 대해 R64 참 잔차0.048770465558N, fresh 2.409698383e-9N. 선형 목표와 비선형 종료 목표를 구분한다.
- GPU 탐색 시간은 λ별 trial/evaluate/line_decide/조건부 상태 복사를 포함한다. host wall에는 λ 기록용 동기화/readback이 포함된다. setup·초기 RHS·A64 확인·저장 행렬 factor는 result.json에 별도 기록했다. 전체 process wall은 execution.json이며 프로파일러 시간과 섞지 않았다.

## 종료 판정

두 저장 보정은 `line_search_checked_frozen_candidate`까지만 기록한다. 저장본에 u/v 배열은 있지만 substep 진입의 control/a0/predictor와 완전한 재시작 계약이 저장돼 있지 않아, 이를 완전한 timestep 시작 checkpoint로 간주하지 않았다. 한 substep 전체 Newton·독립 audit는 미실행이다. 새로운 HL01 재생/frame236 checkpoint는 만들지 않았다.

기존 M1/M2 및 HL01 R64 운영 선택, production_enabled=false, training_eligible=false를 유지했다. 전역 rebuild·fresh P32·전체 FP32·새 solver 개발을 진행하지 않았다. 기존 closeout ZIP SHA256 불변을 확인했으며 원본 결과를 수정하지 않았다.

Canonical 원시 결과: `experiments/artifacts/runs/teacher_precision_v3/frozen_line_search_20260917/`. measurement/line_search.csv는 λ별 raw, measurement/*_line_output.npz는 실제 승인 후 상태와 변위 차이, result.json은 환경·policy·판정이다. logs/commands.jsonl에 실제 재현 argv와 process wall이 있다. provenance.json은 원본 snapshot/closeout ZIP/frozen runtime hash를 보존한다.
