# ADR-0015: D3/D4 positive-evidence-only S1 registration

- **Date:** 2026-08-24
- **Author:** A | B
- **Status:** accepted / jointly ratified
- **Decision scope:** D3 active NTNI source rows and D4 normalized field
- **Review class:** Tier A decision; Tier B implementing code

## Ratification

Human Person A and Human Person B jointly approved **D3/D4-A** in the project
Work chat on 2026-08-24: use only verified official surfaces for a
positive-evidence-only S1; preserve uncovered intervals as unknown; generate
no absence evidence; and define `keyword_policy.fields = [full_text]` as a
local normalized extraction contract over captured linked notices/documents.

This ADR durably records that decision. It does not substitute an AI decision
for either human vote.

## Decision

### D3 source rows

The candidate-generating S1 surface is the official NDC active-notices JSON
endpoint for each of the ten already-approved districts. Each JSON row links
to an official NTNI HTML notice.

The exact district codes and endpoints are frozen in
`src/grainsys/ingest/ntni.py::NTNI_DISTRICTS` and documented with authoritative
evidence in `docs/sources/USACE_NTNI_S1_POSITIVE_ONLY.md`.

The registered identity values are:

- `sweep_id = S1`
- `authority = U.S. Army Corps of Engineers`
- district = the exact district name in `NTNI_DISTRICTS`
- `vehicle = NTNI active notices by district JSON with linked HTML notice`
- endpoint = the exact HTTPS endpoint returned by `district_endpoint(code)`

### Positive-evidence-only semantics

These sources are not exhaustive for the 2010-01-01 through 2024-12-31 sample.
No registered S1 row in this ADR may generate absence evidence. An empty
listing, unavailable historical interval, failed retrieval, non-HTML linked
document, or unsupported representation remains unknown; none becomes zero.

### D4 field

`keyword_policy.fields = [full_text]`.

`full_text` is a project-normalized field over the exact captured bytes of a
linked NTNI HTML notice. It is not asserted to be a source-native JSON field.
The normalizer removes non-visible script/style/noscript/template content,
decodes HTML character references, collapses whitespace, and fails closed on
unsupported media types, encodings, empty output, undocumented item fields,
unregistered hosts, or unregistered district codes.

The previously ratified D4 terms, `match = whole_word`, and
`case_sensitive = false` are unchanged.

## Explicit exclusions

- No historical-completeness or retention claim.
- No absence-generating family promotion.
- No district-owned secondary vehicle is silently included.
- No PDF text extractor is authorized by this ADR.
- No networking, candidate minting, evidence capture, episode creation, market
  outcome access, live preregistration, manifest, or tag is performed here.
- No source release clock or `release_ts` is invented.

## Consequences

The D3/D4 values in this scope are scientifically closed and mechanically
normalizable. Live execution remains blocked by D2 completion, full Phase-0
config persistence, exact-head review, N3 manifest/digests, and the
`prereg-rules-v1` tag.
