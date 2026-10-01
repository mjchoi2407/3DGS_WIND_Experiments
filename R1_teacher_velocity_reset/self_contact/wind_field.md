# 바람 시간 평활·국소화 비교

## 현재 상태

2026-10-01 완료: 기존 균일·시간 평활·평활 국소 바람이 각각120/120프레임, 총360프레임을 같은 GTX1080Ti에서 순차 완료했다. 물성·감쇠는 기존 추천안 그대로다.
시간 평활은 wind2.5–3.2초 위치/법선10–30Hz 성분을28.7%/17.7% 줄였지만3–4초에는47.6%/24.0% 늘렸다. 국소화는 같은 관찰 구간에서 위치9.4% 감소·법선18.0% 증가로 개선이 일관되지 않았다.
사용자는 세 결과 중 가운데 노란색의 움직임을 가장 선호하고, **시간 평활 균일 바람을 후속 실험의 외력 기준으로 채택**했다. 이 시각 선택은 수치 비교 직후의 채택 보류를 대체한다. 국소 바람은 선택하지 않았다. [선택 조건·적용 범위](#사용자-시각-선택과-후속-외력-기준).
실제 프레임 계산은23.15/24.67/24.83분(기준 대비+6.6%/+7.2%). CPU18개·재시도 GPU26개 검사, 공력 oracle·접촉 smoke 및 실제360프레임 독립 외력 검산을 통과했다. 본 실행 재시도0회다.
초기 국소 setup 실패0프레임은 보존하고 연결만 수정한 새 묶음에서 국소를 완주했다. [원인·재검증](#국소-재시도-연결-수정).
[상세 결과](#완료-결과), [재생 명령](#실행과-재생), [전체 분석 JSON](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/analysis/report.json)의 `cases/attempts/windows`를 따른다.
뷰어0–2초는 공통 원본이고2–4초만 새 계산이다. 전체10초·다른 씬·시간/공간 수렴·학습 적격성은 미판정이다. 이전 [내부 감쇠 추천](vibration_search.md#현재-상태)을 대체하지 않는다.

## 사용자 시각 선택과 후속 외력 기준

2026-10-01 사용자 시각 평가로 **`smooth`(가운데 노란색/주황색)**를 선택했다. CG 움직임의 자연스러움을 우선한 후속 실험 기준이며, 이전 수치 비교만으로 내렸던 채택 보류를 대체한다. 당시 수치·실패 기록은 그대로 보존한다.

- 외력 구성: 공간 균일 풍속의 시간 변화를 Gaussian σ0.1초(60Hz에서6프레임, truncate3σ, nearest 경계)로 평활한다. 비교 입력의 풍속 벡터RMS를 원본과 맞춘다. 중력은 기존대로 유지한다.
- 연속 궤적의 중간에서 기존 입력을 바꿀 때 첫0.4초 quintic smoothstep으로 전환한다. 선택 근거인 이번 실행은 wind2초/궤적7초부터 적용한120프레임이다.
- 물성·솔버: 굽힘 강성1/500, 막5ms·굽힘20ms, 전역 감쇠0, 기하 재사용, 기본64/조건부128, 접촉·검산·rollback을 유지한다. 공간 국소화는 채택하지 않는다.
- 실제 선택 원본은 [동결 suite](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/bundle/suite.json)의 `smooth`와 [선택된 외력](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/bundle/smooth/reference_rectangle/wind/inputs/forcing.npz)의 `wind/gravity`다. 재사용 구현은 [smooth_wind](../../../code/wind3dgs/evaluation/teacher_gpu_wind_field.py)의 같은 이름 함수다.
- 이번 RMS 보정 gain은1.2304518106766804이며 해당120프레임에만 해당한다. 다른 구간·바람 입력에서는 해당 배열에 맞춰 다시 계산해야 하며, 이 값을 전체wind의 고정 배율로 승계하지 않는다. 전체wind 처음부터 적용한 새 궤적은 아직 생성·검증하지 않았다.

같은 솔버에서 바람만 바꾼 결과를 사용자가 선호했으므로 **외력의 시간 변화가 시각적 품질에 영향을 준다**는 근거는 있다. 그러나 이번 평활 입력도3–4초 수치 진동은 증가했다. 솔버의 시간 이산화, 프레임별 공력 hold, 천의 고유 진동 중 어느 영향이 남는지를 분리한 시험은 아니므로 '솔버는 원인이 아니다' 또는 '잔진동이 해결됐다'로 결론내리지 않는다.

이번 갱신은 후속 실험의 조건 선택이다. 완료된 비교 실행의 `reference/smooth/local` 입력·출력·manifest, 기본 솔버 API와 기존 실행 스크립트는 바꾸지 않았다. 새 전체 궤적 묶음에 평활 입력을 반영하는 작업과 실행은 별도이며, R1 수렴·학습 적격성 완료를 의미하지 않는다.

## 조건과 판단 범위

- 사각형 P3, 굽힘 강성1/500, 막5ms·굽힘20ms, 기하 재사용, 전역 감쇠0. 기존 공력60Hz 평가·프레임 hold,64substeps/조건부128, 접촉·독립 검산·rollback 유지.
- 이전 선정안의 wind2초/궤적7초 `frame_0119.npz` raw hi/lo 위치·속도를 세 조건에 그대로 전달한다. 새 계산은 wind2–4초120프레임씩이다.
- `reference`: 기존 공간 균일 풍속. 천 전체의 힘이 같은 것은 아니며, 현재 법선·속도·면적에 따라 공력이 달라진다.
- `smooth`: 원본 전체 바람 배열을 Gaussian σ0.1초로 평활하고, 비교120프레임의 풍속 벡터RMS를 기준과 맞춘다. 첫0.4초는 quintic smoothstep으로 기존 입력에서 전환한다.
- `local`: 위와 같은 시간 입력에 고정 월드 공간 Gaussian 풍속장을 곱한다. 공통7초 형상에서 rest 가로70%·높이50% 노드 위치를 중심으로 σ0.30m, 초기 현재 면적 가중 풍속RMS를1로 정규화한다. 공간 전환도0.4초이며 이후 중심·폭·gain을 고정한다. 바깥의 정지 공기 항력은 유지한다.
- 풍속RMS 일치는 실제 힘·일의 일치를 뜻하지 않는다. 초기 정규화 후 천이 국소장을 벗어나면 받는 바람이 약해질 수 있으므로 실제 공력·일·노출 풍속도 함께 보고한다.
- 사전 지정 분석 구간: 전체2–4초, 전환 후2.4–4초, 관찰점 주변2.5–3.2초, 마지막3–4초. 공통512점 위치 및 표시 삼각형 법선의10–30Hz 성분, raw 두 번 차분, 큰 움직임·속력, 실제 GPU 프레임 비용을 비교한다. 짧은 구간 스펙트럼은 CG 보조 지표다.

## 실행과 재생

프로젝트 루트에서 상태를 확인한다. 기존 결과·로그가 있으면 재실행은 거절한다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_wind_field.sh --action status
```

완료 분석 후 재생한다. 하늘색=기존, 주황=시간 평활, 초록=시간 평활+국소. 기본 시작점은 사용자가 지적한 wind2.8초다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_wind_field.sh
```

뷰어의0–2초는 세 조건 모두 기존 선정안의 같은 기록이다.2–4초가 이번 새 비교이며 전체10초 실행으로 해석하지 않는다. Space 재생/정지, 시간 슬라이더, 배속을 제공한다.
새 독립 실행 묶음을 만들 때는 `run_gpu_wind_field.sh --out <새경로> --action prepare` 후 각 조건 `reference/smooth/local`의 `--action oracle`, `smoke`, `run`을 순서대로 사용한다. GPU 비교는 순차 실행한다.
분석은 `PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.analyze_gpu_wind_field --root <bundle> --out <새분석경로>`이다.

## 검증과 한계

새 국소 GPU 공력은 서로 다른 원본 상태3개에서 독립 NumPy 적분·조립과 대조했고, 최대 힘 오차4.34e-19N였다. 기본 경로는 opt-in이 없으면 원래 공력 커널을 그대로 사용한다.
완료된360프레임 모두 이전 raw 상태로 외력을 다시 구성해 저장 `held_force_n`을 검산했고, 프레임 hash·핀·시간·외력·감쇠 장부·checkpoint도 통과했다. 최대 외력 오차8.67e-19N, 받아들인 substep은조건별7,680개다.
R1의 고정 외력 시간/공간 비교와 별개인 시각 진단이다. [R1 CG 개발 경계](../../../ideas/development/r1_teacher_probe_oracle.tex)의 `sec:r1-cg-development-entry`는 변경하지 않는다.

## 국소 재시도 연결 수정

최초 `bundle/local`은0프레임에서 setup 실패했다. full 바람120개에 맞춘 activation이 재시도용1프레임 솔버에도 적용되어 길이 검사가 거절했다. 기존 smoke는1프레임 입력이어서 이 연결 문제를 발견하지 못했다. 실패 report/log는 보존했다.
`ResidentContactRetryFrame.__init__`에서 base의 held force를 복사하는 half에는 국소 strategy를 생성하지 않도록 수정했다. 실제 공력 재계산·복구 조건·dt·검산은 바꾸지 않았다. 국소 다중 프레임·강제code1/2 복구·실패rollback·다음 외력4개와 기존 재시도22개, 총26개 GPU 검사 통과.
[국소 동결 묶음](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/bundle_local_v2/manifest.json), [새 순차 실행 기록](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/local_v2_events.jsonl)으로 국소만 새 실행해120프레임을 완료했다. 기존 두 완료 결과는 재사용하며 `comparison_roots`가 원본·물성·초기값·외력·native 동일 및 teacher runtime 차이가 retry 연결 하나뿐임을 검증한다. 초기 실패를 국소 완료 결과로 덮어쓰지 않는다.
분석·뷰어의 기본값은 기준/평활=`bundle`, 국소=`bundle_local_v2`이다. 사용자 지정 묶음은 `--root <기준묶음> --local-root <국소묶음>`으로 지정한다.

## 완료 결과

감쇠 막5ms·굽힘20ms의 **이번 기존 균일 바람**을100% 기준으로 삼는다. 이전 감쇠 비교의 감소율과 누적하지 않는다. 아래 감소율이 음수이면 진동 증가다.

| 바람 | 구간(wind초) | 위치10–30Hz 감소 | 법선10–30Hz 감소 | 큰 움직임 유지 | 속력 유지 |
| --- | --- | --- | --- | --- | --- |
| 시간 평활 | 2–4 | 1.9% | 0.2% | 117.1% | 106.7% |
| 평활+국소 | 2–4 | 7.6% | -3.2% | 140.5% | 124.7% |
| 시간 평활 | 2.4–4 | -20.7% | -13.7% | 116.7% | 107.5% |
| 평활+국소 | 2.4–4 | -3.3% | -1.1% | 139.6% | 127.3% |
| 시간 평활 | 2.5–3.2 | 28.7% | 17.7% | 102.5% | 99.6% |
| 평활+국소 | 2.5–3.2 | 9.4% | -18.0% | 128.6% | 120.6% |
| 시간 평활 | 3–4 | -47.6% | -24.0% | 121.9% | 111.1% |
| 평활+국소 | 3–4 | -9.1% | -1.0% | 143.4% | 131.4% |

2.5–3.2초의3–10Hz 위치 성분도 평활37.3%·국소20.0% 감소했지만,3–4초에는 각각23.3%·36.5% 증가했다.10–30Hz만 선택해 결론을 바꾼 것이 아니며 전체 시각 품질은 재생으로 판단해야 한다.
첫0.4초 전환을 제외한2.4–4초에서 국소 바람은 큰 움직임을39.6% 늘리고 위치/법선 빠른 성분은약3.3%/1.1% 늘렸다. 동작 대비 떨림의 인상이 다를 수 있지만 **절대 잔진동 감소**로 보고하지 않는다.

| 바람 | 입력 풍속RMS(m/s) | 실제 노출 풍속RMS(m/s) | 합력RMS(N) | 순 바람 일(J) | 프레임 계산(분) |
| --- | --- | --- | --- | --- | --- |
| 기존 | 1.2853 | 1.2853 | 0.1907 | 0.03258 | 23.15 |
| 시간 평활 | 1.2853 | 1.2853 | 0.1898 | 0.04614 | 24.67 |
| 평활+국소 | 1.2853 | 1.2433 | 0.1919 | 0.04769 | 24.83 |

풍속RMS를 같게 맞춰도 궤적과 힘·속도의 관계가 달라져 실제 바람의 일이 늘었다. 진동을 단순히 바람 세기의 문제로 단정하지 않는다. 비용은 setup 제외 단일 순차 실측이며 반복 벤치마크는 아니다. 원본 기준 재생은 최대 u_hi 차이1.11e-16m, v_hi 차이1.24e-14m/s로 기존 추천 궤적과 일치했다.

[비교 HTML](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/analysis/index.html), [진동·입력·실제 합력 그림](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/analysis/motion.png), [2.8초 세 표면 렌더](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/viewer_2p8.png), [compact 검증 기록](wind_field_checks.json)을 제공한다. 뷰어는 세 표면 표시와 공통 앞부분·241상태·시간 연결을 확인했으며, 화면의 운동을 좋다고 판정한 것은 아니다.

## 동결 원본과 실패 분모

- `bundle/manifest.json` SHA256: `61f99bb31e421c110f7cc1ec61c75aee9fd772883b8500d5ab5be9b5f6f9ad22`.
- `bundle_local_v2/manifest.json` SHA256: `c0b4bb9726cb72931e14d431146a99b7a3fad82ba01dd7ca1f4c4a4b205a6c6f`.

- [초기 suite](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/bundle/suite.json)의 `source_bundle/smooth/local_profile`, [초기 실행 기록](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/events.jsonl), [수정 국소 실행 기록](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/local_v2_events.jsonl), [장치 표본](../../artifacts/runs/p3_self_contact/wind_field_compare_20261001_01/monitor.jsonl).
- 본 실행 시도4개: 기존·평활·수정 국소3개 완료, 최초 국소1개는 setup 실패(0프레임). 원본 실패 report/log를 보존한다. 물리 프레임 실패·dt/2 복구는 완료한360프레임에서0회다.
- 공력 oracle은 초기3조건+수정 국소의 각3상태, 접촉 smoke는초기3+수정1프레임이다. 별도 GPU26개 검사에는 의도적으로 주입한 실패와 rollback 검증을 포함하며 본 실험의 수치 실패와 혼합하지 않는다.
- R1의 고정 외력 시간/공간 민감도·생산·학습 완료 계약 변경 없음. code/experiments 미커밋 변경과 기존 artifact 보존, commit/push/fetch/외부 다운로드 없음.
