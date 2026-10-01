# GPU 세 씬 v13: 초기 굽힘과 중력 처짐 후보

## 현재 상태

2026-09-28 사용자 요청으로 [완료 v13 재분석](#완료-v13-재분석)을 실행했다. 세 씬 저장 검산·연결 확인, 처짐과 무풍 후반 잔운동을 수치화했다. 시각 채택·학습은 보류이며 감쇠 샘플 결과와 구분한다.

- 확인일2026-09-28. 서브 컴 RTX5070의 v13 세 씬이60/240/300프레임, 각 연속10초를 완료했다.
- 실제 결과는 `sub_pc/20260928T043613Z-b306cdad658642d089bb9b2330f8fdae/simulation`이며 로컬 준비 폴더와 구분한다.
- 원본 manifest는 아래 준비 hash와 동일하고 `source-snapshot.json`의 runtime 변경은false다.
- [서브 컴 완료 결과와 연결](#서브-컴-완료-결과와-연결)의 뷰어·분석·비교 래퍼를 추가했다.
- 세 씬 표시 캐시 준비·실제4초 화면 렌더링·CPU 분석 완료. 사각형 자기 비교는 `identity_check_only`다.
- 사각형 dt/2 복구는 calm166/wind300프레임(총466), 손수건·삼각형은0개다. 폐기 증거도 보존했다.
- 이 확인은 원본 hash/저장 승인/연결과 표시·분석 검증이다. 힘/CCD를 다시 계산한 검산은 아니다.
- 자연스러운 처짐의 사용자 시각 판정, 두 정밀도 실제 민감도 비교, GS/학습 적격성은 미완료다.
- 이번에 새 시뮬레이션을 실행하거나 원본·동결 runtime을 수정하지 않았다. 기존 v12는 보존한다.
- 로컬 준비 당시 정적 검증은 아래에 보존한다. 근거는 [연결 검증 JSON](v13_sub_connection_checks.json)의 `shapes`/`viewer`다.

## 설정과 초기 상태

| 구간 | 전체 시간 | 프레임 | 외력 |
|---|---|---:|---|
| preload | 0–1초 | 60 | 기존 중력 ramp의 첫60프레임, 무풍 |
| calm | 1–5초 | 240 | 중력 −9.81m/s², 무풍·공기 저항 유지 |
| wind | 5–10초 | 300 | 중력 유지, 기존 ramp 포함 바람240프레임 + 마지막 풍속60프레임 유지 |

60Hz·기본64 substep과 기존 허용오차/물성/접촉/독립 검산을 유지한다.
기존 바람 ramp는 전체5–6초에 해당한다. 마지막9–10초는 기존 마지막 벡터를 유지하므로
경계 풍속이 갑자기 바뀌거나 ramp가 반복되지 않는다. 별도의 preload 옆방향 힘은 넣지 않는다.
이전 phase의 raw hi/lo 위치·속도를 그대로 다음 phase에 전달하며 경계에서 속도를 초기화하지 않는다.
`phase_time_s`는 구간 시간, `trajectory_time_s`는 전체 시간이다.
조건부 code1/code2 GPU dt/2 한 번 재시도, swept2,000,000, cuDSS 결정성1을 유지한다.

초기 굽힘은 고정 모서리에서 접선이 같은 원통형 위치로 P3 노드를 매핑한다.
사각형·삼각형은 수직 고정 모서리에서 수평 바깥 방향으로, 손수건은 윗 고정선에서 아래쪽으로 굽힌다.
기준 rest를 굽힌 모양으로 바꾸지 않고 변위 `u_hi`에 저장한다. 따라서 초기 굽힘 탄성 에너지가 있으며,
중력만의 응답이라고 해석하지 않는다. `u_lo/v_hi/v_lo=0`, 고정점 변위0이다.
연속 원통 매핑은 면내 길이를 보존하며, 실제 P3 보간의 초기 strain 상한도 별도로 확인했다.
실행 시작 접촉 검사는 이 굽힌 상태를 사용한다. 추가 힘으로 천을 밀거나 정지 상태를 강제하지 않는다.

기본5도는 작은 비평면 상태를 만드는 첫 후보다. 실제 자연스러운 처짐의 크기·안정화 시간은
실행 전 보장하지 않는다. 특히 위에서 매단 손수건은 다시 거의 평평해질 수 있다.

## 준비 묶음과 명령

새 run: `experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_drape_v13`.
`manifest.json` SHA256: `7e0c66997a0a0018d1fddc1786a5315cc59094521b879831864c528a8a064190`.
기준 원본은 승인된 bend500 입력이다. `reference_inputs.json`은 변형 전 원본 hash 출처이며,
새 초기 상태와 변형된 phase 입력의 권위 hash는 새 `manifest.json`이다.
기존 v12 manifest는 `0be6397195b505b314fa8b8913aa41b28c2249593f366ea2c05529f5536c994e`로 유지됐다.

아래는 로컬 준비 묶음의 최초 실행 명령이다. 완료된 서브 컴 결과를 보기 위해 재실행하지 않는다. 현재 재생/분석은 아래 서브 컴 전용 명령을 따른다.

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_v13.sh --action run
```

상태와 완료 후 뷰어:

```bash
bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_v13.sh --action status
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v13.sh
```

새 설정으로 별도 묶음을 준비할 때만 `--action prepare --out <새_경로>`를 쓴다.
`--initial-bend-angle-deg`는 prepare에서만 허용하며 기본5도, 허용 범위0초과15도 이하다.
기존 출력은 덮어쓰지 않는다. 기존 `run_gpu_three_scenes.sh`와 `view_gpu_v12.sh`는 v12용으로 유지한다.
v13 뷰어는 완료된 세 phase만 허용한다. 시작 프레임부터 초기 굽힘을 표시하고0–1/1–5/5–10초를 연결한다.
Space 재생/정지, Time 이동, 마우스 드래그 회전, 휠 확대를 사용한다.

## 검증과 한계

- 실행기·초기 형상·기존 v12/v11·뷰어 검사29개 통과. 테스트는 실제 GPU 적분을 실행하지 않았다.
- 첫 테스트에서 새 오류 문구에 대한 기존 정규식과 새 fixture 반환값 사용이 잘못되어2개 실패했다.
  테스트를 수정한 뒤29개 전체가 통과했다. 물리 계산 실패는 아니다.
- 실제 세 씬60/240/300프레임, manifest 전체, 외력 prefix의 v12 동일성, 물성/기본 단계/허용오차 보존 확인.
- 실제 초기 최대 변위는 사각형0.032718m, 손수건0.030537m, 삼각형0.052349m이다.
- CPU `P3ShellBounds.interval(u,0,u,0)`와 `local_metric_certificate`로 정적 P3 비퇴화를 확인했다.
  strain component 상한은 각각5.44e−11/1.91e−10/9.95e−11이고 면적비 하한은 모두0.9999999994초과다.
  이는 초기 국소 기하만 확인한 것이며 자기 접촉·시간 적분·동적 안정성 검증이 아니다.
- 준비 당시 로컬 세 씬 status는 준비 완료·미실행이고 outputs/checks가 없었다. 이후 서브 컴 결과 확인은 아래 절로 갱신했다.
- 준비 단계에서 solver를 실행하거나 기존 run/캐시를 삭제·덮어쓰지 않았다. commit/push·외부 fetch/다운로드 없음.

## v12에서 바꾼 이유

사용자는 뷰어에서 calm의 중력 처짐이 보이지 않는다고 관찰했다.
원본 표본의 `gravity_m_s2`와 `held_force_n`에는 중력 하중이 있었지만,
preload 후 자유 노드 변위 RMS는 사각형0.086mm/손수건0.053mm/삼각형0.148mm 수준이었다.
calm의 추가 변화는 표시 캐시 기준 모두0.001mm 미만이다.
세 rest가 수직 XZ 평면이고 중력도 그 평면 안에 있어 초기 변형이 작은 조건이었다.
평면 밖 초기 굽힘으로 그 대칭 상태를 벗어나는 새 후보를 준비했지만, 자연스러운 처짐을 확보했다고 판정하지 않는다.


## 서브 컴 완료 결과와 연결

완료 run은 [서브 실행 보고](../../artifacts/runs/sub_pc/20260928T043613Z-b306cdad658642d089bb9b2330f8fdae/worker-result.json)의
`completed_frames`와 [동결 입력](../../artifacts/runs/sub_pc/20260928T043613Z-b306cdad658642d089bb9b2330f8fdae/simulation/manifest.json)으로 식별한다.
앞선 `20260928T042251Z-efd3f6e2050f4545b8bff3930e1c3d7f`는 준비 묶음만 있으므로 이번 표시 대상에서 제외했다.

### 바로 실행하는 명령

```bash
# 세 씬 전체10초 뷰어: Space 재생/정지, Time 이동, 마우스 회전/확대
bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v13_sub.sh

# 같은 서브 결과의 CPU 처짐/속도 분석: 별도 새 출력 자동 생성
bash experiments/R1_teacher_velocity_reset/self_contact/analyze_gpu_v13_sub.sh

# 비교기 연결 점검: 같은 결과를 양쪽에서 읽음. 민감도 통과가 아님
bash experiments/R1_teacher_velocity_reset/self_contact/compare_gpu_v13_sub.sh --self-check
```

분석/비교의 기본 출력은 UTC 시각·나노초가 포함된 새 폴더다. `--out <새_경로>`로 지정할 수도 있다.
기존 출력이 있으면 거절한다. 뷰어는 source·코드 버전별 검증 캐시를 재사용한다.
표시 캐시의 상위 `p3_self_contact_v12` 이름은 기존 serial 캐시 루트일 뿐 v12 데이터로 표시한다는 뜻이 아니다.
현재 서브 source cache ID는 `dd99c8ac030f`, 뷰어 버전은 `3af300dfd886`이다.

### 실제 시간·공간 비교를 할 때

현재 확인된 완료 결과는 이 설정의 한 궤적 묶음이다. 실제 시간 비교에는 같은 초기 형상·외력·
1/4/5초 구성과 **같은 RTX5070 GPU 모델**에서 더 정밀하게 완료한 두 번째 결과가 필요하다.
다른 조건인 기존 v12 또는 결과 없는 로컬 v13을 reference로 자동 선택하지 않는다.

```bash
# 기본 candidate는 위 서브 v13, 기본 axis는 time
bash experiments/R1_teacher_velocity_reset/self_contact/compare_gpu_v13_sub.sh \
  --reference <같은_조건의128단계_완료_run>
```

일반 옵션 `--axis`, `--candidate`, `--shape`, `--out`은 그대로 전달한다. 공간 비교는 양쪽 substeps가
같아야 하므로 필요한 경우 `--candidate <시간정밀화_run> --reference <공간정밀화_run> --axis space`를 함께 준다.
`--self-check`는 첫 인자로 사용한다. 옵션 없이 비교 래퍼를 실행하면 필요한 reference를 안내하고 종료2로 끝난다.
수치 조건과 시각 대기 계약은 [비교기 문서](cg_comparator.md#비교-조건과-판정)를 그대로 따른다.

### 실제 연결 검증

- 원본1800프레임·세 씬 각601상태의 hash/시간/외력/구간 연결·저장 승인 flag와 폐기 증거를 확인했다.
  사각형의466개 복구를 기본 dt 무복구 안정성으로 해석하지 않는다.
- 뷰어 세 캐시 준비 후 [calm4초 화면](../../artifacts/runs/shell_playback/p3_self_contact_v13_sub/verification_20260928_01/calm_4s.png)을 실제 렌더링하고 세 씬 배치를 확인했다.
  WSL CUDA/OpenGL interop304는 copy fallback, MSAA는 non-AA fallback으로 표시 완료됐다. 기존 Warp 캐시는 삭제하지 않았다.
- [CPU 분석 보고서](../../artifacts/runs/p3_self_contact/motion_analysis/v13_sub_20260928_01/index.html)는 세 씬 분석 완료다.
- [자기 비교 보고서](../../artifacts/runs/p3_self_contact/cg_comparison/identity_v13_sub_20260928_01/index.html)는 사각형600프레임·wind300/후반120프레임,
  양쪽 복구/폐기466개와0오차를 확인했다. 최종 pass/학습 적격성은false다. HTML 브라우저 재생은 여전히 직접 미검증이다.
- 새 셸3개 구문과 reference 누락 거절을 확인했다. solver/분석/비교 핵심 Python 코드는 변경하지 않았다.
- R1의 개발 진입 조건을 확인했으며 이번 운영 연결은 비교 기준·학습 승인 변경이 아니므로 TeX/PDF는 수정·재빌드하지 않았다.


## 완료 v13 재분석

2026-09-28 사용자가 `analyze_gpu_v13_sub.sh`의 분석을 요청하여 해당 명령을 실제 실행했다.
대상은 위 서브 컴 RTX5070 v13 연속1/4/5초 원본이며, 새로운 감쇠 샘플 결과가 아니다.
원본 manifest는 `7e0c66997a0a0018d1fddc1786a5315cc59094521b879831864c528a8a064190`로 같았다.
이전 분석 출력은 보존하고 [새 HTML 보고서](../../artifacts/runs/p3_self_contact/motion_analysis/v13_sub_20260928T103705982406210Z/index.html)를 생성했다.
상세 검증·구간 수치·보고서 hash는 [재분석 증거](motion_analysis_v13_checks.json)의 `validation`, `shapes`를 따른다.

| 씬 | 완료 프레임 | dt/2 복구 | calm 끝 평균 높이 감소 | calm 마지막1초 속도 RMS | 같은1초 위치 변화 RMS |
|---|---:|---:|---:|---:|---:|
| 사각형 | 600/600 | 466 | 136.793 mm | 0.282057 m/s | 19.841 mm |
| 손수건 | 600/600 | 0 | 0.273 mm | 0.020141 m/s | 3.554 mm |
| 삼각 깃발 | 600/600 | 0 | 158.701 mm | 0.277319 m/s | 25.600 mm |

높이 감소는 초기 굽힌 형상 대비512개 공통 표면점의 면적 가중 평균이며 최대 처짐이 아니다.
속도는 저장 hi/lo 속도의 P3 보간이다. 마지막1초는 전체4–5초, 위치 변화는 그 시간 평균 주위의 RMS다.
위치 변화와 속도에는 느린 흔들림도 포함되어 순수 고주파 진폭으로 해석하지 않는다.

- **완주/연결:** 세 씬 총1,800프레임, 모든 구간·체크포인트 raw 위치/속도 경계와 외력·시간 기록을 분석기가 확인했다. 원본/폐기 증거 hash와 새 산출물31개 hash를 확인했다.
- **저장 검산:** 채택 프레임의 flags는 전부0, 기록된 최대 힘 잔차 비율은 전체 약0.299969, 국소 면적비 하한은 전체 최소0.123472로 양수다. 고정 표면점의 변위·속도는0이다. 이는 기록된 검산의 확인이며 물리 잔차/CCD를 다시 계산한 것은 아니다.
- **복구 의존:** 사각형은 preload0/calm166/wind300회 복구했다. 총465회 code2와1회 code1이며 폐기 증거466개를 보존했다. wind 전체가128substeps로 채택됐으므로 기본64단계만으로 완주했다고 보고하지 않는다. 손수건·삼각형은 복구0회다.
- **처짐:** 사각형·삼각형의 중력 처짐은 확인된다. 위 모서리가 고정된 수직 손수건은 추가 평균 낙하가 작으며, 이것만으로 중력 누락을 뜻하지 않는다.
- **움직임:** 사각형은 무풍 초반 큰 움직임이 감소하지만 후반에도 속도가 남는다. 삼각형도 복구 없이 유사한 후반 속도를 보여 dt/2만을 잔떨림의 원인으로 단정할 수 없다. wind 마지막1초 속도 RMS는 사각형0.541805/손수건0.089043/삼각형0.514065 m/s다.

판정은 **저장 결과 분석 완료·시각 채택 보류**다. 사용자 관찰의 판 같은 반동/떨림이 해결됐다고
간주하지 않으며, 시간·공간 민감도나 학습 적격성을 승인하지 않는다. 다음은 준비된
[짧은 감쇠 비교](damping_sample.md#바로-실행)의 실제 결과로 잔떨림과 큰 움직임의 보존을 보는 것이다.
이번 분석 중 감쇠 샘플 실행/새 시뮬레이션은 하지 않았다. 관련 R1의 시각/민감도/감쇠 미채택 경계는
유지되어 TeX/PDF 수정·빌드가 필요하지 않았다.
