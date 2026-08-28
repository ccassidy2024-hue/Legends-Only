"""S1 fixture SHA must bind frozen D5 pointers; restore is exact."""

from __future__ import annotations

from pathlib import Path

from grainsys.discovery.recover_s1 import (
    bind_frozen_s1_expectations,
    expected_s1_from_fixtures,
    restore_s1_original_objects,
)


def test_frozen_s1_pointers_bind_fixture_html() -> None:
    bound = bind_frozen_s1_expectations()
    assert len(bound) == 37
    fixtures = expected_s1_from_fixtures()
    for rec in bound:
        fx = fixtures[rec.control_number]
        assert rec.expected_sha256 == fx.expected_sha256
        assert rec.html_bytes == fx.html_bytes
        assert rec.capture_dir == f"S1-{rec.control_number}"


def test_restore_s1_originals_are_exact(tmp_path: Path) -> None:
    result = restore_s1_original_objects(data_root=tmp_path)
    assert result.original_exact_restored == 37
    assert result.still_missing_original == 0
    for rec in bind_frozen_s1_expectations():
        obj = tmp_path / "sweeps" / "S1" / rec.capture_dir / "objects" / rec.expected_sha256
        assert obj.is_file()
        assert obj.read_bytes() == rec.html_bytes
    again = restore_s1_original_objects(data_root=tmp_path)
    assert again.original_exact_restored == 37
