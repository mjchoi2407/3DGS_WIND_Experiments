# 공간 수렴 보완 실행

2026-09-08 Wind3DGS experiments-side R1. 사용자 승인한 공간 수렴 보완 계획을 연속 진행한다.
[실험 README](../R1_teacher_spatial_remediation/README.md)와
[code 계약](../../code/sessions/2026-09-08_07_teacher_spatial_remediation.md)을 따른다.
기존 공간 실패·15개 Newton 개발용 샘플과 raw artifact는 보존한다.

고정 quadratic field의 내부 힘과 ring/질량 원인을 분리하고, 독립 spline 판·P2 C0IP 후보의
원래 초기값/추가 압력 응답을 비교한다. 새 처방 압력 조건으로 기존 실패를 덮어쓰지 않는다.
결과는 ignored `artifacts/runs/teacher_spatial_remediation/`와 compact evidence에 기록한다.
Teacher 채택·비선형 shell·공기역학·본 학습 데이터 적격성은 별도 미검증이다.

## 최종 실행·검산 기록
신규 27개+회귀 72개가 통과했다. 원인/P2와 P3를 각각 독립 재실행했고 runtime.json 외 byte가 일치했다.
| run | 시간 [s] | inventory 파일 | inventory byte |
| --- | ---: | ---: | ---: |
| 20260908_cubic_v1 | 104.291 | 16 | 146317681 |
| 20260908_cubic_v1_replay | 106.025 | 16 | 146317681 |
| 20260908_reference_v1 | 45.784 | 55 | 45156771 |
| 20260908_reference_v1_replay | 41.826 | 55 | 45156770 |

원인/P2 report SHA-256: `b5c3929f2e65160f9f8127fe4ea9612e41a0871a5554c4efd5bcec0e77249fd7`.

P3 report SHA-256: `799a48aa00e9eb40085ad030298d90a409959332092fbfdc784b312bc2cb46ac`.

P3 처방 압력 조건은 공간·방향·독립 기준 비교에서 연속 시간 상한을 포함해 1%를 통과했다.
최대 n=8→16 속도 차이 0.13638%, 상한 0.52662%다. 기존 x² 속도 실패는 보존했다.

원래 공간 실패 run의 1,509 inventory와 producer source 30개도 검산했다. 새 두 run의 완료 inventory는
각각 55/16개이며 replay에서 54/15개가 byte 일치했고 유일한 차이는 runtime.json이다.
한국어 수렴 그래프·내부 힘/고유진동수 그림을 생성하고 직접 확인했다. Matplotlib 기본 cache는 read-only라
최초 생성에서 /tmp fallback을 썼고, 재생성 스크립트는 workspace-local cache를 쓰도록 보정했다.

사용자에게 본 학습 초기 상태 범위를 질문했다. 답변 전 기존 입력군·기준을 제외하지 않는다.
비선형 shell·실제 바람·새 producer 연결은 후속 범위다. 기존 Newton 15개 샘플의 적격성은 false로 유지한다.
Code/experiments 파일만 추가·갱신했다. Root/ideas 기존 변경은 유지했고 stage·commit·push·fetch는 하지 않았다.
