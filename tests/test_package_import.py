"""Smoke tests for repository package importability."""

from grainsys import __version__


def test_package_version() -> None:
    assert __version__ == "0.1.0"
