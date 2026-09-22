# 완료한 두 메시의 저장 결과 뷰어

## 대상과 실행

기존 `20260912_three_scenes_10s_v4`의 완료된 `reference_rectangle`과 `handkerchief`를 읽는다.
각600프레임·10초의 저장 경계와 초기 상태를 표시한다. 물리 계산을 다시 실행하지 않는다.

```bash
bash experiments/R1_teacher_velocity_reset/timestep_search/view_completed_meshes.sh
```

- 왼쪽은 직사각형, 오른쪽은 손수건이며 비교를 위해 표시 위치만 평행 이동했다. 크기·변위 배율은1이다.
- 처음에는 정지 상태다. Space로 재생/일시정지, 시간 슬라이더로0–10초 이동, 속도 슬라이더로 느리게/빠르게 재생한다.
- 왼쪽 드래그는 회전, 휠은 확대/축소다. 빨간 점은 고정점이고 체크무늬는 보기 위한 임시 표시 재질이다.
- 하나만 보려면 `--shape reference_rectangle` 또는 `--shape handkerchief`를 붙인다.
- 기존 Newton live viewer와 달리 저장된 위치만 표시한다. 재생 속도 조절은 물리 조건을 변경하지 않는다.

## 원본과 표시 정확도의 경계

표시 캐시는 `experiments/artifacts/runs/shell_playback/20260913_completed_v1/<shape>/`에 별도 보존한다.
첫 준비에서 완료 report, 재구성 코드·입력 hash와 확정600개 trace SHA256을 확인하고,
각 프레임 마지막 위치를 고정밀 hi/lo에서 복원해 rest에 더한다. 초기 상태와 시간·고정점도 검사한다.
원본 NPZ/report/설정은 수정하지 않는다. 캐시 재사용 시 원본 report 및 캐시 파일 hash를 확인한다.
원본 trace의 재검증은 캐시 최초 생성 시점의 검사이며 매 재생에서 원본 전체를 다시 읽지는 않는다.

P3 원소의10개 계산점을9개 표시 삼각형으로 연결한다. 이는 고차 곡면을 유한 개의 평면으로
근사하는 표시 방식이며 곡면의 모든 점을 정확히 렌더링하는 것은 아니다.
60Hz 저장 경계만 보여주며 내부64단계를 모두 재생하지 않는다. 표시 위치는 float32이고,
반올림 최대오차는 캐시 manifest에 남긴다. 표시용 캐시는 teacher 학습·물리 정확도 판정에 사용하지 않는다.
이번 화면은 메시 재생이며3DGS 렌더링·원본 고해상도 외관은 아니다.

## 구현과 검증

구현은 `code/wind3dgs/evaluation/view_shell_recording.py`가 소유한다.
P3 표시 분할의 방향·면적 보존과 마지막 시각을 포함한 프레임 선택 단위 검사를 수행한다.
두 씬 각600개 trace SHA256·고정점·시간·finite 검사를 통과했고 캐시 재사용 hash도 확인했다.
표시 위치 float32 최대 반올림 오차는 직사각형5.95e-8m, 손수건2.99e-8m 미만이다.
단위 검사2개·shell 문법 통과. 실제 OpenGL에서5초 상태의 두 메시를3회 렌더링하고 화면을 확인했다.
[검사 결과](checks.json), [실제 표시 화면](preview.png).
현재 WSL 환경에서는 CUDA/OpenGL 직접 공유가 불가능해 설치된 뷰어의 복사 경로를 사용한다.
해당 fallback으로 실제 화면 출력은 통과했으며 이것은 시뮬레이션 실패가 아니다.
추가 dependency 설치·외부fetch·다운로드·물리 실행은 하지 않는다.
