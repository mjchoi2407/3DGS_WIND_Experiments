# GPU 세 씬 v12 준비·v11 결과

## 현재 상태

- 2026-09-27: 사용자가 직렬10초를 승인했다. 새 v12는 preload→calm→wind 연속 전달과
  code1/code2 GPU dt/2 복구를 적용해 준비했다. 실행기 검사8개·동결 manifest·세 씬
  600프레임 구성을 확인했다. 본 실행은 사용자 대기이며 장기 완주는 미검증이다.
  기존 v11 분기 계약을 v12에서만 대체한다. [현행 실행·계약·검증](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v12.md#현재-상태).

- 2026-09-27 정리 검증: 관련 회귀33개 통과. 본 시뮬레이션·체크포인트 재생은 하지 않았다.
- 미완료: v12 장기 완주·양 GPU 비교·시간 수렴, 새 연속10초 뷰어와 R1 Gate.
- 다음은 사용자 v12 실행 결과의 완료·검산·상태 연결 확인이다. 원본 v11은 보존한다.

## 이전 v11 근거

- 확인일 2026-09-24. 원본 v11 사각형 wind 메인169·서브193 실패 직전 상태를
  메인 GTX1080Ti에서 각각 1프레임 재생해 기본 code1을 재현했고, 진단 opt-in GPU
  dt/2는 두 상태 모두 독립 검산을 통과했다. RTX5070 직접 복구·wind 잔여 구간과
  직렬10초 궤적은 미검증이다. [원본·입력·명령·결과](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#사각형-wind-code1-dt2-격리-진단).
- 확인일 2026-09-24. 동일 manifest의 메인·서브 v11에서 손수건·삼각 깃발은 preload/calm/wind 120/240/240 전부 승인됐다. 사각형은 메인 wind169·서브 wind193 표시 프레임에서 Newton15회 한도(code1)로 실패했다. 양쪽 실패 지점에서 이전 후보 초과(code10)는 아니다. [원본 report와 실패 진단](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#v11-사용자-실행-결과).
- 완료 두 씬의 preload→wind 저장 경계를 기존 메시 뷰어에 연결했다. 메인·서브 각각 별도 캐시를 만들고 7개 단위/회귀·양쪽 headless 표시를 통과했다. 물리 계산·원본 변경은 없다. [명령·캐시 hash·표시 범위](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#완료-두-씬-뷰어).
- v11 동결 설정은 원래 물성·바람·dt·허용오차를 유지하고 swept 용량2M·cuDSS 결정성을 적용한다. [당시 설정·제한 검증](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#v11-변경과-검증-범위).
- 미완료: RTX5070 직접 복구·wind 잔여 구간, 양 GPU 궤적·성능 비교 및 R1 Gate 판정.
  완료 두 씬의 표시 화면은 새 수치 검산이나 3DGS 결과가 아니다. [검증 범위](../R1_teacher_velocity_reset/self_contact/three_scenes_gpu_v11.md#사각형-wind-code1-dt2-격리-진단).
- 당시 대기였던 직렬10초 선택과 code1 신규 bundle 반영은 위 v12 준비로 대체됐다.
