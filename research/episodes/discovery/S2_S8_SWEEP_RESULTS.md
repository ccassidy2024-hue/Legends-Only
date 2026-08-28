# S2-S8 outcome-blind sweep results (v2 authorized)

**Live auth tag:** `prereg-rules-v2`  
**Reviewed PR #46 head:** `07fe83e1d168fffc2b0d352b94b8713677e0cbdc`  
**Canonical main (merge):** `ef4a2d244bf8299c10260f1c711a7a0f7add407c`  
**Config digest:** `d3ef01162de1d443041242eec08749de0e9c16d30fab9ba4a8822146aff19871`  
**Retrieved on:** 2026-08-28  

No market outcomes were read. UNKNOWN is not zero. Inner PDF full_text extraction remains UNKNOWN.

## Per-family execution

| Family | Coverage | Sweep | records_matched | D5 hits | Notes |
|--------|----------|-------|-----------------|--------:|-------|
| S1 | (prior v1 execution) | enumerated | 37 | 37 | Prior NTNI keyword hits retained |
| S2 | unknown | not_attempted | null | 0 | Registry-only corroboration; no archive endpoint; no independent candidates |
| S3 | present | enumerated | 0 | 0 | NAVCEN listing HTTP 200; listing-page keyword scan 0 hits; inner MSIB PDFs UNKNOWN (3 listing rows parsed for 2024 filter) |
| S4 | present | enumerated | 4197 | 4197 | Digest-verified HURDAT2; POINT_ONLY Haversine NM-sphere; 17078 sample-period positions; 4197 storm-node pairs within 100 NM inclusive |
| S5 | present | enumerated | 0 | 0 | AMS GTR listing HTTP 200; listing-page keyword scan 0; weekly PDF full_text UNKNOWN |
| S6 | present | enumerated | 0 | 0 | LPMS portal HTTP 200; listing-page keyword scan 0; lock XML body UNKNOWN |
| S7 | present | enumerated | 0 | 0 | STB search HTTP 200; listing-page keyword scan 0; docket document full_text UNKNOWN |
| S8 | unknown | not_attempted | null | 0 | No verified notice URL in ratified v2 config |

## Complete D5

| Field | Value |
|-------|-------|
| candidate_count | 4234 |
| required_sweep_families | S1, S4 |
| hit_set_digest | `1cb416ee3b6e9103b4edd60748865d7dd147c80611adfb6c6b5b37eba5258d97` |
| candidates_digest | `df7f7ffb41f339d75d6a8a2ef68ab113c70490822e03ad21c9ebd8e26dae2c66` |
| candidate_universe_version | `d5cu-1cb416ee3b6e9103b4edd60748865d7dd147c80611adfb6c6b5b37eba5258d97` |

Families S2/S3/S5/S6/S7/S8 were executed and recorded in coverage, but produced no positive-evidence D5 hits. The complete-hit-set gate therefore lists only families with hits (S1, S4). That is not treated as absence of events for the zero-hit families.

## Next

D6 evidence-pack / episode adjudication over the 4234-hit universe, still outcome-blind.

Marker: `V2_AUTH_AND_S2_S8_D5_COMPLETE`
