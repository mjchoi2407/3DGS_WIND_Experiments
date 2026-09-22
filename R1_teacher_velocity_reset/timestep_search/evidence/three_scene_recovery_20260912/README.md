# 빌드 문자열 호환성·시간 한도 복구와 비용 급증 분석

사용자 요청: Python 호환성 검사 보완, 첫 씬 한도를 임시 제거, 비용 급증 구간의 대응 방법 조사.
기존 v2 원본은 보존하고 새 v3로 검산된 prefix를 복사한다. 364frame(6.0667초) 이후 재개,
추가 두 씬은 rest에서 시작한다. 세 씬 모두 이번 묶음의 시간 한도는 없다.
기존 프로세스 사용 시간도 누적 기록에 보존한다. 중단된 frame364의 미확정 부분은 v2에 보존한다.

## 호환성 보완

기존 Python3.12.3의 빌드 날짜 문자열만 달라 후속 worker가 시작 전 차단됐다.
새 키는 Python 버전(패치 포함), 구현, ABI cache tag, machine, byte order,
NumPy/SciPy/Warp 버전이다. Legacy sys.version은 첫 버전 토큰만 비교하며
새 실행은 상세 키를 동결한다. 빌드 설명은 migration provenance에 남긴다.
이는 서로 다른 수치 라이브러리나 Python 패치 변경을 무시하는 처리가 아니다.

## 병목과 전문 자료

느린 구간: frame159~172 및191~210(약2.65~2.883초,3.183~3.517초).
frame167은 전체 풀이110.693초 중 보조 행렬32회 재구축에85.588초(약77%)를 썼다.
한 번 재구축에276개 coloring 방향의 HVP와 희소 LU 분해가 필요하다.
4회마다 갱신은 frame당4회가 아니라 **선형 풀이4번마다**이며, 2회 Newton×64step이면 최대32회다.
첫 rest 단계는 수렴에 성공했지만 최대 선형 반복35가 임계32를 넘어 다음step부터 current로 전환됐다.
대표 첫 rest 단계1.185초 대비 후속 current 단계 평균1.738초로, 반복 수 감소가 비용 감소를 뜻하지 않았다.
[실측](preconditioner_cost.json).

검토 우선순위:
1. 성공한 rest 풀이를 반복 수만으로 즉시 바꾸지 않고, 실제 비용을 보고 전환한다.
   먼저 동일 느린 상태에서 rest 유지와 현행 전환을 비교한다. 선형 풀이의 참 잔차·최종 힘 기준은 유지한다.
2. current가 필요한 경우 보조 행렬 갱신 간격4→16→64를 비교한다.
   실제 HVP 연산자와 참 잔차는 항상 현재 상태를 쓰며, 재사용하는 것은 보조 행렬뿐이다.
3. 고정 간격 대신 반복 증가·수렴 악화·재시도에 맞춰 보조 행렬을 갱신한다.
   프레임을 넘어 재사용하려면 재시작 이력 계약도 함께 검증해야 한다.

PETSc는 preconditioner 갱신 간격을 지정하는 공식 API를 제공한다.
https://petsc.org/main/manualpages/SNES/SNESSetLagPreconditioner/
SUNDIALS CVODE도 행렬 구성·분해 비용을 줄이기 위해 재사용하며,
이전 풀이 성공/실패·시간 계수 변화·마지막 갱신 이후 단계 수를 갱신 판단에 사용한다.
https://sundials.readthedocs.io/en/v7.2.0/cvode/Usage/ (3.4.3.10.2)
위 방법의 본 코드 적용 효과는 **아직 미시험 가설**이다. 이번 복구 묶음의 물리·보조 풀이 정책은 변경하지 않는다.


## 검증과 실행

CPU6개 검사 통과: 빌드 날짜 차이는 허용하고 Python 패치·NumPy·ABI 변경은 거부하는 검사 포함.
[로그](tests.log). 새 환경에서 직사각형 frame363과 추가 두 씬 frame1을 각각64단계 재계산했다.
모두 공식 원식 검산 통과, 기존 저장 경로와 위치·속도 차이0.
[GPU 결과](compatibility_gpu_checks.json), [시험 코드](compatibility_probe.py).
기존 확정364프레임의 trace·metadata·단계 로그를 원본 hash로 검증하고 독립 복사 후 다시 검사했다.
기존 v2 report와 v3 provenance report의 바이트 일치도 확인했다. 원본을 수정하지 않았다.
[복구 정보](migration.json), [v3 계획](plan.json), [동결 hash](runtime_manifest.json).

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_three_scenes.sh
```

같은 명령이 이제 `20260912_three_scenes_10s_v3`를 사용한다.
직사각형은6.0667초(364frame)에서, 추가 두 씬은0초에서 시작한다.
이번 v3는 **세 씬 모두 시간 한도 없음**이며, 수치 실패·검산 실패·사용자 중단 처리는 유지한다.
시간 한도 제거는 이번 묶음에만 적용했다. 원래 준비 함수의 기본4시간 한도는 유지한다.
검증용 일부 프레임만 재계산했고 본 궤적의 새 프레임은 아직 계산하지 않았다.
순수한 환경 호환성 키와 controller/복구 설정 변경이며 행렬 전환·재사용 정책은 현행 그대로다.

전문 자료는 실제 웹 조회했고 코드·실험 원격 fetch나 dependency 다운로드·설치는 하지 않았다.
Code/experiments 변경은 미커밋·미푸시 상태다.
