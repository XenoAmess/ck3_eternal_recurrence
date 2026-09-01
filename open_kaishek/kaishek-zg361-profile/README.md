# Kaishek 361 domain profile (Phase 0)

This module contains the first, schema-only projection of
`mod_zhongguo_style/docs/361-domain-runtime-architecture.md`.
`src/main/resources/zg361/domains.json` describes all 38 domains (A–AL), the
1–361 mechanism coverage, state graphs, permission boundary, bounded capacity,
cleanup and stale-deadline contracts. It intentionally does **not** execute a
domain runtime or claim CK3 readiness.

Run the dependency-free validator and tests from this directory:

```text
py tools/validate_domains.py
py -m unittest discover -s tests -v
```

The Java `DomainGraphValidator` exposes the corresponding domain, ACL and
state-graph checks as a typed projection; the Python validator remains the
authoritative JSON-level checker for coverage metadata and global boundaries.
Neither implementation depends on Quarkus or a JSON library.

The offline synthetic 014 vertical slice is implemented by
`Synthetic361Pipeline`: it generates a BOM-bearing `.txt`, runs the lossless
parser and schema validator, lowers to strict IR, and executes three explicitly
certified in-memory handlers (`delivered -> appeal_open -> closed`). The
fixture profile is not the CK3 profile and must not be described as live or
differential-certified. See [`../docs/synthetic-361-slice.md`](../docs/synthetic-361-slice.md)
for the boundary and reproduction command.
