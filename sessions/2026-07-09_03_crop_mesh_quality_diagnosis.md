# 2026-07-09 crop mesh 품질 진단

## 관찰

- crop mesh extraction 결과에서 경계부뿐 아니라 crop 내부 디테일도 뭉쳐 보이는 문제가 확인되었다.
- 사용자가 본 문제는 crop 바깥 문맥이 사라진 경계 불연속보다, 남아 있는 Gaussian들끼리 alpha field가 합쳐지며 세부 구조가 사라지는 현상에 가깝다.

## 정량 확인

crop PLY 기준 Gaussian 최대 scale과 최근접 Gaussian 거리의 비율을 확인했다.

| scene | crop gaussians | nn p50 | scale/nn p50 | scale/nn p90 | scale/nn p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `bonsai` | 50,257 | 0.00419 | 1.53 | 4.61 | 6.80 |
| `flowers` | 6,798 | 0.01311 | 1.38 | 3.73 | 5.36 |
| `garden` | 1,804 | 0.01197 | 1.60 | 4.56 | 6.18 |
| `treehill` | 19,019 | 0.01148 | 1.24 | 4.76 | 7.37 |
| `stump` | 68,656 | 0.00932 | 1.39 | 5.14 | 7.59 |

opacity는 대부분의 crop에서 거의 1.0으로 포화되어 있었다.

## 해석

- 현재 GOF mesh extraction은 `alpha - 0.5`를 SDF처럼 사용해 marching tetrahedra를 수행한다.
- Gaussian scale이 최근접 거리보다 큰 경우가 많고 opacity가 포화되어 있으므로, 렌더링에서는 자연스럽게 보이던 여러 splat이 mesh extraction에서는 하나의 두꺼운 alpha volume으로 합쳐질 수 있다.
- 특히 낮은 density 설정으로 학습한 모델은 적은 수의 큰 Gaussian이 넓은 영역을 설명하므로, mesh proxy에서는 leaf/branch 같은 세부 구조가 둥글고 뭉친 표면으로 바뀌기 쉽다.

## 다음 실험 후보

1. mesh extraction 전용으로 alpha iso-threshold를 `0.5`보다 높이는 변형을 테스트한다.
   - 기대 효과: 두꺼운 blob을 안쪽으로 수축시켜 붙은 부위를 분리할 수 있다.
   - 위험: 얇은 구조가 끊기거나 구멍이 늘 수 있다.
2. crop PLY의 `scale_*` 값을 임시로 줄인 뒤 GOF mesh extraction을 테스트한다.
   - 기대 효과: 남아 있는 Gaussian들 사이의 alpha overlap이 줄어 덩어리화가 완화될 수 있다.
   - 위험: 원래 GOF가 학습한 opacity field와 달라지므로 물리적으로 정확한 복원은 아니다.
3. 최종 연구용 asset은 mesh용 고밀도 학습 설정으로 다시 뽑는다.
   - densification을 더 오래 유지하고 threshold를 낮춰 더 작고 많은 Gaussian을 만들 필요가 있다.
   - 단순 렌더링 품질보다 mesh proxy 품질을 기준으로 설정을 골라야 한다.
