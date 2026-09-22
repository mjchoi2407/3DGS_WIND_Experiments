# 세 씬 64회 재구축 적용·이어가기 v4

## 현재 상태

2026-09-12 사용자 요청으로 검증된64회 재구축을 세 씬에 공통 적용한 동결 묶음을 준비했다.
본 계산 미시작. 직사각형은 기존364frame(6.0667초)부터, 삼각 깃발과 손수건은0초부터 시작한다.
세 씬 모두 시간 한도 없음, 목표600frame/10초. 기존 원본v2/v3와 검증 결과는 보존했다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_three_scenes.sh
```

상태 조회는 같은 명령에 `--status-only`를 붙인다.
출력: `experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4`.

## 적용 정책

재구축 간격을 선형 풀이4회에서64회로 변경했다. 세 씬의 이후 모든 프레임에 같은 설정을 적용한다.
rest/current 전환 기준32와 선형 실패 시 fallback, 프레임 경계의 이력 초기화는 유지한다.
행렬이 오래됐을 때 조기 갱신하거나 측정 비용에 따라 전환하는 새 정책까지 구현한 것은 아니다.
기존 최종 힘·위치 기준, 내부 힘 목표30%/EW 상한1e-4,4배dt, 물리·바람은 유지했다.
64회는 step64회나frame64회를 뜻하지 않고 보조 풀이 build 요청64회다.
[5프레임 효과 검증](../preconditioner5_20260912/README.md).

첫 씬의 frame0~363은 기존4회 재구축으로 생성됐으며, 새 설정은 frame364부터 적용된다.
확정 trace·metadata·step journal을 hash 검증 후 독립 복사하고, 이전 구간을64회 결과로 다시 표시하지 않는다.
각 씬 report의 preconditioner_segments와 새 frame metadata에 설정을 남긴다.
[계획](plan.json), [구간별 설정](policy_segments.json), [복구 출처](migration.json), [동결 hash](runtime_manifest.json).
실패/중단 보존·순차 실행·비용/잔차/느린 구간 기록은 이전과 동일하다.

## 검증

- CPU7개 검사 통과. 기존prefix 보존 후 설정 변경 경계 기록·새 씬ready 복구 검사 포함.
- 실제GPU에서 첫 씬의frame364(6.0667~6.0833초)64step 검산 통과.
  이 미래 프레임은 별도 검증에서만 계산했으며 본 실행의 완료프레임 수는364로 유지했다.
- 추가 두 씬의frame1(비영 바람)각64step 검산 통과, 기존 저장 위치·속도 경로 차이0.
- [GPU 결과](gpu_checks.json), [시험 코드](gpu_probe.py), [CPU 로그](tests.log).
- Wrapper shell 문법·동결hash·세 씬한도null·첫 씬364/추가씬0 상태 확인 완료.

추가 두 메시의 큰 변형 구간과 전체10초에서64회 재사용의 효과는 미검증이다.
새 frame364에는 기존 확정 궤적이 없어 기존 궤적 차이는null로 기록했다.
GPU 검산은 힘 재평가·운동방정식 재구성이고 시간 세분 정확도·공간 수렴 인증은 별도 미완료다.
로컬 원본만 사용했으며 외부fetch·다운로드·commit·push는 하지 않았다.
