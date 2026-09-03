# Workforce exact-split audit (2026-09-03)

This is an independent audit of the corrected workforce A/B experiment. It
does not change the canonical mod source, release manifests, daily reports, or
live-readiness files. The CK3 process used for the exact-pair observation was
already owned by the serial recovery run; this audit did not start or stop a
new game process, and it performed no gameplay, purchase, or store action.

## Decision

The corrected byte-exact split is RED. Splitting the 324 top-level workforce
effects into two independently named files did not clear the "Total of : 881"
startup stall. Therefore the split is not a production fix and must not be
promoted to the canonical tree or release projection.

The earlier split result is retained only as a historical reachability record.
It is not valid evidence for a production split because the first splitter had
a UTF-8 BOM offset bug.

## Frozen source and candidate artifacts

| item | value |
| --- | --- |
| source | Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903\direct-union-v2\common\scripted_effects\zg361_workforce_endgame_runtime_effects.txt |
| source bytes / SHA-256 | 4,636,271 / 926453fe4b3621b5381743d61f5d03ac29c1d498181702e05a9532739d334d8a |
| source shape | UTF-8 BOM (3 bytes), 563-byte header, 324 brace-balanced top-level blocks |
| corrected block manifest | _runtime/phase2-workforce-block-bisect-corrected-20260903/manifest.json |
| exact-pair manifest | _runtime/phase2-workforce-split-exact-20260903/manifest.json |

The corrected manifest proves all_block_hashes_match=true and
part_a_body_plus_part_b_body_equals_source_body=true, with ranges 0..161 and
162..323. The exact-pair manifest uses a raw byte boundary at the end of block
161: part A is the source prefix, and part B is the source suffix with the
same 563-byte header prepended so that each CK3 file is independently headed
and BOM-valid. Removing that duplicated header from part B makes the
concatenation byte-identical to the frozen source.

The product mounted by the formal run came from
_runtime/phase2-workforce-split-exact-clean-20260903/mod_zhongguo_style:

| mounted file | blocks | bytes | SHA-256 |
| --- | ---: | ---: | --- |
| common/scripted_effects/zg361_workforce_endgame_runtime_effects_part_a.txt | 0..161 | 1,643,771 | 2e12236b0c7ad17d99f0b799fd21bd0b2e5d6309468383327f6fbcc6ed6b332b |
| common/scripted_effects/zg361_workforce_endgame_runtime_effects_part_b.txt | 162..323 | 2,993,063 | 0c83e2743254d6d4d9e6989a564a858b279099ad0209ee57d5acbf98fccf3579 |

The old monolithic file was absent from this disposable product. The full
mounted tree had 265 files and 15,938,098 bytes.

## Partial-arm classification (do not call these functional GREEN)

The following observations are deliberately coverage/diagnostic results, not
feature acceptance. A CK3 frontend marker can be reached while definitions
needed by the complete workforce/event graph are absent or malformed; that
marker therefore cannot promote an arm to `fixture-live` or `production-live`.

| arm | observed evidence | correct classification |
| --- | --- | --- |
| `control-exclude-m360` | report SHA `469FFA9C06D14F6F673268C93FFEF3BF37DA324028E55F1E275B412ACE62DDE9`; `result=frontend`, 264 files, 200 frames, exit 0, cleanup proven; the m360 family is intentionally excluded and the log still contains 6,960 unused-variable diagnostics | coverage-limited control; not functional GREEN |
| old BOM-offset split | report SHA `239545DEE09C156B16672C68774089B7AD659BEEC418DB6F1AADCAE3E5A962A7`; frontend/history markers were reached, but the artifact was byte-shifted (`header_bytes=560` recorded versus the 563-byte source header) | malformed artifact and coverage-limited reachability; not functional GREEN |
| single-block include diagnostics (`block3`, `block4`) | reports SHA `83F7D2C6ABA34C3934FF206367A72456C22280DBC9620A44109BBF57295820C9` and `1A538954FFD55D62DF0C2BCF618997DC8C3A398ECFCA67DD30E500B47A6C9691`; each reached frontend/history with 200 frames only because almost all workforce definitions were omitted; each retained 6,919 unused-variable diagnostics | coverage-limited partial arm; not functional GREEN |
| left/right halves (`left-full`, `right-full`) | reports SHA `F19609136D13574411AA3993A65A8B2600EBB4707E908C53CD729638F1870C37` and `B6ACC4AC0671FCF3F7514F10C444311A4BFA6618A98059C79EB674D4742E89AA`; both reached frontend/history with 200 frames, but each mounted only one half and logged thousands of unused-variable diagnostics | coverage-limited half diagnostics; not functional GREEN |

In short: `control-exclude-m360` is coverage-limited; the old split is
malformed and coverage-limited; and the single-block include plus left/right
halves are coverage-limited diagnostics (with any bytes inherited from the old
split also malformed). **None of these arms is functional GREEN.**

The single-block and half runs answer only “can this reduced projection reach a
frontend?” They do not establish complete definitions, gameplay behavior,
cross-file references, or a valid split. The exact BOM-correct full split is
the only candidate arm that can answer that question, and its RED
`Total of : 881` result is recorded in the exact-candidate section below.

## Thirty-minute full-run plan (pending result)

This is a queued plan, not a claimed run. It must remain behind the serial CK3
gate and must not overwrite the frozen artifacts above.

* **T+0 to T+3:** freeze the exact candidate tree, source SHA, executable SHA,
  DLC/load order, disposable `-userdir`, and projection tree hash; verify the
  two part files are present and the old monolith is absent.
* **T+3 to T+5:** start exactly one CK3 instance under the existing formal
  runner; record the launch/pipe timestamps and accept only pre-authorized
  agreements or notifications (no purchase/store actions).
* **T+5 to T+25:** observe without injecting gameplay; require the frontend
  marker, `End loading of history`, 200 heartbeat frames, and no parser or
  missing-localization errors. Capture debug/error logs continuously.
* **T+25 to T+30:** close and prove process cleanup, hash the report/logs/tree,
  and classify **GREEN only if all acceptance fields pass**. Any timeout,
  `Total of : 881` stall, missing history marker, nonzero exit, or incomplete
  cleanup is RED and must be retained as a failed attempt.

**Status: PENDING.** No valid thirty-minute A+B run is attributed to this
audit; the already completed exact run remains the functional evidence and is
RED.

### Attempt observed after the plan (invalid target)

The run directory
`_runtime/formal-phase2-full-exact-1800-20260903/` later completed a
30-minute timeout, but its mounted tree was not the exact candidate described
above. Its report SHA-256 is
`241254233107098CF5F385F1C4472D94CA3E1C8D93D6CFFF869A8C38C0F7A79A`; the
product tree records 264 files / 15,937,535 bytes and contains the monolith
`zg361_workforce_endgame_runtime_effects.txt` (4,636,271 bytes), with no
`_part_a` or `_part_b`. A valid exact A+B tree is 265 files / 15,938,098
bytes, so the 563-byte difference is the duplicated part-B header. The run
also stopped at `Total of : 881` (frontend/history not verified), with CK3
exit 1 and cleanup proven. Classify this attempt as an invalid-target
monolithic control, not as an exact-split result; a correctly mounted
30-minute A+B run is still pending.

## Corrected A/B test plan and result

All arms use the same Steam CK3 executable/CWD, DLC load, disposable userdir,
warm-cache policy, fixture, and one-at-a-time CK3 gate. No arm advances
gameplay or touches a purchase/store UI.

1. Monolithic control. Keep the frozen monolith and record the known
   direct-union baseline. This is a control, not a new claim.
2. Half diagnostics. Mount only blocks 0..161 (A), then only 162..323 (B),
   against the same non-workforce baseline. Reaching the frontend is useful
   for localization/parse triage, but missing definitions are expected;
   neither half alone can be accepted as a product.
3. Exact candidate (the acceptance arm). Mount both distinct files above,
   exclude the monolith, and require all of the following: CK3 window present,
   gui/frontend_main.gui complete, End loading of history, 200 heartbeat
   frames, exit code 0, and proven cleanup. Capture the projection tree,
   report, debug log, error log, and hashes before classifying the result.

The exact candidate run was
_runtime/formal-phase2-workforce-split-exact-20260903/report.json (report
SHA-256 E10D6C31BAD79FCEA2759DABED8537CC634BBFBD40965A3E23D76B6ECB0B6DB3):

| observation | result |
| --- | --- |
| result / wall-clock | timeout, 180 s (13:29:08-13:33:04 Asia/Shanghai) |
| frontend contract | verified=false; frontend GUI marker was true, history marker false |
| loader marker | last relevant marker was Total of : 881; no End loading of history |
| frames / process | 200 frames; CK3 exit code 1 |
| error log | 0 bytes, 0 lines (SHA e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855) |
| debug log | 288,738 bytes, 2,552 lines (SHA 3141cc6c3301940a21a5add3310551c73a8469f57803a2b58f47ef51d9298d33) |
| cleanup | cleanup_proven=true; no CK3 process remained |

An empty error log plus the same Total881 stall seen in the full event
projection means the exact split removed neither a parser error nor the
underlying broad-load/native dependency issue. Keep native/provider=RED.

## Why the first split artifact is invalid

The original diagnostic utility decoded with utf-8-sig and then initialized
its byte offset table at zero. The decoded text no longer contained the
three-byte BOM, while the subsequent slices still addressed original bytes.
Consequences recorded in
_runtime/phase2-workforce-block-bisect-20260903/manifest.json include a
header_bytes=560 value where the source header is 563 bytes and shifted/cut
block boundaries. Its left/right hashes were
83e38bbd214decf48e546e60db4f37b1006dfafcede1eb448883411f613a1eaa and
aa50319d1331896e41eb9de7bc80d1167a3bac3e4725c50fd85d42daadacc1e1.
The associated formal run reached the frontend, but that result is only a
startup-reachability observation; it cannot validate the corrupted slices as
production files. The corrected splitter seeds offsets after the BOM and
records the no-drift invariant. The byte-exact candidate above still timed
out, so the old apparent GREEN must not be used to justify a split patch.

## Offline implementation impact if a future exact split becomes GREEN

No implementation is applied by this audit. If a future, byte-exact split
passes the acceptance arm, the minimum coherent patch is:

### 1. Generator and generated-output contract

Change mod_zhongguo_style/tools/gen_361_workforce_endgame_runtime.py so the
single render_effects payload is deterministically partitioned at complete
top-level blocks (preferably from the generator's section list, with a strict
brace-balanced fallback). Emit two uniquely named .txt files, each with a BOM
and generated header; preserve the event file and nine localization files.
The mounted/release output must contain the two parts and no old monolith, or
the builder must explicitly reject a tree containing both.

Add a parity assertion that:

* all 324 block names and per-block hashes occur exactly once across A+B;
* each part is brace/quote balanced and BOM-valid;
* removing the second header and concatenating bodies reproduces the
  monolithic renderer byte-for-byte (or by an explicitly documented canonical
  normalization); and
* no duplicate scripted-effect definition is present when both parts are
  loaded.

### 2. Readers and static tests

Update the fixed single-file readers/constants in:

* mod_zhongguo_style/tools/test_zg361_workforce_endgame_runtime.py (output
  count, path allowlist, BOM/braces, route-C path set, and a shared
  read-concatenated-parts helper);
* mod_zhongguo_style/tools/test_zg361_phase2_central_runtime.py;
* mod_zhongguo_style/tools/test_zg361_workforce_exit_fact.py.

Extend tools/test_phase2_workforce_block_segments.py with the BOM-offset and
exact recomposition regression (the current utility test is disposable until
its owner commits it). Search-driven review should also check loader-stage
fixture strings in tools/test_zg361_phase2_loader_stage.py; its event path is
unchanged, so no edit is needed unless a new assertion names an effect file.
The readiness data and mechanism ledger mostly cite generator/spec paths, not
the generated filename, but must be regenerated or reviewed if their output
inventory changes.

### 3. Projection catalogs and release projection

Regenerate, rather than hand-edit, every disposable catalog that currently
contains the monolith row:

* _runtime/phase2-direct-union-v2-static-closure-r1-20260903/:
  projection-callable-core.json and projection-event-core.json;
* _runtime/phase2-event-loc-manifests-20260903/:
  projection-event-core-locfanout-201.json and
  projection-event-core-locfull-261.json;
* _runtime/phase2-group-bisect-20260903/ direct-union variants,
  workforce/projection-workforce.json, and all-new/projection-all-new.json.

Replace one monolith row with two part rows, then recompute every declared
file-list/tree/source digest and the projection file count (net +1). The
core-51 manifest (tools/phase2_product_projection_core.json) does not mount
workforce and should remain unchanged. Regenerate
docs/phase2-promo/phase2-localization-fanout-manifest-2026-09-03.json with
the same two paths; its localization ownership rows remain attached to the
workforce-endgame family.

tools/zg361_phase2_product_projection.py already accepts hash-bound relative
paths generically. tools/build_mod_zhongguo_style_release.py already
allowlists recursive .txt files, but its release tests should gain an
explicit assertion that the old monolith is absent and both parts are present;
otherwise a stale generated file could silently be shipped alongside the
parts.

### 4. Human-readable references

After (and only after) a GREEN candidate, update the source/output inventory in
mod_zhongguo_style/docs/361-workforce-endgame-ck3-runtime-spec.md, the owner
line in docs/phase2-promo/phase2-group-dependency-scan-2026-09-03.md, and the
path/file tables in docs/phase2-promo/phase2-direct-union-v2-static-closure-2026-09-03.md.
Retain the monolith's source SHA as historical lineage, and distinguish it
from the two mounted release paths. Do not rewrite old run reports.

### 5. Verification order

Run the generator checks and dedicated unit tests first, then projection
manifest generation, validate_static.py, and the ZhongGuo release
reproducibility check. Only after all static checks are GREEN should the
serial CK3 control/half/exact sequence be repeated, followed by a real seed
and gameplay smoke. A startup/frontend result alone is not enough to promote
the split to fixture-live or production-live.

## Risk register

| risk | minimum mitigation |
| --- | --- |
| old monolith and parts load together, causing duplicate definitions or stale code | generator/release assertion requiring exactly A+B; projection manifests exclude the monolith |
| comments, headers, BOM, or inter-block whitespace drift during splitting | byte-level parity test and per-block SHA manifest; never use decoded offsets for byte slices |
| cross-file load order or namespace semantics differ from one file | exact pair live load plus event/seed smoke; retain deterministic A-before-B names |
| stale loc/projection catalogs silently mount the old path | regenerate all catalogs and verify file-list/tree digests; reject stale source SHA |
| the current RED is misread as evidence for another split patch | preserve this report as a failed attempt and keep native/provider readiness RED |
| larger file count changes release or localization fan-out assumptions | update count assertions and run deterministic release/loc audits before CK3 |

Current disposition: corrected exact split is a failed diagnostic, not a
canonical change. Continue investigating the Total881 broad-load stall and
cross-file dependency boundary; do not implement the inventory above until a
new exact candidate has a genuinely GREEN history-complete run.
