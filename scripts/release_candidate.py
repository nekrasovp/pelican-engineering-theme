#!/usr/bin/env python3
"""Build and verify immutable, deterministic release-candidate artifacts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "pelican-engineering-theme"
VERSION = "0.1.0"
WHEEL = "pelican_engineering_theme-0.1.0-py3-none-any.whl"
SDIST = "pelican_engineering_theme-0.1.0.tar.gz"
EXPECTED_FILES = (WHEEL, SDIST)
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")


def run_text(command: list[str], *, cwd: Path = ROOT) -> str:
    """Run a read-only command and return normalized stdout."""
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_records(directory: Path) -> list[dict[str, int | str]]:
    """Return exact candidate artifact records in stable filename order."""
    return [
        {
            "name": name,
            "bytes": (directory / name).stat().st_size,
            "sha256": sha256_file(directory / name),
        }
        for name in EXPECTED_FILES
    ]


def validate_expected_sha(value: str) -> str:
    """Require a full lowercase commit SHA."""
    if SHA_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"expected source SHA must be 40 lowercase hex digits: {value!r}"
        )
    return value


def export_exact_source(destination: Path, source_sha: str) -> None:
    """Export one committed source tree without ignored checkout state."""
    destination.mkdir(parents=True, exist_ok=False)
    with tempfile.NamedTemporaryFile(suffix=".tar") as raw_archive:
        subprocess.run(
            ["git", "archive", "--format=tar", source_sha],
            cwd=ROOT,
            stdout=raw_archive,
            check=True,
        )
        raw_archive.flush()
        with tarfile.open(raw_archive.name) as archive:
            archive.extractall(destination, filter="data")


def normalize_sdist(path: Path, source_date_epoch: int) -> None:
    """Canonicalize archive ownership and timestamps across build hosts."""
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as raw_temp:
        normalized = Path(raw_temp.name)
    try:
        with (
            tarfile.open(path, "r:gz") as source,
            normalized.open("wb") as raw_target,
            gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw_target,
                mtime=source_date_epoch,
            ) as compressed_target,
            tarfile.open(
                fileobj=compressed_target, mode="w|", format=tarfile.PAX_FORMAT
            ) as target,
        ):
            for member in source.getmembers():
                member.mtime = source_date_epoch
                member.uid = 0
                member.gid = 0
                member.uname = ""
                member.gname = ""
                member.pax_headers = {
                    key: value
                    for key, value in member.pax_headers.items()
                    if key not in {"atime", "ctime", "mtime"}
                }
                payload = source.extractfile(member) if member.isfile() else None
                target.addfile(member, payload)
        normalized.replace(path)
    finally:
        normalized.unlink(missing_ok=True)


def build_once(
    destination: Path, source_date_epoch: int, *, source_root: Path = ROOT
) -> None:
    """Build one sdist/wheel pair with deterministic timestamp input."""
    destination.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(source_date_epoch)
    subprocess.run(
        ["uv", "build", "--out-dir", str(destination)],
        cwd=source_root,
        env=environment,
        check=True,
    )
    # uv creates this marker for its output directory; it is not a candidate asset.
    (destination / ".gitignore").unlink(missing_ok=True)
    normalize_sdist(destination / SDIST, source_date_epoch)
    actual = sorted(path.name for path in destination.iterdir() if path.is_file())
    if actual != sorted(EXPECTED_FILES):
        raise RuntimeError(
            f"build produced {actual!r}, expected {sorted(EXPECTED_FILES)!r}"
        )


def build_candidate(
    destination: Path, report_path: Path, expected_source_sha: str
) -> dict[str, Any]:
    """Build twice, reject drift, and write immutable candidate provenance."""
    expected = validate_expected_sha(expected_source_sha)
    actual = validate_expected_sha(run_text(["git", "rev-parse", "HEAD"]))
    if actual != expected:
        raise RuntimeError(
            f"actual source SHA {actual} does not match expected source SHA {expected}"
        )

    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=normal"])
    if dirty:
        raise RuntimeError("candidate build requires a clean exact-source checkout")

    source_date_epoch = int(run_text(["git", "show", "-s", "--format=%ct", actual]))
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError(f"candidate destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    if report_path.exists():
        raise RuntimeError(f"candidate report already exists: {report_path}")

    with tempfile.TemporaryDirectory(prefix="pet-candidate-build-") as raw_temp:
        temporary = Path(raw_temp)
        first = temporary / "first"
        second = temporary / "second"
        first_source = temporary / "first-source"
        second_source = temporary / "second-source"
        export_exact_source(first_source, actual)
        export_exact_source(second_source, actual)
        build_once(first, source_date_epoch, source_root=first_source)
        build_once(second, source_date_epoch, source_root=second_source)
        first_records = artifact_records(first)
        second_records = artifact_records(second)
        if first_records != second_records:
            raise RuntimeError(
                "candidate artifacts are not byte-reproducible across two builds"
            )
        for name in EXPECTED_FILES:
            shutil.copy2(first / name, destination / name)

    report: dict[str, Any] = {
        "schema_version": 1,
        "project": PROJECT,
        "version": VERSION,
        "candidate_only": True,
        "published": False,
        "source_sha": actual,
        "expected_source_sha": expected,
        "source_date_epoch": source_date_epoch,
        "reproducible_builds": 2,
        "builder": run_text(["uv", "--version"]),
        "files": artifact_records(destination),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    errors = candidate_report_errors(report, destination, expected)
    if errors:
        raise RuntimeError("candidate self-verification failed: " + "; ".join(errors))
    return report


def candidate_report_errors(
    report: dict[str, Any], artifact_dir: Path, expected_source_sha: str
) -> list[str]:
    """Return fail-closed source, identity, and artifact provenance errors."""
    expected = validate_expected_sha(expected_source_sha)
    errors: list[str] = []
    exact_values: dict[str, object] = {
        "schema_version": 1,
        "project": PROJECT,
        "version": VERSION,
        "candidate_only": True,
        "published": False,
        "source_sha": expected,
        "expected_source_sha": expected,
        "reproducible_builds": 2,
    }
    for key, value in exact_values.items():
        if report.get(key) != value:
            errors.append(f"report {key} is {report.get(key)!r}, expected {value!r}")

    source_date_epoch = report.get("source_date_epoch")
    if not isinstance(source_date_epoch, int) or source_date_epoch <= 0:
        errors.append("report source_date_epoch must be a positive integer")
    builder = report.get("builder")
    if not isinstance(builder, str) or not builder.startswith("uv "):
        errors.append("report builder must identify uv")

    raw_files = report.get("files")
    if not isinstance(raw_files, list):
        errors.append("report files must be a list")
        raw_files = []
    expected_names = list(EXPECTED_FILES)
    actual_names = [item.get("name") for item in raw_files if isinstance(item, dict)]
    if actual_names != expected_names:
        errors.append(
            f"report artifact names are {actual_names!r}, expected {expected_names!r}"
        )

    for name in EXPECTED_FILES:
        path = artifact_dir / name
        if not path.is_file():
            errors.append(f"missing candidate artifact: {name}")
            continue
        matching = [
            item
            for item in raw_files
            if isinstance(item, dict) and item.get("name") == name
        ]
        if len(matching) != 1:
            errors.append(f"report must contain exactly one record for {name}")
            continue
        record = matching[0]
        actual_bytes = path.stat().st_size
        actual_digest = sha256_file(path)
        if record.get("bytes") != actual_bytes:
            errors.append(f"candidate byte size mismatch for {name}")
        if record.get("sha256") != actual_digest:
            errors.append(f"candidate SHA-256 mismatch for {name}")

    extra = sorted(
        path.name
        for path in artifact_dir.iterdir()
        if path.is_file() and path.name not in EXPECTED_FILES
    )
    if extra:
        errors.append(f"unexpected candidate artifacts: {extra!r}")
    return errors


def load_report(path: Path) -> dict[str, Any]:
    """Load one JSON object candidate report."""
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("candidate report must be a JSON object")
    return {str(key): value for key, value in raw.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--dist", type=Path, required=True)
    build.add_argument("--report", type=Path, required=True)
    build.add_argument("--expected-source-sha", required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--dist", type=Path, required=True)
    verify.add_argument("--report", type=Path, required=True)
    verify.add_argument("--expected-source-sha", required=True)

    args = parser.parse_args()
    if args.command == "build":
        report = build_candidate(args.dist, args.report, args.expected_source_sha)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    errors = candidate_report_errors(
        load_report(args.report), args.dist, args.expected_source_sha
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Exact release-candidate provenance verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
