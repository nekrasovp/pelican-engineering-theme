from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_minimal_example_builds(tmp_path: Path) -> None:
    example = tmp_path / "example"
    shutil.copytree(ROOT / "examples/minimal", example)
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

    assert (example / "output/index.html").is_file()
    assert (example / "output/small-technical-note.html").is_file()
    assert (example / "output/theme/css/scaffold.css").is_file()
