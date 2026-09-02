"""Reproduce all saved results in the repository."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*arguments):
    subprocess.run([sys.executable, *map(str, arguments)], cwd=ROOT, check=True)


run(ROOT / "src" / "rainflow_analysis.py", "--method", "rainflow_4point")
run(ROOT / "src" / "rainflow_analysis.py", "--method", "rainflow_3point_demo")
run(ROOT / "tools" / "run_task_5.py")
