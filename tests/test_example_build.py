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
    assert (example / "output/theme/js/theme.js").is_file()

    index = (example / "output/index.html").read_text(encoding="utf-8")
    assert index.index("data-pet-theme-loader") < index.index('rel="stylesheet"')
    assert 'meta name="theme-color" content="#f7f8f3"' in index
    assert "data-pet-theme-toggle" in index
    assert "/theme/js/theme.js" in index
