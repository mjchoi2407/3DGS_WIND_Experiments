#!/usr/bin/env bash
# 기본 동작은 입력 준비뿐이다. 실행은 action/backend를 명시해야 한다.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
# native CCD 오류가 다른 프로그램 메모리까지 소진하지 않도록 프로세스 한도를 둔다.
ulimit -v 4194304
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_self_contact_scene_suite "$@"
