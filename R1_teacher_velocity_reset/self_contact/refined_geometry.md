# GPU 기하 미인증 해결·v2 실행

후속 실행 스크립트는 같은 기하·충돌 승인 조건의 성능 후보 **manual_v3**로 갱신했다.
[v3 성능 점검](performance.md)과 [현재 실행 명령](gpu.md#세-시뮬레이션-실행)을 따른다.
아래 v2 실험과 당시 manual_v2 준비 기록은 과거 근거로 보존한다.

## 현재 상태

확인일2026-09-22. 기존 기하 충분조건 때문에 거절됐던 **4사례12구간을 모두 정밀 GPU 검산으로 인증했다.**
면/엣지/고속×barrier1,000/10,000의6사례56단계 모두 힘·위치·에너지·핀·기하·시간 CCD 검산을 통과했다.
사용자 승인에 따라 기하 판정 방법만 보강했고 재료·barrier·dt와 접촉 최소 간격은 유지했다.
관련106개 검사는 skip 없이 통과했다. 큰 회전/늘어남의 승인뿐 아니라 실제 퇴화·시간 중간 붕괴·
거의 퇴화·비유한 값·버퍼/깊이 한도 거절과 GPU 프레임 복원도 포함한다.

초기 v1의 실패는 [이전 GPU 보고](gpu.md)에 그대로 보존한다. 새 수학적 인증 없이 flag를 지운 것이 아니다.
원리·수치 여유·GPU 큐/graph 계약은 [정밀 인증 API](../../../code/docs/refined_metric_certificate.md)가 소유한다.
전체 장기 궤적·곡면 전역 인증·proxy 응답 수렴·실장면 물성 calibration·R1/학습 적격성은 별도다.
사용자 요청으로 v2 본 계산은 종료했다. 수동 실행 전용 `manual_v2`는 파일 준비·hash 검증만 완료했으며 미실행이다.
추가 비용의 저장 결과 대조와 비교 한계는 [비용 보고](cost.md)를 따른다.

## 왜 해결됐는가

기존 `1-3s>0`은 변형 방향과 부호를 최악값 하나로 묶은 충분조건이다.
새 검사는 실패 영역의 두 접선으로 만든2×2 Gram 행렬을 그대로 사용한다.
영역 전체에 대한 양의 면적 하한을 계산하고, 불확실하면 검사 영역만 공간4분할×시간2분할한다.
최대 깊이2, GPU 큐 `max(1024,8*elements)`가 준비되며 한도 초과 시 계속 거절한다.
실제 상태는 이전과 같은 Newmark 계산 결과다. 검사 영역 세분화는 simulation mesh/dt 변경이 아니다.

또한 hi/lo를 더한 뒤 큰 좌표끼리 빼던 기하 control 계산을 보정 뺄셈으로 바꿨다.
2^40 공통 이동에서도 국소 변형을 lo에 보존하는 GPU 반례/정상 검사를 통과했다.
이 기하 단위 검사를 전체 접촉의 임의 절대 좌표 정밀도 보장으로 확대하지 않는다.

## 같은 접촉 사례 재계산 결과

v1과 같은 E100Pa,h1mm,면밀도0.1kg/m², 초기8mm 간격, 외력0,dt1ms.
면/엣지8단계, 고속12단계다. 양쪽 run은 같은 GTX1080Ti에서 개별 순차 실행했으며
다른 시점의 짧은 표본 시간으로 가속 배수를 주장하지 않는다.

| 사례 | k | 기존 미인증 | v2 최종 판정 | 최대 세분 깊이 | GPU 풀이 / 검산 |
| --- | ---: | ---: | --- | ---: | ---: |
| 면0.2m/s | 1,000 | 0 | 8/8 통과 | 0 | 0.360 / 0.130s |
| 엣지0.2m/s | 1,000 | 0 | 8/8 통과 | 0 | 0.374 / 0.139s |
| 면1m/s | 1,000 | 2 | 12/12 통과 | 0 | 0.548 / 0.147s |
| 면0.2m/s | 10,000 | 1 | 8/8 통과 | 0 | 0.422 / 0.138s |
| 엣지0.2m/s | 10,000 | 2 | 8/8 통과 | 1 | 0.386 / 0.135s |
| 면1m/s | 10,000 | 7 | 12/12 통과 | 1 | 0.557 / 0.186s |

깊이0은 영역을 나누지 않았다는 뜻이다. 기존 검사가 실패한 경우에도 행렬 하한을 추가 계산했다.
검사한 모든 하한은 양수이며, 의도적으로 불확실한 반례는 승인하지 않았다.
기존 raw hi/lo 전 성분과 새 결과의 최대 차이는8.89e-16 이하로, 궤적을 바꿔 실패를 피한 것이 아니다.
별도 CPU longdouble 행렬 인증 및 IPC Tight Inclusion 시간 CCD와 대조했다.

원시 run:

- `experiments/artifacts/runs/p3_self_contact/gpu_strength_v2`
- `experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v2`

`coarse_geometry_flags`와 `geometry_refinement`를 새 NPZ에 추가했다.
앞의 flags는 이전 기준의 실패를 보존하고, 후자는 양의 면적비 하한/영역 수/깊이/미인증 수/status를 저장한다.
기존6열 물리·기하 `checks`는 덮어쓰지 않는다.

작은 보고서·비교 그림·원시6사례·명령은 [완료 근거 묶음](refined_gpu_checks/README.md)에 보존했다.
각 run의 `run_manifest.json`과 보고서/동결 manifest가 source·config·native·입력 hash를 소유한다.

## 실제 세 씬 연결 검증

초기3검사와 각 씬의 rest 시작 중력/최대풍64단계 프레임을 새 GPU 정책으로 재실행했다.
총6프레임384단계가 모두 flag0이며 GPU 그래프의 자식/조건 분기까지 host copy/callback0이다.
아래는 setup·파일 저장을 제외한 GPU 풀이+독립 검산의 단일 실행 시간이다.

| 씬 | 중력 프레임 | 최대풍 프레임 |
| --- | ---: | ---: |
| 직사각형 | 13.117s | 23.276s |
| 손수건 | 3.428s | 4.187s |
| 삼각 깃발 | 3.111s | 13.325s |

이 짧은 프레임에는 활성 접촉이 없다. 실제 접촉 승인은 앞의6사례에서 확인했으며,
전체 씬의 장기 접힘·시간 수렴·학습 적격성이 검증된 것은 아니다.
전체 실행 준비 때 WSL 밖으로 추정되는 추가 GPU 부하도 관측했다. 다른 작업을 종료하지 않았으며,
위 시간과 전체 run 시간으로 단독 GPU 성능이나 가속 배수를 주장하지 않는다.

## 세 씬 스크립트

기존 개별 스크립트 이름을 유지하고 사용자 직접 실행용 기본 출력을
`experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v2`로 분리했다.
준비된 입력/runtime/native manifest는 검증한 v2와 정확히 같다. 새 GPU 계산은 시작하지 않았다.
v1은 기록용이며 새 실행기는 이전 기하 정책의 run 실행 요청을 거절한다.
원본 bend500 mesh/forcing/material/plan의 byte/hash와 preload→calm/wind 분기 계약은 유지한다.

```bash
# workspace 루트. 사용자가 실행할 때만 계산한다. 한 씬씩 선택 실행:
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_rectangle.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_handkerchief.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_triangular_flag.sh
# 또는 아래 하나로 세 씬을 순차 실행한다. 개별 실행과 중복하지 않는다.
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action run
# 상태 확인
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_three_scenes.sh --action status
```

각 씬만 실행할 때는 `run_gpu_rectangle.sh`, `run_gpu_handkerchief.sh`, `run_gpu_triangular_flag.sh`를 사용한다.
중복 실행은 execution lock으로 막는다. 기존 outputs/log를 덮어쓰거나 자동 재개하지 않는다.
본 계산이 실행 중인지·완료·실패인지는 해당 run의 `run.log`와 `outputs/report.json`을 따른다.
각 씬은 접촉 ON preload120프레임과 같은 preload에서 독립 시작하는 calm/wind 각240프레임이다.
2026-09-22 검증 후 시작했던 v2 순차 실행은 사용자 요청으로 종료했다. 직사각형 preload70프레임의
파일 hash·모든4,480개 검산 flag0을 확인해 보존했고, 손수건/삼각 깃발 본 계산은 시작하지 않았다.
종료한 두 프로세스의 부재를 확인하고 v2 report를 `interrupted`로 기록했다. 종료 전 report는
`report.before_user_stop.json`, 종료 사유는 `interruption.json`으로 보존했다.
미저장 진행 프레임·최종 preload checkpoint를 승인하거나 자동 재개하지 않는다. 삭제한 출력은 없다.
이후 본 계산은 사용자가 위 스크립트로 직접 시작한다.

재검증 재현:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_validation.sh \
  --out experiments/artifacts/runs/p3_self_contact/gpu_strength_v2_repeat
```

현재 환경은 Python3.12.3/NumPy2.4.4/SciPy1.18.1/ipctk1.6.0/Warp1.17.0,
GTX1080Ti·driver582.28/API13000이다. cuDSS와 shim은 v1과 같은 원본 hash를 유지한다.
실행 source와 입력은 새 run에서 동결하며 v1 artifact를 수정하지 않는다. Git fetch·commit·push 없음.
