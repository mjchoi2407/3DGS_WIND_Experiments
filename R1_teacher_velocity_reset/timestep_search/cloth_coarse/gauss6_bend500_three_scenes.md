# Gauss6차·8분할·굽힘1/500의 세 씬 실행

2026-09-14 사용자 선택의 샘플 설정이다. 기본 Newmark 실행은 보존하고 별도 Gauss run을 만든다. [국소 비용/정확도 비교](gauss_timestep_sweep.md)의8분할 후보이며 teacher 적격성이나 전체 궤적 정확도 채택이 아니다.

## 조건

- GPU 상주3단계6차 Gauss, FP64 hi/lo, `dt=1/30720초`, 60Hz의프레임당512단계. 원래64단계의8분할이며8차 적분기가 아니다.
- 기준 대비 굽힘0.002(1/500). 기존 면내 강성·면밀도·메시·고정 조건 유지.
- 직사각형 `reference_rectangle`: 384삼각형·1813 P3 계산점·49고정점.
- 삼각 깃발 `triangular_flag`: 144삼각형·703계산점·37고정점.
- 손수건 `handkerchief`: 192삼각형·925계산점·8고정점. 기존 손수건 부착 조건을 깃발 조건으로 바꾸지 않는다.
- **중력2초 → 동일 checkpoint에서 무풍4초와 바람4초**. 원래 중력/바람1초 smooth ramp, 속도 reset 없음. 각 씬은120+240+240=600프레임을 계산한다. 물리 시간10초짜리 단일 연속 궤적은 아니다.
- 공력+중력은 기존식으로 프레임 시작에 한 번 계산하고512단계 동안 고정한다. 별도 검산 버퍼에서 단계별 힘·갱신·에너지 장부·고정점·유한성·P3×cubic 국소 기하를 확인한다. 셀프컬리전 없음.
- 보조 행렬은 Newton 선형 풀이64회 간격의 기존 Gauss 재사용 후보다. 프레임별 외력 변경 후 힘/잔차는 새로 평가한다. 실패 시 자동 허용오차 완화나 보조 행렬 재시도는 없다.

## 씬별 실행

workspace 루트에서 다음 중 맡은 씬만 실행한다. 메인컴과 서브컴의 GPU를 각각 사용하므로 서로 다른 컴퓨터에서는 동시에 실행할 수 있다. 같은 GPU의 속도 측정은 한 씬씩 실행한다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss6_bend500_reference_rectangle.sh
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss6_bend500_triangular_flag.sh --sub-pc
bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss6_bend500_handkerchief.sh --sub-pc
```

위 예는 메인컴에 직사각형, 서브컴에 나머지 두 씬을 배정한다. 서브컴 GPU가 하나면 삼각 깃발 종료 후 손수건을 실행한다. `--sub-pc`는 **해당 컴퓨터에서 실행할 때 출력 경로를 선택하는 옵션**이며 원격으로 컴퓨터에 접속하거나 작업을 보내지 않는다.

- 메인 출력: `artifacts/runs/teacher_timestep_search/gauss6_split8_bend500_<shape>_v1/`.
- `--sub-pc` 출력: `artifacts/runs/sub_pc/gauss6_split8_bend500_<shape>_v1/`.
- 새 비교는 `--out experiments/artifacts/runs/.../<새run ID>`로 분리한다. 기존 설정·동결 코드 변경은 거부한다.
- `--prepare-only`: 입력·runtime·cuDSS·workspace shim을 동결하고 계산하지 않는다. 컴파일러`cc`와 기존 동결 cuDSS가 필요하다. 입력·설정·코드·binary hash가 manifest에 저장된다.
- `--status-only`: 동일 스크립트/`--sub-pc`/`--out` 옵션으로 상태 조회.
- `--smoke --out <새경로>`: 각 단계1프레임(총1536적분 단계), 같은 dt/메시/굽힘을 쓰되 ramp1프레임의 연결 검증. 본 궤적이나 성능 근거로 쓰지 않는다.
- 실행 소유권 lock과 worker process group을 유지한다. Ctrl+C는 해당 run의 worker를 종료하고 확정 chunk를 보존하며, 마지막 미저장 구간을 완료 처리하지 않는다. interrupted/실패 실행은 자동 재개하지 않는다.
- 각 run/장치에서 Warp cache를 분리한다. source snapshot은 실행 도중 공유 code의 수정에 영향을 받지 않는다.

## 기록과 재생

매 프레임 GPU 완료 후 계산+독립 검산 시간을 출력한다. 체크포인트 저장 간격은기본2초(`save_frames=120`)다. 준비/저장 시간은 report에 별도 기록한다. 이전 국소 비동기 풀이 시간과 직접 비교하지 않는다.

**원시 hi/lo 위치·속도는60Hz 프레임 경계에서 보존**하고, 모든512적분 단계의11개 검산 값·flag·에너지 장부를 함께 저장한다. 기존 Newmark의 모든 substep 상태 기록과 구분하며, 중간 Gauss stage 전체를 디스크에 저장하는 teacher 원본 형식은 아니다. 저장량은 직사각형 기준 상태 약21MB/2초와 검산 약5.4MB/2초이며 외력·metadata가 추가된다. 메모리와 디스크를 모든 stage 기록량만큼 확대하지 않는다.

재생기는 `resident_gauss_gpu_v1`의 `recorded_substeps=1`을 사용하고 실제 적분 분할512와 혼동하지 않는다. 예:

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500.sh reference_rectangle wind
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500.sh triangular_flag wind --sub-pc
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500.sh handkerchief wind --sub-pc
```

`wind` 대신 `preload`/`calm`, 또는 `--out <run>`을 지정할 수 있다. 학습 적격/Gate는 유지하고 시각 확인·연속 안정성 시험용으로 사용한다.

## 검증 근거

현행 검증 및 본 실행 준비 상태는 [검증 JSON](gauss6_bend500_three_scenes.json)을 따른다. smoke 원본은 `artifacts/runs/teacher_timestep_search/gauss6_sequence_smoke_v2/<shape>/`다. 초기v1의 중첩 CUDA graph 초기화 실패는 보존했고, 풀이/독립 검산 그래프를 순서대로 제출하는 경로로 수정했다. 단계 내부 host 수치 조회를 도입하지 않는다.

기존 GPU/CPU 검산 동등성의 소유 문서는 [선행 보고서](gauss_gpu_comparison.md)다. 이번에는 연속 프레임 외력·중력·분기·검산·저장·뷰어 연결을 확인하며,4초 본 실행/학습 정확도/셀프컬리전 완료로 확대하지 않는다. 본 실행은 사용자가 해당 컴퓨터에서 시작한다. 외부 fetch·commit·push 없음.


## 완료된 세 씬 재생 연결 — 2026-09-14

report/config 기준 세 씬 모두 preload120·calm240·wind240프레임 완료를 확인했다. 직사각형은 main GTX1080Ti, 삼각 깃발/손수건은 서브컴 RTX5070 결과다. 동일 Gauss6차8분할·1/500 설정이며 장치 간 속도 비교나 추가 정확도 검산은 이번 재생 연결에서 수행하지 않았다.

- 직사각형: `teacher_timestep_search/gauss6_split8_bend500_reference_rectangle_v1`.
- 삼각 깃발: `sub_pc/20260914T033418Z-4c977dfc6d2e4e5295ead7991dd58962/simulation`.
- 손수건: `sub_pc/20260914T033603Z-f402b992660342b0a8a0bbf83fe967ea/simulation`.

위 경로는 모두 `experiments/artifacts/runs/` 아래다. 서브컴의 이름 고정 준비 폴더는 ready이므로 완료 결과와 혼동하지 않는다. 실제 완료 경로를 고정한 `view_gauss6_bend500_completed.sh`를 추가했다. 세 바람 구간의 입력/청크 검증 및 재생 캐시 준비를 통과했다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500_completed.sh reference_rectangle
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500_completed.sh triangular_flag
bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500_completed.sh handkerchief
```

기본은 바람4초이며 씬 뒤에 `preload`/`calm`을 지정할 수 있다. 저장 결과 재생만 수행한다. 실행기/물성/기준·동결 결과는 변경하지 않았으며 학습 적격성은 미판정이다.
