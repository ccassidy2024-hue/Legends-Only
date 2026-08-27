"""Live B100 production-config persistence tests (no sweep execution)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from grainsys.discovery.config import (
    DiscoveryConfigError,
    load_prereg_rules,
    prereg_rules_path,
)
from grainsys.discovery.governance import sha256_file
from grainsys.discovery.sweep import SweepEnumerator

REPO = Path(__file__).resolve().parents[1]

B100_DIGEST = "9e937523d31bc324d9b33628ffd81c78fb74e5141aab2d18174a1677da8ce3c1"
B100_AUDIT = REPO / "research" / "episodes" / "discovery" / "proposals" / "FULL_CONFIG_B100.yaml"


def test_live_prereg_rules_bytes_match_approved_b100_digest() -> None:
    live = prereg_rules_path(REPO)
    assert sha256_file(live) == B100_DIGEST
    assert sha256_file(B100_AUDIT) == B100_DIGEST
    assert live.read_bytes() == B100_AUDIT.read_bytes()


def test_live_b100_registries_and_archives() -> None:
    cfg = load_prereg_rules(REPO)
    gauges = cfg["s2_gauge_registry"]["gauges"]
    nodes = cfg["s4_node_registry"]["nodes"]
    assert len(gauges) == 10
    assert len(nodes) == 10
    assert {g["station_id"] for g in gauges} == {
        "07010000",
        "07022000",
        "07032000",
        "07289000",
        "07374000",
        "07374510",
        "03612500",
        "03611500",
        "05586100",
        "05558300",
    }
    assert {n["node_id"] for n in nodes} == {
        "GULF-01",
        "GULF-02",
        "GULF-03",
        "GULF-04",
        "GULF-05",
        "PNW-01",
        "PNW-02",
        "PNW-03",
        "PNW-04",
        "PNW-05",
    }
    families = {row["sweep_id"] for row in cfg["source_archives"]}
    assert families == {"S1", "S3", "S4", "S5", "S6", "S7", "S8"}
    enum = SweepEnumerator(cfg)
    assert len(list(enum.iter_archives(sweep_id="S4"))) == 1
    assert list(enum.iter_archives(sweep_id="S4"))[0].district is None


def test_b100_bindings_record_matches_live_digest() -> None:
    path = REPO / "docs" / "governance" / "prereg_v2_b100_bindings.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["marker"] == "PR42_AB_APPROVED_B100_V2"
    assert data["full_config"]["sha256"] == B100_DIGEST
    assert data["pr42"]["head"] == "840d9891473d3ebf248c2d44a9bbeac270d614ca"
    assert data["selected"]["s2"] == "USE_B_OPERATIONAL_RESTRICTION_ONLY"
    assert data["selected"]["s4_radius_nm"] == 100
    assert data["authorization_status"]["sweeps_authorized"] is False
    assert data["v2_manifest_bindings_planned"]["tag_status"] == "not_created"


def test_schema_03_rejects_invented_s2_threshold_mode(tmp_path: Path) -> None:
    live = prereg_rules_path(REPO)
    data = yaml.safe_load(live.read_text(encoding="utf-8"))
    data["s2_gauge_registry"]["interpretation"] = "LWRP_THRESHOLD"
    out = tmp_path / "config" / "discovery" / "prereg_rules.yaml"
    out.parent.mkdir(parents=True)
    # Copy episode schema so basin vocabulary is available.
    schema_src = REPO / "research" / "episodes" / "episode_schema.yaml"
    schema_dst = tmp_path / "research" / "episodes" / "episode_schema.yaml"
    schema_dst.parent.mkdir(parents=True)
    schema_dst.write_bytes(schema_src.read_bytes())
    out.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(DiscoveryConfigError, match="OPERATIONAL_RESTRICTION_ONLY"):
        load_prereg_rules(tmp_path)


def test_schema_03_rejects_non_100nm_radius(tmp_path: Path) -> None:
    live = prereg_rules_path(REPO)
    data = yaml.safe_load(live.read_text(encoding="utf-8"))
    data["s4_node_registry"]["proximity_radius_nm"] = 50
    out = tmp_path / "config" / "discovery" / "prereg_rules.yaml"
    out.parent.mkdir(parents=True)
    schema_src = REPO / "research" / "episodes" / "episode_schema.yaml"
    schema_dst = tmp_path / "research" / "episodes" / "episode_schema.yaml"
    schema_dst.parent.mkdir(parents=True)
    schema_dst.write_bytes(schema_src.read_bytes())
    out.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(DiscoveryConfigError, match="proximity_radius_nm"):
        load_prereg_rules(tmp_path)
