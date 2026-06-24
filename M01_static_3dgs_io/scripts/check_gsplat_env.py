#!/usr/bin/env python3
"""Compatibility wrapper for the reusable M01 gsplat environment checker."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from wind3dgs.m01_static_3dgs_io.check_gsplat_env import main  # noqa: E402


if __name__ == "__main__":
    main()

