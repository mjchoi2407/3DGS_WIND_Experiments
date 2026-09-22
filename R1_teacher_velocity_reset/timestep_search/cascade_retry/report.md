# Newmark → half2 → Gauss8 고부하 표본 결과

2026-09-18. **국소 복구와 일부 시간 감소는 확인했지만, 동일 정확도의 가속으로 채택하지 않는다.** 기존 Newmark → Gauss8과 비교해 실패 표본의 계산+검산 시간이 줄었으나 끝 속도 차이가 질량 가중 상대 L2로26–29%다. 단순히 느리지만 수렴한 표본에서는 재시도가 작동하지 않아 개선 근거가 없다. 기존 생산/세 씬 기본 스크립트와 training_eligible=false를 유지한다.

## 측정 결과

GTX1080Ti·M1 base·force block256/256/256, half/Gauss 복구 R64. 두 반복을 A/B → B/A 순서로 실행했다. 아래는 두 값의 중앙값이며 모든 실패 시도·재시도와 독립 검산 비용을 포함한다. 별도 반복의 과거 실행 시간으로 배속을 만들지 않았다.

| 표본 | 기존 Gauss 복구(s) | half2 우선(s) | 계산 시간 감소 | 복구 결과 |
| --- | ---: | ---: | ---: | --- |
| 직사각형 실패 frame103 (104번째) | 43.789 | 35.637 | 18.62% | 두 반복 모두 half2 성공·Gauss 불필요 |
| 삼각형 실패 frame120 (121번째) | 12.003 | 11.278 | 6.04% | 두 반복 모두 half2 성공·Gauss 불필요 |
| 최근 직사각형 frame118 (119번째) | 54.321 | 56.352 | -3.74% | 양쪽 재시도0·개선 없음 |

12/12프레임, 800개 채택 단계의 기존 검산을 통과했다. 실패 표본의 기본 Newmark는 두 정책 모두 동일 substep(직사각형37,삼각형60;0기반)에서 line-search code3이었다. 모든 표본에서 원본 저장 held와 재구성 held의 성분 차이는 정확히0이었다. M1 내부 R64 fallback은0회였다.

직사각형의 Gauss 재시도 자체는약0.87–0.91초, half2는약0.26–0.28초다. 전체약8.15초 감소의 대부분은 다른 복구 끝 상태에서 남은 Newmark 구간의 반복이 줄어든 영향이다. 이를 같은 선형계의 순수 커널 가속으로 해석하지 않는다. 삼각형은 전체 이득이 작고2회씩의 제한 측정이다.

### 준비와 전체 프로세스 비용

| 표본 | 기존 setup(s) | 새 setup(s) | 기존 process wall(s) | 새 process wall(s) |
| --- | ---: | ---: | ---: | ---: |
| 직사각형 실패 frame103 (104번째) | 8.734 | 12.825 | 53.067 | 49.020 |
| 삼각형 실패 frame120 (121번째) | 6.478 | 5.418 | 19.040 | 17.259 |
| 최근 직사각형 frame118 (119번째) | 7.999 | 10.837 | 62.774 | 67.832 |

setup에는 import/모델·solver·Graph 준비가 포함된다. lazy audit 초기화는 기존 run_frame 타이머 안에 남겼다. process wall은 독립 worker 시작부터 종료·NPZ/JSON 기록까지 포함한다. half solver 추가 준비 비용은 전체 실행에 한 번 드는 비용이므로 프레임당 계산 시간과 분리한다. 2회 중앙값을 긴 데이터 생성 전체 가속률로 확장하지 않는다.

## 수치 차이: 검산 통과와 궤적 일치는 다르다

| 표본 | 위치 성분 최대 차이(mm) | 속도 성분 최대 차이(m/s) | 속도 질량 가중 상대 L2 | 속도 비가중 상대 L2 |
| --- | ---: | ---: | ---: | ---: |
| 직사각형 실패 frame103 (104번째) | 0.0473301 | 0.415289 | 28.684% | 30.1708% |
| 삼각형 실패 frame120 (121번째) | 0.0315449 | 0.955237 | 26.2828% | 31.2296% |
| 최근 직사각형 frame118 (119번째) | 2.04637e-09 | 2.60049e-09 | 1.52964e-08% | 2.33574e-08% |

위치는 원시 u_hi+u_lo, 속도는 v_hi+v_lo를 longdouble로 합성하여 비교했다. 질량 가중 차이는 sqrt(δvᵀMδv / v_GaussᵀMv_Gauss), 비가중 차이는 ||δv||₂/||v_Gauss||₂다. 공통 rest 위치이므로 변위 차이와 위치 차이는 같다. 두 반복에서 위 차이는 재현됐다. 같은 방법끼리의 반복 속도 상대 L2 차이는최대2.38e-10 수준으로 정책 간 차이보다 작다.

직사각형의 끝 운동에너지 차이는약1.07e-6 J, 삼각형은약3.95e-5 J다. 작은 위치 차이와 에너지 장부 통과만으로 각 점의 속도까지 같다고 판정할 수 없다. 기존 에너지 장부 절대 오차는모든 채택 단계에서6.94e-18 J 이하였으나 이는 시간 적분 오차의 상한이 아니다.

이 수치는 **기존 Gauss 복구 결과와의 차이**이며 참해 대비 오차가 아니다. 더 세밀한 공통 참조를 새로 계산하지 않았다. 기존 공식 force/correction/EW/line-search/audit 기준은 변경하지 않았고, 회귀/학습 적격성 예산은 budget_not_defined다. 수렴 통과·국소 성능·정책 간 차이·생산 적용을 별도 판정한다.

## 표본 선정·환경·한계

- 직사각형103/삼각형120은 newmark_dt_fixed_bend500_v1의 실제 failure_state를 그대로 사용했다. 보고서의 hash와 일치한다. 완전한 프레임 시작 상태이며 frozen linear snapshot이 아니다.
- 최근 직사각형118은 중단 보존 run의 확정 저장 프레임0–119 안에서 원래 계산+검산 시간이 가장 컸다. 로그에는190까지 있으나 이후 상태는 확정 저장되지 않았으므로 선택하지 않았다. 전체 궤적/전체 생성 대상의 최댓값은 아니다.
- 각 후보는 같은 raw hi/lo, 전체 원본 forcing 배열의 해당 index, 동일 held·물성·공식 policy를 사용했다. 기존 preload2초 뒤 wind branch의 phase time은각각103/60,120/60,118/60초다. 이미 잘린 forcing에 offset을 중복 적용하지 않았다.
- 각 독립 프로세스에서 전처리기와 Graph를 새로 준비했다. 과거 프레임 간 cache 이력을 장기 replay로 복원하지 않았다. 같은 GPU에서 순차 측정했지만 GPU clock/그래픽 부하는 고정하지 않았다.
- 최근 frame118 첫 baseline worker와 짧은 CPU LaTeX 빌드 기간이 겹쳤다. 계산 타이머와의 정확한 중첩 길이는 미측정이며 원시값을 삭제하지 않았다. 해당 표본의 작은 시간 차이는 가속/고유 회귀 확정으로 쓰지 않는다. 두 실패 표본 측정은 이 빌드 이전에 완료됐다.
- 현행 로컬 환경은GTX1080Ti sm61,driver582.28/API13000,Warp1.17.0/toolkit12.9다. native cuDSS/shim과 source hash는 동결 manifest에 있다. Graph inventory/실제 launch 기록은 각 result.json에 보존했다.
- sub_pc의 최근20260918T020901Z-f78338ad407f4eb080d58fc0c0651ea3도 읽었다. RTX5070이며 eager_cuda adapter를 사용한 다른 실행이다. 이번에는 원격 실행/fetch/download 없이 로컬 공유 사본만 확인했으며1080Ti Graph 표본과 시간을 합치지 않았다. 5070의 이번 정책 성능·Graph 복구는 미검증이다.
- 실제 표본에서는 half2가 모두 성공해 half 실패→Gauss 복구는 발생하지 않았다. 해당 경로는 작은 실제 GPU fixture에서 partial half 폐기·정확한 상태 복원·Gauss 검산으로 확인했다. 실제 고하중에서 해당 최종 복구 성공률을 확인한 것은 아니다.
- fixture4종: half 성공, half 부분 실패 후 Gauss, half 검산 오류 시 중단, Gauss 최종 실패 후 프레임 보존. 기본 실패 조건만 재사용하며 허용오차/선탐색 계수/전처리 갱신 기준을 바꾸지 않았다. 추가 HL01/최고비용 frame236 재생과 새 solver 개발은 없다.

## 판단과 재현

**현행 Newmark → Gauss8 기본은 유지한다.** Half2 우선은 일부 실패 구간의 저비용 복구 후보지만, 현재 표본에서 동일 정확도 유지가 확인된 teacher 가속으로 채택할 근거는 부족하다. 모든 구간에서 빠른 방식이 아니며 handkerchief/긴 궤적/5070/실제 half 실패 이후 고하중 Gauss 회복은 이번 검증 범위 밖이다.

[재현 명령](README.md), [원시 프레임 CSV](frames.csv), [쌍별 차이 CSV](pairs.csv), [원시 시도 CSV](attempts.csv).
Canonical 결과: `experiments/artifacts/runs/teacher_timestep_search/cascade_retry_samples_20260918/`.
그 안의 cases.json·cases/*는 source/input hash와 입력, runtime_scenes는 동결 runtime/환경, execution.json과 controller.log·각 worker log는 실제 실행 명령과 과정, runs/*/result.npz는 상태/검산/dt/method, result.json은 모든 시도·반복·시간·Graph를 소유한다. changes.patch·implementation_hashes.json·verification.json도 함께 남겼다. 918개 동결/input hash와 원본 snapshot3개의 보존을 확인했다.

R1에는 제한 개발 비교 계약을 반영했고 PDF 및 delivery bundle의 R1 항목을 실제 갱신했다. R0의 teacher 결과 비승계 경계를 확인했으며 계약/Gate 변경이 없어 수정하지 않았다. 관련 code/experiments/ideas worktree 변경만 남겼고 stage/commit/push는 하지 않았다.
