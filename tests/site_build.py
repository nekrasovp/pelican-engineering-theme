from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_NOTEBOOK_FIXTURE = (
    ROOT / "tests/fixtures/plugin003-nbconvert-basic-v1/representative.fragment.html"
)


def add_external_notebook_contract_article(example: Path) -> Path:
    """Add the exact vendored fragment as trusted content without conversion."""
    metadata = (
        b"Title: External Notebook Contract Round Trip\n"
        b"Date: 2026-07-22\n"
        b"Slug: external-notebook-contract\n"
        b"Status: hidden\n"
        b"Jupyter_Notebook: true\n"
        b"Notebook_Html_Contract: nbconvert-basic.v1\n\n"
    )
    target = example / "content/external-notebook-contract.md"
    target.write_bytes(metadata + EXTERNAL_NOTEBOOK_FIXTURE.read_bytes())
    return target


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
