#!/usr/bin/env python3
"""Install one exact artifact and build only the files embedded in README."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FILE_BLOCK = re.compile(
    r"<!-- quickstart-file: ([^\s]+) -->\s*\n"
    r"```(?:python|markdown)\n(.*?)\n```",
    re.DOTALL,
)
EXPECTED_FILES = {"pelicanconf.py", "content/hello.md"}


def extract_quickstart_files(readme: str) -> dict[str, str]:
    """Extract the exact quick-start configuration and content blocks."""
    files: dict[str, str] = {}
    for raw_name, content in FILE_BLOCK.findall(readme):
        if raw_name in files:
            raise ValueError(f"duplicate quickstart file: {raw_name}")
        path = Path(raw_name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe quickstart file path: {raw_name}")
        files[raw_name] = content + "\n"
    if set(files) != EXPECTED_FILES:
        raise ValueError(
            f"README quickstart files are {sorted(files)!r}, "
            f"expected {sorted(EXPECTED_FILES)!r}"
        )
    return files


def run(command: list[str], *, cwd: Path) -> None:
    """Run without checkout Python-environment leakage."""
    environment = os.environ.copy()
    for variable in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(variable, None)
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def verify_onboarding(readme: Path, artifact: Path, python: str) -> None:
    """Build a generic site using only README file blocks and one artifact."""
    readme = Path(os.path.abspath(readme))
    artifact = Path(os.path.abspath(artifact))
    if not artifact.is_file():
        raise FileNotFoundError(f"candidate artifact does not exist: {artifact}")
    files = extract_quickstart_files(readme.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="pet-readme-proof-") as raw_temp:
        proof = Path(raw_temp)
        environment = proof / ".venv"
        proof_python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        run(["uv", "venv", "--python", python, str(environment)], cwd=proof)
        run(
            ["uv", "pip", "install", "--python", str(proof_python), str(artifact)],
            cwd=proof,
        )
        site = proof / "quickstart"
        for relative, content in files.items():
            target = site / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        import_check = (
            "import pathlib,sysconfig; import pelican_engineering_theme as t; "
            "m=pathlib.Path(t.__file__).resolve(); "
            "p=pathlib.Path(sysconfig.get_paths()['purelib']).resolve(); "
            "assert m.is_relative_to(p),(m,p); assert t.__version__=='0.1.0'"
        )
        run([str(proof_python), "-I", "-c", import_check], cwd=proof)
        run(
            [
                str(proof_python),
                "-I",
                "-m",
                "pelican",
                "content",
                "-s",
                "pelicanconf.py",
                "-o",
                "output",
            ],
            cwd=site,
        )
        required = (
            site / "output/small-technical-note.html",
            site / "output/theme/css/scaffold.css",
            site / "output/theme/js/theme.js",
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise RuntimeError(f"README-only build is missing files: {missing!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--python", default=os.path.abspath(sys.executable))
    args = parser.parse_args()
    verify_onboarding(args.readme, args.artifact, args.python)
    print(f"README-only installed-artifact build passed: {args.artifact.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
