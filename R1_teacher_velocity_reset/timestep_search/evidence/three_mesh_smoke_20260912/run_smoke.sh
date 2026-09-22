#!/usr/bin/env bash
set -u
out=experiments/artifacts/runs/teacher_timestep_search/20260912_three_mesh_smoke_v1
mkdir -p "$out"
for shape in reference_rectangle triangular_flag handkerchief; do
  PYTHONPATH=code OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 timeout 900 .venv/bin/python -u -m wind3dgs.evaluation.teacher_sample_shell_probe "$out/$shape" "$shape" > "$out/$shape.log" 2>&1
  result=$?
  printf '%s\n' "$result" > "$out/$shape.exit_code"
done
