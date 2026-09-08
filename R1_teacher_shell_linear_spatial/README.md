# Shell 선형 공간 응답 검사

2026-09-08 Wind3DGS R1 개발 진단. 사용자의 샘플 학습데이터 생성·검증까지 연속 진행 지시에 따라
[공간 검사 설계](../../code/sessions/2026-09-08_05_teacher_shell_linear_spatial_design.md)를 실행한다.

1m 사각형, 같은 x² 초기 변위, n=4/8/16과 forward/backward/checkerboard의 9개 사례다.
전체 normal modal 해를 10,241개 공통 시각에 저장하고 공통 3,072개 probe에서 비교한다.
시간 적분 step은 없고 기존 비선형 시간 검증 결과는 입력 무결성·시간 척도 연결에만 사용한다.
기준은 각 방향의 위치·속도 차이 감소 및 finest 1% 이하, n=16 방향 pair 1% 이하다.
`teacher_eligible=false`, `convergence_status=not_assessed`이며 학습 데이터 적격성과 구분한다.

```bash
bash code/scripts/audit_teacher_shell_linear_spatial.sh \
  --full-source-run ../experiments/artifacts/runs/teacher_shell_full_refinement/20260908_reference_v1 \
  --output ../experiments/artifacts/runs/teacher_shell_linear_spatial/my_new_run
bash code/scripts/audit_teacher_shell_linear_spatial.sh \
  --verify ../experiments/artifacts/runs/teacher_shell_linear_spatial/my_new_run
```

Launcher가 code로 이동하므로 인자는 code 기준이다. 실행당 상한 1,800초, 출력 덮어쓰기·자동 resume는 없다.
Raw run은 ignored `artifacts/runs/teacher_shell_linear_spatial/`에 보존한다.
128 frame chunk·이전 chunk hash·마지막 성공 checkpoint와 실패/부분 파일을 구분한다.
실제 결과와 전체 frame 검산은 실행 후 아래에 갱신한다.

## 실제 결과와 검산

두 run의 9개 사례·각 92,169 frame이 완료됐다. Source·algebra·mapping·linear response 검사는 통과했으나
**공간·방향 기준은 실패**했다. 아래는 A와 Aω_*로 정규화한 공통 probe RMS의 고정 시각 최대 차이다.

| 방향 | n=4→8 위치 [%] | n=8→16 위치 [%] | n=4→8 속도 [%] | n=8→16 속도 [%] |
| --- | ---: | ---: | ---: | ---: |
| forward | 5.956244 | 2.927207 | 22.169172 | 23.209961 |
| backward | 5.956244 | 2.927207 | 22.169172 | 23.209961 |
| checkerboard | 3.857861 | 1.395752 | 21.043244 | 22.685509 |

위치는 감소하지만 finest 1%에 못 미쳤고, 속도는 감소하지 않았다.
N=16 방향 비교는 forward↔backward 위치 0.570938%·속도 8.558328%,
forward/backward↔checkerboard 위치 21.203509%·속도 51.546194%다.
필터·모드 제거·n 추가·초기 함수 변경·판정 기준 완화는 적용하지 않았다.
이 유한 ladder의 실패는 모든 shell/초기값이 발산한다는 판정이 아니다.

최대 상대 에너지 drift는 6.00209e-12, 무차원 EOM 잔차는 1.45258e-12다.
기존 mapper에는 정확히 표현 가능한 dyadic mesh만 float32로 전달하고 proper rotation 후 앞면 −Y를 명시했다.
고정된 9개 사례의 3,072 probe 모두 지원됐고 초기 P1 오차는 A/(4n²) bound와 float64 roundoff 범위 안이다.

각 run의 **모든 frame**을 다시 계산해 K/M·modal 식·반력·pin·에너지, 매핑과 비교 시계열·CSV·판정을 확인했다.
두 report와 1,508개 inventory 파일의 byte가 일치한다. 차이가 나는 유일한 inventory 파일은 runtime.json이다.
Report SHA-256은 `3a0d8e7ee5be505b190008d387c67a113a027ce0651595cb43b0812c8c33ba1a`다.

| run | audit [s] | 전체 frame 검산 [s] | inventory 파일 | inventory byte |
| --- | ---: | ---: | ---: | ---: |
| 20260908_reference_v1 | 113.373 | 30.874 | 1509 | 266249546 |
| 20260908_reference_v1_replay | 40.772 | 29.878 | 1509 | 266249545 |

CPU/I/O cache와 다른 검증의 자원 사용이 포함된 실행 시간이며 성능 benchmark가 아니다.
두 raw run은 `artifacts/runs/teacher_shell_linear_spatial/`에 보존한다.
[원본 report](evidence/report.json), [원본 manifest](evidence/manifest.json),
[재실행 manifest](evidence/replay_manifest.json), [검산 결과](evidence/verification.json),
[provenance](provenance.json)를 함께 회수한다. Snapshot은 기존 25개+신규/재사용 5개, 총 30개다.
CLI는 계산이 완료돼도 물리 기준 실패 시 exit 1을 반환한다. `--verify`는 보존된 실패 판정까지 재계산해 통과할 수 있다.

신규 16개와 기존 184개, probe/map/trajectory 28개를 합친 **228개 검사**를 확인했다.
첫 확장 실행에서 Newton probe-trajectory 10개가 기본 cache의 read-only 권한 때문에 실패했고,
`WARP_CACHE_PATH=code/outputs/warp-cache`로 해당 10개를 다시 실행해 모두 통과했다.
그 외 수치 실패는 없었다. CPU 환경의 CUDA driver 오류 출력은 GPU 검증 통과를 뜻하지 않는다.
새 [개발용 샘플](../R1_teacher_sample_dataset/README.md)은 기존 Newton native 경로의 별도 데이터이며,
이 선형 shell 공간 검사를 통과한 Teacher로 표시하지 않는다. Commit·push·fetch는 수행하지 않았다.
