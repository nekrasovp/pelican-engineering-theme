from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_example(name: str, target: Path) -> Path:
    """Copy and build one source example, returning its output directory."""
    example = target / name
    shutil.copytree(ROOT / "examples" / name, example)
    return build_copied_example(example)


def build_copied_example(example: Path) -> Path:
    """Build an already copied example without checkout import leakage."""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pelican",
            "content",
            "-s",
            "pelicanconf.py",
            "-o",
            "output",
        ],
        cwd=example,
        env=environment,
        check=True,
    )
    return example / "output"
