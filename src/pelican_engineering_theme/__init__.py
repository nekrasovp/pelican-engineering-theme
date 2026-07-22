"""Installed-resource access for pelican-engineering-theme."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

__all__ = ["__version__", "get_theme_path"]

__version__ = "0.1.0"


def get_theme_path() -> Path:
    """Return the existing filesystem directory containing the Pelican theme."""
    resource = resources.files(__package__).joinpath("theme")
    if not resource.is_dir():
        raise FileNotFoundError("installed theme resources are missing")

    path = Path(str(resource))
    if not path.is_dir():
        raise FileNotFoundError("installed theme is not a filesystem directory")
    return path
