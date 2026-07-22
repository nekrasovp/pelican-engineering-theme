#!/usr/bin/env python3
"""Verify the identity and required package data in built distributions."""

from __future__ import annotations

import argparse
import email
import hashlib
import tarfile
import zipfile
from collections.abc import Iterable
from pathlib import Path

NAME = "pelican-engineering-theme"
NORMALIZED_NAME = "pelican_engineering_theme"
VERSION = "0.0.0.dev0"
PACKAGE = "pelican_engineering_theme"
LICENSE_SHA256 = "36deab88361eb4a1ae20f2d94764a7f734e3902ee79865726be944b0b6d316ab"

REQUIRED_PACKAGE_FILES = {
    f"{PACKAGE}/__init__.py",
    f"{PACKAGE}/theme/templates/archives.html",
    f"{PACKAGE}/theme/templates/article.html",
    f"{PACKAGE}/theme/templates/author.html",
    f"{PACKAGE}/theme/templates/authors.html",
    f"{PACKAGE}/theme/templates/base.html",
    f"{PACKAGE}/theme/templates/categories.html",
    f"{PACKAGE}/theme/templates/category.html",
    f"{PACKAGE}/theme/templates/index.html",
    f"{PACKAGE}/theme/templates/page.html",
    f"{PACKAGE}/theme/templates/period_archives.html",
    f"{PACKAGE}/theme/templates/tag.html",
    f"{PACKAGE}/theme/templates/tags.html",
    f"{PACKAGE}/theme/static/css/scaffold.css",
}


def package_data_errors(members: Iterable[str], prefix: str = "") -> list[str]:
    """Return missing required package-data errors for an archive inventory."""
    member_set = set(members)
    return [
        f"missing required package file: {prefix}{required}"
        for required in sorted(REQUIRED_PACKAGE_FILES)
        if f"{prefix}{required}" not in member_set
    ]


def metadata_errors(raw_metadata: bytes) -> list[str]:
    """Return exact identity, version, and license metadata errors."""
    project_metadata = email.message_from_bytes(raw_metadata)
    expected = {
        "Name": NAME,
        "Version": VERSION,
        "License-Expression": "MIT",
    }
    errors = [
        f"metadata {field} is {project_metadata.get(field)!r}, expected {value!r}"
        for field, value in expected.items()
        if project_metadata.get(field) != value
    ]
    if project_metadata.get_all("License-File") != ["LICENSE"]:
        errors.append("metadata License-File must contain only 'LICENSE'")
    return errors


def license_errors(raw_license: bytes, archive_path: str) -> list[str]:
    """Return an error unless an archive contains the exact repository license."""
    digest = hashlib.sha256(raw_license).hexdigest()
    if digest == LICENSE_SHA256:
        return []
    return [f"license digest for {archive_path} is {digest}, expected {LICENSE_SHA256}"]


def verify_wheel(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        errors.extend(package_data_errors(members))
        metadata_path = f"{NORMALIZED_NAME}-{VERSION}.dist-info/METADATA"
        if metadata_path not in members:
            errors.append(f"missing wheel metadata: {metadata_path}")
        else:
            errors.extend(metadata_errors(archive.read(metadata_path)))
        license_path = f"{NORMALIZED_NAME}-{VERSION}.dist-info/licenses/LICENSE"
        if license_path not in members:
            errors.append(f"missing wheel license: {license_path}")
        else:
            errors.extend(license_errors(archive.read(license_path), license_path))
    return errors


def verify_sdist(path: Path) -> list[str]:
    errors: list[str] = []
    prefix = f"{NORMALIZED_NAME}-{VERSION}/src/"
    with tarfile.open(path, mode="r:gz") as archive:
        members = archive.getnames()
        errors.extend(package_data_errors(members, prefix=prefix))
        metadata_path = f"{NORMALIZED_NAME}-{VERSION}/PKG-INFO"
        try:
            metadata_member = archive.extractfile(metadata_path)
        except KeyError:
            metadata_member = None
        if metadata_member is None:
            errors.append(f"missing sdist metadata: {metadata_path}")
        else:
            errors.extend(metadata_errors(metadata_member.read()))
        license_path = f"{NORMALIZED_NAME}-{VERSION}/LICENSE"
        try:
            license_member = archive.extractfile(license_path)
        except KeyError:
            license_member = None
        if license_member is None:
            errors.append(f"missing sdist license: {license_path}")
        else:
            errors.extend(license_errors(license_member.read(), license_path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path)
    args = parser.parse_args()

    wheels = sorted(args.dist.glob("*.whl"))
    sdists = sorted(args.dist.glob("*.tar.gz"))
    errors: list[str] = []
    if len(wheels) != 1:
        errors.append(f"expected one wheel, found {len(wheels)}")
    if len(sdists) != 1:
        errors.append(f"expected one sdist, found {len(sdists)}")
    if len(wheels) == 1:
        errors.extend(verify_wheel(wheels[0]))
    if len(sdists) == 1:
        errors.extend(verify_sdist(sdists[0]))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Verified {wheels[0].name} and {sdists[0].name}")
    print(f"Identity: {NAME} {VERSION}; license: MIT")
    print(f"Required package files: {len(REQUIRED_PACKAGE_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
