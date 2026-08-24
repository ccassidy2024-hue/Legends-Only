# USACE NTNI S1 source evidence — positive-evidence-only

- **Checked:** 2026-08-24
- **Authority:** U.S. Army Corps of Engineers (USACE), Navigation and Civil
  Works Decision Support Center (NDC)
- **Purpose:** D3/D4 preregistration evidence only
- **Coverage classification:** positive-evidence-only; never absence-generating

## Authoritative evidence

1. NDC describes NTNI as a centralized point of access and states that the
   current website and process were introduced in 2015:
   <https://www.iwr.usace.army.mil/About/Technical-Centers/NDC-Navigation-and-Civil-Works-Decision-Support/NDC-Navigation-Notices/>
2. The official NTNI navigation-notices page states that notices are removed
   seven days past the end date on the latest amendment:
   <https://ndc.ops.usace.army.mil/ords/f?p=107:1>
3. The official Data Web Services page documents the by-district JSON resource
   as returning active notices and a link to each notice:
   <https://ndc.ops.usace.army.mil/ords/r/ntni/notices/data-web-services>

These sources do not establish exhaustive retrospective coverage for
2010-01-01 through 2024-12-31. Reachability, visible rows, issue-number
continuity, and oldest observed records are not completeness evidence.

## Frozen active-notice endpoints

All endpoints were reachable on 2026-08-24 and exposed the documented item
fields `controlnumber`, `noticeno`, `issuedate`, `begindate`, `waterways`, and
`noticelink`. Current row counts and current visible dates are deliberately not
treated as stable coverage facts.

| District | Code | Vehicle | Endpoint |
|---|---|---|---|
| St. Paul District | MVP | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVP> |
| Rock Island District | MVR | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVR> |
| St. Louis District | MVS | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVS> |
| Memphis District | MVM | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVM> |
| Vicksburg District | MVK | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVK> |
| New Orleans District | MVN | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/MVN> |
| Louisville District | LRL | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRL> |
| Huntington District | LRH | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRH> |
| Pittsburgh District | LRP | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRP> |
| Nashville District | LRN | NTNI active notices by district JSON | <https://ndc.ops.usace.army.mil/ords/ntni/json_data/notices_by_district/LRN> |

## D4 normalized field contract

`keyword_policy.fields = [full_text]` names a local, reproducible normalization
field. It is not represented as an NTNI JSON field. For a captured linked NTNI
HTML notice, `full_text` is visible HTML text after character-reference
decoding, removal of script/style/noscript/template content, whitespace
collapse, and trimming.

PDF-only and other unregistered representations fail closed. District-owned
historical pages and bulletin vehicles are not silently included merely
because they are reachable; multi-vehicle inclusion requires explicit later
registration. No source in this record generates absence evidence.
