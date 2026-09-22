# experiments 작업 요약

## 현재 상태

- **Artifact 정리 완료:** 시각·성능 확인이 끝난 raw 궤적을 playback/report-only로 전환해 327.3GB 회수. 기하 실패·최신 적응형·1/500·checkpoint는 보존했고 10초 9개 playback hash/진입을 검증했다. [인계](2026-09-22_01_artifact_cleanup.md).

- **Adaptive Mixed32 세 장면 준비:** 현행 후보만 실행하고 예전 FP64 hi/lo는 완료 구간 비교에만 재사용. CPU 준비·manifest 검증 통과, GPU 본 실행 대기. [인계](2026-09-20_04_adaptive_integrator.md).

- **Gauss 전용 FP32 우선/FP64 묶음 복구:** 양 GPU 고부하3프레임과 프리로드를 통과/복구0. RTX5070 혼합은 R64 대비 고부하22.83%·저부하13.92% 단축, GTX1080Ti는 각각2.66%·-3.59%로 약함. 저부하는 Newmark 유지. [인계](2026-09-20_03_gauss_precision_frame.md).

- **추가 FP32/M2 국소 비교 준비:** P 조립·inner reduction/작은 문제 FP32, FP64 검산 유지·단계별 터미널 시간. GPU 사용자 실행 대기. [인계](2026-09-20_02_extended_precision_probe.md).

- **고부하 FP64/FP32 연산 비교 준비:** 저장3프레임·동일 입력·Graph 고정 작업량·변환 비용 분리. GPU 사용자 실행 대기. [인계](2026-09-20_01_highload_precision_bench.md).

- **182–200 비교 완료:**38회 기존 검산 통과·half438회 복구 성공. 전체시간 소폭 감소와 큰 속도 차이를 분리하며 기본값 유지. [인계](2026-09-19_01_wind_window_comparison.md).

- **wind120→200 복원 스크립트 준비:** 원본 동결 경로·매 프레임 저장·명시적 재개·후속19개 비교 입력. ready120이며 사용자 GPU 실행 대기. [인계](2026-09-18_02_cascade_retry_samples.md).

- **half2→Gauss8 고부하 표본 비교:** 기존3표본 완료·기본 적용 보류. 후속182–200은 사용자 승인 후 재생 스크립트 준비 완료. [인계](2026-09-18_02_cascade_retry_samples.md).

- **Newmark 절반 dt 복구 별도 준비:** GPU 자동 선택 유지·half는 R64, 제한 GPU 제어/검산 통과. 본 실행 대기. [인계](2026-09-18_01_gpu_half_retry.md).

- **GTX1080Ti 공통 경로 진단:** C/D 지연 미재현·원인 미확정. R64 정상 시간 확인 후 W1 M1 약18.3% 단축, 기존 검산 통과. [인계](2026-09-17_03_launcher_diagnostic.md).

- **GPU 자동 선택 세 씬 준비:** 기존 M1/M2/R64 연결,1080Ti 세 씬 제한 검산 통과. 본 실행 대기·5070 환경 보류. [인계](2026-09-17_02_gpu_auto_scenes.md).

- **frame225 추가 최적화 분기 종료:** 선형/line search 통과와 전체 Newton 미검증을 분리. 운영 채택 보류·기존 선택 유지. [인계](2026-09-17_01_frozen_line_search.md).

- **Teacher 가속 개발 제한 종료:** 사례별 M1/M2/R64 동결, 두 제한 시험 완료. 생산/학습 적격성 유지·5070 Graph 미해결. [인계](2026-09-16_05_bounded_closeout.md).

- **FP32 v3 완료 결과 취합:** 두 GPU 완료 시험을 ZIP으로 보존. 메인 HL01 mixed는 사용자 요청으로 종료, 미완료 시험 제외. [인계](2026-09-16_04_completed_v3_bundle.md).

- **dual_gpu v2 준비:** C0/W1 균형 반복·보정 FP32 Graph 측정·판정 분리. GPU는 사용자 실행 대기. [인계](2026-09-16_02_dual_gpu_v2.md).

- **두 GPU force launch 시험 준비:** 동일 입력·GPU별 sweep/cache/FP32 비교·수동 취합 스크립트. 사용자 실행 대기, GPU 미측정. [인계](2026-09-16_01_dual_gpu_launch.md).

- **Teacher 성능 진단 실행 준비:** 사용자 RTX 5070에서 checkpoint3회/별도 Nsight Systems. 현재 환경은 GTX 1080 Ti라 GPU 미측정, FP32 상위 연산 비교는 후속. [인계](2026-09-15_04_precision_profiling.md).

- **수렴 실패 시 Gauss6차8분할:** 현행 retry 스크립트 교체, 실제 실패2프레임 복구·세 씬 smoke 완료, 본3씬 ready0. [인계](2026-09-15_03_newmark_dt_retry.md).

- **Newmark 고정/절반dt 복구 세 씬 준비:** 로컬 스크립트2개·본6개 ready0. 실제 실패 프레임 복구와18개 짧은 phase 검증 통과, 본 실행 미시작. [인계](2026-09-15_03_newmark_dt_retry.md).

- **로그의 실제 기하 실패5건 재계산:** Gauss도 옛 투영 경고 유지, 두 방법 모두 현재 국소 검산 통과. 이 경고는 고차 전환으로 해결되지 않았다. [인계](2026-09-15_02_integrator_switch.md).

- **기하 경고 전용 전환 재시험 완료:** 128분할 감시 제거, 두 국소 상태 모두 Newmark 한 번으로 검산 통과. 프리로드1~2초 범위 재확인, 순간속도 정확도 문제/실제 기하 경고 해결은 미완료. [인계](2026-09-15_02_integrator_switch.md).

- **Newmark/Gauss 전환 비교:** 같은 두 저장 상태의 반복 비교·검산 완료. 모두 고차 재계산으로 추가 비용 발생, 바람 시간 편차 분리. 기본 채택/학습 적격성 미완료. [인계](2026-09-15_02_integrator_switch.md).

- **Gauss 스케일링·FP64 보정 비교:** 스케일링 단독 개선 없음. 혼합 후보 두 국소 프레임의 원래 검산 통과, 추가 보정 비용 포함 가속은 제한적. 교대 검산 시간/실패 분모 보존, 전 구간 채택 미완료. [인계](2026-09-15_01_gauss_fp32.md).

- **Gauss6차8분할·1/500 세 씬 재생 연결:** 세 씬의 중력/무풍/바람 완료 report 확인, 실제 main/sub_pc 결과와 바람 재생 캐시 연결. 추가 시간 수렴/teacher 정확도 검증은 미완료. [인계](2026-09-14_02_gauss_sequences.md).

- **타임스텝 비용 탐색 완료:** 두 국소 상태×두 GPU 적분기×6분할의24개 계산·검산 통과. Newmark dt절반에서 반복 감소가 단계 증가를 상쇄했으나 teacher 정확도는 별도다. [인계](2026-09-14_01_gpu_gauss.md).

- **GPU Gauss6차 비교 완료:** 기존 솔버/세분 Newmark/CPU·GPU Gauss의16개 완료 lane, Gauss64개 고유 substep CPU/GPU 검산 통과. 두 국소 구간에서 Gauss16의 비용/참조 차이 개선, 장기·teacher 채택은 미완료. [인계](2026-09-14_01_gpu_gauss.md).

- **선행 Teacher 정확도 진단:** 순간속도 시간오차와 기존6차Gauss의 가능성 확인. 당시 독립 검산/가속 미완료 상태는 위 후속과 구분하며 전체궤적/학습 적격성은 미완료다. [인계](2026-09-13_09_gravity_wrinkles.md).

- **1/500 실패 재현/개선 후보:** GMRES 한도 실패 재현, dt절반3프레임 검산 통과. 시간 수렴/전체 안정성 미완료. 원본 재개·기본값 변경 없음. [진단](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/bend500_failure_diagnosis.md).

- 확인일2026-09-14. 손수건1/100과 깃발1/100·1/300 본 실행 분석/재생 완료. [깃발1/300 결과](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_bend300_results.md).
- **깃발1/500 실패:** 중력·무풍 완료, 바람2초 직후 선형 풀이 실패. [명령·상태](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_bend500.md). 프레임별 진행은 기록하지 않는다.
- 최초 하이브리드 비교는 사용자 종료·재개 보류. 양쪽 완주 성능비 없음. [측정 계약](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_speed_compare.md).
- 다음은1/500 결과 확인과 별도 셀프컬리전 설계. 연구 Gate·학습 적격성은 미완료. [인계](2026-09-13_09_gravity_wrinkles.md).

## 이전 작업 링크 — 당시 상태

- **2026-09-14 굽힘1/500 준비:** 별도 run ready0·설정/외력 검증 통과, GPU 미실행. 하이브리드 비교는 사용자 종료로 보류. [실행](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_bend500.md).

- **2026-09-14 굽힘1/300 완료:** 38400단계 경고0·재생 연결. 바람 궤적 변경, 잔주름 개선은 미판정. [결과](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_bend300_results.md).

- **굽힘1/300 준비:** 별도 깃발 run ready0, CPU9개 통과·GPU 미실행. 1/100과 비교 후 접촉 모델 검토. [인계](2026-09-13_09_gravity_wrinkles.md).

- **깃발 중력 비교 완료:** 38400단계 경고0. 중력만으로 하강0.132mm, 바람에는 큰 접힘. 세 단계 재생 준비 완료. [분석](../R1_teacher_velocity_reset/timestep_search/cloth_coarse/gravity_flag_results.md).

- **최초 하이브리드 비교 준비:** 같은 깃발 중력 조건의 별도 두 lane 순차 비교. CPU8개 통과, 기존 GPU 실행 중으로 GPU 검증/본 측정 미실행. [인계](2026-09-13_09_gravity_wrinkles.md).

- **깃발 조건 수정:** 중력 실험 기본 대상을 왼쪽 고정 직사각형 깃발로 변경. 별도 본 실행 준비·384단계 smoke 통과. [인계](2026-09-13_09_gravity_wrinkles.md).

- **중력 처짐 주름 샘플 준비:** 손수건1/100·중력2초 후 위치/속도 보존해 무풍4초·바람4초 비교. 정착 판정 없음. 본38400단계 경고0·재생 확인 완료. 중력 하강0.060mm로 주름 유도 조건 재검토 필요. [인계](2026-09-13_09_gravity_wrinkles.md).

- **국소 기하 검사 샘플 통과:** 회전 불변 인증 구현 후3메시×128단계에서 국소/물리 경고0, 기존10초345,600구간의 저장 상한 재분류도 통과. FP64 hi/lo 유지·자기 교차 별도·strict 기본값 보존. [인계](2026-09-13_08_geometry_diagnosis.md).

- **FP64 hi/lo 고정·10초 기하 진단:** 추가 정밀도 최적화 보류. 경고5조건은 초기 평면 투영 충분조건의 큰 회전 한계와 일관되며 대표10상태에서 비인접 교차 후보는 발견하지 못했다. 전체 비접촉 인증·새 검사·접촉 모델은 미완료. [인계](2026-09-13_08_geometry_diagnosis.md).

- **직사각형 Newton 정체 진단:** 완료4초 결과의 대표3상태×3경로 GPU 대조에서 hi/lo는 모두2회 수렴. Pure/보정은 위치 보정이 반올림 수준에 이르며 힘 잔차가 내부 목표 근처에서 정체했다. 상태·기하 산술의 정밀도 한계 근거이며 새 결합 후보는 미구현. [인계](2026-09-13_07_precision_comparison.md#현재-상태).

- **FP64 세 경로4초 준비:** 새 두 풀이×세 메시 ready, 종료 후 기존 메인컴 공통 정상 구간과 자동 비교. 짧은 GPU 검증 통과, 본 실행 미시작. [인계](2026-09-13_07_precision_comparison.md).

- **서브컴10초 재생 연결:** 완료된3조건×3메시를 기존10초 wrapper로 선택 재생. 손수건1/100의 원본 검증·캐시 생성 통과. [인계](2026-09-13_01_saved_mesh_viewer.md).

- **GPU 최적화 종합 결과:** 완료 원본에서 단계별 생성 비용·검산·타이머 범위와 현행 시각 확인 실행의 차이를 정리. [인계](2026-09-13_06_gpu_optimization_summary.md).

- **천 비교 GPU 갱신:** 3조건×3메시4초 새 동결 준비, GPU 계산·검산·2초 저장·재개 짧은 검증 통과. 서브컴 원본에서 기하 flag 단독 실패 확인·실제 교차 판정 대기. [인계](2026-09-13_03_cloth_coarse_preparation.md).

- **GPU 상주 검산 완료:** 기존 완료 궤적640구간의 GPU 검산·기존 검사기 대조 통과. 검산 전용 실행기 준비. [인계](2026-09-13_05_resident_gpu_audit.md).

- **평가 재사용·무압축 후보:** 이전 기준5개 재사용·새 후보만 실행. [명령](../R1_teacher_velocity_reset/timestep_search/gpu_resident/README.md#채택-평가-재사용무압축-후보--현행-다음-실행).

- **current 우선 후보 준비:** 기존 기준4개 재사용·후보만 실행. [명령](../R1_teacher_velocity_reset/timestep_search/gpu_resident/README.md#current-우선-후보--현행-다음-실행).

- **새 후보만 실행:** 기존 기준 캐시 재사용·중복 보조 풀이 제거 준비 및 짧은 검산 통과. [현행 명령](../R1_teacher_velocity_reset/timestep_search/gpu_resident/README.md#보조-행렬-적용-개선기준-재사용--현행-실행).

- **병렬 합산 비교 준비:** 내부 계측 분석 후 합산5경로 병렬화·짧은 검산 통과. [현행 실행](../R1_teacher_velocity_reset/timestep_search/gpu_resident/README.md#병렬-합산-비교--현행-다음-실행).

- **현행 GPU 계측:** WSL+Pascal Nsight 실패 후 내부 timestamp wrapper 준비·짧은 검산 통과. [현행 실행](../R1_teacher_velocity_reset/timestep_search/gpu_resident/README.md#gpu-내부-timestamp-계측--현행-실행-방법).

- **GPU 비교 완료·추적 준비:** 생성2.047배 개선·검산 통과. 동일 동결 코드의 node 추적 스크립트 준비, 사용자 실행 대기. [인계](2026-09-13_04_gpu_resident_preparation.md).

- **GPU 상주 비교 준비:** 적분·current 행렬 GPU 갱신과10프레임 비교 스크립트·동결 입력 준비. 짧은 검증 완료, 본 비교는 사용자 실행 대기. [인계](2026-09-13_04_gpu_resident_preparation.md).


- **완료 궤적의 판 같은 움직임 분석:** 두 씬은 전체 기울어짐이 크고 손수건은 부착부 굽힘 집중. 대표 원본 정적 분석 완료, 물성·수치 원인의 단독 기여는 미확정. 새 물리 실행 없음. [진단·근거](2026-09-13_02_cloth_motion_analysis.md).

- **완료 메시 저장 재생 뷰어:** 직사각형·손수건10초 캐시와 실제 OpenGL 표시 확인, 물리 재계산 없음. [사용법·검증](2026-09-13_01_saved_mesh_viewer.md).

- **새 삼각 깃발10초 준비 완료:** 검증 입력으로 별도600프레임·초기rest부터, 시간 한도 없음. ready0프레임·계산 미시작. [전용 실행 명령](../R1_teacher_velocity_reset/timestep_search/evidence/triangle_failure_20260912/README.md#새-삼각-깃발-10초-실행-준비).

- **삼각 깃발 입력 수정·0.1초 검증 완료:** 고른576면 입력,384단계 GPU 검산·대표3단계 CPU 검산 통과. 새 메시10초·수렴은 미완료. 기존 두 씬10초 완료·옛 삼각 깃발 실패 보존. [변경·검증](../R1_teacher_velocity_reset/timestep_search/evidence/triangle_failure_20260912/README.md#고른-삼각-격자-01초-검증).

- **서브컴 결과 저장 폴더 준비:** `artifacts/runs/sub_pc/` 전용 SMB 쓰기 공유·권한 검증 완료, 서브컴 마운트 대기. [인계](2026-09-12_03_sub_pc_results_share.md).

- **세 씬 v4 손수건 재개 복구:** 종료 흔적을 보존하고312프레임·936파일 hash 검증 후 `paused` 복구. 직사각형 완료·삼각 깃발 수치 실패 유지, 계산 재시작은 사용자 대기. [현재 상태·복구 근거](2026-09-12_01_three_mesh_shell.md#현재-상태).

- **메시 후보 통합 기록:** 13개 후보의 확보 상태·우선순위와 학습/평가 분리 검토안 정리. 원본8그룹 학습4/개발2/평가2는 제안이며 대상 배정·학습 적격성은 미확정. [통합 목록](../mesh_candidate_audit/README.md#통합-후보와-데이터-분할-검토안) · [인계](2026-09-12_02_free_mesh_audit.md).

- **추가 무료 메시 5개 검토:** Grass·Fern·Celandine 4K 새 다운로드·구조 검사, Skirt 기존 결과 재사용. Monstera 로그인 요구로 미확보. Grass/Skirt 조건부 우선, Fern은 알파에 의존하는 윤곽 때문에 후순위. 물리 실행·학습 적격성 미검증. [근거](../mesh_candidate_audit/evidence/extra/README.md).

- **무료 메시 후속 후보 5개 기록:** 우선순위·선정 이유·필요 보완·진행 순서 보존. 실제 구조 감사 기반이며 물리 실행/최종 채택은 미완료. [후보 목록](../mesh_candidate_audit/README.md#후속-활용-후보-5개--2026-09-12-선정) · [인계와 한계](2026-09-12_02_free_mesh_audit.md).

- **세 씬64회 재구축 v4 준비 완료:** 첫 씬6.0667초부터·추가 두 씬0초부터, 시간 제한 없음. 짧은 GPU/CPU검증 통과·본 계산 미시작. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/reuse64_batch_20260912/README.md).

- **비용 급증5프레임 비교 완료:** 재구축64회 후보가 검산을 유지하며 가장 빨랐다. 본 실행 미반영·사용자 결정 대기. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/preconditioner5_20260912/README.md).

- **세 씬 v3 복구 준비:** 빌드 문자열 호환성 보완·세 씬 시간 한도 없음. 첫 씬364프레임 보존 재개, 추가 두 씬0초부터. 검증 통과·본 계산 미시작. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/three_scene_recovery_20260912/README.md).

- **2026-09-12 세 씬 10초 순차 실행 준비 완료:** 동결·단계별 비용/실패 기록·재시작 검증 통과. 사용자 요청으로 v2는 첫 씬만4시간 제한, 추가 두 씬은 시간 제한 없음. 본 계산은 ready·0프레임이다. [인계](2026-09-12_01_three_mesh_shell.md).

- **최신 검증(2026-09-12):** 같은 어려운 4프레임에서 수렴 여유 3조건 비교 완료, 각 256단계 원식 검산 통과. 내부 30% 목표+EW 상한 1e-4는 최대 잔차가 공식 허용치의 2.075%, 현재 EW보다 풀이 시간 17.1% 감소했다. 후속 검증 우선 후보이며 장기 기본값은 미채택이다. 공통 코드·본 실행 미변경, 다른 상태·재시작 검증이 남았다. [조건·결과·한계](../R1_teacher_velocity_reset/timestep_search/evidence/inexact4_margin_20260912/README.md).

- **최신 검증(2026-09-12):** 본 실행 v2는 첫 2.5초·150프레임 검산 통과 후 계획된 정지다. 사용자 승인으로 어려운 127~130번 연속 프레임의 strict/EW 비교를 완료했다. 양쪽 256단계 통과, EW 풀이 시간 28.8%·HVP 36.9% 감소. 최대 힘 잔차가 허용치의 99.24%여서 다음은 수렴 여유·비용 균형 보완이다. 장기 기본값 미채택, 본 실행 미변경. [조건·결과·한계](../R1_teacher_velocity_reset/timestep_search/evidence/inexact4_hard_20260912/README.md). 아래 준비·실행 대기 표기는 이전 상태다.

- **최신 검증(2026-09-11):** 사용자 승인으로 4배의 동일 1프레임(64단계)에 내부 선형 허용오차 조절을 시험했다. 네 조건 모두 기존 최종 힘 기준과 독립 검산 통과. EW2형은 HVP 39.5% 감소, 공유 GPU 관측 계산 시간 약 33% 감소. 관련 8개 검사 통과. [조건·결과·한계](../R1_teacher_velocity_reset/timestep_search/evidence/inexact4_20260911/README.md). 장기 기본값은 미채택이며 진행 중 본 실행은 변경하지 않았다. 다음은 어려운 상태·연속 구간 검증이다. 아래 준비/대기 표기는 이전 시점 기록이다.

- **최신 정정(2026-09-11):** 사용자 확인으로4시간은 새10초 본 실행 전체의 한도이며 이전 실행·개발 시간을 차감하지 않는다. 초기 상태·사용0초의4배 전환v2를 준비만 했다.2.5초마다 정지하고 같은 본 실행의 시간은 누적한다. [새 실행·검증](../R1_teacher_velocity_reset/timestep_search/evidence/adaptive4_four_hour_20260911/README.md). 아래 잔여 예산 표기는 이전 해석이며 이번v2에는 적용하지 않는다.

- **최신(2026-09-11):** 초기rest·어려운 구간current 전환을 구현하고 개발 검증했다. 같은 전환1배 대비 초기0.1초4배의 가속과1% 수치 보간 비교 통과, GPU 재개 차이0·16개 검사 통과. [정확한 범위·비용·새 실행](../R1_teacher_velocity_reset/timestep_search/evidence/adaptive4_20260911/README.md). 새본 실행은 잔여7368.317275초로 준비만 했으며2.5초/10초/공간 수렴은 미완료다.

- **최신 판정(2026-09-11):** 4배 실행 연결·21개 검사·실제GPU 재시작 검증 완료. 본 실행은 초기0.1초 비용이 과거1배보다 커서 기존 사용자 비용 조건에 따라 일시 중단했다. 확정7frame 보존,2.5초/전체 정확도 미완료. 수치 실패·예산 소진이 아니다. [비용·잔여 예산·다음 분기](../R1_teacher_velocity_reset/timestep_search/evidence/segments4_20260911/README.md). 초기rest 보조 풀이 활용 검토 여부를 질문한다.

- **최신 결과(2026-09-11):** 4배+현재 행렬 재사용의 짧은 전체 수치 보간 비교가1% 이내이며 같은 최적화1배보다 빨랐다.64배는1단계만 통과,32배는 재사용/매번 재구축 모두 비선형 line_search 실패. 준뉴턴·장기 검증은 미완료이며4배 긴 구간 우선 여부의 사용자 선택 대기. [근거](../R1_teacher_velocity_reset/timestep_search/evidence/acceleration4_20260911/README.md).

- **최신(2026-09-11):** 4배부터 실제 속도 개선 후32배·64배 확장으로 사용자 방침 변경. [시험·판정](../R1_teacher_velocity_reset/timestep_search/evidence/acceleration4_20260911/README.md). 같은 최적화의1배와 비교하며 기존256배 전용 방침은 과거 기록이다.

- **최신(2026-09-11):** 사용자 승인으로 물리·허용오차·256배를 유지한 빠른 탄성 진동 분리 시험을 수행했다. 시작/중간 접선 지수 후보는 시간 정확도 미달로 보류하고, Gauss6 경로+지수 보정 후보와2/4분할 참조의 국소 끝 상태 차이 감소를 확인했다. [현재 판정·근거](2026-09-10_02_teacher_timestep_search.md). 결합 후보의 끝 상태1% 비교는 통과했으나 전체 시간 곡선·n=32 재개·엄격한 형식 간 동등성은 미완료다. 다음은 지수 작용 정밀도·비용 및 전체 곡선 검산 보완이다. 본 실행 잔여7998초 유지, 기존 wrapper는 Newmark용이며 새 장기 실행은 미연결이다.2.5초/10초·해상도 수렴·R1 채택은 미완료이며 작은 Δt 자동 전환은 하지 않는다. 아래 이전 선택 대기는 과거 기록이다.

- **64배 풀이 개선:** restart240×3으로 실패 단계와 후속4단계 검산 통과.64배 새 v4(잔여7998초) 준비 완료·사용자 실행 대기.64배 검증 후256배 진행 결정. [최신 인계](2026-09-10_02_teacher_timestep_search.md). 아래 이전 실행 대기 표기는 과거 기록이다.

- **한도12 채택:** 64배 Δt·기존 정확도 기준을 유지한 v3 준비 완료.15개 검사·동결 CUDA smoke 통과, 남은 예산3시간21분12초·사용자 실행 대기. [최신 인계](2026-09-10_02_teacher_timestep_search.md).

- **선형 반복 한도 시험:** v2 첫2.5초 통과 후 수렴 실패. 한도12로 실패 step+다음4개 step 및 독립 검산 통과. 장기 설정 선택 대기·기본 코드 미변경. [최신 인계](2026-09-10_02_teacher_timestep_search.md).

- **초기 실행 실패 보완:** 위치 갱신 반올림 검사 오탐 수정·실제 조건24 interval 검산 완료. v1 보존, v2 사용자 실행 대기. [최신 인계](2026-09-10_02_teacher_timestep_search.md).

- **GPU 고정밀 기하 시험:** 고정밀 상태·저장·탐색 API, 단기 원식 검산과 재시작 및25개 검사 통과. 4분할10초를2.5초씩 이어가는 합계4시간 동결 계획 준비 완료·사용자 실행 대기. [최신 인계](2026-09-10_02_teacher_timestep_search.md).

- **[실험 인계·정밀도 보완](2026-09-10_02_teacher_timestep_search.md)**: 2026-09-11 직접 누적은 후속 정체가 남은 부분 개선이다. 고정밀 별도 시험은 8 step·hi/lo 재시작을 통과했지만 CPU 비용이 커 정식 반영은 보류다. 4배 바람은 저장 구간의 진폭·위상 차이를 확인했으며 기존10초 추천 없음·필수19/20 통과 판정을 유지한다.

확인 기준: 2026-09-11 후속 진단. 전체 궤적 물리 재검산은 하지 않았다. 아래 전체 성능 비교는 앞서 검토한 별도 실험이다.

- 선행 실험 근거는 [Teacher note](2026-09-09_02_teacher_velocity_reset.md#현재-상태), 최신 상태는 위 인계를 먼저 읽는다.
- [약한 바람](../R1_teacher_velocity_reset/p3_shell_random/README.md) 검증 완료. [4배 바람](../R1_teacher_velocity_reset/p3_shell_random/scale4/README.md)은 별도 판정이며 R1 전체/학습 적격성은 미완료다.
- [전체 1.5초 성능 비교](../R1_teacher_velocity_reset/p3_shell_random/profiling/full_run/README.md): 양쪽90 frame·검산·비교 완료. HVP/graph 방식의 전체 실행 근거를 확보했으며 다른 부하와 재시작 영향 때문에 성능값은 잠정 결과로 해석한다.
- [GPU 성능 보고](../R1_teacher_velocity_reset/p3_shell_random/profiling/README.md): HVP/graph 검증 통과, CuPy 희소 풀이는 미채택. 사용자는 CPU 풀이+HVP/graph로 계속 진행하고 추가 최적화를 보류하기로 선택했다.

- [개선 경로 사용자 실행](../R1_teacher_velocity_reset/p3_shell_random/scale4/fast_handoff/README.md): 기본 v2 묶음116/116 task 종료. 마지막 reset의 공간 속도 비교가1% 기준에 미달했으며 결과 검토가 남았다.

## 기록 찾기와 작성

- [과거 목록](history.md)은 필요할 때만 검색한다. 최근 날짜 전체를 일괄 읽지 않는다.
- 현행 기록 규칙과 간결한 형식은 [공통 지침](../../AGENTS.md#간결한-작업-기록)을 따른다.
- 중간 보고 원문은 기록하지 않는다. 결과·결정·재발 방지·근거 링크만 남긴다.

- [기록·맥락 최적화](2026-09-10_01_token_context_optimization.md): 운영 문서 정리; 연구·구현 진척과 별개다.
