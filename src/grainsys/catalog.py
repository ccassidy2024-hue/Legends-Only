"""Catalog: one YAML file per series, compiled into a single table.

catalog.csv is a BUILD ARTIFACT. It should be gitignored. Never hand-edit it.
Do not invent source IDs or release delays — leave unknowns explicit.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

# Fields the template is designed to support. Values may be null / "unknown" /
# "TODO" — inventing concrete IDs or delays is forbidden.
TEMPLATE_FIELDS = [
    "series_id",
    "name",
    "description",
    "source",
    "source_identifier",
    "source_url",
    "frequency",
    "units",
    "geography",
    "economic_role",
    "transformation",
    "period_definition",
    "release_schedule",
    "release_delay_days",
    "revision_behavior",
    "staleness_limit_days",
    "verified",
    "notes",
]

# Optional role vocabulary for structural pair gating (exploratory screening).
VALID_ECONOMIC_ROLES = {
    "trigger",
    "constraint",
    "constraint_price",
    "stock",
    "flow",
    "signal",
    "adaptation",
    "outcome",
    "unknown",
    "TODO",
}

# Files that are templates/docs, not series records.
SKIP_STEMS = {"_template", "README"}


def load_catalog(catalog_dir: str | Path = "catalog/series") -> pd.DataFrame:
    """Load every series YAML into one DataFrame (excludes `_template.yaml`)."""
    catalog_dir = Path(catalog_dir)
    files = [
        f
        for f in sorted(catalog_dir.glob("*.yaml")) + sorted(catalog_dir.glob("*.yml"))
        if f.stem not in SKIP_STEMS
    ]
    if not files:
        return pd.DataFrame(columns=TEMPLATE_FIELDS)

    records: list[dict] = []
    errors: list[str] = []
    for f in files:
        with f.open(encoding="utf-8") as fh:
            d = yaml.safe_load(fh) or {}
        d["_file"] = f.name

        if not d.get("series_id"):
            errors.append(f"{f.name}: missing series_id")
        elif f.stem != d["series_id"]:
            errors.append(f"{f.name}: filename must match series_id '{d['series_id']}'")

        role = d.get("economic_role")
        if role is not None and role not in VALID_ECONOMIC_ROLES:
            errors.append(
                f"{f.name}: economic_role '{role}' not in {sorted(VALID_ECONOMIC_ROLES)}"
            )

        records.append(d)

    if errors:
        raise ValueError("catalog validation failed:\n  " + "\n  ".join(errors))

    df = pd.DataFrame(records)
    dupes = df["series_id"][df["series_id"].duplicated()].tolist()
    if dupes:
        raise ValueError(f"duplicate series_id: {dupes}")
    return df.sort_values("series_id").reset_index(drop=True)


def build_catalog_csv(
    catalog_dir: str | Path = "catalog/series",
    out: str | Path = "catalog/catalog.csv",
) -> Path:
    df = load_catalog(catalog_dir)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["_file"], errors="ignore").to_csv(out, index=False)
    return out


def plausible_pairs(catalog: pd.DataFrame) -> list[tuple[str, str]]:
    """Generate structurally plausible (x, y) screening pairs from economic_role.

    Pairs are restricted to forward movement through the system. This is the
    project's main defence against combinatorial false discovery.
    """
    order = [
        "trigger",
        "constraint",
        "constraint_price",
        "adaptation",
        "flow",
        "stock",
        "signal",
        "outcome",
    ]
    rank = {r: i for i, r in enumerate(order)}
    role_col = "economic_role" if "economic_role" in catalog.columns else "role"

    pairs = []
    for _, xi in catalog.iterrows():
        for _, yi in catalog.iterrows():
            if xi["series_id"] == yi["series_id"]:
                continue
            rx, ry = rank.get(xi.get(role_col), 99), rank.get(yi.get(role_col), 99)
            if rx < ry:
                pairs.append((xi["series_id"], yi["series_id"]))
    return pairs


if __name__ == "__main__":  # pragma: no cover
    path = build_catalog_csv()
    cat = load_catalog()
    verified = int(cat["verified"].fillna(False).astype(bool).sum()) if not cat.empty else 0
    print(f"wrote {path}: {len(cat)} series, {verified} verified")
    print(f"plausible screening pairs: {len(plausible_pairs(cat))}")
