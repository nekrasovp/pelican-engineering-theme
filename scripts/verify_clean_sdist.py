#!/usr/bin/env python3
"""Install an sdist in a clean environment and run its unpacked tests."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTEST_SPEC = "pytest>=8.4,<9"


def run(command: list[str], *, cwd: Path | None = None) -> None:
    """Run without Python path or active-environment leakage from the checkout."""
    environment = os.environ.copy()
    for variable in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(variable, None)
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def find_source_root(unpack_root: Path) -> Path:
    """Return the single unpacked source tree."""
    candidates = [
        path
        for path in unpack_root.iterdir()
        if path.is_dir() and (path / "pyproject.toml").is_file()
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"expected one unpacked source tree, found {candidates}")
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sdist", type=Path)
    parser.add_argument("--python", default=os.path.abspath(sys.executable))
    args = parser.parse_args()

    sdist = Path(os.path.abspath(args.sdist))
    if not sdist.is_file():
        parser.error(f"sdist does not exist: {sdist}")

    with tempfile.TemporaryDirectory(prefix="pet-sdist-proof-") as raw_temp:
        proof_root = Path(raw_temp)
        unpack_root = proof_root / "unpacked"
        environment_path = proof_root / ".venv"
        unpack_root.mkdir()
        shutil.unpack_archive(sdist, unpack_root)
        source_root = find_source_root(unpack_root)

        python_relative = "Scripts/python.exe" if os.name == "nt" else "bin/python"
        proof_python = environment_path / python_relative
        run(["uv", "venv", "--python", args.python, str(environment_path)])
        run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(proof_python),
                str(sdist),
                PYTEST_SPEC,
            ],
            cwd=proof_root,
        )

        import_check = (
            "import pathlib, sysconfig; "
            "import pelican_engineering_theme as theme; "
            "module = pathlib.Path(theme.__file__).resolve(); "
            "purelib = pathlib.Path(sysconfig.get_paths()['purelib']).resolve(); "
            "assert module.is_relative_to(purelib), (module, purelib); "
            "print(f'import={module}')"
        )
        run([str(proof_python), "-I", "-c", import_check], cwd=proof_root)
        run(
            [str(proof_python), "-I", "-m", "pytest", "-q"],
            cwd=source_root,
        )
        print(f"Clean unpacked-sdist tests passed: {sdist.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
