# Phase 2 product projections and startup recovery

This note documents the bounded product-source switch used while diagnosing the
CK3 Phase 2 startup stall.  It is a diagnostic/replay input, not a replacement
for the canonical source tree and not a Workshop release manifest.

## Why there are projections

The broad Phase 2 source currently contains 279 runtime files and can remain in
the long `on_action` load phase.  The byte-authoritative legacy baseline from
the formal currentbridge run that reached CK3 Frontend contains 51 files
(7,137,587 bytes).  The checked-in
`tools/phase2_product_projection_core.json` binds every one of those 51 rows.
It is intentionally **not** described as a complete Phase 2 implementation:
it is the smallest known startup/bisect baseline.

Two hashes identify the same baseline with different algorithms and must not be
interchanged:

* `ddac4703d99b7e498e276c37c685af28b2006ad73f4124f9cd77e745aa14a693` is the
  bootstrap snapshot (`path -> {size, sha256}` map) used by the runner.
* `84e36658728e57b43005300c6e51e398edb6420e3c43dd2f42762c491bc9e36a` is the
  formal `product_tree` hash (a sorted list of `{path, bytes, sha256}` rows).

The core manifest checks the first hash against the supplied source bytes and
retains the second as independent provenance.  A current canonical source with
changed bytes therefore returns a typed `ProductProjectionError`; it is never
silently downgraded to broad content.

## CLI behavior

`tools/zg361_phase2_product_projection.py` only validates and copies files; it
does not launch CK3.  The destination must be fresh, source and destination
must be disjoint, required root files (`descriptor.mod` and `thumbnail.png`)
must be present, and every selected row is checked for size and SHA-256.
Runtime paths are limited to the same `common/events/gfx/gui/localization`
allowlist used by the release builder.  Source-only folders and traversal,
duplicate, missing, or symlinked entries are rejected.

The default remains broad:

```powershell
py tools/zg361_phase2_product_projection.py `
  --source Z:\path\to\mod_zhongguo_style `
  --output Z:\path\to\projection-manifest.json
```

The checked-in core baseline is selected explicitly.  Use the exact frozen
legacy overlay (or its disposable bisect copy), not the current canonical tree:

```powershell
py tools/zg361_phase2_product_projection.py `
  --source Z:\ck3_mod_rewrite\_runtime\phase2-bisect-source-legacy51-20260903\mod_zhongguo_style `
  --output Z:\tmp\core-generated.json `
  --projection core
```

The generator command above creates a new manifest from the source.  For the
formal byte-authoritative baseline, pass the checked-in
`tools/phase2_product_projection_core.json` to the seed runner instead.

## Group A/B runs from `_runtime/phase2-group-bisect-20260903`

Each group directory is an external product root and remains untouched.  For
example, prepare independent hash-bound manifests for `none` and `workforce`:

```powershell
$bisect = 'Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903'
py tools/zg361_phase2_product_projection.py `
  --source "$bisect\none\zhongguo_361" `
  --output "$bisect\none\projection-none.json" `
  --projection none
py tools/zg361_phase2_product_projection.py `
  --source "$bisect\workforce\zhongguo_361" `
  --output "$bisect\workforce\projection-workforce.json" `
  --projection workforce
```

Then give one generated manifest and its matching source to one runner attempt:

```powershell
py tools/run_zg361_phase2_seed_capture.py `
  ...existing pinned runner arguments... `
  --product-source "$bisect\none\zhongguo_361" `
  --product-projection none `
  --product-projection-manifest "$bisect\none\projection-none.json"
```

Repeat in a fresh attempt directory for `workforce` (or `b1`, `b2`,
`career`, `credit`, `feedback`, `generated`, `incident`, `manager`,
`phase3`, or `scoreboard`).  Never pair a manifest with a different group:
the per-file and source-tree checks make that mismatch a typed RED before the
CK3 launch boundary.  A named projection always requires an explicit manifest;
only `broad` and the checked-in `core` have defaults.

The CK3 launch portion of each attempt remains exclusive/serial.  Manifest
generation, source comparison, and report inspection can run in parallel as
long as they do not share a destination or launch CK3.  Keep each A/B report,
including a failed attempt, so the first group that loses Frontend is
auditable.

## Runner integration and provenance

`run_zg361_phase2_seed_capture.py` carries three options:

* `--product-projection broad|core|<name>` (default `broad`);
* `--product-projection-manifest PATH` (required for named groups);
* `--product-source PATH` (optional external product root; otherwise the clean
  source's `mod_zhongguo_style`).

The runner forwards projection-specific arguments to the isolated acceptance
bootstrap and records source, projection, manifest, and mounted tree hashes in
both preflight and capture reports.  Old frozen exports that do not understand
the new arguments fail with a typed “refresh the clean source export” error;
they are never allowed to silently mount the broad tree.  The existing two-
argument bootstrap call is preserved for the default broad path so CK3-free
fakes and older compatibility tests remain valid.

No projection command performs gameplay, store, purchase, or payment actions.
After an actual startup A/B, use the existing CK3 acceptance procedure and
record the result separately from this file-selection evidence.
