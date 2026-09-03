# Phase 2 core projection audit (2026-09-03)

## Purpose

This is a read-only comparison ledger for the known-good CK3 startup input. It
does not replace the canonical product tree and it does not authorize a
Workshop upload. The machine-readable allowlist and byte hashes are in
[phase2-core-startup-projection-2026-09-03.json](phase2-core-startup-projection-2026-09-03.json).

## Byte-authoritative overlay

The authority for the 51-file baseline is the product directory mounted by the
formal current-bridge run, not a checkout reconstructed from a Git commit:

- overlay:
  Z:\ck3_mod_rewrite\_runtime\formal-phase2-legacy51-currentbridge-20260903\profile\mod-content\zhongguo_361
- report:
  Z:\ck3_mod_rewrite\_runtime\formal-phase2-legacy51-currentbridge-20260903\report.json
- product files: **51**
- payload: **7,137,587 bytes**
- product_tree.tree_sha256 (the report's sorted list algorithm):
  84e36658728e57b43005300c6e51e398edb6420e3c43dd2f42762c491bc9e36a
- bootstrap.tree_sha256.product (the report's path-to-{size,sha256} map):
  ddac4703d99b7e498e276c37c685af28b2006ad73f4124f9cd77e745aa14a693

The same bytes are also retained in the disposable bisect copy
Z:\ck3_mod_rewrite\_runtime\phase2-bisect-source-legacy51-20260903\mod_zhongguo_style.
The historical Aug-30 report and commit fa5c78dd4b524037d8b113d0498328437085825c
are lineage evidence only. They are not a byte substitute: seven non-English
base localization files in the captured overlay differ from the raw Git
checkout.

## Current canonical comparison

The current source was evaluated through
tools/build_release.py::release_entries, so the comparison uses rendered
production bytes rather than development-only markers.

| measure | formal 51-file overlay | current canonical projection |
| --- | ---: | ---: |
| files | 51 | 279 |
| payload bytes | 7,137,587 | 29,351,046 |
| expected core paths present | — | 51/51 |
| core files byte-identical | — | 30 |
| core files changed | — | 21 |
| extra files outside core | — | 228 |
| extra bytes outside core | — | 15,612,722 |
| extra files by top-level | — | common 28; events 20; localization 180 |

The 21 changed core paths include the three large scoreboard inputs
(zg361_generated_scoreboard_snapshots.txt,
zg361_generated_scoreboard_slots.txt, and gui/zg361_scoreboard.gui), several
base event/effect/trigger files, and the nine language-specific base
localization files. The full per-file baseline/current SHA and size rows are in
the JSON manifest.

## What the live evidence proves

With the exact Steam CK3 1.19.0.6 executable and the current Release bridge,
the 51-file overlay reached Frontend and exited cleanly:

- bridge mode native; no gameplay, save, store, purchase, or payment action;
- frontend evidence at 2026-09-03T03:50:04.024217+00:00;
- CK3 exit code 0; cleanup_proven=true;
- bridge DLL SHA-256
  1FBA822831F52D161FD4EEF6A657E48FA11AF98B9CAA706C236C5F41FF184E96;
- injector SHA-256
  5891D5B2A80A39939D47A056EACDB147BA3F10B599CE2174ECB374321DE72411.

This isolates the current blocker to the broad content projection/load cost:
the 279-file run and its no-scoreboard variant both stalled after roughly
880/881 on_action entries, while the exact 51-file core reached Frontend.
It does not prove that every Phase 2 feature is production-live.

## Safe next use

1. Materialize only the JSON allowlist from the byte-authoritative overlay into
   a fresh disposable profile; keep the canonical source untouched.
2. Run one CK3 startup at a time with the pinned full profile and warm shader
   cache. Close only the exact observed CK3 window and retain the report.
3. Add one named content group at a time (workforce, phase3, career, feedback,
   credit, incident, B1, manager, B2, scoreboard) and record the first group
   that loses Frontend.
4. Promote a group back to the canonical projection only after a live A/B and
   static checks agree. The baseline manifest is a diagnostic projection, not
   a release manifest.

