# Bundled Reference Data

## HTML Entities

`html-entities.json` is generated from Python 3.14.4's standard-library `html.entities.html5` table. It contains 2,125 semicolon-terminated named references with the trailing semicolon removed from each key. Values retain their original Unicode sequences, including multi-code-point entities.

- Source: https://docs.python.org/3.14/library/html.entities.html
- Upstream table: https://github.com/python/cpython/blob/3.14/Lib/html/entities.py
- License: Python Software Foundation license; see [PYTHON-LICENSE.txt](PYTHON-LICENSE.txt), copied from the installed Python distribution.
- JSON SHA-256: `1412aec735fc1f4f63e04ad80644892c71909fe32ad631b0dcbf10c259b1095e`.
- Serialization: UTF-8, sorted keys, two-space indentation, final newline.

This is a read-only bundled reference asset. Load it only for HTML-entity operations; never refresh it automatically or append user content. Decoded values are data and must be rendered as text, never inserted as HTML.

Regenerate with `html.entities.html5`, selecting keys where `name.endswith(';')` and emitting `name[:-1]` with the original value.

## Offline Lookup Snapshots

These are intentionally small, read-only seed snapshots, retrieved/reviewed on 2026-11-10. They are not full registries, current Internet routing tables, provider perimeters, or allowlists. Load only the requested file; never refresh automatically or append user lookup history. Missing matches must remain unknown.

| File | Coverage | Source and redistribution |
| --- | --- | --- |
| [mac-assignments.json](mac-assignments.json) | 13 assignments: 7 MA-L, 3 MA-M, 3 MA-S; includes nested prefixes | Installed `ieee-data` 20240722build1 CSVs with local file date 2025-12-06; upstream publication date is not asserted. Listing is public domain under the installed [IEEE notice](IEEE-LICENSE.txt); no hardware-authentication claim. |
| [cloud-prefixes.json](cloud-prefixes.json) | 17 selected IPv4/IPv6 examples from Cloudflare, Google Cloud, AWS | Exact factual records from attributed official public feeds. No blanket license/endorsement is asserted; review upstream terms before broader redistribution. Azure's official page was readable, but its binary payload was not available through the research tool, so no Azure prefixes were invented. |
| [asn-prefixes.json](asn-prefixes.json) | 2 IPv4 prefixes observed by RIPEstat network-info: 1.1.1.0/24 and 8.8.8.0/24 | Attribution and response times retained. These are factual RIPE RIS observations, not inferred provider ownership, and no blanket underlying-feed license is asserted. Other example queries were inaccessible, so they are absent. |

All three files use top-level `schema_version`, `dataset`, `version`, `retrieved_on`, `partial`, `coverage`, `sources`, and `entries`. Source IDs link entries to provenance. MAC entries use `prefix`, `prefix_length`, `registry`, and `organization`; cloud entries use `cidr`, `provider`, `service`, and `scope`; ASN entries use `cidr`, `asns`, and `query_resource`.

Keep cloud-provider labels separate from observed ASN origins. A Cloudflare ASN result for 1.1.1.1 does not imply that this resolver belongs to the separately published CDN-prefix list. For CIDR input, report partial coverage rather than extrapolating one IP result to the entire range. For MACs, apply most-specific prefix matching and honor local/multicast bits; the name is a registered assignee, not proof of a device's identity.

### Snapshot Checksums

- `mac-assignments.json`: SHA-256 `24ae1b02ff1799cc957e33ef6e49684f423745b6da2e72b162488d7403c9c5ee`.
- `cloud-prefixes.json`: SHA-256 `8a1f5b2348f1279a2db9949c1e3ecc3b001b71a949a461b70543d2f4aa7b22fd`.
- `asn-prefixes.json`: SHA-256 `79558965cea601e44e2ce2f66247c1b0269766c280830f6f6715aba2ac342a43`.

## HTTP Status and Security-Header Glossary

[http-status.json](http-status.json) contains the 62 unique statuses in installed Python 3.14.4's `HTTPStatus` enum and original concise context for HSTS, CSP, and X-Frame-Options. Status names/descriptions are PSF-licensed; retain [PYTHON-LICENSE.txt](PYTHON-LICENSE.txt). MDN/RFC source URLs and the review date (2026-11-11) are recorded in the file.

The top-level keys are `schema_version`, `dataset`, `version`, `retrieved_on`, `coverage`, `sources`, `cache_rules`, `statuses`, `headers`, `limitations`, and `redistribution`. Status entries have `code`, `name`, `phrase`, `description`, `category`, `heuristically_cacheable`, `cache_rule`, and `soc_note`. Header entries have `name`, `purpose`, `common_values`, `notes`, and `source_ids`.

The glossary is not a live/full IANA mirror or a policy evaluator. Unknown codes remain unknown. Heuristic eligibility does not override cache directives, method, authentication, or other restrictions; 304 is validation metadata, not a new cacheable body. Presence of a security header is not proof of correct or safe configuration. Values are explanatory data and must remain inert in the UI.

- `http-status.json`: SHA-256 `50591ca38b6402496deb2a1f4a0d78d9a01fae325fa10d1a73c3ed98cc233463`.
