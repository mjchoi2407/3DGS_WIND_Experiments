# GPU 프레임 진행·solver/collision 계측 v8

## 결과

2026-09-22부터 세 씬 사용자 실행 스크립트는 `three_scenes_gpu_bend500_manual_v8`을 사용한다.
BVH v5의 수치 경로·입력·물성·승인 기준은 유지하고, 프레임마다 GPU 내부 구간 시간을
터미널과 `<shape>/run.log`에 동시에 출력한다. 별도 진행 조회 명령은 필요 없다.

출력의 `solver 전체`는 적분·Newton/Krylov 및 그 안의 접촉 계산을 포함한다.
`collision 합계`는 solver와 독립 audit에서 호출된 접촉 evaluate/HVP/path의 합이고,
`audit 전체`에도 audit collision이 포함된다. 따라서 세 값은 중첩되며 서로 더하지 않는다.
`GPU 프레임`은 graph 제출부터 장치 동기화까지의 벽시계 시간이다. GPU marker kernel과
scheduling 비용이 계측값에 포함되며 순수 kernel 시간으로 해석하지 않는다.

기본 출력 예시는 다음과 같다.

```text
reference_rectangle/wind: 1/240프레임 [passed] | GPU 프레임 3.909초 | solver 전체 3.757초 (그중 collision 0.384초) | collision 합계 0.485초 (solver 0.384/audit 0.101) | audit 전체 0.329초 (그중 collision 0.101초) | GMRES 누적 788
```

부모 프로세스는 worker 표준 출력을 줄 단위로 터미널과 로그에 복제한다. 이는 프레임 종료 뒤의
CPU 파일 I/O일 뿐 solver/collision 수치 계산을 CPU로 옮기지 않는다. 실패 프레임도 `[failed]`와
시간을 먼저 출력한 뒤 GPU rollback 결과를 저장한다.

## 제한 검증

GTX1080Ti에서 rest 시작 중력/최대풍 각1프레임, 세 씬 총6프레임·384 substep이 승인됐다.

| 씬 | 구간 | GPU 프레임 | solver 전체 | collision 합계 | audit 전체 |
| --- | --- | ---: | ---: | ---: | ---: |
| 직사각형 | 중력 | 2.133s | 1.836s | 0.336s | 0.322s |
| 직사각형 | 최대풍 | 3.909s | 3.757s | 0.485s | 0.329s |
| 손수건 | 중력 | 1.625s | 1.371s | 0.274s | 0.256s |
| 손수건 | 최대풍 | 2.399s | 2.230s | 0.380s | 0.263s |
| 삼각 깃발 | 중력 | 1.489s | 1.222s | 0.252s | 0.264s |
| 삼각 깃발 | 최대풍 | 2.252s | 2.072s | 0.361s | 0.265s |

관련 GPU 회귀는 **140개 통과, skip0/fail0**다. 동일 smoke의 v5 대비 v8 위치 hi 최대 차이는
`4.46e-17m`, 속도 hi 최대 차이는 `4.52e-13m/s` 이하다. 여섯 프레임의 v5 대비 시간 변화는
`-6.5%`부터 `+2.9%`, 중앙값 `+0.95%`였다. 단일 순차 실행 대조라 계측 overhead의 확정값으로
쓰지 않지만, 뚜렷한 퇴행은 관찰되지 않았다.

v8 suite/manifest SHA-256은 각각
`992ab0144021613aeb26eb3442005abb9e420a783f224425b68c1882c6404f59`,
`6eea4a53db03041fe584ace97ffc9ba81da853ce75503b753915d97e7c2a4f95`다.
세 씬 smoke만 존재하며 본 `outputs`는 없다.

## v5 장기 실행에서 확인된 실패

사용자가 시작했던 v5 직사각형 실행은 preload120프레임과 calm240프레임을 완료한 뒤,
wind에서104프레임을 승인하고 다음 프레임(index104)에서 중단됐다. 실패 코드는99,
`failure_flags=[0,14]`, `first_bad=1`이며 contact/path status는 모두0이다.
프레임 시작 상태로 복원한 원본은 `manual_v5/reference_rectangle/outputs`에 보존했다.
따라서 이를 세 씬 장기 완주나 training 적격성 근거로 세지 않는다. v8은 진행 계측을 추가한
새 실행 묶음이며 이 장기 수치 실패 자체를 우회하거나 승인 기준을 완화하지 않는다.

## 사용자 실행

개별 스크립트는 별도 옵션 없이 해당 씬 전체 실행을 시작한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_rectangle.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_handkerchief.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_triangular_flag.sh
```

세 씬을 한 GPU에서 순차 실행할 때만 묶음 스크립트에 `--action run`을 준다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
```
