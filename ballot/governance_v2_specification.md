# prereg-rules-v2 Governance Specification

**Status:** PROPOSED — Requires A+B ratification before implementation  
**Classification:** B-RED — Guard code changes require counterpart implementation review

---

## Current State (v1)

```python
# governance.py line 45
PREREG_TAG = "prereg-rules-v1"

# Authorization check (lines 647-659)
if PREREG_TAG not in {t.strip() for t in tag_proc.stdout.splitlines()}:
    raise RatificationError(f"tag {PREREG_TAG} absent; block")

tagged = _git(root, "rev-list", "-n", "1", PREREG_TAG).stdout.strip()
if not is_descendant_commit(root, head=head, ancestor=tagged):
    raise RatificationError(
        f"execution commit {head} is not a descendant of {PREREG_TAG} "
        f"({tagged}); block"
    )
```

**v1 Semantics:**
- Exact tag name `prereg-rules-v1` required
- Execution commit must descend from that exact tag
- Digest must match manifest bound at that tag
- No amendment path exists

---

## Proposed v2 Governance Mechanism

### Tag Versioning Pattern

```python
# Proposed change to governance.py
PREREG_TAG_PREFIX = "prereg-rules-v"

def find_applicable_prereg_tag(repo_root: Path, head: str) -> str:
    """Find highest prereg-rules-vN tag that HEAD descends from.
    
    Returns the tag name (e.g., "prereg-rules-v2") or raises RatificationError.
    """
    tag_proc = _git(repo_root, "tag", "-l", f"{PREREG_TAG_PREFIX}*")
    tags = [t.strip() for t in tag_proc.stdout.splitlines() if t.strip()]
    
    # Filter to valid versioned tags and sort by version number descending
    versioned_tags = []
    for tag in tags:
        suffix = tag[len(PREREG_TAG_PREFIX):]
        if suffix.isdigit():
            versioned_tags.append((int(suffix), tag))
    
    versioned_tags.sort(reverse=True)  # Highest version first
    
    for version_num, tag in versioned_tags:
        if is_descendant_commit(repo_root, head=head, ancestor=tag):
            return tag
    
    raise RatificationError("no applicable prereg-rules-v* tag; block")
```

### Supersession Behavior

1. **New tag creation:** When `prereg-rules-v2` is created with a manifest binding a new digest, commits descending from v2 use that manifest.

2. **v1 remains valid:** Commits that descend from v1 but NOT from v2 continue to use v1 manifest and digest.

3. **Highest applicable wins:** If a commit descends from both v1 and v2, the v2 manifest takes precedence.

4. **Forward compatibility:** Future v3, v4, etc. follow the same pattern.

### Manifest Binding Behavior

Each `prereg-rules-vN` tag has an associated manifest file:

```yaml
# config/discovery/prereg_ratification_manifest.yaml at v2 tag
schema_version: "2.0"
prereg_tag: prereg-rules-v2
prereg_config_digest: <exact digest of ratified variant>
ratification_date: <ISO date>
supersedes: prereg-rules-v1
ratification_record:
  s2_mechanics: <A or B>
  s4_radius_nm: <50 or 100>
  a_ratifier: <name>
  b_ratifier: <name>
```

### Authorization Guard Changes

The `assert_sweep_authorized()` function must be modified to:

1. Call `find_applicable_prereg_tag()` instead of checking exact `PREREG_TAG`
2. Load manifest from the applicable tag
3. Verify digest matches the config at execution commit
4. Log which tag version authorized the sweep

---

## Implementation Requirements

### Code Changes Required

| File | Change | Classification |
|------|--------|----------------|
| `src/grainsys/discovery/governance.py` | Add `find_applicable_prereg_tag()` | B-RED |
| `src/grainsys/discovery/governance.py` | Modify `assert_sweep_authorized()` | B-RED |
| `tests/test_governance.py` | Add v2 versioning tests | B-RED |

### Test Acceptance Criteria

1. **Tag enumeration:** `find_applicable_prereg_tag()` correctly identifies highest applicable tag
2. **Supersession:** v2 takes precedence over v1 when commit descends from both
3. **v1 isolation:** Commits only descending from v1 continue to work unchanged
4. **Missing tag:** Raises `RatificationError` when no applicable tag exists
5. **Digest binding:** Authorization requires digest match from applicable tag's manifest

### Proposed Test Cases

```python
def test_find_applicable_prereg_tag_prefers_highest():
    """When commit descends from v1 and v2, v2 is returned."""
    # Setup: create v1 tag, commit, create v2 tag, commit
    # Assert: find_applicable_prereg_tag returns "prereg-rules-v2"

def test_find_applicable_prereg_tag_v1_only():
    """When commit descends only from v1, v1 is returned."""
    # Setup: create v1 tag, commit (no v2)
    # Assert: find_applicable_prereg_tag returns "prereg-rules-v1"

def test_find_applicable_prereg_tag_no_tags():
    """When no prereg tags exist, raises RatificationError."""
    # Assert: RatificationError("no applicable prereg-rules-v* tag; block")

def test_assert_sweep_authorized_uses_applicable_tag():
    """Authorization loads manifest from applicable tag, not hardcoded v1."""
    # Setup: v2 tag with different digest than v1
    # Assert: sweep authorized under v2 with v2 digest
```

---

## Ratification Sequence

1. **Tier-A ballot:** Human A+B ratify one config variant (A/B × 50/100)
2. **Create v2 tag:** Tag exact commit with `prereg-rules-v2`
3. **Bind manifest:** Manifest at tag contains exact ratified digest
4. **B-RED implementation:** Implement guard code changes with counterpart review
5. **Post-implementation:** Sweeps using ratified config are authorized

---

## What This Branch Does NOT Include

- ❌ Guard code changes to `governance.py`
- ❌ New test implementations
- ❌ Actual `prereg-rules-v2` tag creation

These require B-RED counterpart review AFTER Tier-A ratification.
