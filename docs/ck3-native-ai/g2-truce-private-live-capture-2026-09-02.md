# G2 private truce live capture (2026-09-02)

This is the single bounded paused exact-build follow-up for the `GEN-034`
`evaluated_days` gap. It classifies the production reader failure before the
existing output reset; it does not change the public terms schema, readiness,
offsets, or any termination action.

## Frozen inputs and offline gate

- Parent source baseline: `09f21c8958d9f880d4993c69ce967abc88bdb175`.
- CK3: `1.19.0.6`; `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- Checkpoint SHA-256:
  `60108A5DA03DC3A8315A3E79897D9CF2F49763910A8AA15A462E7DD0B6AAF164`.
- Driver-state SHA-256:
  `4FB901C77AF6D95A05EAB2B0E900AE2E07A652B4C14729835DECB69FC8CFF57E`.
- Requested frame: CharacterID `29829`, WarID `50331699`,
  `date_raw=53223936`.
- `open_kaishek` was bound to clean main
  `17caa288eb980aab0b652358e9e94a9901131619`; CLI JAR SHA-256
  `421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
  The `ck3-war-days-trigger-11906` parser/validator preflight was GREEN while
  IR/runtime and root scan were explicitly skipped. Artifact:
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluator-private-capture-20260902T1645\open-kaishek-preflight.json`,
  SHA-256
  `DC3A2FC7216531BD74795788859DD418E11702E2F1B5F4D621D92CE0EBD6F058`.
  This is schema-only offline evidence (`ck3_started=false`), not CK3 live
  evidence.

## Private capture boundary

The production DLL still excludes the capture by default. The one-off
candidate was built with the explicit CMake option
`XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1=ON`; the capture additionally
requires `XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH` at runtime. It appends one
private JSONL row after the observer and context destruction but before the
production failure path clears the observation. No row is serialized through
MCP, and no public header, wire key, readiness bit, action route, or native
offset changes.

The fresh MSVC build passed the focused
`xar_ck3_native_bridge_game_access_fixture` (`1/1`). Candidate identities:

- `xar_ck3_bridge.dll` SHA-256
  `4C8D2C001B8CFADCA8D0ADB4D40353466C4D1EED965F5D11C96DFE573E1FA9CF`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `8789020EC1584E717388CBEAA7CE711F3CE3DAB6D5993976A8A9AD3DB03CB108`.

## Single live result

The retained runner report is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-evaluator-private-capture-20260902T1645\live\report.json`,
SHA-256
`31377779207957E3D18D7260945F5CD933DCCC497F2C1844A95D5CC01F02421E`.
The private sidecar is `g2-truce-private-capture.jsonl` beside that report,
SHA-256
`47514E299D87F6878229115BB60897F5E23FA28DACEE81937619D21A44D268EF`.

The exact-build, paused frame, character, date, concrete
`query-war-termination-terms-v1-50331699` capability, and same-frame query
identity all passed. Both allowed read-only terms queries returned the same
four-domain payload. Both private rows also agreed:

- `failure_code=9`, `failure=root_shape_drift`;
- `pointer_shape_verified=false`;
- `evaluated_days=-1` and `evaluator_double_read_stable=false`;
- `expiry_observable=false`;
- `context_destroyed=true`.

This proves the current reader exits inside the loaded attacker-defeat tree
shape traversal before invoking the duration evaluator. It does not prove a
duration or expiry value. No time advance or surrender, white-peace, enforce,
or other mutation command was sent. Cleanup was GREEN
(`shutdown_ok=true`, `tree_gone=true`, `driver_closed=true`) and the immutable
checkpoint/driver hashes were unchanged.

## Readiness and next entry

`evaluated_days_observable=false`, `truce_ready=false`,
`decision_ready=false`, and `GEN-034=unresolved` remain correct. The four
previously observed terms domains remain production-live read-only primitives;
expiry, generic war-bound loss, campaign/budget/white-peace comparison,
decision, typed action, and postcondition remain unavailable.

Do not replay this checkpoint with the same undifferentiated reader. The next
smallest entry is a private, staged loaded-tree shape capture that identifies
which `ResolveUniqueTruceNode` check returns `root_shape_drift` and records the
corresponding observed vtable/count/capacity value. It must again be
OFF-by-default, run after an `open_kaishek` preflight, preserve the public v1
wire, and issue no war-termination mutation. Only new exact-build evidence may
justify an offset or shape-contract change.

## Staged loaded-tree follow-up

The next bounded follow-up used parent baseline
`2c64c420666f0b0adacad783f732bcef7545e884` and the same frozen CK3,
checkpoint, driver state, CharacterID, WarID, and paused date. The
OFF-by-default candidate split every `ResolveUniqueTruceNode` read and
comparison into a named private stage while preserving the production return
codes and public wire. It recorded actual vtables, counts, and capacities only
in the private JSONL sink.

The required `open_kaishek` gate again bound clean main
`17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The `ck3-war-days-trigger-11906` parser/validator preflight was GREEN; artifact:
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-staged-shape-capture-20260902T165942\open-kaishek-preflight.json`,
SHA-256
`5FB98B7BD312F97EB695BDA1DD8735AE9362DC20FB0F0752561211AFF053DB08`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `0FDAF90717B49E573CB39A00BB4B7FA8BF08F5DCF33EF8F8A0182792F762329B`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `B7909865ED03E6DD4E905CB7E4797341312CE16F8DA27ED8888AE3D864FE8779`.

The single live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-staged-shape-capture-20260902T165942\live\report.json`,
  SHA-256
  `0DE94D78563A2A21256E9F28FFA87D445E4754AE3FE5688834010450CE336E06`;
- private JSONL beside it, SHA-256
  `D93DDF01465EED6F5F8B660276E22658B848ABA981D39DA88EFFA6832E748A28`.

Both captured rows are identical and identify the first failed check as
`root_capacity_mismatch`. The loaded root vtable RVA is `0x44CF030`, exactly
matching the frozen `Jomini::Effect` vtable, and vtable slot 11 is non-null.
The actual root vector is `capacity=13, count=12`; the stale reader contract
expects `capacity=19, count=14`. All three values were read before the
comparison, so the `count=12` evidence remains valid even though capacity is
the first named failure. Traversal correctly stopped before dereferencing the
hard-coded child index; no downstream scripted/template/hidden/context/truce
shape was claimed. The duration evaluator was not invoked and both rows remain
`evaluated_days=-1`, `pointer_shape_verified=false`, and
`expiry_observable=false` with `context_destroyed=true`.

The runner is RED only because the public paused double-sample semantic proof
still cannot pass without duration. Cleanup is GREEN (`shutdown_ok=true`,
`tree_gone=true`, `driver_closed=true`), no war-termination mutation or time
advance was sent, and the source checkpoint/driver hashes remain unchanged.
Focused validation passed the private source contract (`3/3`) and the native
game-access fixture.

This narrows the next reverse entry: enumerate the 12 actual root children in
a private capture, record their vtables, and locate a unique
`scripted_effect_vtable` child before changing the stale `19/14/index 9`
contract. Do not blindly replace constants from this one boundary and do not
repeat either prior undifferentiated probe. Public truce, expiry, decision, and
action readiness remain unchanged; `GEN-034` is still unresolved.

## Root-child enumeration follow-up

A fresh branch from parent baseline
`4dc8b650a0056f31afb56880c6ff1d3f22702097` added a second private-only
stage before the stale root capacity gate. It uses the runtime vector bounds,
caps collection at 16 children, and records every child vtable plus the number
and last index of matches to the exact-build scripted-effect vtable. The
production `19/14/index 9` contract, public wire, readiness, and all action
paths are unchanged.

The focused private source contract passed `4/4`; the native game-access
fixture and fresh instrumented MSVC build also passed. The required offline
gate bound `open_kaishek`
`17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The `ck3-war-days-trigger-11906` preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-root-child-capture-20260902T171309\open-kaishek-preflight.json`,
SHA-256
`614026B2BB82805324323083CF2CD5EDD372707BB86A9E72954FA321C4E307ED`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `E4991667AA7B34620A9103B98B3099931DEDC1571831C729559BB47F68311BB9`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `728FDA6F9A995FB52D818909C6E40546CCFD1E0D36F15979E383C646CBADA7A8`.

The single paused live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-root-child-capture-20260902T171309\live\report.json`,
  SHA-256
  `1E24C2B4A1DD298DA3D8AC8EDF9360836A2E71724BB967D12621AFF8689367C7`;
- private JSONL beside it, SHA-256
  `83EAD5659D71E6877EFCB1641EA319B371C5E623FCA76442558BD8FFF30AE93E`.

Both rows are identical and report `root_child_capture_status=complete`,
`capture_limit=12`, `completed=12`, and no failed index. In order, the child
vtable RVAs are:

```text
0: 0x44D27B8   1: 0x44D27B8   2: 0x44DF210   3: 0x44D1E18
4: 0x44D27B8   5: 0x444B548   6: 0x44CF0F8   7: 0x44CF0F8
8: 0x44D27B8   9: 0x44CF0F8  10: 0x44CF0F8  11: 0x44CF0F8
```

The exact scripted-effect vtable RVA `0x44CF0F8` therefore has five matches,
at indices `6, 7, 9, 10, 11`; vtable identity alone does not locate a unique
truce script child. `root_scripted_match_count=5` and the stored
`root_scripted_match_index=11` is only the last match, not a uniqueness claim.
The attempt consequently remains at the same expected
`root_capacity_mismatch` return and never evaluates duration.

This is a useful negative result and closes the vtable-only hypothesis. The
next smallest distinct private capture is limited to those five candidate
children: record each selector count, template pointer/vtable, and only enough
default subtree shape to distinguish the unique `cadd_truce` script. Do not
repeat root enumeration and do not promote index 9 merely because it was the
old hard-coded value. Cleanup and source invariants were GREEN, no mutation or
time advance was sent, and `GEN-034` readiness remains unchanged.

## Five scripted-candidate shape follow-up

A fresh branch from parent baseline
`9b8bd246247d61bf0c3233d38c45477e9a4d5fd4` added a distinct private
capture for only the five vtable-matched root indices `6/7/9/10/11`. For each
candidate it records selector count, template pointer/vtable, default-effect
pointer/vtable, and the default vector pointer/capacity/count. It neither
changes nor bypasses the production `19/14/index 9` gate.

The focused private source contract passed `5/5`; the native game-access
fixture and fresh instrumented MSVC build passed. The offline gate again bound
`open_kaishek` `17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR
SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The GREEN `ck3-war-days-trigger-11906` preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-scripted-candidate-capture-20260902T173317\open-kaishek-preflight.json`,
SHA-256
`E3A8AA2A469D65F7145B5DDBE6BFBF06EABEB67376B14A4BC68B9C972BC6D234`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `99C4462D1FD5AADB6BBFDAE7EDD779C84570B2CA9F277C981C24C6F42ED9D743`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `FFC5739AAAB2E9A99654BC62B0D03C1C6C05F3CC956C996C054A48B56ADF8DE3`.

The single paused live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-scripted-candidate-capture-20260902T173317\live\report.json`,
  SHA-256
  `A2F1B623AF5E1FB5B636656F3C1CE905FDC655E56B48A4FA5DB2B654CFEEB8C0`;
- private JSONL beside it, SHA-256
  `D5E538CD4329E166991ACFDF0ED78561A1A7F42C5C4DD6D5D231D66A3679F53B`.

Both rows are identical. The five candidate results are:

| Root index | Selector count | Template vtable RVA | Default vtable RVA | Default capacity/count | Capture status |
| --- | ---: | --- | --- | --- | --- |
| `6` | `8` | `0x44DCD38` | none | none | `default_effect_null` |
| `7` | `0` | `0x44DCD38` | `0x44CF030` | `4/4` | `complete` |
| `9` | `0` | `0x44DCD38` | `0x44CF030` | `1/1` | `complete` |
| `10` | `0` | `0x44DCD38` | `0x44CF030` | `1/1` | `complete` |
| `11` | `0` | `0x44DCD38` | `0x44CF030` | `2/2` | `complete` |

The stale expected default shape `6/5` matches none of them
(`scripted_semantic_match_count=0`). This disproves the old downstream shape
for the current loaded tree. The minimal capture excludes indices 6, 7, and
11 from sharing the same default vector shape, but indices 9 and 10 remain
indistinguishable at `selector=0`, correct template/default vtables, and
`capacity/count=1/1`. The old hard-coded index 9 is not sufficient evidence to
name CAddTruce.

The next smallest distinct entry is therefore restricted to indices 9 and 10:
record the sole default child's vtable and the minimum safe nested shape needed
to distinguish their effect types. Do not repeat the five-candidate prefix,
promote the old index by assumption, or alter the production root contract
before that evidence. The runner remains expected RED before duration;
cleanup/source invariants were GREEN, no mutation or time advance was sent,
and `GEN-034` readiness remains unchanged.

## Indices 9/10 sole-child follow-up

A fresh branch from parent baseline
`3d88d2af49431004b28e1b5d22ba99255e34b844` narrowed the private
instrumentation to root indices `9/10` only. The prior 12-child enumeration is
not replayed. For each candidate it reads the sole default child's vtable,
common effect vector capacity/count, and its first nested child's vtable. It
also tests only the already-frozen `Hidden(1/1) -> Context` prefix; no new
production identity or offset is inferred.

The focused private source contract passed `5/5`; the native game-access
fixture and fresh instrumented MSVC build passed. The offline gate bound
`open_kaishek` `17caa288eb980aab0b652358e9e94a9901131619` and CLI JAR
SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
The GREEN `ck3-war-days-trigger-11906` preflight artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-sole-child-20260902T174428\open-kaishek-preflight.json`,
SHA-256
`34D8F588FEB0FD1B289532F9BF5DBF86F89F0DFD68ACD7AA31A735409BC28C40`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `06247E00A4282CE8FBFF8B7500E58624EC913EA1E5FEA6E1911D65F0CE8251D0`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `09AE215DC57B0CE6B885083BED909AB2234E422506C230B8EB93058BCF48F7C9`.

The single paused live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-sole-child-20260902T174428\live\report.json`,
  SHA-256
  `3E1F6139FF8FEFBDAD7DC0DD11C823F2A8D365ED9C20B304A90481BCE9F992B7`;
- private JSONL beside it, SHA-256
  `55769B6FC23443A0B50EF070A877E18DE7C3F18C3F5C3700B5119F5E26D70322`.

Both rows are identical and both candidates completed:

| Root index | Sole-child vtable RVA | Sole-child capacity/count | Nested child 0 vtable RVA |
| --- | --- | --- | --- |
| `9` | `0x44D27B8` (frozen Context vtable) | `1/1` | `0x44D1E18` |
| `10` | `0x44D1D50` | `1/1` | `0x44D27B8` (frozen Context vtable) |

The paths are now structurally distinct, but neither matches the stale frozen
`Hidden(0x44D1C88) -> Context` prefix, so
`caddtruce_prefix_match_count=0`. The proximity of `0x44D1D50` to the old
Hidden RVA is not type evidence. Index 9 contains Context first and then an
unidentified effect; index 10 contains an unidentified effect and then
Context. This capture cannot yet prove which path reaches CAddTruce, so the
result is an explicit NO-GO rather than an index promotion.

The next smallest entry is limited to the exact Context node already observed
on each path: read its `scope_count`, common `children/capacity/count`, and
child-0 vtable. A unique child-0 match to the frozen Truce vtable
`0x4461CA8` would identify the CAddTruce path; absence on both paths requires a
new ledger entry rather than a broader walk. Cleanup/source invariants were
GREEN, no mutation or time advance was sent, and production/readiness remain
unchanged.

## Exact Context child-0 follow-up

A fresh branch from parent baseline
`062548173d717b6bcc8234cfb3bee0df1eb7be4c` retained only root indices
`9/10` and selected the exact Context node already observed on each path. The
private capture reads Context `scope_count`, children/capacity/count, child-0
vtable, and that child's common capacity/count. It computes a duration address
only after an exact match to the frozen Truce vtable; it never calls the
duration evaluator.

The focused source contract passed `5/5`; the native game-access fixture and
fresh instrumented MSVC build passed. The initial required gate bound
`open_kaishek` `17caa288eb980aab0b652358e9e94a9901131619`; its GREEN artifact
is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-context-child-20260902T180601\open-kaishek-preflight.json`,
SHA-256
`83079F60D4DC19E0542E14B413CFBD1DD1947F4E08CA6719B4F274F4487EEFEC`.
Before live, current support advanced to `open_kaishek`
`425514e2e937bb829b2415f9da7870609e9c736f` with the same CLI JAR SHA-256
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
Its already-completed equivalent G2 Context-path preflight was bound without
repeating the gate:
`Z:\ck3_mod_rewrite_process_assets\zg361\open-kaishek-support-20260902T1807\g2-context-path-preflight.json`,
SHA-256
`BBEEE5782733D09A0A3A66F6B9A6F2448693E704E77FA504CD6DF4A17E134792`.
Candidate identities were:

- `xar_ck3_bridge.dll` SHA-256
  `A8EB37CC769AC9DC212A91FD2DF9BC8237406D5C2E4A8A4F2E8A0DB2707ED845`;
- `xar_ck3_bridge_injector.exe` SHA-256
  `70187EC7A01898017F7C9925EE429F15BFC5F55A36428904D65E8C663E0CE00B`.

The single paused live attempt retained:

- report
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-context-child-20260902T180601\live\report.json`,
  SHA-256
  `D2C82BFB70113F51418B0E1F1195D33550955E4513529587DB53ECCAE6E8FBCC`;
- private JSONL beside it, SHA-256
  `47519D81A5EF6D902A218F50017609F44EDE6EFE1E223F5299406575AB4B48AA`.

Both rows are identical and both Context captures completed:

| Root path | Context depth | Context scope/capacity/count | Context child-0 vtable RVA | Child-0 capacity/count |
| --- | ---: | --- | --- | --- |
| index `9` | `0` | `1 / 1 / 1` | `0x44D1E18` | `1/1` |
| index `10` | `1` | `1 / 1 / 1` | `0x41E36D0` | `6/6` |

Neither child-0 matches the frozen Truce vtable `0x4461CA8`, so
`truce_vtable_match_count=0` and no duration address was produced. The paths
are more sharply separated, but CAddTruce is still not identified; this is a
NO-GO, not evidence to change the stale production tree contract.

The next smallest distinct entry follows only the shapes just observed:
index 9 may read the sole child under `0x44D1E18(1/1)`; index 10 may enumerate
only the six children under `0x41E36D0(6/6)`. Record child vtables and stop as
soon as an exact `0x4461CA8` match is classified. Do not revisit other root
indices or repeat Context-prefix fields. Cleanup/source invariants were GREEN,
no mutation or time advance was sent, and public/readiness remain unchanged.
