#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
workspace_dir="$(cd -- "$script_dir/../../../.." && pwd)"
cd -- "$workspace_dir"
exec "$workspace_dir/.venv/bin/python" -u "$script_dir/control_full_comparison.py" "$@"
