from __future__ import annotations

import gzip
import io
import tarfile
from pathlib import Path

from pytest import MonkeyPatch

from scripts.release_candidate import (
    EXPECTED_FILES,
    build_once,
    candidate_report_errors,
    normalize_sdist,
    sha256_file,
)
from scripts.validate_docs import (
    EXPECTED_CAPTURES,
    ROOT,
    render_tree_sha256,
    screenshot_provenance_errors,
)
from scripts.validate_release_policy import WORKFLOW, release_policy_errors
from scripts.verify_readme_onboarding import extract_quickstart_files


def valid_candidate_report(directory: Path, source_sha: str) -> dict[str, object]:
    for name in EXPECTED_FILES:
        (directory / name).write_bytes(f"candidate:{name}".encode())
    return {
        "schema_version": 1,
        "project": "pelican-engineering-theme",
        "version": "0.1.0",
        "candidate_only": True,
        "published": False,
        "source_sha": source_sha,
        "expected_source_sha": source_sha,
        "source_date_epoch": 1,
        "reproducible_builds": 2,
        "builder": "uv 0.test",
        "files": [
            {
                "name": name,
                "bytes": (directory / name).stat().st_size,
                "sha256": sha256_file(directory / name),
            }
            for name in EXPECTED_FILES
        ],
    }


def valid_screenshot_manifest(directory: Path) -> dict[str, object]:
    captures: list[dict[str, object]] = []
    for name, (route, theme, width, height) in EXPECTED_CAPTURES.items():
        path = directory / name
        path.write_bytes(f"screenshot:{name}".encode())
        captures.append(
            {
                "file": name,
                "route": route,
                "theme": theme,
                "viewport": {"width": width, "height": height},
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": 1,
        "source_kind": "first-party-generic-example",
        "candidate_only": True,
        "runtime_network_requests": 0,
        "source_tree_sha256": render_tree_sha256(),
        "capture_tool": "playwright test / Chromium test",
        "captures": captures,
    }


def test_real_release_workflow_is_explicit_and_protected() -> None:
    assert release_policy_errors(WORKFLOW.read_text(encoding="utf-8")) == []


def test_release_policy_rejects_push_trigger_and_missing_environment() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow = workflow.replace(
        "  release:\n    types: [published]", "  push:\n    branches: [main]"
    ).replace("      name: pypi", "      name: unprotected")

    errors = release_policy_errors(workflow)

    assert any("trigger" in error for error in errors)
    assert any("pypi environment" in error for error in errors)


def test_release_policy_rejects_unpinned_action_and_overwrite_bypass() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    workflow = workflow.replace(
        "pypa/gh-action-pypi-publish@ba38be9e461d3875417946c167d0b5f3d385a247",
        "pypa/gh-action-pypi-publish@release/v1",
    ).replace("gh release upload", "gh release upload --clobber")

    errors = release_policy_errors(workflow)

    assert any("reviewed full SHA" in error for error in errors)
    assert any("--clobber" in error for error in errors)


def test_release_policy_rejects_implicit_repository_resolution() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8").replace(
        '--repo "${GITHUB_REPOSITORY}"', ""
    )

    errors = release_policy_errors(workflow)

    assert any("repository explicitly" in error for error in errors)


def test_candidate_report_rejects_stale_or_wrong_source(tmp_path: Path) -> None:
    expected = "a" * 40
    report = valid_candidate_report(tmp_path, expected)
    report["source_sha"] = "b" * 40

    errors = candidate_report_errors(report, tmp_path, expected)

    assert any("source_sha" in error for error in errors)


def test_candidate_report_rejects_modified_artifact(tmp_path: Path) -> None:
    expected = "a" * 40
    report = valid_candidate_report(tmp_path, expected)
    (tmp_path / EXPECTED_FILES[0]).write_bytes(b"modified")

    errors = candidate_report_errors(report, tmp_path, expected)

    assert any("SHA-256 mismatch" in error for error in errors)


def test_build_accepts_only_uv_output_marker(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    destination = tmp_path / "build"

    def fake_uv_build(*args: object, **kwargs: object) -> None:
        del args, kwargs
        for name in (*EXPECTED_FILES, ".gitignore"):
            (destination / name).write_bytes(name.encode())

    monkeypatch.setattr("scripts.release_candidate.subprocess.run", fake_uv_build)
    monkeypatch.setattr("scripts.release_candidate.normalize_sdist", lambda *args: None)

    build_once(destination, 1)

    assert sorted(path.name for path in destination.iterdir()) == sorted(EXPECTED_FILES)


def test_sdist_normalization_removes_host_metadata_drift(tmp_path: Path) -> None:
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    for path, timestamp, owner in ((first, 10, "first"), (second, 20, "second")):
        with (
            path.open("wb") as raw,
            gzip.GzipFile(filename=path.name, mode="wb", fileobj=raw, mtime=timestamp)
            as compressed,
            tarfile.open(fileobj=compressed, mode="w|") as archive,
        ):
            payload = b"candidate"
            member = tarfile.TarInfo("candidate/file.txt")
            member.size = len(payload)
            member.mtime = timestamp
            member.uid = timestamp
            member.gid = timestamp
            member.uname = owner
            member.gname = owner
            archive.addfile(member, io.BytesIO(payload))

    normalize_sdist(first, 1)
    normalize_sdist(second, 1)

    assert first.read_bytes() == second.read_bytes()


def test_screenshot_provenance_rejects_stale_input_tree(tmp_path: Path) -> None:
    manifest = valid_screenshot_manifest(tmp_path)
    manifest["source_tree_sha256"] = "0" * 64

    errors = screenshot_provenance_errors(manifest, tmp_path)

    assert any("source_tree_sha256" in error for error in errors)


def test_screenshot_provenance_rejects_modified_capture(tmp_path: Path) -> None:
    manifest = valid_screenshot_manifest(tmp_path)
    first = next(iter(EXPECTED_CAPTURES))
    (tmp_path / first).write_bytes(b"wrong-source-image")

    errors = screenshot_provenance_errors(manifest, tmp_path)

    assert any(first in error and "SHA-256" in error for error in errors)


def test_render_tree_ignores_generated_cache(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    source = tmp_path / "source"
    cache = source / "__pycache__"
    cache.mkdir(parents=True)
    (source / "tracked.txt").write_text("tracked", encoding="utf-8")
    generated = cache / "generated.pyc"
    generated.write_bytes(b"first")
    monkeypatch.setattr("scripts.validate_docs.ROOT", tmp_path)
    monkeypatch.setattr("scripts.validate_docs.RENDER_INPUTS", (source,))

    first = render_tree_sha256()
    generated.write_bytes(b"second")

    assert render_tree_sha256() == first


def test_readme_quickstart_is_the_only_onboarding_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    files = extract_quickstart_files(readme)

    assert set(files) == {"pelicanconf.py", "content/hello.md"}
    assert "get_theme_path" in files["pelicanconf.py"]
    assert "A small technical note" in files["content/hello.md"]


def test_readme_quickstart_rejects_duplicate_file() -> None:
    block = "<!-- quickstart-file: pelicanconf.py -->\n```python\nVALUE = 1\n```\n"

    try:
        extract_quickstart_files(block + block)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate quickstart file was accepted")
