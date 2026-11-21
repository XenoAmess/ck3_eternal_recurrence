# Superman Qiang: current hotfix input qualification

Machine: `desktop-3fevhd2-1c74096080`. This private source candidate targets CK3
1.21.0.3 / Steam build 26785313 / EXE SHA-256
`859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28`.
Product version remains 1.2.1, canonical Workshop item 3812991990. No runtime
gameplay rule, product inventory, descriptor, localization, source hook,
insertion, event priority, inline dependency or fixture predicate changes.

The nine inputs were absent from the earlier 292-file selection. That selection
therefore could not establish whether these inputs changed. The independent
[current audit](2026-11-22-florin-121003-source-audit.json) now records every
actual consumer source file, full SHA, size and stable file identity. All nine
full-file SHAs exactly match the retained
[266 audit](2026-11-19-florin-source-audit.json). All eleven selected definitions
and ten inline helper definitions also match their retained original bytes and
AST. The existing source verifier checked the complete local-name inventories
for all eight encounter files against the actual installation.

Only the reviewed identity constants in `product.py` and `runtime_data.py`, and
the two vanilla-hook source metadata files, advance to the actual hotfix.
The generator changes eleven controlled projection headers from `CK3 1.21.0`
to `CK3 1.21.0.3`; removing that comment-only version difference restores each
old runtime file byte for byte. The other 24 of 35 runtime files remain exact.
The eleven projection ASTs remain equal, and inverse projection still restores
the pinned original definitions. The prior Temujin TARGET/REASON wrapper
migration remains intact; this hotfix introduces no new wrapper change.

The actual incremental checks were:

| Check | Actual result |
| --- | --- |
| Existing generator against the current installation | 0, 1.922s |
| Existing generated parity CLI against current source | 0, 1.761s |
| Existing static validator, current nine source files and full EXE | GREEN / zero errors, 4.042s |
| Existing provenance/schema negatives and two renderer checks | 19 tests, zero skips/failures/errors, 2.137s |
| Stale 266 game-version and EXE metadata, separately | Both rejected by the existing source contract |

The validator checked all 33 generated outputs, the 35-file inventory, nine
languages with 25 keys each, structural syntax, duplicate definitions and the
seven-attribute ledger constraints. This is structural/source qualification,
not the Java generic parser or engine grammar qualification. The two Python
leaves restore exactly to their old bytes after reversing only the reviewed
identity literals; no Python algorithm changes. The existing 62 runtime and
16 release regressions and earlier double build remain their historical 266
qualification; they were not rerun as an unrelated full suite.

Actual commands, stdout/stderr, source pins, full static report, focused test
log and negative inputs are retained in
`D:/ck3-state/upgrade-20261118/superman-florin267-input-source-a01/`.
`qualification-final.json` binds the outputs. No Game, Steam, Native live call,
build/package/tag, primary write or Git mutation occurred. This candidate is
not a formal release or current engine business PASS.

## Next actual acceptance and retained boundaries

The existing shared `source-health-1-1` case remains the shortest bounded
business route: maximum four natural days, the original 20 health predicates,
a real physical baseline before the original `sxat.2` begin choice, actual
after-state SAVE/readback, and the real trait/seven-net-attribute presentation.
The producer queues setup on day one, baseline on the following day, then
verification after the real begin choice. The fixture source, schedule,
thresholds and case remain unchanged by this unit. A START/BASELINE marker is
never the twenty-case result.

Both health and natural-simulation fixtures currently register through
`on_game_start_after_lobby`. Their new-game callback does not by itself supply
a Saved-v3 bootstrap. If Root chooses an existing Saved source, a separately
explicit fixture-only Saved adapter must preserve the original setup and
predicates before the scene is sealed. This unit does not silently add one or
call the legacy 1.20 launcher. No new whole-SDK gate is required.

The original natural-simulation case remains its six-cell, maximum-35-day
contract with twelve real character identities, three independently saved
phases and a real monthly callback. Its distinct subsequent zero-day cold
process compares exact experience, month epochs, partner lists and identity.
Neither a source injection nor this input qualification supplies monthly or
cold credit. The historical R0030/R0031 bounded successes remain on
1.20.0.4 / build25734779 / EXE98702, with their original raw/error boundaries.
The historical R19--R22 targeted20/cold/UI successes remain on 1.20.0.3 / EXE94b553.
The source-only Florin 266 qualifications retain their original scope.
These are preserved evidence, not newly observed 267 business results.

The current curated SDK pairs do not qualify the product-specific `sxat.2/.4`
or `sxanf.2/.6` option routes, the View Sexual Experience interaction/notification,
or the trait/seven-net-attribute presentation. Those are specific future
read/action needs; ordinary Core/Date/SAVE/Exit capability does not prove them.
Use actual runtime player and fixture reference IDs, not old 31254/65831 IDs.
Health raw/scale, base health, six skill arrays, signed balances/modifiers,
experience and real before/after physical origins must retain their original
readback distinctions. A current checkpoint/parser path must be bound to its
actual output rather than an old SDK-directory example.

The unresolved notification repetition issue, earlier failures, and untested
clinical/forced-pregnancy/twin/pilgrimage/narrative branches remain recorded.
This nine-input hotfix review neither erases those limits nor adds those old
uncovered branches as a new complete migration matrix.
