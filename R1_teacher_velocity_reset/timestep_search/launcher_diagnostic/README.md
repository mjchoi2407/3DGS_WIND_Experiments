# GTX1080Ti 공통 경로 성능 진단

[진단 보고서](report.md): 과거2.5배 저하는 현재 재현되지 않았고 원인은 미확정이다.
부모 CUDA 초기화 유무의 C/D 교대3쌍은 모두 기존 R64 시간·검산·반복량을 유지했다.
이후 동일 W1 checkpoint3프레임의 R64/M1 세 쌍에서 M1 계산+검산 시간은 약18.3% 줄었다.
과거 무풍 시간으로 바람 가속률을 보정하지 않았다. 생산 solver 변경은 없다.

Canonical 원시 결과: `experiments/artifacts/runs/teacher_launcher_diagnostic/20260917/`.
동일 이름의 sibling ZIP에는 raw CSV/NPZ,로그,telemetry,checkpoint/forcing/source/native hash,
실제 import/Graph 관측,실행 명령과 이번 진단 도구 diff가 있다. JIT cache와 pycache는 제외한다.
Nsight Systems report 변환은 GPU UUID 오류로 실패했다. 해당 오류와 observer 결과를 보존했고
profiler 실행 시간은 일반 집계에서 제외했다. A/B는 C/D가 정상 속도여서 실행하지 않았다.

기존 바람 실행은 확인 시 이미 interrupted였다. 프리로드·무풍 완료 checkpoint와 바람120프레임
확정 chunk hash/검산을 확인하고 보존했다. 추가 종료 신호나 장시간 재생은 하지 않았다.
