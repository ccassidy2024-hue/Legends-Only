#!/usr/bin/env python3
"""Create synthetic S1 sweep capture fixtures for D5 builder testing.

This script creates deterministic fixture data representing the 37 canonical
S1 keyword hits documented in S1_SWEEP_RESULTS.md. The fixtures enable
running the D5 candidate universe builder in CI environments without
requiring actual USACE NTNI network access.

The synthetic control numbers are deterministic and reproducible.
"""

import hashlib
import os
from pathlib import Path

import yaml

# District hit counts from S1_SWEEP_RESULTS.md
DISTRICT_HITS = {
    "MVR": 11,  # Rock Island - Upper Mississippi
    "LRH": 9,   # Huntington - Ohio
    "LRL": 6,   # Louisville - Ohio
    "LRN": 5,   # Nashville - Ohio
    "MVS": 3,   # St. Louis - Middle Mississippi
    "MVK": 2,   # Vicksburg - Lower Mississippi
    "MVM": 1,   # Memphis - Lower Mississippi
}

# Synthetic issue dates (deterministic, within sample period 2010-2024)
BASE_YEAR = 2020


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_fixtures(data_root: Path) -> dict:
    """Create S1 sweep capture fixtures and return summary."""
    sweeps_dir = data_root / "sweeps" / "S1"
    
    total_hits = 0
    candidates_created = []
    
    for district_code, hit_count in DISTRICT_HITS.items():
        for i in range(1, hit_count + 1):
            total_hits += 1
            
            # Deterministic control number
            control_number = f"{district_code}-2020-{i:04d}"
            candidate_id = f"S1-{control_number}"
            
            # Create candidate directory
            cand_dir = sweeps_dir / candidate_id
            objects_dir = cand_dir / "objects"
            objects_dir.mkdir(parents=True, exist_ok=True)
            
            # Synthetic HTML content (deterministic)
            html_content = f"""<!DOCTYPE html>
<html>
<head><title>NTNI Notice {control_number}</title></head>
<body>
<h1>Notice to Navigation Interests</h1>
<p>District: {district_code}</p>
<p>Control Number: {control_number}</p>
<p>This notice contains information about dredging operations.</p>
</body>
</html>""".encode("utf-8")
            
            content_hash = sha256_hex(html_content)
            
            # Write the object
            object_path = objects_dir / content_hash
            object_path.write_bytes(html_content)
            
            # Synthetic issue date (spread across sample period)
            month = ((total_hits - 1) % 12) + 1
            day = ((total_hits - 1) % 28) + 1
            issue_date = f"{BASE_YEAR}-{month:02d}-{day:02d}"
            
            # Create manifest
            manifest = {
                "sweep_id": "S1",
                "candidate_id": candidate_id,
                "records": [
                    {
                        "source_reference": control_number,
                        "sha256": content_hash,
                        "retrieved_on": f"{issue_date}T12:00:00Z",
                        "original_filename": f"{control_number}.html",
                        "content_type": "text/html",
                    }
                ],
            }
            
            manifest_path = cand_dir / "manifest.yaml"
            with manifest_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(manifest, f, default_flow_style=False)
            
            candidates_created.append({
                "candidate_id": candidate_id,
                "control_number": control_number,
                "district": district_code,
                "sha256": content_hash,
            })
    
    return {
        "total_hits": total_hits,
        "districts": len(DISTRICT_HITS),
        "candidates": candidates_created,
        "sweeps_dir": str(sweeps_dir),
    }


def main():
    data_root = Path(os.environ.get("GRAIN_DATA_ROOT", "/tmp/grain_data"))
    print(f"Creating S1 fixtures in: {data_root}")
    
    summary = create_fixtures(data_root)
    
    print(f"\n=== S1 Fixture Summary ===")
    print(f"Total candidates: {summary['total_hits']}")
    print(f"Districts: {summary['districts']}")
    print(f"Location: {summary['sweeps_dir']}")
    
    print("\nCandidates by district:")
    by_district = {}
    for c in summary["candidates"]:
        d = c["district"]
        by_district[d] = by_district.get(d, 0) + 1
    for d, count in sorted(by_district.items()):
        print(f"  {d}: {count}")
    
    print(f"\nFirst 5 candidate IDs:")
    for c in summary["candidates"][:5]:
        print(f"  {c['candidate_id']}")


if __name__ == "__main__":
    main()
