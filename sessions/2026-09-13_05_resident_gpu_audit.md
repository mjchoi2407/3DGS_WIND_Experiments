# GPU 상주 검산 실행과 대조

## 현재 상태

- 확인일:2026-09-13. 채택 평가 재사용·무압축 후보의 완료 궤적에 GPU 상주 검산을 적용했다.
- 같은640구간의 기존 검산과 전체 단계별 판정 대조 통과. GPU 계산·초기 준비·파일 읽기를 분리해 기록했다.
- 기존 생성 결과만 읽었다. 시뮬레이션·하이브리드 검산을 재실행하거나 기존 결과를 덮어쓰지 않았다.
- 새 `run_gpu_audit.sh`는 코드 동결·원본 해시·cuDSS 환경을 준비하고 새 경로에 검산 결과를 쓴다.
- 향후 `profile_run.py --reuse-audit` 새 후보는 GPU 검산이 기본이다. 기존 검산기는 `--legacy-audit`로 선택 가능하다.
- [명령·출력·메모리 설정](../R1_teacher_velocity_reset/timestep_search/gpu_resident/README.md#gpu-상주-검산--현행-실행),
  [수치·통과 기준·해시·시간 범위](../R1_teacher_velocity_reset/timestep_search/gpu_resident/audit_validation/README.md).
- 실제640구간 최종 동결 실행·회귀7개·다음 생성 실행기의 준비 검증 완료. 사용자 실행용 기본 출력 경로는 아직 만들지 않았다.
- 다음:사용자 실행 결과 확인. 다른 메시·장기 안정성·학습 적격성은 별도 검증이며 기존 Gate 유지.
- Experiments 관련 worktree·새 검증 산출물만 갱신. 커밋·푸시 없음.
