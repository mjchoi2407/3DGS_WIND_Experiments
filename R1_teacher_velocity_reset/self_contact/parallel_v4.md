# GPU 접촉 병렬 실행 개선·v4

이 문서는 당시v4 검증 근거다. 현재 실행 스크립트와 추가 비용 개선은 [BVH v5](broadphase_v5.md)를 따른다.

## 현재 판정

2026-09-22. 병렬 작업 분배를 개선한 `gpu_contact_parallel_v1`을 구현하고 실제 GTX1080Ti에서
**121개 회귀, 국소6사례56단계, 세 씬6프레임384단계** 검사를 통과했다.
물성·dt·barrier·FP64 실제 연산·힘/기하/CCD 승인 기준은 바꾸지 않았다.
세 스크립트는 새 `three_scenes_gpu_bend500_manual_v4`를 사용한다. 기존v1/v2/v3는 보존했다.
본 preload/calm/wind 궤적은 실행하지 않았으며 검증 프로세스는 모두 종료됐다.

아래 초기 검증 당시에는 **실측 가속 배수가 미확정이었다.** 사용자가 다른 GPU 작업 중임을 확인한 환경이다.
새 경로에 추가 버퍼와 launch 비용이 있으며 모든 작은 사례에서 더 빠르다고 주장하지 않는다.
이번 채택은 직접 실행할 개발 후보의 기능 검증이지 최종 성능/R1 채택이 아니다.
후속으로 사용자 GPU 유휴 확인 후 [초기v1/v4 및 ON/OFF 재측정](idle_performance.md)을 완료했다.
전체 개선과 마지막 병렬화만의 불확실한 추가 효과를 구분하며, 아래 공유 부하 기록은 그대로 보존한다.

## 병렬 처리의 변경과 남은 부분

| 구간 | v3 구조 | v4 구조 |
| --- | --- | --- |
| AABB 진단 후보 수 | 후보마다 공용 atomic | primitive 질의 스레드의 지역 합을 한 번 기록 |
| 미분 공통 항 | 쌍마다12행에서 최근접 feature/barrier/mollifier 반복 | 쌍마다 한 번 계산·GPU 버퍼 재사용 |
| gradient/Hessian·조립·HVP | 전체 버퍼 용량만큼 논리 스레드 실행 후 guard | 고정 worker가 GPU의 실제 후보 수까지만 stride 처리 |
| 시간 중간 CCD | 후보별 검사 후 공용 alpha atomic | 128후보 단위 GPU 큐·블록별 최소 보폭 합산 |

원래부터 후보 쌍은 GPU에서 병렬 검사했다. v4는 병렬화 자체의 신규 도입이 아니라 작업 분배와
공용 메모리 경합의 개선이다. GPU 큐는 먼저 끝난 블록에 다음 묶음을 배정하지만 한 묶음 안의
CCD 반복 편차까지 없애지는 않는다. 같은 쌍의 시간 전진과 이전 상태에 의존하는 substep은 순차다.

BVH 구축/refit/질의, 정밀 거리/힘/HVP, 경로 CCD, 솔버·독립 검산·실패 복원은 GPU다.
전체 frame graph와 자식/조건 본문62개에서 host copy/callback0을 확인했다.
고정 topology·초기 구조 준비와 프레임 파일 출력은 CPU이며 이를 GPU 계산 fallback으로 세지 않는다.

남은 병목 후보는 primitive별 BVH 순회·질의 내부 거리 검사, 활성 후보 슬롯의 atomic,
정점별 힘/HVP 합산 atomic, 변형이 큰 고정 BVH의 품질, FP64 shell/선형 풀이 비용이다.
Nsight의 SM 점유율·메모리 처리량 profile이나 단독 GPU 시간 기여도까지 검증한 것은 아니다.

## 작업량·메모리의 변화

GTX1080Ti의28개 SM에서 pair worker는896개, 행별 미분 논리 실행 폭은10,752다.
직사각형의 기존696,192개 논리 실행 폭보다 작다. worker가 여러 후보를 처리하므로
필요한 후보 계산을 생략하거나64.7배 빨라졌다는 의미는 아니다. 공통 항 준비 kernel이 추가된다.
CCD는 최대56블록×128스레드로 시작하며 GPU 큐에서 나머지를 처리한다.

공통 항 버퍼는 후보당160byte이고 솔버/독립 검산에 각각 별도 할당한다.

| 씬 | 추가 공통 항 버퍼 합계 | 유지된 접촉 Hessian 합계 |
| --- | ---: | ---: |
| 직사각형 | 17.71MiB | 63.74MiB |
| 손수건 | 9.03MiB | 32.52MiB |
| 삼각 깃발 | 6.87MiB | 24.71MiB |

총 VRAM/peak가 아닌 이 배열들의 산술값이다. CCD cursor는 객체당4byte다.
용량·정확한 byte·실행 폭은 [비교 JSON](parallel_v4_checks/comparison.json)이 소유한다.

## 검증 결과

- 관련18개 모듈 **121 passed in50.54s, skip0/fail0**. 저장소 전체 검사나 속도 벤치마크가 아니다.
- 새 검사8개는 force-only/full-Hessian×worker1/3의 다중 순회, 정확 용량/한 칸 부족,
  후보 중복·누락, 독립 전수 AABB 개수, CCD 블록1/3×반복 한도1/128을 포함한다.
  후보 수0/1/127/128/129/1,025/2,049/0의 그래프 재실행과 마지막 후보만 위험한 경우를 대조했다.
  기존 CPU IPC 힘·에너지·HVP, 터널링/이차 되돌림, 비유한 값, 기하 한도·GPU rollback 검사도 유지했다.
- 동결v4의 면/엣지/고속×barrier1,000/10,000:56단계 전체 GPU 승인·CPU oracle 대조 통과.
- 세 씬의 rest 시작 중력/최대풍 각1프레임:384단계 전체 flag0. 장기 접힘/실접촉 궤적의 근거는 아니다.
- 같은v3 대비 최대 hi 위치 차이2.52e-17m, hi 속도5.40e-13m/s, 외력 차이0.
  사전 상태 대조 한도rtol1e-7/atol2e-9와 기존 GPU 검산을 유지했다. Wind의 총 GMRES 반복은
  직사각형788→787, 손수건527→526, 삼각 깃발547→548로 달랐다. 완전한 반복 수/bitwise 동치를 주장하지 않는다.
- 측정 도구도 작은2단계 면 접촉에서 기존/재사용/새 병렬3경로의 요소별 graph와 프레임 실행을 확인했다.
  각 경로 예열1회·측정1회는 모두 승인됐다. 공유 GPU 결과에서는 새 경로가 항상 빠르지 않았고,
  [원본](parallel_v4_checks/measurement_tool_check.json)은 `performance_eligible=false`로 보존한다.

소스244개와 입력/native hash, 원시 상태, 재현 명령은 [검증 snapshot](parallel_v4_checks/README.md)을 따른다.
R1에는 제한 개발 검증으로 반영하고 PDF/bundle을 갱신했다. Gate·학습 적격성은 그대로 미완료다.

## 사용자 실행·비용 재측정

본 시뮬레이션은 사용자가 한 GPU에서 하나씩 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_rectangle.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_handkerchief.sh
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_triangular_flag.sh
```

기존 경로/재사용만/새 병렬/동일 실행기 접촉 OFF 비용을 비교하려면 GPU가 빈 것을 확인한 뒤 실행한다.
OFF는 접촉이 없었던 프레임의 실험 대조군에만 사용하며 운영 경로의 fallback이 아니다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_performance.sh --gpu-idle-confirmed
```

출력은 `artifacts/runs/p3_self_contact/performance_idle_v4`다. `--shape reference_rectangle`로
범위를 줄이거나 `--components-only`로 요소별 연산만 측정할 수 있다. 재실행에는 새 `--out`이 필요하다.
위 기본 출력의 첫 측정은 완료됐다. 다시 실행하려면 반드시 새 `--out`을 지정한다.
각 성분은 graph 내부20회 연산·CUDA event3표본, 프레임은 같은 상태로 초기화·예열 후 순서 회전한다.
`reuse_on`은 새 pair/CCD 구조만 끈 대조이며 AABB 진단 카운터 지역 집계는 공통이다.
따라서 동결v3 전체 비용의 정확한 재현과 구분한다. 단독 조건에서도 시간 분산·실패 분모를 확인해야 한다.

원격 fetch·다운로드·설치·commit·push는 하지 않았다. 다른 GPU 작업은 중단하지 않았다.
