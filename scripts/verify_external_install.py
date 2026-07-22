#!/usr/bin/env python3
"""Install a wheel outside the checkout and build a copied generic example."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path | None = None) -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--python", default="3.13")
    args = parser.parse_args()

    wheel = args.wheel.resolve()
    if not wheel.is_file():
        parser.error(f"wheel does not exist: {wheel}")

    with tempfile.TemporaryDirectory(prefix="pet-wheel-proof-") as raw_temp:
        proof_root = Path(raw_temp)
        environment_path = proof_root / ".venv"
        run(["uv", "venv", "--python", args.python, str(environment_path)])

        python_relative = "Scripts/python.exe" if os.name == "nt" else "bin/python"
        python = environment_path / python_relative
        run(["uv", "pip", "install", "--python", str(python), str(wheel)])

        check = (
            "import pathlib, sysconfig; "
            "import pelican_engineering_theme as theme; "
            "module = pathlib.Path(theme.__file__).resolve(); "
            "purelib = pathlib.Path(sysconfig.get_paths()['purelib']).resolve(); "
            "assert module.is_relative_to(purelib), (module, purelib); "
            "path = theme.get_theme_path(); "
            "assert path.is_dir(); "
            "print(f'import={module}'); "
            "print(f'theme={path}')"
        )
        run([str(python), "-I", "-c", check], cwd=proof_root)
        for example_name, article in (
            ("minimal", "small-technical-note.html"),
            ("full", "configurable-shell.html"),
        ):
            example_path = proof_root / example_name
            shutil.copytree(ROOT / "examples" / example_name, example_path)
            run(
                [
                    str(python),
                    "-I",
                    "-m",
                    "pelican",
                    "content",
                    "-s",
                    "pelicanconf.py",
                    "-o",
                    "output",
                ],
                cwd=example_path,
            )
            required_outputs = {
                "index.html",
                article,
                "theme/css/scaffold.css",
                "theme/js/theme.js",
            }
            if example_name == "full":
                required_outputs.update(
                    {
                        "404.html",
                        "archives.html",
                        "authors.html",
                        "categories.html",
                        "index2.html",
                        "index3.html",
                        "pages/about.html",
                        "tags.html",
                    }
                )
            missing = [
                output
                for output in sorted(required_outputs)
                if not (example_path / "output" / output).is_file()
            ]
            if missing:
                raise RuntimeError(
                    f"external {example_name} build is missing: {missing}"
                )
            run(
                [
                    str(python),
                    "-I",
                    str(ROOT / "scripts/validate_shell.py"),
                    str(example_path / "output"),
                ],
                cwd=proof_root,
            )
            run(
                [
                    str(python),
                    "-m",
                    "scripts.validate_content",
                    str(example_path / "output"),
                ],
                cwd=ROOT,
            )
            print(f"External installed-wheel {example_name} build passed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
