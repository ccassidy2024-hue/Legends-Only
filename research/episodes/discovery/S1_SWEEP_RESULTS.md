# S1 NTNI Sweep Results

**Execution timestamp:** 2026-08-25T01:42:00Z
**Provenance tag:** `prereg-rules-v1`
**Execution commit:** `a74e3fb925b80f308407cc2f1508d6aecd868326`
**Config digest:** `a0eee0add8057c82fb6251daf2d93745a157b129862c4bd2ae25d0027ef3df0e`

## Summary

| Metric | Value |
|--------|-------|
| Total NTNI district endpoints | 10 |
| Successfully parsed | 7 |
| Failed to parse (source data issue) | 3 |
| Total notices scanned | 62 |
| Keyword hits | 37 |
| Capture failures | 0 |

## Source Failures (Hard Source Issue)

Three USACE NTNI district endpoints returned notice records with null `begindate` or `issuedate` fields, which violates the documented NTNI API schema. The ratified `ntni.py` parser correctly failed closed on these records.

| District | Endpoint | Error |
|----------|----------|-------|
| St. Paul (MVP) | ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVP | `items[3].begindate` is null |
| New Orleans (MVN) | ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVN | `items[2].begindate` is null |
| Pittsburgh (LRP) | ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRP | `items[2].issuedate` is null |

**Governance note:** These are hard source failures requiring A+B review before any parser modification. The ratified code correctly failed closed. Modification to `src/grainsys/ingest/ntni.py` would require manifest update and re-ratification per N3 governance.

## Keyword Hits by District

| District | Basin | Hits |
|----------|-------|------|
| Rock Island (MVR) | Upper Mississippi | 11 |
| Huntington (LRH) | Ohio | 9 |
| Louisville (LRL) | Ohio | 6 |
| Nashville (LRN) | Ohio | 5 |
| St. Louis (MVS) | Middle Mississippi | 3 |
| Vicksburg (MVK) | Lower Mississippi | 2 |
| Memphis (MVM) | Lower Mississippi | 1 |

## Keyword Distribution

Based on D4 registered terms matching in `full_text` field:

- `dredging`: 20 hits
- `closure`: 13 hits
- `lockage`: 5 hits
- `restriction`: 1 hit
- `high water`: 2 hits
- `grounding`: 1 hit

(Note: some notices matched multiple terms)

## Captured Evidence

All 37 keyword hits have been captured under `$GRAIN_DATA_ROOT/sweeps/S1/`:
- Content-addressed objects at `objects/<sha256>`
- Append-only manifests at `manifest.yaml`
- Candidate ID format: `S1-{controlnumber}`

## Next Steps

1. **BLOCKED:** MVP, MVN, LRP districts require source-handling ADR decision
2. **READY:** 37 captured hits ready for D5 candidate universe construction
3. **PENDING:** S2-S8 sweeps (different source families)

## Marker

`LOCK1_S1_SWEEP_COMPLETE_37_HITS_3_SOURCE_FAILURES`
