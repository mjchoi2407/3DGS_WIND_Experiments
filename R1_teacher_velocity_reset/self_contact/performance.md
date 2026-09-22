# GPU 셀프 컬리전 성능 점검·v3

아래는 v3의 보존 기록이다. 현재 실행 스크립트·동결 출력은 [병렬 개선 v4](parallel_v4.md)를
따르며, 이 문서의 v3 시간/버퍼/검증을 v4 전체 성능으로 승계하지 않는다.

## 현재 판정

2026-09-22. **중복 연산 제거·GPU 기능 검증·직접 실행용 세 스크립트 준비 완료.**
최종 가속 배수와 순수 접촉 추가 시간은 미확정이다. 측정 중 같은 입력의 시간이 수배 바뀌었고,
사용자가 다른 GPU 작업의 동시 실행을 확인했다. 해당 부분 측정은 성능 채택 근거로 쓰지 않는다.
본 preload/calm/wind 시뮬레이션은 시작하지 않았다. 과거 v2 종료 결과·manual_v2도 보존한다.

실제 거리·힘·CCD·솔버·독립 검산·복원은 계속 GPU에서 실행한다. 최종 세 씬 그래프의
cuDSS 자식 및 조건 분기 본문62개까지 검사하여 **host copy/callback0**을 확인했다.
초기 topology/구조 준비와 프레임 파일 저장은 CPU다. CPU 프로세스 사용률0을 뜻하지 않는다.
상태 FP64 hi/lo·실제 접촉 FP64·보수 AABB FP32를 유지하며 전체 FP32 이식은 아니다.

## 반영한 변경

1. 첫 GMRES cycle의 중복 보조 RHS 계산과 채택 trial의 다음 Newton 재평가를 제거했다.
   재시작·새 입력·거절된 trial에는 재사용하지 않는다. 첫 수정 후보의 직사각형 중력 프레임에서
   힘 평가256→192회를 계수기로 확인했다. 독립 검산65회는 그대로 유지했다.
2. 활성 접촉0이면 미분·힘 조립·HVP를 GPU 분기에서 생략한다. 출력은 먼저0으로 지운다.
   BVH·교차·퇴화·시간 CCD는 생략하지 않으므로 멀리 있던 천이 새로 접근해도 검사한다.
3. 독립 검산의 불필요한 Hessian 계산·저장을 없앴다. 힘·에너지·시간 경로는 별도 객체에서
   재계산한다. 솔버의 정확한 접촉 Hessian은 유지한다.
4. 접촉 에너지와 큰 proxy의 오차 집계를 FP64 블록 축약으로 바꿨다. 작은 proxy의 계수1,024개
   이하는 추가 launch를 피하려 기존 단일 kernel을 유지한다. 비유한 값·오차 예산 검사는 유지한다.
5. GMRES 작업 배열의0초기화를 병렬 device memset으로 바꿨다. Restart240이면 기존에는
   H의57,840개 원소를 한 스레드에서 순차 초기화했다. Arnoldi·종료 조건·restart 길이는 바꾸지 않았다.

후속 단독 profile에서 각 항목의 시간 기여를 분리해야 한다. 특히5번은 구조적 순차 작업을
제거한 것으로, 아직 전체 시간의 주원인이라고 확정한 것은 아니다.
구현·캐시 무효화·승인 계약은 [code 문서](../../../code/docs/p3_gpu_self_contact.md#접촉-성능-정책)가 소유한다.

### 메모리의 확정된 감소

| 씬 | v2 Hessian 배열 합계 | v3 Hessian 배열 합계 | 감소 |
| --- | ---: | ---: | ---: |
| 직사각형 | 127.48MiB | 63.74MiB | 약63.74MiB |
| 손수건 | 65.04MiB | 32.52MiB | 약32.52MiB |
| 삼각 깃발 | 49.43MiB | 24.71MiB | 약24.71MiB |

솔버+검산의 **접촉 Hessian 배열만** 약50% 감소했다. 총 VRAM/peak/allocator 메모리가
절반이라는 뜻은 아니다. 정확한 byte와 capacity는 [비교 JSON](performance_v3_checks/comparison.json)에 있다.

## 정확성 검증

- 최종 소스의 관련 **113 passed in52.84s, skip0/fail0**. 테스트 벽시계 시간은 속도 벤치마크가 아니다.
  GPU 힘/에너지/HVP와 CPU IPC, 후보 완전성/overflow, 빈 접촉↔활성 접촉 전환,
  force-only 경로, 비유한 오차 거절, GMRES restart/새 RHS/zero RHS, trial 거절 뒤 재사용,
  공간/시간 붕괴·기하 한도 거절·GPU rollback·큰 원점 hi/lo를 포함한다.
- 최종 동결v3의 국소6사례(면/엣지/고속×k1,000/10,000), **56단계 모두 승인**.
  별도 CPU IPC 시간 CCD·상태·기하 인증 대조를 통과했다.
- 최종 세 씬의 rest 시작 중력/최대풍 **6프레임·384단계 모두 flag0**.
  실제 장기 접힘을 대표하지 않는 연결 검사이며 본 `outputs/`는 만들지 않았다.
- 같은 v2 저장 프레임 대비 hi 위치 차이≤1.85e-17m, hi 속도 차이≤4.90e-13m/s, 외력 차이0.
  사전 상태 대조 한도는 rtol1e-7/atol2e-9, GPU 승인 조건은 원래 기준을 유지한다.
  손수건 wind의 총 GMRES 반복은528→527이며 나머지 카운터는 같았다.
  반복 횟수의 완전 일치나 bitwise 동치를 주장하지 않는다.

원본 hash·suite·각 phase 결과·국소 상태는 [최종 검증 snapshot](performance_v3_checks/README.md)에 있다.
R1 접촉 절은 구현 상태/성능 보류를 반영했고 PDF·delivery bundle을 재빌드했다.
방법/Gate·학습 적격성은 변경하지 않았다.

## 공유 GPU 측정의 보존과 한계

`artifacts/runs/p3_self_contact/performance_frames_v3`는 최종v3 직전의 첫 수정 후보다.
GMRES 병렬 초기화와 작은 proxy 분기는 아직 포함하지 않는다. 당시 Python 소스를 hash 대조 후
`runtime/`에 동결했다. 수정 전 구조/수정 후보/동일 실행기의 접촉 OFF를 순차 실행하고,
매번 같은 상태로 되돌려 예열1회·측정3회, 실행 순서를 회전했다. CPU 저장/초기화는 시간에서 제외했다.

직사각형2조건·손수건2조건은 완료했지만, 삼각 깃발 진행 중 사전600초 제한으로 종료됐다.
별도 kill은 보내지 않았으며 다른 작업은 중단하지 않았다. 같은 손수건 중력의 수정 전 시간이
9.015/9.743/2.521초로 흔들렸다. 사용자가 동시 GPU 작업을 확인한 뒤 재측정을 늘리지 않았다.

- [부분 원본 보고](performance_v3_checks/shared_gpu_prototype_report.json)와
  [종료·부하 판정](performance_v3_checks/comparison.json)을 보존한다.
- 원본 `report.json`의 마지막 `running`은 강제 종료 전 snapshot이며, 인접
  `measurement_status.json`의 `incomplete`가 최종 상태다. 실행 중이라는 뜻이 아니다.
- 초기 component 측정(`performance_components_v3`)은 CPU 반복 제출 지연까지 섞여 있다.
  후속 도구는 연산20회를 한 graph에 넣고 CUDA event로 측정한다.
- 위 공유 부하 시간, 과거 [v2 관측 배수](cost.md), 최종 단독 재측정을 섞지 않는다.
  이 기록에서 최종v3의 가속 배수·순수 접촉 증가율을 확정하지 않는다.

## 사용자 실행

이 절은 v3 준비 당시 안내다. 같은 스크립트 이름의 현재 대상·출력명은 위 v4 보고를 따른다.

기존 세 이름은 그대로이며 기본 출력만 `three_scenes_gpu_bend500_manual_v3`로 갱신했다.
각 스크립트는 이제 실제 본 시뮬레이션을 시작한다. 한 GPU에서는 하나씩 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_rectangle.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_handkerchief.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_triangular_flag.sh
```

GPU가 비었을 때 별도 성능 대조만 하려면:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_performance.sh --gpu-idle-confirmed
```

최종 동결 소스·native를 사용하고 `performance_idle_v3`에 저장한다. 본 시뮬레이션 대신 각
초기 중력/최대풍 프레임과 국소 접촉 사례만 비교한다. OFF는 활성 접촉이 없는 씬 프레임의
대조군에만 쓰며 실제 접촉 사례와 운영 실행기의 fallback으로 사용하지 않는다.
`--shape reference_rectangle --repeats 3`으로 범위를 줄일 수 있고, 재실행에는 새 `--out`이 필요하다.
시간 분산·실패 분모를 확인한 뒤 최종 성능 수치를 채택해야 한다.

남은 후보는 대변형 BVH 재구축, 반복 경로 검사 중복의 안전한 재사용, 비접촉 shell의
FP64 힘/HVP와 보조 행렬 비용이다. 기존 접촉 OFF의 M1/M2·Gauss 경로를 접촉 ON에
자동 적용하지 않는다. 추가 정밀도 변경에는 접촉 포함 검증이 필요하다.
네트워크 fetch·다운로드·설치·commit·push는 수행하지 않았다.
